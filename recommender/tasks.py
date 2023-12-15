import os

from celery import Celery


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery(
    "proj",
    broker="amqp://guest@localhost//",
    backend="rpc://",
)


# define a task for scraping the image from musinsa
@app.task(queue="scrape")
def scrape_reviews(product_id, max_photos=200):
    """
    product_id를 상품ID로 갖는 상품의 리뷰를 크롤링하는 함수. 아직 DB에 저장하지 않음
    musinsa-scraper.scraper 코드를 조금 손봐서 구현

    return:
        [
            {
                "proudct_size": "L",
                "content": "옷 좋아요~~",
                "gender": "M",
                "height": 170,
                "weight": 70,
                "image": str()
            },
            ...
        ]
    """
    # import the modules that require the pipenv environment
    import requests
    from bs4 import BeautifulSoup
    from scraper.scraper import parse_reviews, to_size_dict_list

    try:
        int(product_id)
    except (ValueError, TypeError):
        raise ValueError(f"malformed product ID {product_id}")

    BASE_URL = "https://www.musinsa.com/app/goods/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76"
    }
    # make GET request to product page
    url = BASE_URL + str(product_id)
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    html = response.content
    soup = BeautifulSoup(html, "html.parser")
    # read size table
    size_table = soup.find("table", id="size_table")
    size_list = to_size_dict_list(size_table)

    # save size table as json
    if size_list is None:
        raise ValueError(
            f"size table malformed for product with product ID {product_id}"
        )

    # parse reviews
    size_names = [it["size"] for it in size_list]
    reviews = parse_reviews(product_id, size_names, max_photos)

    return reviews


# define a task for running the keypoint estimation on the image
@app.task(queue="estimate")
def estimate_mesh(reviews_obj):
    """
    load MultiPerson model

    scrape_reviews()가 리턴하는 객체에 담긴 리뷰들에 대해 mesh estimation 진행
    multiperson/demo.py의 코드 이용

    Input:
        - reviews_obj: list of python dict

    return: list of python dict
        [
            {
                "proudct_size": "L",
                "content": "옷 좋아요~~",
                "gender": "M",
                "height": 170,
                "weight": 70,
                "image": ??,

                "betas":  , # python list (10,)
                "meshed_image": meshed_image_name , # 원본 이미지에서 추출한 mesh
                                                                # meshed_image_name = str(uuid.uuid4()) + ".png"
                # -> /home/myungjune/projects/multiperson/output/maifit_mesh
            },
            ...
        ]
    """
    print(f"estimate_mesh called with {len(reviews_obj)}")
    n = min(3, len(reviews_obj))
    print(f"head {n} reviews: ")
    for i in range(n):
        print(reviews_obj[i])
    print()

    # import the modules that require the conda environment
    from recommender.body_shape_estimator import BodyShapeEstimator

    bse = BodyShapeEstimator()

    for review in reviews_obj:
        image_path = review["image"]

        assert os.path.exists(image_path)

        est = bse.extract_betas_and_mesh(image_path)
        # append into review
        if est is not None:
            if "betas" in est:
                review["betas"] = est["betas"]
            if "meshed_image" in est:
                review["meshed_image"] = est["meshed_image"]
        # if est is None -> review will not have betas, and meshed_image

    return reviews_obj


# define a task for saving the scraped image and the mesh estimation result to the database
@app.task(queue="scrape")
def save_result(reviews_mesh_obj, product_id):
    """
    estimate_mesh()의 결과를 장고ORM 이용해 DB에 저장
    """
    # import the modules that require the pipenv environment
    import uuid
    import pickle
    import tempfile
    import django
    from django.core.files import File
    from recommender.models import Good, Review

    # load the django settings
    django.setup()
    # load the product instance from the database
    try:
        good = Good.objects.get(id=product_id)
    except Good.DoesNotExist:
        raise ValueError(
            f"trying to save reviews of good with id {product_id}, which does not exist."
        )

    # save the image content and the result content to the database
    for data in reviews_mesh_obj:
        if "betas" not in data or "meshed_image" not in data:
            # remove temporary file 'review image' if body shape estimation failed
            if os.path.exists(data["image"]):
                os.remove(data["image"])
            continue

        review = Review()
        review.good = good
        review.product_size = data["product_size"]
        review.content = data["content"]
        review.gender = data["gender"]
        review.height = data["height"]
        review.weight = data["weight"]

        with open(data["image"], "rb") as f:
            review.image.save(str(uuid.uuid4()) + ".jpg", File(f))

        # save the betas list as a pickle file and have inferred_model reference it
        # open a temporary file in write binary mode
        with tempfile.NamedTemporaryFile() as tmp:
            # dump the betas list to the temporary file
            pickle.dump(data["betas"], tmp)
            # assign the temporary file to the inferred_model field, without specifying the path or name
            review.inferred_model.save(str(uuid.uuid4()) + ".pkl", File(tmp))

        with open(data["meshed_image"], "rb") as f:
            review.overlayed_image.save(str(uuid.uuid4()) + ".jpg", File(f))

        # remove temporary files: review image, meshed image
        if os.path.exists(data["image"]):
            os.remove(data["image"])
        if os.path.exists(data["meshed_image"]):
            os.remove(data["meshed_image"])


@app.task(queue="estimate")
def estimate_mesh_image(image):
    """
                load MultiPerson model

    유저 사진에 대해 mesh estimation 진행하고 그 결과를 리턴

    param:
        image:  # path

    return: # python dict
        {
            "betas": # 앞과 같음
            "meshed_image": # 앞과 같음
        }
    """

    from recommender.body_shape_estimator import BodyShapeEstimator

    bse = BodyShapeEstimator()
    if not os.path.exists(image):
        return None

    est = bse.estimate(image)
    if est is None:
        return None
    else:
        return {"betas": est["betas"], "meshed_image": est["meshed_image"]}


@app.task(queue="scrape")
def save_client(user_mesh_obj, client_id):
    """
    estimate_mesh_image()의 리턴값을 받아 DB에 저장
    """
    import uuid
    import pickle
    import tempfile
    import django
    from django.core.files import File
    from recommender.models import Client

    # load the django settings
    django.setup()

    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        raise ValueError(
            f"trying to save client with id {client_id}, which does not exist."
        )
    if user_mesh_obj is None:
        # if body shape estimation failed
        return None

    with tempfile.NamedTemporaryFile() as tmp:
        # dump the betas list to the temporary file
        pickle.dump(user_mesh_obj["betas"], tmp)
        # assign the temporary file to the inferred_model field, without specifying the path or name
        client.inferred_model.save(str(uuid.uuid4()) + ".pkl", File(tmp))

    with open(user_mesh_obj["meshed_image"], "rb") as f:
        client.overlayed_image.save(str(uuid.uuid4()) + ".jpg", File(f))

    # remove temporary file: meshed image
    if os.path.exists(user_mesh_obj["meshed_image"]):
        os.remove(user_mesh_obj["meshed_image"])

    return 0

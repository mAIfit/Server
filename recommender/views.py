from rest_framework import mixins
from rest_framework import generics
from rest_framework.response import Response

from recommender.models import Good, Client
from recommender.serializers import GoodSerializer
import subprocess
import threading
from PIL import Image
from rest_framework.parsers import MultiPartParser, FormParser


def scrape_item(product_id: int) -> dict:
    # TODO
    # This is the function that scrapes the basic information of a good
    # The function should return a dictionary with keys "image", "brand", and "name"
    return {
        "image": f"https://example.com/images/{product_id}.jpg",
        "brand": f"Brand {product_id}",
        "name": f"Product {product_id}"
    }

def scrape_reviews(product_id: int) -> None:
    # TODO
    # This is the function that scrapes the reviews of a good
    # The function should save the reviews to the database
    subprocess.run(["python", "scraper", "reviews", str(product_id)])


class GoodView(generics.GenericAPIView):
    queryset = Good
    serializer_class = GoodSerializer

    lookup_url_kwarg = "good_id"

    def get(self, request, good_id):
        # TODO: 상품 정보와 리뷰 scraping 시작
        # 이미 존재하는 상품은 다시 scraping 하지 않음 (QuerySet API filter().exists()로 존재여부 확인)
        # 상품 정보 scraping -> DB에 저장
        # 상품 리뷰 scraping 시작 (async)

        good_data = scrape_item(good_id)
        good, created = Good.objects.get_or_create(id=good_id, defaults=good_data)
        if created:
            review_thread = threading.Thread(target=scrape_reviews, args=(good_id,))
            review_thread.start()
        
        serializer = self.get_serializer(good)
        return Response(serializer.data)


def check_image(image) -> dict:
    # TODO
    # This is the function that checks the validity of the received image
    # The function should return a dictionary with keys "is_valid", "invalid_reason", and "bounding_box"
    return {
        "is_valid": True,
        "invalid_reason": None,
        "bounding_box": {
            "left": 5,
            "top": 20,
            "right": 120,
            "bottom": 140
        }
    }

def crop_and_format(image, bounding_box) -> Image:
    # TODO
    # This is the function that crops and formats the image
    # The function should return an Image object
    # For simplicity, I will just crop the image with the bounding box
    return image.crop((bounding_box["left"], bounding_box["top"], bounding_box["right"], bounding_box["bottom"]))

def infer_image(image_path) -> None:
    # TODO
    # This is the function that runs the system command to infer the image
    # The function should save the inference result to the database
    subprocess.run(["python", "infer", "image", image_path])

class ClientView(generics.GenericAPIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        # TODO: check correctness of request.data.get("image")
        gender = request.POST.get('gender')
        height = request.POST.get('height')
        image = request.FILES.get('image')

        image_data = check_image(image)
        if not image_data["is_valid"]:
            return Response({
                "is_valid": False,
                "invalid_reason": image_data["invalid_reason"],
                "id": None,
                "bounding_box": None
            })
        
        formatted_image = crop_and_format(image, image_data["bounding_box"])
        client = Client.objects.create(gender=gender, height=height, image=image, formatted_image=formatted_image)

        infer_thread = threading.Thread(target=infer_image, args=(client.image.path,))
        infer_thread.start()

        return Response({
            "is_valid": True,
            "invalid_reason": None,
            "id": client.id,
            "bounding_box": image_data["bounding_box"]
        })


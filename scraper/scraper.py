import os
import uuid
from bs4 import BeautifulSoup
import requests

def parse_review_page(review_list, size_names, start_idx, max_photos):
    photo_idx = start_idx
    reviews = []
    for review_div in review_list:
        # read body size info
        body_size_tag = review_div.find("p", "review-profile__body_information")
        if body_size_tag is None:
            # review with hidden body size
            continue

        body_size_info = str(body_size_tag.text).split("·")
        body_size_info = [str(sz).strip() for sz in body_size_info]
        if (
            len(body_size_info) != 3
            or body_size_info[0] not in ["남성", "여성"]
            or body_size_info[1].find("cm") == -1
            or body_size_info[2].find("kg") == -1
        ):
            # malformed body size
            continue

        # read product option info
        product_option_tag = review_div.find("span", "review-goods-information__option")
        if product_option_tag is None:
            # malformed option info
            continue

        # check product option valid
        product_size = str(product_option_tag.text).strip()
        if len(product_size) == 0 or product_size not in size_names:
            continue
        
        # add review info
        review_content = str(review_div.find("div", "review-contents__text").text).strip()

        # save only first photo
        img_list_tag = review_div.find("ul", "review-content-photo__list")
        if img_list_tag is None: 
            # review with no image
            continue
        img_tag = img_list_tag.find("img") # first image of review

        # download review image
        img_url = "https:" + str(img_tag["src"])
        r = requests.get(img_url)
        if r.status_code != 200:
            print(f"get image request failed on url: {r.url}")
            print(f"response code: {r.status_code}", end="\n\n")
            return ([], photo_idx)

        img_content = r.content
        img_dir = os.getcwd()
        temp_dir = os.path.join(img_dir, "temp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        img_name = str(uuid.uuid4()) + ".jpg"
        img_path = os.path.join(temp_dir, img_name)
        with open(img_path, "wb") as f:
            f.write(img_content)
        full_img_path = str(os.path.abspath(img_path))

        # fill in and add review_size dict
        review_size = {}
        review_size["content"] = review_content
        review_size["gender"] = "M" if body_size_info[0] == "남성" else "F"
        review_size["height"] = body_size_info[1][:-2]
        review_size["weight"] = body_size_info[2][:-2]
        review_size["product_size"] = product_size
        review_size["image"] = full_img_path

        reviews.append(review_size)
        photo_idx += 1

        if photo_idx >= max_photos:
            break

    return (reviews, photo_idx)
        

def to_size_dict_list(size_table):
    # Convert size_table into a list of size dicts
    # size dict is a dictionary with keys "name", "length", "shoulder", ...

    try:
        header_row = size_table.find("thead").find("tr")
        header_items = [str(header_row.th.text).strip()]  # "cm"

        th_tags = header_row.find_all("th", "item_val")
        header_items += [str(th.text).strip() for th in th_tags]

        size_rows = size_table.find("tbody").find_all("tr", id=False)
        size_items = []
        for row in size_rows:
            row_items = [str(row.th.text).strip()]  # "S"
            td_tags = row.find_all("td", "goods_size_val")
            row_items += [str(td.text).strip() for td in td_tags]

            size_items.append(row_items)
    except AttributeError:
        print("size_table to size_dict failed")
        print("unexpected format size_table")
        print(size_table.prettify(), end="\n\n")
        return None

    # return if header_items count != size_item count
    if len(header_items) != len(size_items[0]):
        print("size_table to size_dict failed")
        print("unexpected format size_table")
        print(size_table.prettify(), end="\n\n")
        return None

    # return if length unit is not centimeter
    if header_items[0] != "cm":
        print("size_table to size_dict failed")
        print("length unit is not 'cm'")
        return None

    # header items conversion
    conversion = {
        "cm": "size",
        "총장": "length",
        "어깨너비": "shoulder",
        "가슴단면": "breast",
        "소매길이": "arm",
    }

    # convert header to appropriate names
    converted_header_items = []
    for header_item in header_items:
        try:
            converted_header_items.append(conversion[header_item])
        except KeyError:
            print("size_table to size_dict failed")
            print(f"unexpected header item: {str(header_item)}")
            return None
        except Exception as e:
            print("size_table to size_dict failed")
            print(e, end="\n\n")
            return None

    # ret: a list of size dicts
    # size dict: a dictionary with keys "name", "length", "shoulder", ... and corresponding values
    ret = []
    for size_item in size_items:
        size_obj = {}
        for idx, h in enumerate(converted_header_items):
            try:
                if len(size_item[idx]) == 0:
                    raise ValueError
                size_obj[h] = (
                    size_item[idx] if idx == 0 else float(size_item[idx])
                )  # first item "S", "M", "L", ..., second~ item are lengths
            except ValueError:
                print("size_table to size_dict failed")
                print(f"unexpected table data item: {size_item[idx]}")
                print("expected table data item is a float", end="\n\n")
                return None
            except TypeError:
                print("size_table to size_dict failed")
                print(f"unexpected table data item: {size_item[idx]}")
                print("exepcted table data item type is a string", end="\n\n")
                return None
            except Exception as e:
                print("size_table to size_dict failed")
                print(e, end="\n\n")
                return None

        ret.append(size_obj)

    return ret

def parse_reviews(product_id, size_names, max_photos):
    # Given product_id of product, get review photo, size, contents
    url = "https://goods.musinsa.com/api/goods/v2/review/style/list"
    params = {
        "sort": "up_cnt_desc",
        "selectedSimilarNo": product_id,
        "goodsNo": product_id,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76"
    }

    reviews = []
    page = 1  # review pagination
    review_num = 0  # 'number' in review_size.json
    while True:
        params["page"] = page
        response = requests.get(url, params, headers=headers)
        response.raise_for_status()

        html = response.content
        soup = BeautifulSoup(html, "html.parser")
        review_list = soup.find("div", "review-list-wrap").find_all(
            "div", "review-list"
        )
        if len(review_list) == 0:
            break

        print(f"Parsing reviews {review_num}/{max_photos}")

        more_reviews, next_review_num = parse_review_page(
            review_list, size_names, review_num, max_photos
        )
        reviews += more_reviews
        review_num = next_review_num
        page += 1

        if next_review_num >= max_photos:
            break
    
    return reviews

def parse_item_page(soup):
    item = dict()

    option_box_tag = soup.find(
        "div", {"class": ["option_box_grey", "box_option_inventory"]}
    )
    option_div_tags = option_box_tag.find_all("div", "option_cont")

    if (
        len(option_div_tags[0].find_all("select")) != 1
        or len(option_div_tags[1].find_all("select")) != 0
    ):
        print(f"more than or less than 1 product option", end="\n\n")
        return None

    # download product image
    img_tag = soup.find("img", id="bigimg")
    img_url = img_tag["src"]
    img_url = "https:" + img_url

    r = requests.get(img_url)
    if r.status_code != 200:
        print(f"get image request failed on url: {r.url}")
        print(f"response code: {r.status_code}", end="\n\n")
        return None

    img_content = r.content
    item["image"] = img_content

    # product name
    title_span = soup.find("span", "product_title")
    if title_span is None:
        return None
    product_name = title_span.find("em")
    if product_name is None: 
        return None
    item["name"] = product_name.text

    # product brand
    product_article = soup.find("div", "wrap_product").find("ul", "product_article")
    if product_article is None:
        return None
    brand_name = product_article.find("li").find("p", "product_article_contents").find("a").text
    if brand_name is None:
        return None
    
    item["brand"] = brand_name

    return item


def parse_item(product_id):
    pid = str(product_id)

    BASE_URL = "https://www.musinsa.com/app/goods/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76"
    }
    # make GET request to product page
    url = BASE_URL + pid
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"request failed on url: {response.url}")
        print(f"response code: {response.status_code}", end="\n\n")
        return None
    
    html = response.content
    product_soup = BeautifulSoup(html, "html.parser")

    return parse_item_page(product_soup)
import subprocess
import threading

from django.shortcuts import get_object_or_404
from django.db.models import F, Value
from django.db.models.functions import Abs
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser
from PIL import Image

from recommender.models import Good, Client, Review
from recommender.serializers import GoodSerializer, ReviewSerializer


def scrape_item(product_id: int) -> dict:
    # TODO
    # This is the function that scrapes the basic information of a good
    # The function should return a dictionary with keys "image", "brand", and "name"
    return {
        "image": f"https://example.com/images/{product_id}.jpg",
        "brand": f"Brand {product_id}",
        "name": f"Product {product_id}",
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
        "bounding_box": {"left": 5, "top": 20, "right": 120, "bottom": 140},
    }


def crop_and_format(image, bounding_box) -> Image:
    # TODO
    # This is the function that crops and formats the image
    # The function should return an Image object
    # For simplicity, I will just crop the image with the bounding box
    return image.crop(
        (
            bounding_box["left"],
            bounding_box["top"],
            bounding_box["right"],
            bounding_box["bottom"],
        )
    )


def infer_image(image_path) -> None:
    # TODO
    # This is the function that runs the system command to infer the image
    # The function should save the inference result to the database
    subprocess.run(["python", "infer", "image", image_path])


class ClientView(generics.GenericAPIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        # TODO: check correctness of request.data.get("image")
        gender = request.POST.get("gender")
        height = request.POST.get("height")
        image = request.FILES.get("image")

        image_data = check_image(image)
        if not image_data["is_valid"]:
            return Response(
                {
                    "is_valid": False,
                    "invalid_reason": image_data["invalid_reason"],
                    "id": None,
                    "bounding_box": None,
                }
            )

        formatted_image = crop_and_format(image, image_data["bounding_box"])
        client = Client.objects.create(
            gender=gender, height=height, image=image, formatted_image=formatted_image
        )

        infer_thread = threading.Thread(target=infer_image, args=(client.image.path,))
        infer_thread.start()

        return Response(
            {
                "is_valid": True,
                "invalid_reason": None,
                "id": client.id,
                "bounding_box": image_data["bounding_box"],
            }
        )


def get_body_shape_difference(client, review):
    # TODO
    """
    calculates the body shape difference between the client and a review
    args:
        client: Client, review: Review
    cannot assume that the review's body shape is already calculated. run inference if the review's body shape is not yet calculated
    return:
        float that represents the difference. smaller is more similar
    """


class ReviewListView(generics.ListAPIView):
    queryset = Review
    serializer_class = ReviewSerializer
    lookup_url_kwarg = "good_id"

    # get user using user_id found in the query parameter
    # respond with 400 BAD REQUEST if user_id is not provided, or if "Client" with id=user_id is not found in the database
    # filter queryset to only the one's with height difference lte 5
    # for each review in queryset, call function get_body_shape_difference(client, review)
    # this function returns a float. annotate each review with the returned value as "difference"
    # once every object in the queryset is annotated, order the queryset as ascending order of difference
    # return queryset
    def get_queryset(self):
        good_id = self.kwargs.get(self.lookup_url_kwarg)
        client_id = self.request.query_params.get("user_id")
        if not client_id:
            raise ValidationError("user_id is required")
        client = get_object_or_404(Client, id=client_id)
        queryset = super().get_queryset().filter(good_id=good_id)
        queryset = queryset.annotate(
            height_diff=Abs(F("height") - Value(client.height))
        )
        queryset = queryset.filter(height_diff__lte=5)

        queryset = queryset.annotate(
            difference=lambda review: get_body_shape_difference(client, review)
        )
        queryset = queryset.order_by("difference")
        return queryset

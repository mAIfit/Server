from django.urls import path
from . import views

urlpatterns = [
    path(
        "goods/<int:good_id>", views.GoodView.as_view(), name="good_detail"
    ),  # 상품 scrape, 상품 정보 반환
    path("clients", views.ClientView.as_view(), name="client_list"), # 유저 저장, 유저 ID 반환
    path(
        "goods/<int:good_id>/reviews", views.ReviewListView.as_view(), name="good_reviews"
    ),  # 상품에 대한 리뷰 목록(유사 체형순), user_id 파라미터 요구
    path(
        "reviews/<int:review_id>/body_shapes",
        views.review_body_shapes,
        name="review_body_shapes",
    ),  # 리뷰에 대한 3D 모델 보기, user_id 파라미터로 요구
]

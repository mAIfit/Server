from rest_framework import serializers

from recommender.models import Good, Review, Client


class GoodSerializer(serializers.ModelSerializer):
    brand = serializers.CharField(source="brand.name")

    class Meta:
        model = Good
        fields = ["image", "brand", "name"]


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["id", "image", "height", "weight", "product_size", "content"]

class ReviewImageSerializer(serializers.ModelSerializer):
    review_overlayed_image = serializers.ImageField(source="overlayed_image")
    review_model_image = serializers.ImageField(source="model_image")
    class Meta:
        model = Review
        fields = ["review_overlayed_image", "review_model_image"]

class ClientImageSerializer(serializers.ModelSerializer):
    user_overlayed_image = serializers.ImageField(source="overlayed_image")
    user_model_image = serializers.ImageField(source="model_image")
    class Meta:
        model = Client
        fields = ["user_overlayed_image", "user_model_image"]
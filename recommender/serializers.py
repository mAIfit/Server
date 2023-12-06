from rest_framework import serializers

from recommender.models import Good, Review


class GoodSerializer(serializers.ModelSerializer):
    brand = serializers.CharField(source="brand.name")

    class Meta:
        model = Good
        fields = ["image", "brand", "name"]


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["id", "image", "height", "weight", "product_size", "content"]

from rest_framework import serializers

from recommender.models import Good

class GoodSerializer(serializers.ModelSerializer):
    brand = serializers.CharField(source="brand.name")

    class Meta:
        model = Good
        fields = ["image", "brand", "name"]
    
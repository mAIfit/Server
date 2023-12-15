from recommender.models import Client, Review
from recommender.views import get_body_shape_difference


def main():
    client = Client.objects.get(id=47)
    review = Review.objects.get(id=15)

    cosine_dist = get_body_shape_difference(client, review)
    print(cosine_dist)


if __name__ == "__main__":
    main()

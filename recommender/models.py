from django.db import models

# 무신사 상품
class Good(models.Model):
    id = models.IntegerField(primary_key=True) # 무신사의 상품ID와 동일하게 사용
    image = models.ImageField(upload_to='goods/') # 상품 이미지
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE) # brand 모델에 대한 ForeignKey
    name = models.CharField(max_length=128) # 최대 128자

# 상품의 브랜드
class Brand(models.Model):
    name = models.CharField(max_length=64) # 최대 64자

# client 모델은 고객의 정보와 3D 모델을 나타냅니다.
class Client(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES) # 성별 선택
    height = models.FloatField() # 고객의 키
    image = models.ImageField(upload_to='clients/') # 고객의 전신 사진
    formatted_image = models.ImageField(upload_to='clients/', null=True) # crop, format된 전신 사진, null 허용
    inferred_model = models.FileField(upload_to='clients/', null=True) # 추론 결과로 저장된 파일(pkl), null 허용
    overlayed_image = models.ImageField(upload_to='clients/', null=True) # 전신 사진 + 3D 모델 겹친 이미지, null 허용
    model_image = models.ImageField(upload_to='clients/', null=True) # 중립 자세의 3D 모델 사진, null 허용

# review 모델은 상품에 대한 리뷰와 3D 모델을 나타냅니다.
class Review(models.Model):
    good = models.ForeignKey('Good', on_delete=models.CASCADE) # good 모델에 대한 ForeignKey. 리뷰가 어떤 상품에 대한 것인지 지정
    product_size = models.CharField(max_length=10) # 상품의 사이즈. ex) "L", "XL"
    content = models.CharField(max_length=400, blank=True) # 최대 400자, allow empty string ""
    gender = models.CharField(max_length=1, choices=Client.GENDER_CHOICES) # 성별 선택
    height = models.FloatField() # 리뷰 작성자의 키
    weight = models.FloatField() # 리뷰 작성자의 몸무게
    image = models.ImageField(upload_to='reviews/') # 리뷰 작성자의 전신 사진
    formatted_image = models.ImageField(upload_to='reviews/', null=True) # 자르고 정렬된 전신 사진, null 허용
    inferred_model = models.FileField(upload_to='reviews/', null=True) # 추론 결과로 저장된 파일(pkl), null 허용
    overlayed_image = models.ImageField(upload_to='reviews/', null=True) # 전신 사진 + 3D 모델 겹친 이미지, null 허용
    model_image = models.ImageField(upload_to='reviews/', null=True) # 중립 자세의 3D 모델 사진, null 허용

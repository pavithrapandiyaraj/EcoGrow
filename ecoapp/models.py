from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    # Adding email as a required field
    email = models.EmailField(unique=True)  # Ensure the email is unique for each user

    class Meta:
        verbose_name = 'Custom User'
# models.py
from django.db import models

class CropRecommendation(models.Model):
    N = models.FloatField()
    P = models.FloatField()
    K = models.FloatField()
    temperature = models.FloatField()
    humidity = models.FloatField()
    ph = models.FloatField()
    rainfall = models.FloatField()
    recommended_crop = models.CharField(max_length=100)

    def __str__(self):
        return f"Recommended Crop: {self.recommended_crop}"
    
# ecoapp/models.py
from django.db import models

class FertilizerRecommendation(models.Model):
    temperature = models.FloatField()
    humidity = models.FloatField()
    moisture = models.FloatField()
    soil = models.CharField(max_length=20)
    crop = models.CharField(max_length=20)
    nitrogen = models.IntegerField()
    phosphorous = models.IntegerField()
    potassium = models.IntegerField()
    predicted_fertilizer = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.crop} - {self.predicted_fertilizer}"

    

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Register your custom user model with the admin panel
admin.site.register(CustomUser, UserAdmin)
# admin.py
from django.contrib import admin
from .models import CropRecommendation

admin.site.register(CropRecommendation)

# ecoapp/admin.py
from django.contrib import admin
from .models import FertilizerRecommendation

admin.site.register(FertilizerRecommendation)


from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('index/', views.index, name='index'),
    path('logout/', views.logout_view, name='logout'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('crop-form/', views.crop_form, name='crop_form'),
    path('fertilizer/', views.fertilizer_view, name='fertilizer'),
    path('disease/', views.disease_view, name='disease'),  # 👈 Add this line
]

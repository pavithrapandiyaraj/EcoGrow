from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
import requests
import pickle
import numpy as np
import os
import joblib
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array

from .forms import CustomUserCreationForm, ContactForm, DiseaseForm
from .models import FertilizerRecommendation

# ------------------ Authentication Views ------------------

def home(request):
    return render(request, 'home.html')

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', 'index')
            return redirect(next_url)
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index')

@login_required(login_url='login')
def index(request):
    return render(request, 'index.html')

# ------------------ About & Contact ------------------

def about(request):
    return render(request, 'about.html')

def contact(request):
    submitted = False
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                send_mail(
                    f"Eco Grow Contact - {cd['name']}",
                    cd['message'],
                    cd['email'],
                    [settings.DEFAULT_FROM_EMAIL],
                    fail_silently=False,
                )
                submitted = True
            except Exception as e:
                print(f"Error sending email: {e}")
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form, 'submitted': submitted})

# ------------------ Crop Recommendation ------------------

def crop_form(request):
    if request.method == "POST":
        form_data = {
            'N': request.POST['N'],
            'P': request.POST['P'],
            'K': request.POST['K'],
            'temperature': request.POST['temperature'],
            'humidity': request.POST['humidity'],
            'ph': request.POST['ph'],
            'rainfall': request.POST['rainfall'],
        }
        try:
            resp = requests.post('http://localhost:5000/predict', json=form_data)
            if resp.status_code == 200:
                prediction = resp.json().get('crop')
                return render(request, 'crop_form.html', {'prediction': prediction})
            else:
                error = resp.json().get('error', 'Prediction failed')
                return render(request, 'crop_form.html', {'error': error})
        except Exception as e:
            return render(request, 'crop_form.html', {'error': str(e)})
    else:
        return render(request, 'crop_form.html')

# ------------------ Fertilizer Recommendation ------------------

# Load fertilizer model and encoders
fert_model = pickle.load(open("ml/fertilizer_model/fertilizer_model.pkl", "rb"))
le_soil = pickle.load(open("ml/fertilizer_model/soil_encoder.pkl", "rb"))
le_crop = pickle.load(open("ml/fertilizer_model/crop_encoder.pkl", "rb"))
le_fert = pickle.load(open("ml/fertilizer_model/fert_encoder.pkl", "rb"))

def fertilizer_view(request):
    prediction = None
    if request.method == "POST":
        temp = float(request.POST['temperature'])
        hum = float(request.POST['humidity'])
        mois = float(request.POST['moisture'])
        soil = le_soil.transform([request.POST['soil']])[0]
        crop = le_crop.transform([request.POST['crop']])[0]
        n = int(request.POST['nitrogen'])
        p = int(request.POST['phosphorous'])
        k = int(request.POST['potassium'])

        features = np.array([[temp, hum, mois, soil, crop, n, p, k]])
        result_encoded = fert_model.predict(features)[0]
        prediction = le_fert.inverse_transform([result_encoded])[0]

        # Optional: Save to DB
        FertilizerRecommendation.objects.create(
            temperature=temp, humidity=hum, moisture=mois, soil=request.POST['soil'],
            crop=request.POST['crop'], nitrogen=n, phosphorous=p, potassium=k,
            predicted_fertilizer=prediction
        )

    return render(request, 'fertilizer.html', {'prediction': prediction})

# ------------------ Disease Prediction ------------------

import os
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import joblib
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from PIL import Image

# Load the model and class indices once to avoid reloading on each request
MODEL_PATH = os.path.join(settings.BASE_DIR, "ml/disease_model/disease_model.h5")
CLASS_INDICES_PATH = os.path.join(settings.BASE_DIR, "ml/disease_model/class_indices.pkl")

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
model = load_model(MODEL_PATH)

if not os.path.exists(CLASS_INDICES_PATH):
    raise FileNotFoundError(f"Class indices file not found: {CLASS_INDICES_PATH}")
class_indices = joblib.load(CLASS_INDICES_PATH)
labels = {v: k for k, v in class_indices.items()}


def predict_disease(image_file):
    """
    Predict the disease from the uploaded image file.

    Args:
        image_file (InMemoryUploadedFile): The image file uploaded by the user.

    Returns:
        str: The predicted label for the disease.
        float: The confidence level of the prediction.
    """
    # Handle InMemoryUploadedFile (from Django form)
    if isinstance(image_file, InMemoryUploadedFile):
        # Convert InMemoryUploadedFile to BytesIO
        image_bytes = BytesIO(image_file.read())
        img = Image.open(image_bytes)
        img = img.resize((128, 128))  # Resize image to match model's expected input size
        img_array = np.array(img) / 255.0  # Normalize the image
        img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
    else:
        raise ValueError("Invalid image input")

    # Predict the disease
    prediction = model.predict(img_array)
    class_idx = np.argmax(prediction)  # Get the index of the predicted class
    confidence = float(prediction[0][class_idx])  # Get the confidence score

    # Get the predicted label
    predicted_label = labels[class_idx]
    return predicted_label, confidence


# Your view function where you handle the form submission, such as:
from django.shortcuts import render
from django.http import JsonResponse
from .forms import DiseaseForm

def disease_view(request):
    if request.method == "POST" and request.FILES['image']:
        image_file = request.FILES['image']
        
        try:
            label, confidence = predict_disease(image_file)
            return JsonResponse({
                "label": label,
                "confidence": confidence
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    
    return render(request, 'disease.html')

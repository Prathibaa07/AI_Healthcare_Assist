from django.urls import path
from . import views

urlpatterns = [
    path('analyze/', views.analyze_symptom, name='analyze_symptom'),
    path('transcribe/', views.transcribe_audio, name='transcribe_audio'),
]

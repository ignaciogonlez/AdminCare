from django.urls import path
from .views import ChatbotAPIView

urlpatterns = [
  path('api/chatbot/', ChatbotAPIView.as_view(), name='chatbot-api'),
]

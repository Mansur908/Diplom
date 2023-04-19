from django.urls import path

from app.views import MainView

urlpatterns = [
    path('', MainView.as_view()),
]
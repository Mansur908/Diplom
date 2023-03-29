from django.urls import path

from app.views import MainPageView, MainView

urlpatterns = [
    path('main/', MainPageView.as_view()),
    path('result/', MainView.as_view()),
]
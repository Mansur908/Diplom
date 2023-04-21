from django.urls import path

from app.views import MainView, AvitoDataView

urlpatterns = [
    path('', MainView.as_view()),
    path('avito/', AvitoDataView.as_view(), name="avito"),
]
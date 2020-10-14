from django.urls import path

from . import views

urlpatterns = [
    path('result/<int:search_id>', views.results, name='result'),
    path('', views.index, name='search'),
    path('help/', views.help_page, name='help')
]

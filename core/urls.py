from django.urls import path, include
from .views import home_view, projetos_view

urlpatterns = [
  path('', home_view, name='home'),
  path('projetos/', projetos_view, name='projetos'),
]
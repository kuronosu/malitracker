from django.urls import path

from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ListProductsView.as_view(), name='list_products'),
    path('follow/<int:pk>/toggle/',
         views.ToggleFollowingView.as_view(), name='toggle_following'),
]

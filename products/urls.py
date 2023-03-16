from django.urls import path

from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ListProductsView.as_view(), name='list_products'),
    path('create/', views.CreateProductView.as_view(), name='create_product'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='detail_product'),
    path('<int:pk>/add-price/', views.AddPriceView.as_view(), name='add_price'),
    path('<int:pk>/follow/toggle/',
         views.ToggleFollowingView.as_view(), name='toggle_following'),
    path('<int:pk>/update/', views.UpdateProductView.as_view(),
         name='update_product'),
    path('<int:pk>/delete/', views.DeleteProductView.as_view(),
         name='delete_product'),
    path('<int:product_pk>/delete-price/<int:pk>/', views.DeletePriceView.as_view(),
         name='delete_price'),
]

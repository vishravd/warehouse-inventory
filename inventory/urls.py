from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('item/<int:pk>/', views.item_detail, name='item_detail'),
    path('add-stock/', views.add_stock, name='add_stock'),
    path('use-stock/', views.use_stock, name='use_stock'),
    path('use-stock/<int:pk>/', views.use_stock, name='use_stock_item'),
    path('capacity/', views.capacity_estimator, name='capacity_estimator'),
    path('register/', views.register, name='register'),
    path('pending-approval/', views.pending_approval, name='pending_approval'),
]

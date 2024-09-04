from django.urls import path
from . import views

urlpatterns = [
    
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/update/<int:pk>/', views.user_update, name='user_update'),
    path('users/delete/<int:pk>/', views.user_delete, name='user_delete'),
    path('groups/', views.group_list, name='group_list'),
    path('groups/create/', views.group_create, name='group_create'),
    path('groups/update/<int:pk>/', views.group_update, name='group_update'),
    path('groups/delete/<int:pk>/', views.group_delete, name='group_delete'),
    path('rights/', views.rights_management, name='rights_management'),
   
]

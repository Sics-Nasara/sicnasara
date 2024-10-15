from django.urls import path
from . import views
from .views import (
    StudentListView, StudentCreateView, SchoolManagementView, SchoolCreateView,
    SchoolUpdateView, SchoolDeleteView, SchoolDetailView, ClasseCreateView,
    ClasseDetailView, ClasseUpdateView, ClasseDeleteView
     , UniformPaymentListView, print_receipt  
      , login_view 
    
)

urlpatterns = [
    path('', views.home, name='home'),
    path('class/<int:pk>/', views.class_detail, name='class_detail'),


    path('login/', login_view, name='login'),

    path('update_paiement/<int:pk>/', views.update_paiement, name='update_paiement'),
    path('add_paiement/<int:pk>/', views.add_payment, name='add_paiement'),

    path('student_update/<int:pk>/', views.student_update, name='student_update'),  # Add this line
    path('logout/', views.logout_view, name='logout'),



    path('uniform_payments/', UniformPaymentListView.as_view(), name='uniform_payments'),


    path('offsite_students/', views.offsite_students, name='offsite_students'),
    path('directly_managed_students/', StudentListView.as_view(), name='directly_managed_students'),
    path('new_student/', StudentCreateView.as_view(), name='new_student'),
    path('change_school/<int:pk>/', views.change_school, name='change_school'),

    path('class_upgrade/<int:pk>/', views.class_upgrade, name='class_upgrade'),


  

    path('school_management/', SchoolManagementView.as_view(), name='school_management'),
    path('schools/create/', SchoolCreateView.as_view(), name='school_create'),
    path('schools/update/<int:pk>/', SchoolUpdateView.as_view(), name='school_update'),
    path('schools/delete/<int:pk>/', SchoolDeleteView.as_view(), name='school_delete'),
    path('schools/detail/<int:pk>/', SchoolDetailView.as_view(), name='school_detail'),

    path('classes/create/<int:pk>/', ClasseCreateView.as_view(), name='classe_create'),
    path('classes/detail/<int:pk>/', ClasseDetailView.as_view(), name='classe_detail'),
    path('classes/update/<int:pk>/', ClasseUpdateView.as_view(), name='classe_update'),
    path('classes/delete/<int:pk>/', ClasseDeleteView.as_view(), name='classe_delete'),
    path('load_classes/', views.load_classes, name='load_classes'),
    # Other URLs
 
 path('class/<int:pk>/manage-tarifs/', views.manage_tarifs, name='manage_tarifs'),
    path('class/<int:pk>/add-tarif/', views.add_tarif, name='add_tarif'),
    path('tarif/<int:pk>/edit/', views.update_tarif, name='update_tarif'),
    path('tarif/<int:pk>/delete/', views.delete_tarif, name='delete_tarif'),
    
 
     path('cash/flow_report/', views.cash_flow_report, name='cash_flow_report'),
     path('mouvements/', views.mouvement_list, name='mouvement_list'),
    path('mouvements/add/', views.add_mouvement, name='add_mouvement'),
    path('mouvements/update/<int:pk>/', views.update_mouvement, name='update_mouvement'),
    path('mouvements/delete/<int:pk>/', views.delete_mouvement, name='delete_mouvement'),
    #path('cash/accounting_export/', views.cash_accounting_export, name='cash_accounting_export'),
    path('student/<int:pk>/', views.student_detail, name='student_detail'),
  
    path('receipt/print/<int:mouvement_id>/', print_receipt, name='print_receipt'),

    path('class/<int:pk>/manage-tarifs/', views.manage_tarifs, name='manage_tarifs'),
   # path('class/<int:pk>/add-tarif/', TarifCreateView.as_view(), name='add_tarif'),
   # path('tarif/<int:pk>/edit/', TarifUpdateView.as_view(), name='edit_tarif'),
   # path('tarif/<int:pk>/delete/', TarifDeleteView.as_view(), name='delete_tarif'),
    #path('tarif/<int:pk>/delete/', TarifDeleteView.as_view(), name='tarif_delete'),
]
# urls.py

from django.urls import path
from . import views
from .views  import ( StudentListView  , StudentCreateView ,   SchoolManagementView  , SchoolCreateView ,
                     SchoolUpdateView , SchoolDeleteView  ,SchoolDetailView  , ClasseCreateView  , ClasseDetailView , ClasseUpdateView  , ClasseDeleteView )

urlpatterns = [
    path('', views.home, name='home'),
    path('class/<int:pk>/', views.class_detail, name='class_detail'),
    
    
    path('student-management/', views.student_management, name='student_management'),
    path('teacher-management/', views.teacher_management, name='teacher_management'),
    path('financial-management/', views.financial_management, name='financial_management'),
    path('reporting/', views.reporting, name='reporting'),
    path('document-management/', views.document_management, name='document_management'),
    path('login/', views.login_view, name='login'),
    path('add_paiement/<int:pk>/', views.add_paiement, name='add_paiement'),
    path('update_paiement/<int:pk>/', views.update_paiement, name='update_paiement'),
    path('student/<int:pk>/', views.student_detail, name='student_detail'),
    path('student_update/<int:pk>/', views.student_update, name='student_update'),  # Add this line
    path('logout/', views.logout_view ,name='logout'),
    path('recording_on_records/', views.recording_on_records, name='recording_on_records'),
    path('working_sessions/', views.working_sessions, name='working_sessions'),
    path('types_of_fees/', views.types_of_fees, name='types_of_fees'),
    path('school_uniforms/', views.school_uniforms, name='school_uniforms'),
    path('late_payment/', views.late_payment, name='late_payment'),
    path('print_receipts/', views.print_receipts, name='print_receipts'),
    path('generic_reports/', views.generic_reports, name='generic_reports'),
    path('cash_inflows_outflows/', views.cash_inflows_outflows, name='cash_inflows_outflows'),
    path('cash_flow_report/', views.cash_flow_report, name='cash_flow_report'),
    path('export_for_accounting/', views.export_for_accounting, name='export_for_accounting'),
    path('offsite_students/', views.offsite_students, name='offsite_students'),
    path('directly_managed_students/',  StudentListView.as_view(), name='directly_managed_students'),
    # path('students/', StudentListView.as_view(), name='student_list'),
    path('new_student/', StudentCreateView.as_view(), name='new_student'),
    path('change_school/', views.change_school, name='change_school'),
    path('class_upgrade/', views.class_upgrade, name='class_upgrade'),
    path('start_school_year/', views.start_school_year, name='start_school_year'),
    path('teacher_registry/', views.teacher_registry, name='teacher_registry'),
    path('class_teachers_association/', views.class_teachers_association, name='class_teachers_association'),
     path('student_documents/', views.student_documents, name='student_documents'),
    path('teacher_documents/', views.teacher_documents, name='teacher_documents'),
    path('accounting_documents/', views.accounting_documents, name='accounting_documents'),
    path('school_management/', SchoolManagementView.as_view(), name='school_management'),
    path('schools/create/', SchoolCreateView.as_view(), name='school_create'),
    path('schools/update/<int:pk>/', SchoolUpdateView.as_view(), name='school_update'),
    path('schools/delete/<int:pk>/', SchoolDeleteView.as_view(), name='school_delete'),
    path('schools/detail/<int:pk>/', SchoolDetailView.as_view(), name='school_detail'),
    path('classes/create/<int:pk>/', ClasseCreateView.as_view(), name='classe_create'),
    path('classes/detail/<int:pk>/', ClasseDetailView.as_view(), name='classe_detail'),
    path('classes/update/<int:pk>/', ClasseUpdateView.as_view(), name='classe_update'),
    path('classes/delete/<int:pk>/', ClasseDeleteView.as_view(), name='classe_delete'),
      
]

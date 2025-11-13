from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('play/', views.student_game, name='student_game'),
    path('api/next-word/', views.get_next_word, name='get_next_word'),
    path('api/submit-answer/', views.submit_answer, name='submit_answer'),
    path('api/end-session/', views.end_session, name='end_session'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/student/<int:student_id>/', views.student_detail, name='student_detail'),
    path('teacher/config/', views.teacher_config, name='teacher_config'),
    path('teacher/student/<int:student_id>/update-bucket/', views.update_student_starting_bucket, name='update_student_starting_bucket'),
]

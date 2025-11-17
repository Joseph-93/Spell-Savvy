from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('play/', views.student_game, name='student_game'),
    path('leaderboard/', views.classroom_leaderboard, name='classroom_leaderboard'),
    path('api/next-word/', views.get_next_word, name='get_next_word'),
    path('api/submit-answer/', views.submit_answer, name='submit_answer'),
    path('api/end-session/', views.end_session, name='end_session'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/student/<int:student_id>/', views.student_detail, name='student_detail'),
    path('teacher/config/', views.teacher_config, name='teacher_config'),
    path('teacher/config/bulk-assign/', views.bulk_assign_students, name='bulk_assign_students'),
    path('teacher/student/<int:student_id>/update-bucket/', views.update_student_starting_bucket, name='update_student_starting_bucket'),
    
    # Classroom management
    path('teacher/classrooms/', views.classroom_list, name='classroom_list'),
    path('teacher/classrooms/create/', views.classroom_create, name='classroom_create'),
    path('teacher/classrooms/<int:classroom_id>/', views.classroom_detail, name='classroom_detail'),
    path('teacher/classrooms/<int:classroom_id>/delete/', views.classroom_delete, name='classroom_delete'),
    path('teacher/classrooms/<int:classroom_id>/regenerate-code/', views.classroom_regenerate_code, name='classroom_regenerate_code'),
    path('teacher/classrooms/<int:classroom_id>/assign-ladder/', views.classroom_assign_ladder, name='classroom_assign_ladder'),
    
    # Bucket ladder management
    path('teacher/ladders/', views.ladder_list, name='ladder_list'),
    path('teacher/ladders/create/', views.ladder_create, name='ladder_create'),
    path('teacher/ladders/<int:ladder_id>/', views.ladder_detail, name='ladder_detail'),
    path('teacher/ladders/<int:ladder_id>/delete/', views.ladder_delete, name='ladder_delete'),
    path('teacher/ladders/<int:ladder_id>/bucket/create/', views.bucket_create, name='bucket_create'),
    path('teacher/buckets/<int:bucket_id>/update/', views.bucket_update, name='bucket_update'),
    path('teacher/buckets/<int:bucket_id>/delete/', views.bucket_delete, name='bucket_delete'),
    path('teacher/buckets/<int:bucket_id>/add-words/', views.bucket_add_words, name='bucket_add_words'),
    path('teacher/buckets/<int:bucket_id>/words/', views.bucket_get_words, name='bucket_get_words'),
    path('teacher/words/<int:word_id>/delete/', views.bucket_remove_word, name='bucket_remove_word'),
]

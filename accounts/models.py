from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extended user model with role-based access and teacher-student relationship"""
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    
    # Legacy field - kept for backward compatibility
    teacher = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='legacy_students',
        limit_choices_to={'role': 'teacher'},
        help_text="Legacy: The teacher this student belongs to (use classroom instead)"
    )
    
    # New classroom-based system
    classroom = models.ForeignKey(
        'game.Classroom',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        help_text="The classroom this student belongs to"
    )
    
    def is_teacher(self):
        return self.role == 'teacher'
    
    def is_student(self):
        return self.role == 'student'
    
    def get_teacher(self):
        """Get the teacher for this student (supports both old and new system)"""
        if self.classroom:
            return self.classroom.teacher
        return self.teacher
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def save(self, *args, **kwargs):
        # Teachers cannot have a teacher or classroom
        if self.role == 'teacher':
            self.teacher = None
            self.classroom = None
        super().save(*args, **kwargs)

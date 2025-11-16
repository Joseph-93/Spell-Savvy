from django.db import models
from django.conf import settings
from django.utils import timezone
import secrets
import string


class Classroom(models.Model):
    """Represents a teacher's classroom (period, class group, etc.)"""
    name = models.CharField(
        max_length=100,
        help_text="Class name (e.g., 'Period 1', 'English 101', 'Morning Class')"
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='classrooms',
        limit_choices_to={'role': 'teacher'}
    )
    join_code = models.CharField(
        max_length=12,
        unique=True,
        db_index=True,
        help_text="Unique code students use to join this classroom"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive classrooms cannot accept new students"
    )
    
    class Meta:
        ordering = ['teacher', 'name']
        unique_together = ['teacher', 'name']
    
    def __str__(self):
        return f"{self.teacher.username} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Generate join code if not set
        if not self.join_code:
            self.join_code = self.generate_join_code()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_join_code():
        """Generate a unique, easy-to-read join code"""
        # Use uppercase letters and numbers, exclude confusing characters (0, O, I, 1, etc.)
        chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
        while True:
            # Generate 8-character code (e.g., 'ABC-DEF-GH')
            code = ''.join(secrets.choice(chars) for _ in range(8))
            # Format as XXX-XXX-XX for readability
            formatted_code = f"{code[:3]}-{code[3:6]}-{code[6:8]}"
            
            # Check if it's unique
            if not Classroom.objects.filter(join_code=formatted_code).exists():
                return formatted_code
    
    def get_join_url(self):
        """Get the full registration URL with join code"""
        from django.urls import reverse
        return reverse('register') + f'?join={self.join_code}'
    
    @property
    def student_count(self):
        """Count of students in this classroom"""
        return self.students.count()


class GameConfiguration(models.Model):
    """Teacher-configurable game parameters"""
    teacher = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='game_config'
    )
    words_to_complete_bucket = models.IntegerField(
        default=200,
        help_text="Number of words to master before progressing to next difficulty"
    )
    recycling_distance = models.IntegerField(
        default=100,
        help_text="Incorrect words will reappear within this many words"
    )
    default_starting_bucket = models.IntegerField(
        default=3,
        help_text="Default starting difficulty bucket for new students (word length)"
    )
    
    def __str__(self):
        return f"Config for {self.teacher.username}"


class Word(models.Model):
    """Word database with difficulty levels"""
    text = models.CharField(max_length=100, unique=True, db_index=True)
    difficulty_bucket = models.IntegerField(
        db_index=True,
        help_text="Difficulty level based on word length"
    )
    word_length = models.IntegerField()
    
    class Meta:
        ordering = ['difficulty_bucket', 'text']
        indexes = [
            models.Index(fields=['difficulty_bucket', 'text']),
        ]
    
    def __str__(self):
        return f"{self.text} (bucket {self.difficulty_bucket})"
    
    def save(self, *args, **kwargs):
        if not self.word_length:
            self.word_length = len(self.text)
        if not self.difficulty_bucket:
            # Map word length to difficulty buckets
            self.difficulty_bucket = self.word_length
        super().save(*args, **kwargs)


class StudentProgress(models.Model):
    """Track overall progress for each student"""
    student = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='progress'
    )
    current_bucket = models.IntegerField(null=True, blank=True)
    total_words_correct = models.IntegerField(default=0)
    total_attempts = models.IntegerField(default=0)
    total_points_earned = models.IntegerField(
        default=0,
        help_text="Total points earned from correct words (points = word length)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Student progress"
    
    def __str__(self):
        return f"{self.student.username} - Bucket {self.current_bucket}"
    
    def get_starting_bucket(self):
        """Get the starting bucket for this student"""
        # Priority: teacher default > system default (3)
        # Get teacher's default setting (support both classroom and legacy)
        teacher = self.student.get_teacher()
        if teacher:
            try:
                config = teacher.game_config
                return config.default_starting_bucket
            except:
                pass
        
        return 3  # System default
    
    @property
    def score(self):
        """
        Calculate student's total score based on:
        - Points from correct words (word length = points)
        - Bucket level bonus (current_bucket * 10)
        - Accuracy bonus (accuracy percentage / 10)
        """
        base_score = self.total_points_earned  # Points based on word length
        bucket_bonus = self.current_bucket * 10
        
        # Calculate accuracy bonus
        if self.total_attempts > 0:
            accuracy = (self.total_words_correct / self.total_attempts) * 100
            accuracy_bonus = int(accuracy / 10)  # 0-10 bonus points
        else:
            accuracy_bonus = 0
        
        return base_score + bucket_bonus + accuracy_bonus
    
    @property
    def accuracy(self):
        """Calculate accuracy percentage"""
        if self.total_attempts == 0:
            return 0
        return (self.total_words_correct / self.total_attempts) * 100


class GameSession(models.Model):
    """Track individual play sessions"""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    words_correct = models.IntegerField(default=0)
    words_attempted = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"
    
    def end_session(self):
        """Mark session as ended"""
        self.ended_at = timezone.now()
        self.is_active = False
        self.save()
    
    @property
    def accuracy(self):
        """Calculate accuracy percentage"""
        if self.words_attempted == 0:
            return 0
        return (self.words_correct / self.words_attempted) * 100


class WordAttempt(models.Model):
    """Track individual word attempts"""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='word_attempts'
    )
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    session = models.ForeignKey(
        GameSession,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    user_spelling = models.CharField(max_length=100)
    is_correct = models.BooleanField()
    attempt_number = models.IntegerField(
        default=1,
        help_text="How many times this word has been attempted"
    )
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-attempted_at']
    
    def __str__(self):
        status = "✓" if self.is_correct else "✗"
        return f"{status} {self.student.username}: {self.word.text}"


class BucketProgress(models.Model):
    """Track progress within each difficulty bucket"""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bucket_progress'
    )
    bucket = models.IntegerField(db_index=True)
    words_mastered = models.IntegerField(
        default=0,
        help_text="Words correctly spelled in this bucket"
    )
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['student', 'bucket']
        ordering = ['bucket']
    
    def __str__(self):
        return f"{self.student.username} - Bucket {self.bucket}: {self.words_mastered} words"


class WordQueue(models.Model):
    """Track words in student's current queue (including recycled words)"""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='word_queue'
    )
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    position = models.IntegerField(
        help_text="Position in queue (lower = sooner)"
    )
    times_failed = models.IntegerField(
        default=0,
        help_text="How many times this word was answered incorrectly"
    )
    is_mastered = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'word']
        ordering = ['position']
    
    def __str__(self):
        return f"{self.student.username}: {self.word.text} (pos {self.position})"


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
    bucket_ladder = models.ForeignKey(
        'BucketLadder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='classrooms',
        help_text="Custom bucket ladder for this classroom. If null, uses default system buckets."
    )
    default_starting_bucket = models.IntegerField(
        default=3,
        help_text="Default starting bucket for new students (only used when bucket_ladder is null)"
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
    
    def uses_custom_ladder(self):
        """Check if this classroom uses a custom bucket ladder"""
        return self.bucket_ladder is not None
    
    def uses_default_buckets(self):
        """Check if this classroom uses default system buckets"""
        return self.bucket_ladder is None


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
    custom_bucket = models.ForeignKey(
        'CustomBucket',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_progresses',
        help_text="Current custom bucket (only used when classroom uses custom ladder)"
    )
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
        if self.custom_bucket:
            return f"{self.student.username} - {self.custom_bucket.name}"
        return f"{self.student.username} - Bucket {self.current_bucket}"
    
    def uses_custom_ladder(self):
        """Check if this student is using a custom bucket ladder"""
        if self.student.classroom:
            return self.student.classroom.uses_custom_ladder()
        return False
    
    def get_current_bucket_identifier(self):
        """Get current bucket identifier (for filtering words)"""
        if self.custom_bucket:
            return ('custom', self.custom_bucket.id)
        return ('default', self.current_bucket)
    
    def get_current_bucket_display(self):
        """Get displayable current bucket name"""
        if self.custom_bucket:
            return self.custom_bucket.name
        return f"Bucket {self.current_bucket}"
    
    def advance_to_next_bucket(self):
        """Advance student to the next bucket in their progression"""
        if self.custom_bucket:
            # Custom ladder - get next bucket
            next_bucket = self.custom_bucket.get_next_bucket()
            if next_bucket:
                self.custom_bucket = next_bucket
                self.save()
                return next_bucket
            return None  # No more buckets
        elif self.current_bucket:
            # Default system - increment bucket number
            next_bucket_num = self.current_bucket + 1
            # Check if next bucket has words
            if Word.objects.filter(difficulty_bucket=next_bucket_num).exists():
                self.current_bucket = next_bucket_num
                self.save()
                return next_bucket_num
            return None  # No more buckets
        else:
            # No bucket set - can't advance
            return None
    
    def has_next_bucket(self):
        """Check if there is a next bucket to advance to"""
        if self.custom_bucket:
            return self.custom_bucket.get_next_bucket() is not None
        elif self.current_bucket:
            next_bucket_num = self.current_bucket + 1
            return Word.objects.filter(difficulty_bucket=next_bucket_num).exists()
        else:
            # No bucket set
            return False
    
    def get_starting_bucket(self):
        """Get the starting bucket for this student"""
        # Check if student's classroom uses custom ladder
        if self.student.classroom and self.student.classroom.uses_custom_ladder():
            # Return the first custom bucket in the ladder
            return self.student.classroom.bucket_ladder.get_first_bucket()
        
        # Use default system buckets
        # Priority: classroom default > teacher default > system default (3)
        if self.student.classroom:
            return self.student.classroom.default_starting_bucket
        
        # Legacy: Get teacher's default setting
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
        - Bucket level bonus (bucket position * 10 for custom, bucket number * 10 for default)
        - Accuracy bonus (accuracy percentage / 10)
        """
        base_score = self.total_points_earned  # Points based on word length
        
        # Calculate bucket bonus based on system type
        if self.custom_bucket:
            # For custom buckets, use position as the multiplier
            bucket_bonus = self.custom_bucket.position * 10
        elif self.current_bucket:
            # For default buckets, use bucket number
            bucket_bonus = self.current_bucket * 10
        else:
            # No bucket set yet
            bucket_bonus = 0
        
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
    word = models.ForeignKey(Word, on_delete=models.CASCADE, null=True, blank=True)
    custom_word = models.ForeignKey(
        'CustomWord',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='attempts',
        help_text="Custom word (only used when classroom uses custom ladder)"
    )
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
        word_text = self.custom_word.text if self.custom_word else self.word.text
        return f"{status} {self.student.username}: {word_text}"
    
    def get_word_text(self):
        """Get the word text (works for both default and custom words)"""
        if self.custom_word:
            return self.custom_word.text
        return self.word.text


class BucketProgress(models.Model):
    """Track progress within each difficulty bucket"""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bucket_progress'
    )
    bucket = models.IntegerField(db_index=True, null=True, blank=True)
    custom_bucket = models.ForeignKey(
        'CustomBucket',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='progress_records',
        help_text="Custom bucket (only used when classroom uses custom ladder)"
    )
    words_mastered = models.IntegerField(
        default=0,
        help_text="Words correctly spelled in this bucket"
    )
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['bucket', 'custom_bucket']
    
    def __str__(self):
        if self.custom_bucket:
            return f"{self.student.username} - {self.custom_bucket.name}: {self.words_mastered} words"
        return f"{self.student.username} - Bucket {self.bucket}: {self.words_mastered} words"


class WordQueue(models.Model):
    """Track words in student's current queue (including recycled words)"""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='word_queue'
    )
    word = models.ForeignKey(Word, on_delete=models.CASCADE, null=True, blank=True)
    custom_word = models.ForeignKey(
        'CustomWord',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='queue_entries',
        help_text="Custom word (only used when classroom uses custom ladder)"
    )
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
        ordering = ['position']
    
    def __str__(self):
        word_text = self.custom_word.text if self.custom_word else self.word.text
        return f"{self.student.username}: {word_text} (pos {self.position})"
    
    def get_word_text(self):
        """Get the word text (works for both default and custom words)"""
        if self.custom_word:
            return self.custom_word.text
        return self.word.text
    
    def get_word_length(self):
        """Get the word length"""
        if self.custom_word:
            return self.custom_word.word_length
        return self.word.word_length


class BucketLadder(models.Model):
    """Teacher-created custom bucket ladder (progression system)"""
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bucket_ladders',
        limit_choices_to={'role': 'teacher'}
    )
    name = models.CharField(
        max_length=100,
        help_text="Name for this bucket ladder (e.g., 'Grade Levels', 'Difficulty Progression', 'Animal Themes')"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of this bucket ladder"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['teacher', 'name']
        unique_together = ['teacher', 'name']
    
    def __str__(self):
        return f"{self.teacher.username} - {self.name}"
    
    def get_ordered_buckets(self):
        """Get all buckets in this ladder in order"""
        return self.custom_buckets.all().order_by('position')
    
    def get_first_bucket(self):
        """Get the first bucket in this ladder"""
        return self.custom_buckets.order_by('position').first()


class CustomBucket(models.Model):
    """Individual bucket within a custom ladder"""
    ladder = models.ForeignKey(
        BucketLadder,
        on_delete=models.CASCADE,
        related_name='custom_buckets'
    )
    name = models.CharField(
        max_length=100,
        help_text="Name for this bucket (e.g., 'Easy Words', 'Grade 3', 'Animals')"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of this bucket"
    )
    position = models.IntegerField(
        help_text="Order in the ladder (lower = earlier)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['ladder', 'position']
        unique_together = ['ladder', 'position']
    
    def __str__(self):
        return f"{self.ladder.name} - {self.position}: {self.name}"
    
    def get_next_bucket(self):
        """Get the next bucket in the ladder (or None if this is the last)"""
        return CustomBucket.objects.filter(
            ladder=self.ladder,
            position__gt=self.position
        ).order_by('position').first()
    
    def get_previous_bucket(self):
        """Get the previous bucket in the ladder (or None if this is the first)"""
        return CustomBucket.objects.filter(
            ladder=self.ladder,
            position__lt=self.position
        ).order_by('-position').first()
    
    @property
    def word_count(self):
        """Count of words in this bucket"""
        return self.custom_words.count()


class CustomWord(models.Model):
    """Word within a custom bucket"""
    bucket = models.ForeignKey(
        CustomBucket,
        on_delete=models.CASCADE,
        related_name='custom_words'
    )
    text = models.CharField(
        max_length=100,
        db_index=True,
        help_text="The word text (letters and hyphens only)"
    )
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['bucket', 'text']
        unique_together = ['bucket', 'text']
    
    def __str__(self):
        return f"{self.bucket.name}: {self.text}"
    
    @property
    def word_length(self):
        """Calculate word length"""
        return len(self.text)


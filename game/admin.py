from django.contrib import admin
from .models import (
    Word, GameConfiguration, StudentProgress, GameSession,
    WordAttempt, BucketProgress, WordQueue, Classroom,
    BucketLadder, CustomBucket, CustomWord
)


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ['name', 'teacher', 'join_code', 'student_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'teacher', 'created_at']
    search_fields = ['name', 'join_code', 'teacher__username']
    readonly_fields = ['join_code', 'created_at']
    ordering = ['teacher', 'name']


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ['text', 'difficulty_bucket', 'word_length']
    list_filter = ['difficulty_bucket']
    search_fields = ['text']
    ordering = ['difficulty_bucket', 'text']


@admin.register(GameConfiguration)
class GameConfigurationAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'words_to_complete_bucket', 'recycling_distance']
    list_filter = ['teacher']


@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'current_bucket', 'total_words_correct', 'total_attempts', 'updated_at']
    list_filter = ['current_bucket']
    search_fields = ['student__username']


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['student', 'started_at', 'ended_at', 'words_correct', 'words_attempted', 'is_active']
    list_filter = ['is_active', 'started_at']
    search_fields = ['student__username']
    date_hierarchy = 'started_at'


@admin.register(WordAttempt)
class WordAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'word', 'is_correct', 'user_spelling', 'attempt_number', 'attempted_at']
    list_filter = ['is_correct', 'attempted_at']
    search_fields = ['student__username', 'word__text']
    date_hierarchy = 'attempted_at'


@admin.register(BucketProgress)
class BucketProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'bucket', 'words_mastered', 'is_completed']
    list_filter = ['bucket', 'is_completed']
    search_fields = ['student__username']


@admin.register(WordQueue)
class WordQueueAdmin(admin.ModelAdmin):
    list_display = ['student', 'word', 'position', 'times_failed', 'is_mastered']
    list_filter = ['is_mastered', 'times_failed']
    search_fields = ['student__username', 'word__text']
    ordering = ['student', 'position']


class CustomBucketInline(admin.TabularInline):
    model = CustomBucket
    extra = 1
    fields = ['position', 'name', 'description', 'word_count']
    readonly_fields = ['word_count']
    ordering = ['position']


@admin.register(BucketLadder)
class BucketLadderAdmin(admin.ModelAdmin):
    list_display = ['name', 'teacher', 'bucket_count', 'created_at', 'updated_at']
    list_filter = ['teacher', 'created_at']
    search_fields = ['name', 'teacher__username']
    inlines = [CustomBucketInline]
    ordering = ['teacher', 'name']
    
    def bucket_count(self, obj):
        return obj.custom_buckets.count()
    bucket_count.short_description = 'Buckets'


class CustomWordInline(admin.TabularInline):
    model = CustomWord
    extra = 3
    fields = ['text']


@admin.register(CustomBucket)
class CustomBucketAdmin(admin.ModelAdmin):
    list_display = ['name', 'ladder', 'position', 'word_count', 'created_at']
    list_filter = ['ladder__teacher', 'ladder']
    search_fields = ['name', 'ladder__name']
    inlines = [CustomWordInline]
    ordering = ['ladder', 'position']


@admin.register(CustomWord)
class CustomWordAdmin(admin.ModelAdmin):
    list_display = ['text', 'bucket', 'word_length', 'added_at']
    list_filter = ['bucket__ladder__teacher', 'bucket__ladder', 'bucket']
    search_fields = ['text', 'bucket__name']
    ordering = ['bucket', 'text']
    
    def word_length(self, obj):
        return obj.word_length
    word_length.short_description = 'Length'


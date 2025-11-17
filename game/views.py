from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q, Avg, Max, Min
from django.utils import timezone
from .models import (
    Word, GameSession, WordAttempt, StudentProgress,
    BucketProgress, WordQueue, GameConfiguration, Classroom,
    BucketLadder, CustomBucket, CustomWord
)
from accounts.models import User
import random
import json
import re


# ===== BUCKET SYSTEM HELPER FUNCTIONS =====

def get_available_words_for_student(progress):
    """
    Get available words for the student's current bucket.
    Returns queryset of Word or CustomWord depending on bucket system.
    """
    if progress.custom_bucket:
        # Custom ladder system
        mastered_or_queued_words = WordQueue.objects.filter(
            student=progress.student
        ).values_list('custom_word_id', flat=True)
        
        return CustomWord.objects.filter(
            bucket=progress.custom_bucket
        ).exclude(id__in=mastered_or_queued_words)
    else:
        # Default system
        mastered_or_queued_words = WordQueue.objects.filter(
            student=progress.student
        ).values_list('word_id', flat=True)
        
        return Word.objects.filter(
            difficulty_bucket=progress.current_bucket
        ).exclude(id__in=mastered_or_queued_words)


def add_words_to_queue(student, word_objs, is_custom=False):
    """Add words to student's queue"""
    max_position = WordQueue.objects.filter(
        student=student
    ).aggregate(max_pos=Max('position'))['max_pos'] or 0
    
    for i, word_obj in enumerate(word_objs):
        if is_custom:
            WordQueue.objects.create(
                student=student,
                custom_word=word_obj,
                position=max_position + i + 1
            )
        else:
            WordQueue.objects.create(
                student=student,
                word=word_obj,
                position=max_position + i + 1
            )


def get_words_in_progress_count(progress):
    """Count words that are in progress (attempted but not mastered)"""
    if progress.custom_bucket:
        words_in_progress = WordQueue.objects.filter(
            student=progress.student,
            custom_word__bucket=progress.custom_bucket,
            is_mastered=False
        )
    else:
        words_in_progress = WordQueue.objects.filter(
            student=progress.student,
            word__difficulty_bucket=progress.current_bucket,
            is_mastered=False
        )
    
    count = 0
    for queue_item in words_in_progress:
        # Check if word has been attempted
        if progress.custom_bucket:
            has_been_attempted = WordAttempt.objects.filter(
                student=progress.student,
                custom_word=queue_item.custom_word
            ).exists()
        else:
            has_been_attempted = WordAttempt.objects.filter(
                student=progress.student,
                word=queue_item.word
            ).exists()
        
        if has_been_attempted:
            count += 1
    
    return count



def home(request):
    """Home page - redirect based on user role"""
    if request.user.is_teacher():
        return redirect('teacher_dashboard')
    else:
        return redirect('student_dashboard')


@login_required
def student_dashboard(request):
    """Dashboard for students to view their progress and stats"""
    if request.user.is_teacher():
        return redirect('teacher_dashboard')
    
    # Get or create student progress
    progress, created = StudentProgress.objects.get_or_create(
        student=request.user
    )
    
    # If this is a new student, set their starting bucket
    if created or (progress.current_bucket is None and progress.custom_bucket is None):
        starting_bucket = progress.get_starting_bucket()
        
        # Check if it's a custom bucket or default bucket
        if isinstance(starting_bucket, CustomBucket):
            progress.custom_bucket = starting_bucket
            progress.current_bucket = None
        else:
            progress.current_bucket = starting_bucket
            progress.custom_bucket = None
        
        progress.save()
    
    # Get recent sessions
    recent_sessions = GameSession.objects.filter(
        student=request.user,
        is_active=False
    ).order_by('-started_at')[:10]
    
    # Calculate overall accuracy
    total_attempts = progress.total_attempts
    accuracy = (progress.total_words_correct / total_attempts * 100) if total_attempts > 0 else 0
    
    # Count total sessions
    total_sessions = GameSession.objects.filter(student=request.user).count()
    
    # Get leaderboard data for current student's classroom
    leaderboard_data = None
    if request.user.classroom:
        leaderboard_data = get_classroom_leaderboard(request.user.classroom, request.user)
    
    context = {
        'progress': progress,
        'recent_sessions': recent_sessions,
        'accuracy': round(accuracy, 1),
        'total_sessions': total_sessions,
        'leaderboard_data': leaderboard_data,
    }
    
    return render(request, 'game/student_dashboard.html', context)


@login_required
def student_game(request):
    """Main game interface for students"""
    if request.user.is_teacher():
        return redirect('teacher_dashboard')
    
    # Get or create student progress
    progress, created = StudentProgress.objects.get_or_create(
        student=request.user
    )
    
    # If this is a new student, set their starting bucket based on teacher config
    if created or (progress.current_bucket is None and progress.custom_bucket is None):
        starting_bucket = progress.get_starting_bucket()
        
        # Check if it's a custom bucket or default bucket
        if isinstance(starting_bucket, CustomBucket):
            progress.custom_bucket = starting_bucket
            progress.current_bucket = None
        else:
            progress.current_bucket = starting_bucket
            progress.custom_bucket = None
        
        progress.save()
    
    # Check if current bucket has any words available
    if progress.uses_custom_ladder():
        # Custom ladder - check if bucket has words
        mastered_word_ids = WordQueue.objects.filter(
            student=request.user,
            is_mastered=True,
            custom_word__isnull=False
        ).values_list('custom_word_id', flat=True)
        
        available_words = CustomWord.objects.filter(
            bucket=progress.custom_bucket
        ).exclude(id__in=mastered_word_ids).exists()
    else:
        # Default system - check if bucket has words
        mastered_word_ids = WordQueue.objects.filter(
            student=request.user,
            is_mastered=True,
            word__isnull=False
        ).values_list('word_id', flat=True)
        
        available_words = Word.objects.filter(
            difficulty_bucket=progress.current_bucket
        ).exclude(id__in=mastered_word_ids).exists()
    
    # If no words in current bucket, check if we can advance or if game is complete
    if not available_words:
        # Check if there are any unmastered words in queue
        has_queue_words = WordQueue.objects.filter(
            student=request.user,
            is_mastered=False
        ).exists()
        
        if not has_queue_words:
            # Check if next bucket exists using the helper method
            if progress.has_next_bucket():
                # Next bucket exists, but current bucket is empty
                # This shouldn't normally happen, but let's handle it
                pass
            else:
                # Game is complete! Redirect to dashboard with message
                if progress.uses_custom_ladder():
                    messages.success(
                        request, 
                        f'🏆 Congratulations! You have completed all buckets in {progress.custom_bucket.ladder.name}!'
                    )
                else:
                    messages.success(
                        request, 
                        f'🏆 Congratulations! You have completed all available buckets up to {progress.current_bucket}-letter words!'
                    )
                return redirect('student_dashboard')
    
    # Get or create active session
    active_session = GameSession.objects.filter(
        student=request.user,
        is_active=True
    ).first()
    
    if not active_session:
        active_session = GameSession.objects.create(
            student=request.user
        )
    
    # Get bucket progress based on system type
    if progress.uses_custom_ladder():
        bucket_progress, _ = BucketProgress.objects.get_or_create(
            student=request.user,
            custom_bucket=progress.custom_bucket,
            defaults={'bucket': None}
        )
    else:
        bucket_progress, _ = BucketProgress.objects.get_or_create(
            student=request.user,
            bucket=progress.current_bucket,
            defaults={'custom_bucket': None}
        )
    
    # Get game configuration from student's teacher or use default
    teacher = request.user.get_teacher()
    if teacher:
        config, _ = GameConfiguration.objects.get_or_create(
            teacher=teacher,
            defaults={
                'default_starting_bucket': 3,
                'words_to_complete_bucket': 200,
                'recycling_distance': 100
            }
        )
    else:
        # If student has no teacher, create a default config
        config, _ = GameConfiguration.objects.get_or_create(
            teacher=User.objects.filter(role='teacher').first() or request.user,
            defaults={
                'default_starting_bucket': 3,
                'words_to_complete_bucket': 200,
                'recycling_distance': 100
            }
        )
    
    # Get leaderboard data for current student's classroom
    leaderboard_data = None
    if request.user.classroom:
        leaderboard_data = get_classroom_leaderboard(request.user.classroom, request.user)
    
    # Calculate words in progress (not yet mastered but in queue)
    # ONLY count words that have been attempted at least once
    if progress.uses_custom_ladder():
        words_in_progress = WordQueue.objects.filter(
            student=request.user,
            custom_word__bucket=progress.custom_bucket,
            is_mastered=False
        )
    else:
        words_in_progress = WordQueue.objects.filter(
            student=request.user,
            word__difficulty_bucket=progress.current_bucket,
            is_mastered=False
        )
    
    # Count how many words need 1, 2, or 3 more correct attempts
    needs_1_more = 0
    needs_2_more = 0
    needs_3_more = 0
    
    for queue_item in words_in_progress:
        # Check if word has been attempted at all based on system type
        if progress.uses_custom_ladder():
            has_been_attempted = WordAttempt.objects.filter(
                student=request.user,
                custom_word=queue_item.custom_word
            ).exists()
        else:
            has_been_attempted = WordAttempt.objects.filter(
                student=request.user,
                word=queue_item.word
            ).exists()
        
        if not has_been_attempted:
            # Skip words that haven't been seen yet
            continue
            
        if queue_item.times_failed > 0:
            # Word has been failed - needs 3 correct total
            if progress.uses_custom_ladder():
                correct_count = WordAttempt.objects.filter(
                    student=request.user,
                    custom_word=queue_item.custom_word,
                    is_correct=True
                ).count()
            else:
                correct_count = WordAttempt.objects.filter(
                    student=request.user,
                    word=queue_item.word,
                    is_correct=True
                ).count()
            
            remaining = 3 - correct_count
            if remaining == 1:
                needs_1_more += 1
            elif remaining == 2:
                needs_2_more += 1
            elif remaining >= 3:
                needs_3_more += 1
        else:
            # Word never failed but has been attempted - needs 1 correct
            if progress.uses_custom_ladder():
                has_correct = WordAttempt.objects.filter(
                    student=request.user,
                    custom_word=queue_item.custom_word,
                    is_correct=True
                ).exists()
            else:
                has_correct = WordAttempt.objects.filter(
                    student=request.user,
                    word=queue_item.word,
                    is_correct=True
                ).exists()
            
            if not has_correct:
                needs_1_more += 1
    
    context = {
        'progress': progress,
        'session': active_session,
        'bucket_progress': bucket_progress,
        'config': config,
        'leaderboard_data': leaderboard_data,
        'words_need_1': needs_1_more,
        'words_need_2': needs_2_more,
        'words_need_3': needs_3_more,
    }
    
    return render(request, 'game/student_game.html', context)


@login_required
@require_http_methods(["GET"])
def get_next_word(request):
    """API endpoint to get the next word for the student"""
    if request.user.is_teacher():
        return JsonResponse({'error': 'Teachers cannot play the game'}, status=403)
    
    # Get student progress
    progress = StudentProgress.objects.get(student=request.user)
    
    # Determine if using custom or default bucket system
    using_custom = progress.uses_custom_ladder()
    
    # Get game configuration
    teacher = request.user.get_teacher()
    if teacher:
        config = GameConfiguration.objects.filter(teacher=teacher).first()
    else:
        config = GameConfiguration.objects.first()
    
    if not config:
        config = GameConfiguration.objects.create(
            teacher=User.objects.filter(role='teacher').first() or request.user
        )
    
    # Get current bucket progress
    if using_custom:
        bucket_progress = BucketProgress.objects.filter(
            student=request.user,
            custom_bucket=progress.custom_bucket
        ).first()
    else:
        bucket_progress = BucketProgress.objects.filter(
            student=request.user,
            bucket=progress.current_bucket
        ).first()
    
    # CHECK IF CURRENT BUCKET IS ALREADY COMPLETE
    if bucket_progress and bucket_progress.words_mastered >= config.words_to_complete_bucket:
        # Check if there are any words still in progress
        words_in_progress_count = get_words_in_progress_count(progress)
        
        # Only advance if there are NO words in progress
        if words_in_progress_count == 0:
            # Bucket should be complete! Mark it and advance
            if not bucket_progress.is_completed:
                bucket_progress.is_completed = True
                bucket_progress.save()
            
            # Check if next bucket exists
            if not progress.has_next_bucket():
                # Game complete!
                bucket_name = progress.get_current_bucket_display()
                return JsonResponse({
                    'game_complete': True,
                    'message': f'Congratulations! You have mastered all available buckets up to {bucket_name}!',
                    'words_mastered': bucket_progress.words_mastered,
                    'final_bucket': bucket_name
                })
            
            # Move to next bucket
            next_bucket_result = progress.advance_to_next_bucket()
            
            # Clean up unmastered words from the old bucket
            if using_custom:
                WordQueue.objects.filter(
                    student=request.user,
                    custom_word__bucket=bucket_progress.custom_bucket,
                    is_mastered=False
                ).delete()
            else:
                WordQueue.objects.filter(
                    student=request.user,
                    word__difficulty_bucket=bucket_progress.bucket,
                    is_mastered=False
                ).delete()
            
            # Create new bucket progress if needed
            if using_custom:
                BucketProgress.objects.get_or_create(
                    student=request.user,
                    custom_bucket=progress.custom_bucket
                )
            else:
                BucketProgress.objects.get_or_create(
                    student=request.user,
                    bucket=progress.current_bucket
                )
            
            return JsonResponse({
                'bucket_complete': True,
                'new_bucket': progress.get_current_bucket_display(),
                'words_mastered': bucket_progress.words_mastered
            })
    
    # Check if there are words in the queue FROM THE CURRENT BUCKET
    if using_custom:
        queue_word = WordQueue.objects.filter(
            student=request.user,
            custom_word__bucket=progress.custom_bucket,
            is_mastered=False
        ).order_by('position').first()
    else:
        queue_word = WordQueue.objects.filter(
            student=request.user,
            word__difficulty_bucket=progress.current_bucket,
            is_mastered=False
        ).order_by('position').first()
    
    # Always try to keep the queue populated with new words
    available_words = get_available_words_for_student(progress)
    
    # If there are available words, add some to the queue to keep it full
    if available_words.exists():
        # Add up to 5 new words to the queue each time
        words_to_add = min(5, available_words.count())
        word_sample = random.sample(list(available_words), words_to_add)
        add_words_to_queue(request.user, word_sample, is_custom=using_custom)
    
    # Get the next word from queue
    if queue_word:
        if using_custom:
            word_obj = queue_word.custom_word
            word_text = word_obj.text
            word_id = f"custom_{word_obj.id}"
        else:
            word_obj = queue_word.word
            word_text = word_obj.text
            word_id = f"default_{word_obj.id}"
    else:
        # Queue is empty - check if we should move to next bucket
        if not available_words.exists():
            # No more words in this bucket
            if not progress.has_next_bucket():
                # No more buckets available - game complete!
                bucket_name = progress.get_current_bucket_display()
                return JsonResponse({
                    'game_complete': True,
                    'message': f'Congratulations! You have completed all available buckets up to {bucket_name}!'
                })
            
            # Move to next bucket
            progress.advance_to_next_bucket()
            
            # Create new bucket progress
            if using_custom:
                BucketProgress.objects.get_or_create(
                    student=request.user,
                    custom_bucket=progress.custom_bucket
                )
            else:
                BucketProgress.objects.get_or_create(
                    student=request.user,
                    bucket=progress.current_bucket
                )
            
            return JsonResponse({
                'bucket_complete': True,
                'new_bucket': progress.get_current_bucket_display()
            })
        
        # Queue is empty but words are available - get first queued word
        if using_custom:
            queue_word = WordQueue.objects.filter(
                student=request.user,
                custom_word__isnull=False,
                is_mastered=False
            ).order_by('position').first()
            
            if queue_word:
                word_obj = queue_word.custom_word
                word_text = word_obj.text
                word_id = f"custom_{word_obj.id}"
            else:
                # Fallback: no words were added (shouldn't happen), add one now
                word_obj = random.choice(available_words)
                max_position = WordQueue.objects.filter(
                    student=request.user
                ).aggregate(max_pos=Max('position'))['max_pos'] or 0
                
                WordQueue.objects.create(
                    student=request.user,
                    custom_word=word_obj,
                    position=max_position + 1
                )
                word_text = word_obj.text
                word_id = f"custom_{word_obj.id}"
        else:
            queue_word = WordQueue.objects.filter(
                student=request.user,
                word__isnull=False,
                is_mastered=False
            ).order_by('position').first()
            
            if queue_word:
                word_obj = queue_word.word
                word_text = word_obj.text
                word_id = f"default_{word_obj.id}"
            else:
                # Fallback: no words were added (shouldn't happen), add one now
                word_obj = random.choice(available_words)
                max_position = WordQueue.objects.filter(
                    student=request.user
                ).aggregate(max_pos=Max('position'))['max_pos'] or 0
                
                WordQueue.objects.create(
                    student=request.user,
                    word=word_obj,
                    position=max_position + 1
                )
                word_text = word_obj.text
                word_id = f"default_{word_obj.id}"
    
    return JsonResponse({
        'word_id': word_id,
        'word': word_text,
        'difficulty_bucket': progress.get_current_bucket_display(),
        'bucket_complete': False
    })



@login_required
@require_http_methods(["POST"])
def submit_answer(request):
    """API endpoint to submit a word answer"""
    if request.user.is_teacher():
        return JsonResponse({'error': 'Teachers cannot play the game'}, status=403)
    
    data = json.loads(request.body)
    word_id_str = data.get('word_id')
    user_spelling = data.get('spelling', '').strip().lower()
    
    # Parse word_id to determine if custom or default
    is_custom = word_id_str.startswith('custom_')
    
    try:
        if is_custom:
            actual_id = int(word_id_str.split('_')[1])
            word_obj = CustomWord.objects.get(id=actual_id)
        else:
            actual_id = int(word_id_str.split('_')[1])
            word_obj = Word.objects.get(id=actual_id)
    except (ValueError, IndexError, Word.DoesNotExist, CustomWord.DoesNotExist):
        return JsonResponse({'error': 'Word not found'}, status=404)
    
    # Get active session
    session = GameSession.objects.filter(
        student=request.user,
        is_active=True
    ).first()
    
    if not session:
        session = GameSession.objects.create(student=request.user)
    
    # Check if answer is correct
    is_correct = user_spelling == word_obj.text.lower()
    
    # Get attempt number for this word
    if is_custom:
        previous_attempts = WordAttempt.objects.filter(
            student=request.user,
            custom_word=word_obj
        ).count()
    else:
        previous_attempts = WordAttempt.objects.filter(
            student=request.user,
            word=word_obj
        ).count()
    
    # Create word attempt record
    if is_custom:
        attempt = WordAttempt.objects.create(
            student=request.user,
            custom_word=word_obj,
            session=session,
            user_spelling=user_spelling,
            is_correct=is_correct,
            attempt_number=previous_attempts + 1
        )
    else:
        attempt = WordAttempt.objects.create(
            student=request.user,
            word=word_obj,
            session=session,
            user_spelling=user_spelling,
            is_correct=is_correct,
            attempt_number=previous_attempts + 1
        )

    
    # Update session stats
    session.words_attempted += 1
    if is_correct:
        session.words_correct += 1
    session.save()
    
    # Update overall progress
    progress = StudentProgress.objects.get(student=request.user)
    progress.total_attempts += 1
    if is_correct:
        progress.total_words_correct += 1
        # Award points based on word length
        progress.total_points_earned += word_obj.word_length
    progress.save()
    
    # Handle word queue
    if is_custom:
        queue_word = WordQueue.objects.filter(
            student=request.user,
            custom_word=word_obj
        ).first()
    else:
        queue_word = WordQueue.objects.filter(
            student=request.user,
            word=word_obj
        ).first()
    
    if queue_word:
        if is_correct:
            # Check if word was already mastered BEFORE this attempt
            was_already_mastered = queue_word.is_mastered
            
            if not was_already_mastered:
                # Check if this word has ever been failed
                has_been_failed = queue_word.times_failed > 0
                
                if has_been_failed:
                    # Word was misspelled before - need 3 correct attempts total to master
                    if is_custom:
                        correct_attempts = WordAttempt.objects.filter(
                            student=request.user,
                            custom_word=word_obj,
                            is_correct=True
                        ).count()
                    else:
                        correct_attempts = WordAttempt.objects.filter(
                            student=request.user,
                            word=word_obj,
                            is_correct=True
                        ).count()
                    
                    if correct_attempts >= 3:
                        # Now mastered after 3 correct attempts!
                        queue_word.is_mastered = True
                        queue_word.save()
                        should_increment_bucket = True
                    else:
                        # Correct, but need more attempts - recycle the word
                        # Get config for recycling distance (use student's teacher's config)
                        teacher = request.user.get_teacher()
                        if teacher:
                            config = GameConfiguration.objects.filter(teacher=teacher).first()
                        else:
                            config = GameConfiguration.objects.first()
                        
                        if not config:
                            config = GameConfiguration.objects.create(
                                teacher=User.objects.filter(role='teacher').first() or request.user
                            )
                        
                        # Calculate new position (AT THE FRONT, within recycling_distance)
                        # Get the minimum position currently in the queue
                        current_min_position = WordQueue.objects.filter(
                            student=request.user,
                            is_mastered=False
                        ).aggregate(min_pos=Min('position'))['min_pos'] or 0
                        
                        # Place it at the front, randomly within 1 to recycling_distance positions from the start
                        new_position = current_min_position + random.randint(1, min(config.recycling_distance, 50))
                        queue_word.position = new_position
                        queue_word.save()
                        should_increment_bucket = False
                else:
                    # Word never failed - mastered on first correct attempt!
                    queue_word.is_mastered = True
                    queue_word.save()
                    should_increment_bucket = True
                
                # Update bucket progress if word was newly mastered
                if should_increment_bucket:
                    # Get or create bucket progress based on system type
                    if progress.uses_custom_ladder():
                        bucket_progress, _ = BucketProgress.objects.get_or_create(
                            student=request.user,
                            custom_bucket=progress.custom_bucket
                        )
                    else:
                        bucket_progress, _ = BucketProgress.objects.get_or_create(
                            student=request.user,
                            bucket=word_obj.difficulty_bucket
                        )
                    bucket_progress.words_mastered += 1
                    
                    # Check if bucket is complete (use student's teacher's config)
                    teacher = request.user.get_teacher()
                    if teacher:
                        config = GameConfiguration.objects.filter(teacher=teacher).first()
                    else:
                        config = GameConfiguration.objects.first()
                    
                    if config and bucket_progress.words_mastered >= config.words_to_complete_bucket:
                        # Before completing bucket, check if there are any words still in progress
                        # (words that have been attempted but not yet mastered)
                        if progress.uses_custom_ladder():
                            words_in_progress = WordQueue.objects.filter(
                                student=request.user,
                                custom_word__bucket=progress.custom_bucket,
                                is_mastered=False
                            )
                        else:
                            words_in_progress = WordQueue.objects.filter(
                                student=request.user,
                                word__difficulty_bucket=word_obj.difficulty_bucket,
                                is_mastered=False
                            )
                        
                        # Count how many have been attempted
                        has_words_in_progress = False
                        words_in_progress_count = 0
                        for queue_item in words_in_progress:
                            # Check based on system type
                            if progress.uses_custom_ladder():
                                has_been_attempted = WordAttempt.objects.filter(
                                    student=request.user,
                                    custom_word=queue_item.custom_word
                                ).exists()
                                word_text = queue_item.custom_word.text if queue_item.custom_word else 'N/A'
                            else:
                                has_been_attempted = WordAttempt.objects.filter(
                                    student=request.user,
                                    word=queue_item.word
                                ).exists()
                                word_text = queue_item.word.text if queue_item.word else 'N/A'
                            
                            if has_been_attempted:
                                has_words_in_progress = True
                                words_in_progress_count += 1
                                # DEBUG
                                print(f'DEBUG: Word in progress: {word_text}, times_failed={queue_item.times_failed}')
                        
                        # DEBUG
                        if progress.uses_custom_ladder():
                            bucket_name = progress.custom_bucket.name if progress.custom_bucket else 'N/A'
                            print(f'DEBUG: Bucket {bucket_name} - Mastered: {bucket_progress.words_mastered}, Required: {config.words_to_complete_bucket}, Words in progress: {words_in_progress_count}')
                        else:
                            print(f'DEBUG: Bucket {word_obj.difficulty_bucket} - Mastered: {bucket_progress.words_mastered}, Required: {config.words_to_complete_bucket}, Words in progress: {words_in_progress_count}')
                        
                        # Only complete bucket if there are NO words in progress
                        if not has_words_in_progress:
                            bucket_progress.is_completed = True
                            bucket_progress.save()
                            
                            print(f'DEBUG: ADVANCING TO NEXT BUCKET')
                            
                            # Check if next bucket exists based on system type
                            if progress.uses_custom_ladder():
                                # Custom ladder - check if there's a next bucket
                                if progress.has_next_bucket():
                                    # Advance to next bucket
                                    progress.advance_to_next_bucket()
                                    progress.save()
                                    
                                    # Clean up unmastered words from the old bucket
                                    WordQueue.objects.filter(
                                        student=request.user,
                                        custom_word__bucket=progress.custom_bucket,
                                        is_mastered=False
                                    ).delete()
                                    
                                    leaderboard_data = None
                                    if request.user.classroom:
                                        raw_leaderboard = get_classroom_leaderboard(request.user.classroom, request.user)
                                        leaderboard_data = serialize_leaderboard_for_json(raw_leaderboard)
                                    
                                    return JsonResponse({
                                        'correct': True,
                                        'bucket_complete': True,
                                        'words_mastered': bucket_progress.words_mastered,
                                        'new_bucket': progress.get_current_bucket_display(),
                                        'session_correct': session.words_correct,
                                        'session_attempted': session.words_attempted,
                                        'total_correct': progress.total_words_correct,
                                        'leaderboard': leaderboard_data
                                    })
                                else:
                                    # No more buckets - game complete!
                                    leaderboard_data = None
                                    if request.user.classroom:
                                        raw_leaderboard = get_classroom_leaderboard(request.user.classroom, request.user)
                                        leaderboard_data = serialize_leaderboard_for_json(raw_leaderboard)
                                    
                                    return JsonResponse({
                                        'correct': True,
                                        'game_complete': True,
                                        'words_mastered': bucket_progress.words_mastered,
                                        'final_bucket': progress.get_current_bucket_display(),
                                        'session_correct': session.words_correct,
                                        'session_attempted': session.words_attempted,
                                        'total_correct': progress.total_words_correct,
                                        'message': f'Congratulations! You have mastered all buckets in {progress.custom_bucket.ladder.name}!',
                                        'leaderboard': leaderboard_data
                                    })
                            else:
                                # Default system - check if next bucket has words
                                next_bucket = word_obj.difficulty_bucket + 1
                                next_bucket_has_words = Word.objects.filter(difficulty_bucket=next_bucket).exists()
                                
                                if not next_bucket_has_words:
                                    # Game complete!
                                    leaderboard_data = None
                                    if request.user.classroom:
                                        raw_leaderboard = get_classroom_leaderboard(request.user.classroom, request.user)
                                        leaderboard_data = serialize_leaderboard_for_json(raw_leaderboard)
                                    
                                    return JsonResponse({
                                        'correct': True,
                                        'game_complete': True,
                                        'words_mastered': bucket_progress.words_mastered,
                                        'final_bucket': word_obj.difficulty_bucket,
                                        'session_correct': session.words_correct,
                                        'session_attempted': session.words_attempted,
                                        'total_correct': progress.total_words_correct,
                                        'message': f'Congratulations! You have mastered all available buckets up to {word_obj.difficulty_bucket}-letter words!',
                                        'leaderboard': leaderboard_data
                                    })
                                
                                # Move to next bucket
                                progress.current_bucket = next_bucket
                                progress.save()
                                
                                # Clean up unmastered words from the old bucket (they won't be used anymore)
                                WordQueue.objects.filter(
                                    student=request.user,
                                    word__difficulty_bucket=word_obj.difficulty_bucket,
                                    is_mastered=False
                                ).delete()
                                
                                leaderboard_data = None
                                if request.user.classroom:
                                    raw_leaderboard = get_classroom_leaderboard(request.user.classroom, request.user)
                                    leaderboard_data = serialize_leaderboard_for_json(raw_leaderboard)
                                
                                return JsonResponse({
                                    'correct': True,
                                    'bucket_complete': True,
                                    'words_mastered': bucket_progress.words_mastered,
                                    'new_bucket': progress.current_bucket,
                                    'session_correct': session.words_correct,
                                    'session_attempted': session.words_attempted,
                                    'total_correct': progress.total_words_correct,
                                    'leaderboard': leaderboard_data
                                })
                        else:
                            # DEBUG
                            print(f'DEBUG: NOT ADVANCING - Still have {words_in_progress_count} words in progress')
                    
                    bucket_progress.save()
            # else: word was already mastered, don't do anything special
        else:
            # Recycle the word - move it back into the queue
            queue_word.times_failed += 1
            
            # Get config for recycling distance (use student's teacher's config)
            teacher = request.user.get_teacher()
            if teacher:
                config = GameConfiguration.objects.filter(teacher=teacher).first()
            else:
                config = GameConfiguration.objects.first()
            
            if not config:
                config = GameConfiguration.objects.create(
                    teacher=User.objects.filter(role='teacher').first() or request.user
                )
            
            # Calculate new position (AT THE FRONT, within recycling_distance)
            # Get the minimum position currently in the queue
            current_min_position = WordQueue.objects.filter(
                student=request.user,
                is_mastered=False
            ).aggregate(min_pos=Min('position'))['min_pos'] or 0
            
            # Place it at the front, randomly within 1 to recycling_distance positions from the start
            # This puts failed words BEFORE most unattempted words
            new_position = current_min_position + random.randint(1, min(config.recycling_distance, 50))
            queue_word.position = new_position
            queue_word.save()
    
    # Get config for words_to_complete
    teacher = request.user.get_teacher()
    if teacher:
        config = GameConfiguration.objects.filter(teacher=teacher).first()
    else:
        config = GameConfiguration.objects.first()
    
    words_to_complete = config.words_to_complete_bucket if config else 200
    
    # Count correct attempts for this word to show progress
    if is_custom:
        correct_attempts_for_word = WordAttempt.objects.filter(
            student=request.user,
            custom_word=word_obj,
            is_correct=True
        ).count()
    else:
        correct_attempts_for_word = WordAttempt.objects.filter(
            student=request.user,
            word=word_obj,
            is_correct=True
        ).count()
    
    # Determine mastery requirement based on whether word has been failed
    if is_custom:
        queue_word_for_response = WordQueue.objects.filter(
            student=request.user,
            custom_word=word_obj
        ).first()
    else:
        queue_word_for_response = WordQueue.objects.filter(
            student=request.user,
            word=word_obj
        ).first()
    
    if queue_word_for_response and queue_word_for_response.times_failed > 0:
        # Word has been misspelled - needs 3 correct attempts
        mastery_required = 3
    else:
        # Word never failed - needs only 1 correct attempt
        mastery_required = 1
    
    # Get updated leaderboard data
    leaderboard_data = None
    if request.user.classroom:
        raw_leaderboard = get_classroom_leaderboard(request.user.classroom, request.user)
        leaderboard_data = serialize_leaderboard_for_json(raw_leaderboard)
    
    # Calculate words in progress (not yet mastered but in queue)
    if progress.uses_custom_ladder():
        words_in_progress = WordQueue.objects.filter(
            student=request.user,
            custom_word__bucket=progress.custom_bucket,
            is_mastered=False
        )
    else:
        words_in_progress = WordQueue.objects.filter(
            student=request.user,
            word__difficulty_bucket=progress.current_bucket,
            is_mastered=False
        )
    
    # Count how many words need 1, 2, or 3 more correct attempts
    # ONLY count words that have been attempted at least once
    needs_1_more = 0
    needs_2_more = 0
    needs_3_more = 0
    
    for queue_item in words_in_progress:
        # Check if word has been attempted at all based on system type
        if progress.uses_custom_ladder():
            has_been_attempted = WordAttempt.objects.filter(
                student=request.user,
                custom_word=queue_item.custom_word
            ).exists()
        else:
            has_been_attempted = WordAttempt.objects.filter(
                student=request.user,
                word=queue_item.word
            ).exists()
        
        if not has_been_attempted:
            # Skip words that haven't been seen yet
            continue
            
        if queue_item.times_failed > 0:
            # Word has been failed - needs 3 correct total
            if progress.uses_custom_ladder():
                correct_count = WordAttempt.objects.filter(
                    student=request.user,
                    custom_word=queue_item.custom_word,
                    is_correct=True
                ).count()
            else:
                correct_count = WordAttempt.objects.filter(
                    student=request.user,
                    word=queue_item.word,
                    is_correct=True
                ).count()
            remaining = 3 - correct_count
            if remaining == 1:
                needs_1_more += 1
            elif remaining == 2:
                needs_2_more += 1
            elif remaining >= 3:
                needs_3_more += 1
        else:
            # Word never failed but has been attempted - needs 1 correct
            if progress.uses_custom_ladder():
                has_correct = WordAttempt.objects.filter(
                    student=request.user,
                    custom_word=queue_item.custom_word,
                    is_correct=True
                ).exists()
            else:
                has_correct = WordAttempt.objects.filter(
                    student=request.user,
                    word=queue_item.word,
                    is_correct=True
                ).exists()
            if not has_correct:
                needs_1_more += 1
    
    # Get bucket progress for response
    if progress.uses_custom_ladder():
        bucket_progress_response = BucketProgress.objects.filter(
            student=request.user,
            custom_bucket=progress.custom_bucket
        ).first()
    else:
        bucket_progress_response = BucketProgress.objects.filter(
            student=request.user,
            bucket=progress.current_bucket
        ).first()
    
    # Use the bucket_progress_response or default values
    if bucket_progress_response:
        words_mastered = bucket_progress_response.words_mastered
    else:
        words_mastered = 0
    
    response_data = {
        'correct': is_correct,
        'correct_spelling': word_obj.text,
        'bucket_complete': False,
        'words_mastered': words_mastered,
        'words_to_complete': words_to_complete,
        'session_correct': session.words_correct,
        'session_attempted': session.words_attempted,
        'total_correct': progress.total_words_correct,
        'word_correct_count': correct_attempts_for_word,
        'word_mastery_required': mastery_required,
        'words_need_1': needs_1_more,
        'words_need_2': needs_2_more,
        'words_need_3': needs_3_more,
        'leaderboard': leaderboard_data
    }
    
    return JsonResponse(response_data)


@login_required
@require_http_methods(["POST"])
def end_session(request):
    """API endpoint to end the current session"""
    session = GameSession.objects.filter(
        student=request.user,
        is_active=True
    ).first()
    
    if session:
        session.end_session()
        
        return JsonResponse({
            'session_id': session.id,
            'words_correct': session.words_correct,
            'words_attempted': session.words_attempted,
            'accuracy': session.accuracy
        })
    
    return JsonResponse({'error': 'No active session'}, status=404)


@login_required
def teacher_dashboard(request):
    """Dashboard for teachers to view student progress"""
    if not request.user.is_teacher():
        return redirect('student_game')
    
    # Get students - support both classroom and legacy teacher assignment
    students = User.objects.filter(
        role='student'
    ).filter(
        Q(classroom__teacher=request.user) | Q(teacher=request.user)
    ).select_related('progress').distinct()
    
    # Get statistics for each student
    student_stats = []
    for student in students:
        progress = getattr(student, 'progress', None)
        
        # Get recent sessions
        recent_sessions = GameSession.objects.filter(
            student=student
        ).order_by('-started_at')[:5]
        
        # Calculate overall accuracy
        total_attempts = WordAttempt.objects.filter(student=student).count()
        correct_attempts = WordAttempt.objects.filter(
            student=student,
            is_correct=True
        ).count()
        
        accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        
        student_stats.append({
            'student': student,
            'progress': progress,
            'recent_sessions': recent_sessions,
            'total_attempts': total_attempts,
            'correct_attempts': correct_attempts,
            'accuracy': accuracy
        })
    
    context = {
        'student_stats': student_stats,
    }
    
    return render(request, 'game/teacher_dashboard.html', context)


@login_required
def student_detail(request, student_id):
    """Detailed view of a specific student's performance"""
    if not request.user.is_teacher():
        return redirect('student_game')
    
    try:
        # Only allow viewing own students
        student = User.objects.get(
            id=student_id,
            role='student',
            teacher=request.user
        )
    except User.DoesNotExist:
        messages.error(request, 'Student not found or you do not have permission to view this student')
        return redirect('teacher_dashboard')
    
    progress = getattr(student, 'progress', None)
    
    # Get all sessions
    sessions = GameSession.objects.filter(student=student).order_by('-started_at')
    
    # Get word attempts grouped by word
    word_performance = WordAttempt.objects.filter(
        student=student
    ).values(
        'word__text',
        'word__difficulty_bucket'
    ).annotate(
        total_attempts=Count('id'),
        correct_attempts=Count('id', filter=Q(is_correct=True)),
        last_attempt=Count('attempted_at')
    ).order_by('-total_attempts')
    
    # Calculate accuracy for each word
    for perf in word_performance:
        perf['accuracy'] = (perf['correct_attempts'] / perf['total_attempts'] * 100) if perf['total_attempts'] > 0 else 0
    
    # Get bucket progress
    bucket_progress = BucketProgress.objects.filter(student=student).order_by('bucket')
    
    # Get teacher's configuration
    config, created = GameConfiguration.objects.get_or_create(
        teacher=request.user,
        defaults={'default_starting_bucket': 3}
    )
    
    # Get list of available buckets (3-20)
    available_buckets = list(range(3, 21))
    
    # Get custom ladder buckets if student is using a custom ladder
    custom_ladder_buckets = []
    if progress and progress.uses_custom_ladder():
        ladder = progress.custom_bucket.ladder
        custom_ladder_buckets = CustomBucket.objects.filter(
            ladder=ladder
        ).order_by('position')
    
    context = {
        'student': student,
        'progress': progress,
        'sessions': sessions,
        'word_performance': word_performance,
        'bucket_progress': bucket_progress,
        'config': config,
        'available_buckets': available_buckets,
        'custom_ladder_buckets': custom_ladder_buckets,
    }
    
    return render(request, 'game/student_detail.html', context)


@login_required
def teacher_config(request):
    """Configuration page for teachers"""
    if not request.user.is_teacher():
        return redirect('student_game')
    
    config, created = GameConfiguration.objects.get_or_create(
        teacher=request.user,
        defaults={'default_starting_bucket': 3}
    )
    
    if request.method == 'POST':
        words_to_complete = request.POST.get('words_to_complete_bucket')
        recycling_distance = request.POST.get('recycling_distance')
        default_starting_bucket = request.POST.get('default_starting_bucket')
        
        try:
            old_default_bucket = config.default_starting_bucket
            new_default_bucket = int(default_starting_bucket)
            
            config.words_to_complete_bucket = int(words_to_complete)
            config.recycling_distance = int(recycling_distance)
            config.default_starting_bucket = new_default_bucket
            config.save()
            
            # ONLY update students who were on the old default bucket
            if old_default_bucket != new_default_bucket:
                # Get students of this teacher who are currently on the old default bucket
                students_to_update = StudentProgress.objects.filter(
                    student__teacher=request.user,
                    current_bucket=old_default_bucket
                )
                
                updated_count = 0
                for progress in students_to_update:
                    # Update their current bucket to the new default
                    progress.current_bucket = new_default_bucket
                    progress.save()
                    
                    # Clear their word queue for fresh words
                    WordQueue.objects.filter(student=progress.student).delete()
                    
                    # End any active sessions
                    GameSession.objects.filter(student=progress.student, is_active=True).update(is_active=False)
                    
                    # Create/update bucket progress
                    BucketProgress.objects.get_or_create(
                        student=progress.student,
                        bucket=new_default_bucket
                    )
                    
                    updated_count += 1
                
                if updated_count > 0:
                    messages.success(
                        request, 
                        f'✅ Configuration updated! {updated_count} student(s) on {old_default_bucket}-letter words moved to {new_default_bucket}-letter words!'
                    )
                else:
                    messages.success(request, 'Configuration updated! No students were on the old default bucket.')
            else:
                messages.success(request, 'Configuration updated successfully!')
                
        except ValueError:
            messages.error(request, 'Please enter valid numbers')
        
        return redirect('teacher_config')
    
    # Get list of available buckets (3-20)
    available_buckets = list(range(3, 21))
    
    # Get count of students currently on the default bucket
    students_on_default_count = StudentProgress.objects.filter(
        student__teacher=request.user,
        current_bucket=config.default_starting_bucket
    ).count()
    
    context = {
        'config': config,
        'available_buckets': available_buckets,
        'students_on_default': students_on_default_count,
    }
    
    return render(request, 'game/teacher_config.html', context)


@login_required
def bulk_assign_students(request):
    """Assign ALL students in the classroom to a specific bucket"""
    if not request.user.is_teacher():
        return redirect('student_game')
    
    if request.method == 'POST':
        try:
            bulk_bucket = int(request.POST.get('bulk_bucket'))
            
            if 3 <= bulk_bucket <= 20:
                # Get ALL students of this teacher
                students_to_update = StudentProgress.objects.filter(
                    student__teacher=request.user
                )
                
                updated_count = 0
                for progress in students_to_update:
                    # Update their current bucket to the specified value
                    progress.current_bucket = bulk_bucket
                    progress.save()
                    
                    # Clear their word queue for fresh words
                    WordQueue.objects.filter(student=progress.student).delete()
                    
                    # End any active sessions
                    GameSession.objects.filter(student=progress.student, is_active=True).update(is_active=False)
                    
                    # Create/update bucket progress
                    BucketProgress.objects.get_or_create(
                        student=progress.student,
                        bucket=bulk_bucket
                    )
                    
                    updated_count += 1
                
                if updated_count > 0:
                    messages.success(
                        request,
                        f'✅ All {updated_count} student(s) have been assigned to {bulk_bucket}-letter words!'
                    )
                else:
                    messages.info(request, 'No students found to update.')
            else:
                messages.error(request, 'Please select a valid bucket (3-20 letters)')
                
        except (ValueError, TypeError):
            messages.error(request, 'Please select a valid bucket')
    
    return redirect('teacher_config')


@login_required
def update_student_starting_bucket(request, student_id):
    """Update a specific student's starting bucket"""
    if not request.user.is_teacher():
        return redirect('student_game')
    
    try:
        # Only allow modifying own students
        student = User.objects.get(
            id=student_id,
            role='student',
            teacher=request.user
        )
    except User.DoesNotExist:
        messages.error(request, 'Student not found or you do not have permission')
        return redirect('teacher_dashboard')
    
    if request.method == 'POST':
        bucket_value_str = request.POST.get('bucket_value')
        custom_bucket_id_str = request.POST.get('custom_bucket_id')
        
        # Get or create progress
        progress, created = StudentProgress.objects.get_or_create(
            student=student
        )
        
        try:
            # Check if updating to a custom bucket
            if custom_bucket_id_str:
                custom_bucket_id = int(custom_bucket_id_str)
                try:
                    # Verify the bucket exists and belongs to a ladder owned by this teacher
                    custom_bucket = CustomBucket.objects.get(
                        id=custom_bucket_id,
                        ladder__teacher=request.user
                    )
                    
                    # Store the old bucket for comparison
                    old_bucket = progress.custom_bucket
                    
                    # IMMEDIATELY change to the new custom bucket
                    progress.custom_bucket = custom_bucket
                    progress.current_bucket = None
                    progress.save()
                    
                    # Clear the student's word queue so they get fresh words from the new bucket
                    WordQueue.objects.filter(student=student).delete()
                    
                    # End any active session since we're changing buckets
                    GameSession.objects.filter(student=student, is_active=True).update(is_active=False)
                    
                    # Create/update bucket progress for the new bucket
                    BucketProgress.objects.get_or_create(
                        student=student,
                        custom_bucket=custom_bucket,
                        defaults={'bucket': None}
                    )
                    
                    if old_bucket != custom_bucket:
                        messages.success(request, f'✅ {student.username} moved to bucket "{custom_bucket.name}" immediately! Their word queue has been reset.')
                    else:
                        messages.success(request, f'Bucket for {student.username} confirmed at "{custom_bucket.name}"')
                        
                except CustomBucket.DoesNotExist:
                    messages.error(request, 'Custom bucket not found or you do not have permission')
                    
            elif bucket_value_str:
                bucket_value = int(bucket_value_str)
                if 3 <= bucket_value <= 20:
                    # Store the old bucket for comparison
                    old_bucket = progress.current_bucket
                    
                    # IMMEDIATELY change the current bucket to the new value
                    progress.current_bucket = bucket_value
                    progress.save()
                    
                    # Clear the student's word queue so they get fresh words from the new bucket
                    WordQueue.objects.filter(student=student).delete()
                    
                    # End any active session since we're changing difficulty
                    GameSession.objects.filter(student=student, is_active=True).update(is_active=False)
                    
                    # Create/update bucket progress for the new bucket
                    BucketProgress.objects.get_or_create(
                        student=student,
                        bucket=bucket_value
                    )
                    
                    if old_bucket != bucket_value:
                        messages.success(request, f'✅ {student.username} moved to {bucket_value}-letter words immediately! Their word queue has been reset.')
                    else:
                        messages.success(request, f'Starting bucket for {student.username} confirmed at {bucket_value}')
                else:
                    messages.error(request, 'Starting bucket must be between 3 and 20')
            else:
                # Reset to teacher's default
                old_bucket = progress.current_bucket
                
                # Update to teacher's default
                new_bucket = progress.get_starting_bucket()
                
                # Check if it's a custom bucket or default bucket
                if isinstance(new_bucket, CustomBucket):
                    progress.custom_bucket = new_bucket
                    progress.current_bucket = None
                    
                    # Clear the word queue for fresh start
                    WordQueue.objects.filter(student=student).delete()
                    
                    # End any active session
                    GameSession.objects.filter(student=student, is_active=True).update(is_active=False)
                    
                    # Create/update bucket progress
                    BucketProgress.objects.get_or_create(
                        student=student,
                        custom_bucket=new_bucket,
                        defaults={'bucket': None}
                    )
                    
                    messages.success(request, f'✅ {student.username} reset to custom bucket "{new_bucket.name}" immediately!')
                else:
                    progress.current_bucket = new_bucket
                    progress.custom_bucket = None
                    
                    # Clear the word queue for fresh start
                    WordQueue.objects.filter(student=student).delete()
                    
                    # End any active session
                    GameSession.objects.filter(student=student, is_active=True).update(is_active=False)
                    
                    # Create/update bucket progress
                    BucketProgress.objects.get_or_create(
                        student=student,
                        bucket=new_bucket,
                        defaults={'custom_bucket': None}
                    )
                    
                    if old_bucket != new_bucket:
                        messages.success(request, f'✅ {student.username} moved to {new_bucket}-letter words (teacher default) immediately!')
                    else:
                        messages.success(request, f'Student bucket reset to teacher default: {new_bucket}')
                
                progress.save()
        except ValueError:
            messages.error(request, 'Please enter a valid number')
    
    return redirect('student_detail', student_id=student_id)


@login_required
def classroom_list(request):
    """View and manage all classrooms for a teacher"""
    if not request.user.is_teacher():
        return redirect('student_game')
    
    classrooms = Classroom.objects.filter(teacher=request.user).order_by('name')
    
    context = {
        'classrooms': classrooms,
    }
    
    return render(request, 'game/classroom_list.html', context)


@login_required
def classroom_create(request):
    """Create a new classroom"""
    if not request.user.is_teacher():
        return redirect('student_game')
    
    if request.method == 'POST':
        classroom_name = request.POST.get('classroom_name', '').strip()
        
        if not classroom_name:
            messages.error(request, 'Please enter a classroom name')
        elif Classroom.objects.filter(teacher=request.user, name=classroom_name).exists():
            messages.error(request, f'You already have a classroom named "{classroom_name}"')
        else:
            classroom = Classroom.objects.create(
                name=classroom_name,
                teacher=request.user
            )
            messages.success(request, f'✅ Classroom "{classroom_name}" created! Join code: {classroom.join_code}')
            return redirect('classroom_detail', classroom_id=classroom.id)
    
    return redirect('classroom_list')


@login_required
def classroom_detail(request, classroom_id):
    """View details of a specific classroom"""
    if not request.user.is_teacher():
        return redirect('student_game')
    
    try:
        classroom = Classroom.objects.get(id=classroom_id, teacher=request.user)
    except Classroom.DoesNotExist:
        messages.error(request, 'Classroom not found')
        return redirect('classroom_list')
    
    # Get students in this classroom
    students = User.objects.filter(
        role='student',
        classroom=classroom
    ).select_related('progress')
    
    # Get statistics for each student
    student_stats = []
    for student in students:
        progress = getattr(student, 'progress', None)
        
        # Get recent sessions
        recent_sessions = GameSession.objects.filter(
            student=student
        ).order_by('-started_at')[:5]
        
        # Calculate overall accuracy
        total_attempts = WordAttempt.objects.filter(student=student).count()
        correct_attempts = WordAttempt.objects.filter(
            student=student,
            is_correct=True
        ).count()
        
        accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        
        student_stats.append({
            'student': student,
            'progress': progress,
            'recent_sessions': recent_sessions,
            'total_attempts': total_attempts,
            'correct_attempts': correct_attempts,
            'accuracy': accuracy
        })
    
    # Generate full join URL for easy copying
    join_url = request.build_absolute_uri(classroom.get_join_url())
    
    # Get all bucket ladders for this teacher
    available_ladders = BucketLadder.objects.filter(teacher=request.user).order_by('name')
    
    # Get list of available default buckets (3-20)
    available_buckets = list(range(3, 21))
    
    context = {
        'classroom': classroom,
        'student_stats': student_stats,
        'join_url': join_url,
        'available_ladders': available_ladders,
        'available_buckets': available_buckets,
    }
    
    return render(request, 'game/classroom_detail.html', context)


@login_required
def classroom_delete(request, classroom_id):
    """Delete a classroom"""
    if not request.user.is_teacher():
        return redirect('student_game')
    
    if request.method == 'POST':
        try:
            classroom = Classroom.objects.get(id=classroom_id, teacher=request.user)
            classroom_name = classroom.name
            
            # Remove students from this classroom (don't delete them)
            User.objects.filter(classroom=classroom).update(classroom=None)
            
            classroom.delete()
            messages.success(request, f'Classroom "{classroom_name}" deleted')
        except Classroom.DoesNotExist:
            messages.error(request, 'Classroom not found')
    
    return redirect('classroom_list')


@login_required
def classroom_regenerate_code(request, classroom_id):
    """Regenerate the join code for a classroom"""
    if not request.user.is_teacher():
        return redirect('student_game')
    
    if request.method == 'POST':
        try:
            classroom = Classroom.objects.get(id=classroom_id, teacher=request.user)
            old_code = classroom.join_code
            classroom.join_code = Classroom.generate_join_code()
            classroom.save()
            messages.success(request, f'✅ New join code generated: {classroom.join_code}')
        except Classroom.DoesNotExist:
            messages.error(request, 'Classroom not found')
    
    return redirect('classroom_detail', classroom_id=classroom_id)


def get_classroom_leaderboard(classroom, current_student):
    """
    Calculate leaderboard for a classroom
    Returns dict with top 5 students and current student's ranking
    """
    # Get all students in the classroom with their progress
    students = User.objects.filter(
        role='student',
        classroom=classroom
    ).select_related('progress')
    
    # Build leaderboard data
    leaderboard = []
    for student in students:
        progress = getattr(student, 'progress', None)
        if progress:
            leaderboard.append({
                'student': student,
                'progress': progress,
                'score': progress.score,
                'accuracy': progress.accuracy,
            })
    
    # Sort by score (descending)
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    
    # Add rankings
    for i, entry in enumerate(leaderboard):
        entry['rank'] = i + 1
    
    # Find current student's ranking
    current_student_data = None
    current_student_index = None
    for i, entry in enumerate(leaderboard):
        if entry['student'].id == current_student.id:
            current_student_data = entry
            current_student_index = i
            break
    
    # Calculate gap to next person
    gap_to_next = 0
    next_student_data = None
    if current_student_index is not None and current_student_index > 0:
        next_student_data = leaderboard[current_student_index - 1]
        gap_to_next = next_student_data['score'] - current_student_data['score']
    
    return {
        'top_5': leaderboard[:5],
        'current_student': current_student_data,
        'gap_to_next': gap_to_next,
        'next_student': next_student_data,
        'total_students': len(leaderboard)
    }


def serialize_leaderboard_for_json(leaderboard_data):
    """
    Convert leaderboard data to JSON-serializable format
    """
    if not leaderboard_data:
        return None
    
    def serialize_student_entry(entry):
        if not entry:
            return None
        return {
            'rank': entry['rank'],
            'username': entry['student'].username,
            'score': entry['score'],
            'accuracy': round(entry['accuracy'], 1),
            'bucket': entry['progress'].current_bucket,
            'words_correct': entry['progress'].total_words_correct,
            'is_current': False,  # Will be set later
        }
    
    # Serialize top 5
    top_5_serialized = []
    for entry in leaderboard_data['top_5']:
        serialized = serialize_student_entry(entry)
        if serialized:
            top_5_serialized.append(serialized)
    
    # Mark current student in top 5
    current_student_serialized = None
    if leaderboard_data['current_student']:
        current_student_serialized = serialize_student_entry(leaderboard_data['current_student'])
        if current_student_serialized:
            current_student_serialized['is_current'] = True
            
            # Mark in top 5 if present
            for entry in top_5_serialized:
                if entry['rank'] == current_student_serialized['rank']:
                    entry['is_current'] = True
    
    # Serialize next student
    next_student_serialized = None
    if leaderboard_data['next_student']:
        next_student_serialized = {
            'username': leaderboard_data['next_student']['student'].username,
            'score': leaderboard_data['next_student']['score'],
        }
    
    return {
        'top_5': top_5_serialized,
        'current_student': current_student_serialized,
        'gap_to_next': leaderboard_data['gap_to_next'],
        'next_student': next_student_serialized,
        'total_students': leaderboard_data['total_students']
    }


@login_required
def classroom_leaderboard(request):
    """Full leaderboard page for students"""
    if request.user.is_teacher():
        return redirect('teacher_dashboard')
    
    if not request.user.classroom:
        messages.warning(request, 'You are not in a classroom yet.')
        return redirect('student_dashboard')
    
    leaderboard_data = get_classroom_leaderboard(request.user.classroom, request.user)
    
    context = {
        'classroom': request.user.classroom,
        'leaderboard_data': leaderboard_data,
    }
    
    return render(request, 'game/leaderboard.html', context)


# ===== BUCKET LADDER MANAGEMENT VIEWS =====

@login_required
def ladder_list(request):
    """View all bucket ladders for a teacher"""
    if not request.user.is_teacher():
        return redirect('student_game')
    
    ladders = BucketLadder.objects.filter(teacher=request.user).order_by('name')
    
    # Add bucket count to each ladder
    for ladder in ladders:
        ladder.bucket_count = ladder.custom_buckets.count()
    
    context = {
        'ladders': ladders,
    }
    
    return render(request, 'game/ladder_list.html', context)


@login_required
def ladder_create(request):
    """Create a new bucket ladder"""
    if not request.user.is_teacher():
        return redirect('student_game')
    
    if request.method == 'POST':
        ladder_name = request.POST.get('ladder_name', '').strip()
        ladder_description = request.POST.get('ladder_description', '').strip()
        
        if not ladder_name:
            messages.error(request, 'Please enter a ladder name')
        elif BucketLadder.objects.filter(teacher=request.user, name=ladder_name).exists():
            messages.error(request, f'You already have a ladder named "{ladder_name}"')
        else:
            ladder = BucketLadder.objects.create(
                name=ladder_name,
                description=ladder_description,
                teacher=request.user
            )
            messages.success(request, f'✅ Bucket ladder "{ladder_name}" created!')
            return redirect('ladder_detail', ladder_id=ladder.id)
    
    return redirect('ladder_list')


@login_required
def ladder_detail(request, ladder_id):
    """View and edit a specific bucket ladder"""
    if not request.user.is_teacher():
        return redirect('student_game')
    
    try:
        ladder = BucketLadder.objects.get(id=ladder_id, teacher=request.user)
    except BucketLadder.DoesNotExist:
        messages.error(request, 'Ladder not found')
        return redirect('ladder_list')
    
    # Get buckets in order
    buckets = ladder.get_ordered_buckets()
    
    # Get classrooms using this ladder
    classrooms_using = Classroom.objects.filter(bucket_ladder=ladder)
    
    context = {
        'ladder': ladder,
        'buckets': buckets,
        'classrooms_using': classrooms_using,
    }
    
    return render(request, 'game/ladder_detail.html', context)


@login_required
def ladder_delete(request, ladder_id):
    """Delete a bucket ladder"""
    if not request.user.is_teacher():
        return redirect('student_game')
    
    if request.method == 'POST':
        try:
            ladder = BucketLadder.objects.get(id=ladder_id, teacher=request.user)
            
            # Check if any classrooms are using this ladder
            classrooms_using = Classroom.objects.filter(bucket_ladder=ladder)
            if classrooms_using.exists():
                messages.error(
                    request, 
                    f'Cannot delete ladder "{ladder.name}" - it is currently assigned to {classrooms_using.count()} classroom(s). Please unassign it first.'
                )
                return redirect('ladder_detail', ladder_id=ladder_id)
            
            ladder_name = ladder.name
            ladder.delete()
            messages.success(request, f'Ladder "{ladder_name}" deleted')
        except BucketLadder.DoesNotExist:
            messages.error(request, 'Ladder not found')
    
    return redirect('ladder_list')


@login_required
def bucket_create(request, ladder_id):
    """Create a new bucket in a ladder"""
    if not request.user.is_teacher():
        return redirect('student_game')
    
    try:
        ladder = BucketLadder.objects.get(id=ladder_id, teacher=request.user)
    except BucketLadder.DoesNotExist:
        messages.error(request, 'Ladder not found')
        return redirect('ladder_list')
    
    if request.method == 'POST':
        bucket_name = request.POST.get('bucket_name', '').strip()
        bucket_description = request.POST.get('bucket_description', '').strip()
        
        if not bucket_name:
            messages.error(request, 'Please enter a bucket name')
        else:
            # Get the next position
            max_position = CustomBucket.objects.filter(ladder=ladder).aggregate(
                max_pos=Max('position')
            )['max_pos'] or 0
            
            bucket = CustomBucket.objects.create(
                ladder=ladder,
                name=bucket_name,
                description=bucket_description,
                position=max_position + 1
            )
            messages.success(request, f'✅ Bucket "{bucket_name}" created!')
    
    return redirect('ladder_detail', ladder_id=ladder_id)


@login_required
def bucket_update(request, bucket_id):
    """Update bucket details"""
    if not request.user.is_teacher():
        return redirect('student_game')
    
    try:
        bucket = CustomBucket.objects.select_related('ladder').get(
            id=bucket_id, 
            ladder__teacher=request.user
        )
    except CustomBucket.DoesNotExist:
        messages.error(request, 'Bucket not found')
        return redirect('ladder_list')
    
    if request.method == 'POST':
        bucket_name = request.POST.get('bucket_name', '').strip()
        bucket_description = request.POST.get('bucket_description', '').strip()
        position = request.POST.get('position')
        
        if bucket_name:
            bucket.name = bucket_name
        if bucket_description is not None:
            bucket.description = bucket_description
        if position:
            try:
                bucket.position = int(position)
            except ValueError:
                messages.error(request, 'Invalid position value')
                return redirect('ladder_detail', ladder_id=bucket.ladder.id)
        
        bucket.save()
        messages.success(request, f'✅ Bucket "{bucket.name}" updated!')
    
    return redirect('ladder_detail', ladder_id=bucket.ladder.id)


@login_required
def bucket_delete(request, bucket_id):
    """Delete a bucket from a ladder"""
    if not request.user.is_teacher():
        return redirect('student_game')
    
    if request.method == 'POST':
        try:
            bucket = CustomBucket.objects.select_related('ladder').get(
                id=bucket_id,
                ladder__teacher=request.user
            )
            ladder_id = bucket.ladder.id
            bucket_name = bucket.name
            
            # Check if any students are currently on this bucket
            students_on_bucket = StudentProgress.objects.filter(custom_bucket=bucket)
            if students_on_bucket.exists():
                messages.error(
                    request,
                    f'Cannot delete bucket "{bucket_name}" - {students_on_bucket.count()} student(s) are currently on this bucket.'
                )
                return redirect('ladder_detail', ladder_id=ladder_id)
            
            bucket.delete()
            messages.success(request, f'Bucket "{bucket_name}" deleted')
            
            return redirect('ladder_detail', ladder_id=ladder_id)
        except CustomBucket.DoesNotExist:
            messages.error(request, 'Bucket not found')
    
    return redirect('ladder_list')


@login_required
def bucket_add_words(request, bucket_id):
    """Add words to a bucket"""
    if not request.user.is_teacher():
        return redirect('student_game')
    
    try:
        bucket = CustomBucket.objects.select_related('ladder').get(
            id=bucket_id,
            ladder__teacher=request.user
        )
    except CustomBucket.DoesNotExist:
        messages.error(request, 'Bucket not found')
        return redirect('ladder_list')
    
    if request.method == 'POST':
        words_input = request.POST.get('words', '').strip()
        
        if not words_input:
            messages.error(request, 'Please enter some words')
            return redirect('ladder_detail', ladder_id=bucket.ladder.id)
        
        # Parse words - accept any whitespace, comma, or other non-letter character (except hyphen) as separator
        # Only keep alphabetic characters and hyphens
        words_list = re.findall(r'[a-zA-Z]+(?:-[a-zA-Z]+)*', words_input)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_words = []
        for word in words_list:
            word_lower = word.lower()
            if word_lower not in seen:
                seen.add(word_lower)
                unique_words.append(word_lower)
        
        # Add words to the bucket
        added_count = 0
        duplicate_count = 0
        
        for word_text in unique_words:
            # Check if word already exists in this bucket
            if not CustomWord.objects.filter(bucket=bucket, text=word_text).exists():
                CustomWord.objects.create(
                    bucket=bucket,
                    text=word_text
                )
                added_count += 1
            else:
                duplicate_count += 1
        
        if added_count > 0:
            messages.success(request, f'✅ Added {added_count} word(s) to "{bucket.name}"!')
        if duplicate_count > 0:
            messages.info(request, f'{duplicate_count} duplicate word(s) were skipped.')
        if added_count == 0 and duplicate_count == 0:
            messages.warning(request, 'No valid words found in the input.')
    
    return redirect('ladder_detail', ladder_id=bucket.ladder.id)


@login_required
def bucket_remove_word(request, word_id):
    """Remove a word from a bucket"""
    if not request.user.is_teacher():
        return redirect('student_game')
    
    if request.method == 'POST':
        try:
            word = CustomWord.objects.select_related('bucket__ladder').get(
                id=word_id,
                bucket__ladder__teacher=request.user
            )
            ladder_id = word.bucket.ladder.id
            word.delete()
            messages.success(request, f'Word removed')
            return redirect('ladder_detail', ladder_id=ladder_id)
        except CustomWord.DoesNotExist:
            messages.error(request, 'Word not found')
    
    return redirect('ladder_list')


@login_required
def bucket_get_words(request, bucket_id):
    """AJAX endpoint to get all words in a bucket"""
    if not request.user.is_teacher():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        bucket = CustomBucket.objects.get(
            id=bucket_id,
            ladder__teacher=request.user
        )
        
        # Get all words in this bucket, ordered alphabetically
        words = CustomWord.objects.filter(bucket=bucket).order_by('text')
        
        words_data = [
            {
                'id': word.id,
                'text': word.text,
                'word_length': word.word_length
            }
            for word in words
        ]
        
        return JsonResponse({
            'success': True,
            'bucket_name': bucket.name,
            'words': words_data,
            'word_count': len(words_data)
        })
        
    except CustomBucket.DoesNotExist:
        return JsonResponse({'error': 'Bucket not found'}, status=404)


@login_required
def classroom_assign_ladder(request, classroom_id):
    """Assign or change the bucket ladder for a classroom"""
    if not request.user.is_teacher():
        return redirect('student_game')
    
    try:
        classroom = Classroom.objects.get(id=classroom_id, teacher=request.user)
    except Classroom.DoesNotExist:
        messages.error(request, 'Classroom not found')
        return redirect('classroom_list')
    
    if request.method == 'POST':
        ladder_id = request.POST.get('ladder_id')
        default_starting_bucket_str = request.POST.get('default_starting_bucket')
        
        # Update default starting bucket if provided
        if default_starting_bucket_str:
            try:
                classroom.default_starting_bucket = int(default_starting_bucket_str)
                classroom.save()
            except ValueError:
                pass
        
        if ladder_id == 'default':
            # Switch to default system buckets
            old_ladder = classroom.bucket_ladder
            classroom.bucket_ladder = None
            classroom.save()
            
            # Move all students to the classroom's default starting bucket
            students = User.objects.filter(classroom=classroom, role='student')
            for student in students:
                progress, _ = StudentProgress.objects.get_or_create(student=student)
                
                # Clear custom bucket reference
                progress.custom_bucket = None
                progress.current_bucket = classroom.default_starting_bucket
                progress.save()
                
                # Clear word queue
                WordQueue.objects.filter(student=student).delete()
                
                # End active sessions
                GameSession.objects.filter(student=student, is_active=True).update(is_active=False)
                
                # Create/update bucket progress for default bucket
                BucketProgress.objects.get_or_create(
                    student=student,
                    bucket=classroom.default_starting_bucket,
                    defaults={'custom_bucket': None}
                )
            
            if old_ladder:
                messages.success(
                    request,
                    f'✅ Classroom "{classroom.name}" switched to default system buckets. All students moved to bucket {classroom.default_starting_bucket}.'
                )
            else:
                messages.success(
                    request,
                    f'✅ Default starting bucket updated to {classroom.default_starting_bucket}.'
                )
        else:
            # Assign custom ladder
            try:
                ladder = BucketLadder.objects.get(id=ladder_id, teacher=request.user)
                
                # Check if ladder has at least one bucket
                first_bucket = ladder.get_first_bucket()
                if not first_bucket:
                    messages.error(request, f'Cannot assign ladder "{ladder.name}" - it has no buckets. Please add buckets first.')
                    return redirect('classroom_detail', classroom_id=classroom_id)
                
                classroom.bucket_ladder = ladder
                classroom.save()
                
                # Move all students to the first bucket in the ladder
                students = User.objects.filter(classroom=classroom, role='student')
                for student in students:
                    progress, _ = StudentProgress.objects.get_or_create(student=student)
                    
                    # Set to custom bucket
                    progress.custom_bucket = first_bucket
                    progress.current_bucket = None  # Clear default bucket
                    progress.save()
                    
                    # Clear word queue
                    WordQueue.objects.filter(student=student).delete()
                    
                    # End active sessions
                    GameSession.objects.filter(student=student, is_active=True).update(is_active=False)
                    
                    # Create/update bucket progress for custom bucket
                    BucketProgress.objects.get_or_create(
                        student=student,
                        custom_bucket=first_bucket,
                        defaults={'bucket': None}
                    )
                
                messages.success(
                    request,
                    f'✅ Classroom "{classroom.name}" assigned to ladder "{ladder.name}". All students moved to "{first_bucket.name}".'
                )
            except BucketLadder.DoesNotExist:
                messages.error(request, 'Ladder not found')
    
    return redirect('classroom_detail', classroom_id=classroom_id)


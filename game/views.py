from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q, Avg, Max, Min
from django.utils import timezone
from .models import (
    Word, GameSession, WordAttempt, StudentProgress,
    BucketProgress, WordQueue, GameConfiguration, Classroom
)
from accounts.models import User
import random
import json


@login_required
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
    if created or progress.current_bucket is None:
        starting_bucket = progress.get_starting_bucket()
        progress.current_bucket = starting_bucket
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
    if created or progress.current_bucket is None:
        starting_bucket = progress.get_starting_bucket()
        progress.current_bucket = starting_bucket
        progress.save()
    
    # Check if current bucket has any words available
    mastered_words = WordQueue.objects.filter(
        student=request.user,
        is_mastered=True
    ).values_list('word_id', flat=True)
    
    available_words = Word.objects.filter(
        difficulty_bucket=progress.current_bucket
    ).exclude(id__in=mastered_words).exists()
    
    # If no words in current bucket, check if we can advance or if game is complete
    if not available_words:
        # Check if there are any unmastered words in queue
        has_queue_words = WordQueue.objects.filter(
            student=request.user,
            is_mastered=False
        ).exists()
        
        if not has_queue_words:
            # Check if next bucket exists
            next_bucket = progress.current_bucket + 1
            next_bucket_has_words = Word.objects.filter(difficulty_bucket=next_bucket).exists()
            
            if not next_bucket_has_words:
                # Game is complete! Redirect to dashboard with message
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
    
    # Get bucket progress
    bucket_progress, _ = BucketProgress.objects.get_or_create(
        student=request.user,
        bucket=progress.current_bucket
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
        # Check if word has been attempted at all
        has_been_attempted = WordAttempt.objects.filter(
            student=request.user,
            word=queue_item.word
        ).exists()
        
        if not has_been_attempted:
            # Skip words that haven't been seen yet
            continue
            
        if queue_item.times_failed > 0:
            # Word has been failed - needs 3 correct total
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
    current_bucket = progress.current_bucket
    
    # Get game configuration (use student's teacher's config)
    teacher = request.user.get_teacher()
    if teacher:
        config = GameConfiguration.objects.filter(teacher=teacher).first()
    else:
        config = GameConfiguration.objects.first()
    
    if not config:
        config = GameConfiguration.objects.create(
            teacher=User.objects.filter(role='teacher').first() or request.user
        )
    
    # CHECK IF CURRENT BUCKET IS ALREADY COMPLETE
    # This handles the case where enough words were mastered but bucket wasn't advanced
    bucket_progress = BucketProgress.objects.filter(
        student=request.user,
        bucket=current_bucket
    ).first()
    
    if bucket_progress and bucket_progress.words_mastered >= config.words_to_complete_bucket:
        # Before advancing, check if there are any words still in progress
        # (words that have been attempted but not yet mastered)
        words_in_progress = WordQueue.objects.filter(
            student=request.user,
            word__difficulty_bucket=current_bucket,
            is_mastered=False
        )
        
        # Count how many have been attempted
        has_words_in_progress = False
        for queue_item in words_in_progress:
            has_been_attempted = WordAttempt.objects.filter(
                student=request.user,
                word=queue_item.word
            ).exists()
            if has_been_attempted:
                has_words_in_progress = True
                break
        
        # Only advance if there are NO words in progress
        if not has_words_in_progress:
            # Bucket should be complete! Mark it and advance
            if not bucket_progress.is_completed:
                bucket_progress.is_completed = True
                bucket_progress.save()
            
            # Check if next bucket exists
            next_bucket = current_bucket + 1
            next_bucket_has_words = Word.objects.filter(difficulty_bucket=next_bucket).exists()
            
            if not next_bucket_has_words:
                # Game complete!
                return JsonResponse({
                    'game_complete': True,
                    'message': f'Congratulations! You have mastered all available buckets up to {current_bucket}-letter words!',
                    'words_mastered': bucket_progress.words_mastered,
                    'final_bucket': current_bucket
                })
            
            # Move to next bucket
            progress.current_bucket = next_bucket
            progress.save()
            
            # Clean up unmastered words from the old bucket (they won't be used anymore)
            WordQueue.objects.filter(
                student=request.user,
                word__difficulty_bucket=current_bucket,
                is_mastered=False
            ).delete()
            
            # Create new bucket progress if needed
            BucketProgress.objects.get_or_create(
                student=request.user,
                bucket=next_bucket
            )
            
            return JsonResponse({
                'bucket_complete': True,
                'new_bucket': next_bucket,
                'words_mastered': bucket_progress.words_mastered
            })
    
    # Check if there are words in the queue FROM THE CURRENT BUCKET
    queue_word = WordQueue.objects.filter(
        student=request.user,
        word__difficulty_bucket=current_bucket,
        is_mastered=False
    ).order_by('position').first()
    
    # Always try to keep the queue populated with new words
    # Get words from current bucket that haven't been mastered or queued
    mastered_or_queued_words = WordQueue.objects.filter(
        student=request.user
    ).values_list('word_id', flat=True)
    
    available_words = Word.objects.filter(
        difficulty_bucket=current_bucket
    ).exclude(id__in=mastered_or_queued_words)
    
    # If there are available words, add some to the queue to keep it full
    if available_words.exists():
        # Add up to 5 new words to the queue each time
        max_position = WordQueue.objects.filter(
            student=request.user
        ).aggregate(max_pos=Max('position'))['max_pos'] or 0
        
        words_to_add = min(5, available_words.count())
        for i, word in enumerate(random.sample(list(available_words), words_to_add)):
            WordQueue.objects.create(
                student=request.user,
                word=word,
                position=max_position + i + 1
            )
    
    if queue_word:
        word = queue_word.word
    else:
        # Queue is empty - check if we should move to next bucket
        mastered_words = WordQueue.objects.filter(
            student=request.user,
            is_mastered=True
        ).values_list('word_id', flat=True)
        
        all_words_in_bucket = Word.objects.filter(
            difficulty_bucket=current_bucket
        ).exclude(id__in=mastered_words)
        
        if not all_words_in_bucket.exists():
            # No more words in this bucket - check if next bucket has words
            next_bucket = current_bucket + 1
            next_bucket_words = Word.objects.filter(difficulty_bucket=next_bucket).exists()
            
            if not next_bucket_words:
                # No more buckets available - game complete!
                return JsonResponse({
                    'game_complete': True,
                    'message': f'Congratulations! You have completed all available buckets up to {current_bucket}-letter words!'
                })
            
            # Move to next bucket
            progress.current_bucket = next_bucket
            progress.save()
            
            # Create new bucket progress
            BucketProgress.objects.get_or_create(
                student=request.user,
                bucket=progress.current_bucket
            )
            
            return JsonResponse({
                'bucket_complete': True,
                'new_bucket': progress.current_bucket
            })
        
        # Queue is empty but words are available - return first queued word
        # (The code above should have already added words to the queue)
        queue_word = WordQueue.objects.filter(
            student=request.user,
            is_mastered=False
        ).order_by('position').first()
        
        if queue_word:
            word = queue_word.word
        else:
            # Fallback: no words were added (shouldn't happen), add one now
            word = random.choice(all_words_in_bucket)
            max_position = WordQueue.objects.filter(
                student=request.user
            ).aggregate(max_pos=Max('position'))['max_pos'] or 0
            
            queue_word, created = WordQueue.objects.get_or_create(
                student=request.user,
                word=word,
                defaults={'position': max_position + 1}
            )
    
    return JsonResponse({
        'word_id': word.id,
        'word': word.text,
        'difficulty_bucket': word.difficulty_bucket,
        'bucket_complete': False
    })


@login_required
@require_http_methods(["POST"])
def submit_answer(request):
    """API endpoint to submit a word answer"""
    if request.user.is_teacher():
        return JsonResponse({'error': 'Teachers cannot play the game'}, status=403)
    
    data = json.loads(request.body)
    word_id = data.get('word_id')
    user_spelling = data.get('spelling', '').strip().lower()
    
    try:
        word = Word.objects.get(id=word_id)
    except Word.DoesNotExist:
        return JsonResponse({'error': 'Word not found'}, status=404)
    
    # Get active session
    session = GameSession.objects.filter(
        student=request.user,
        is_active=True
    ).first()
    
    if not session:
        session = GameSession.objects.create(student=request.user)
    
    # Check if answer is correct
    is_correct = user_spelling == word.text.lower()
    
    # Get attempt number for this word
    previous_attempts = WordAttempt.objects.filter(
        student=request.user,
        word=word
    ).count()
    
    # Create word attempt record
    attempt = WordAttempt.objects.create(
        student=request.user,
        word=word,
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
        progress.total_points_earned += word.word_length
    progress.save()
    
    # Handle word queue
    queue_word = WordQueue.objects.filter(
        student=request.user,
        word=word
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
                    correct_attempts = WordAttempt.objects.filter(
                        student=request.user,
                        word=word,
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
                    bucket_progress, _ = BucketProgress.objects.get_or_create(
                        student=request.user,
                        bucket=word.difficulty_bucket
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
                        words_in_progress = WordQueue.objects.filter(
                            student=request.user,
                            word__difficulty_bucket=word.difficulty_bucket,
                            is_mastered=False
                        )
                        
                        # Count how many have been attempted
                        has_words_in_progress = False
                        words_in_progress_count = 0
                        for queue_item in words_in_progress:
                            has_been_attempted = WordAttempt.objects.filter(
                                student=request.user,
                                word=queue_item.word
                            ).exists()
                            if has_been_attempted:
                                has_words_in_progress = True
                                words_in_progress_count += 1
                                # DEBUG
                                print(f'DEBUG: Word in progress: {queue_item.word.text}, times_failed={queue_item.times_failed}')
                        
                        # DEBUG
                        print(f'DEBUG: Bucket {word.difficulty_bucket} - Mastered: {bucket_progress.words_mastered}, Required: {config.words_to_complete_bucket}, Words in progress: {words_in_progress_count}')
                        
                        # Only complete bucket if there are NO words in progress
                        if not has_words_in_progress:
                            bucket_progress.is_completed = True
                            bucket_progress.save()
                            
                            print(f'DEBUG: ADVANCING TO NEXT BUCKET')
                            
                            # Check if next bucket has words before moving
                            next_bucket = word.difficulty_bucket + 1
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
                                    'final_bucket': word.difficulty_bucket,
                                    'session_correct': session.words_correct,
                                    'session_attempted': session.words_attempted,
                                    'total_correct': progress.total_words_correct,
                                    'message': f'Congratulations! You have mastered all available buckets up to {word.difficulty_bucket}-letter words!',
                                    'leaderboard': leaderboard_data
                                })
                            
                            # Move to next bucket
                            progress.current_bucket = next_bucket
                            progress.save()
                            
                            # Clean up unmastered words from the old bucket (they won't be used anymore)
                            WordQueue.objects.filter(
                                student=request.user,
                                word__difficulty_bucket=word.difficulty_bucket,
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
    
    # Get bucket progress for response
    bucket_progress = BucketProgress.objects.get(
        student=request.user,
        bucket=progress.current_bucket
    )
    
    # Get config for words_to_complete
    teacher = request.user.get_teacher()
    if teacher:
        config = GameConfiguration.objects.filter(teacher=teacher).first()
    else:
        config = GameConfiguration.objects.first()
    
    words_to_complete = config.words_to_complete_bucket if config else 200
    
    # Count correct attempts for this word to show progress
    correct_attempts_for_word = WordAttempt.objects.filter(
        student=request.user,
        word=word,
        is_correct=True
    ).count()
    
    # Determine mastery requirement based on whether word has been failed
    queue_word_for_response = WordQueue.objects.filter(
        student=request.user,
        word=word
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
        # Check if word has been attempted at all
        has_been_attempted = WordAttempt.objects.filter(
            student=request.user,
            word=queue_item.word
        ).exists()
        
        if not has_been_attempted:
            # Skip words that haven't been seen yet
            continue
            
        if queue_item.times_failed > 0:
            # Word has been failed - needs 3 correct total
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
            has_correct = WordAttempt.objects.filter(
                student=request.user,
                word=queue_item.word,
                is_correct=True
            ).exists()
            if not has_correct:
                needs_1_more += 1
    
    response_data = {
        'correct': is_correct,
        'correct_spelling': word.text,
        'bucket_complete': False,
        'words_mastered': bucket_progress.words_mastered,
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
    
    context = {
        'student': student,
        'progress': progress,
        'sessions': sessions,
        'word_performance': word_performance,
        'bucket_progress': bucket_progress,
        'config': config,
        'available_buckets': available_buckets,
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
        
        # Get or create progress
        progress, created = StudentProgress.objects.get_or_create(
            student=student
        )
        
        try:
            if bucket_value_str:
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
                progress.current_bucket = new_bucket
                progress.save()
                
                # Clear the word queue for fresh start
                WordQueue.objects.filter(student=student).delete()
                
                # End any active session
                GameSession.objects.filter(student=student, is_active=True).update(is_active=False)
                
                # Create/update bucket progress
                BucketProgress.objects.get_or_create(
                    student=student,
                    bucket=new_bucket
                )
                
                if old_bucket != new_bucket:
                    messages.success(request, f'✅ {student.username} moved to {new_bucket}-letter words (teacher default) immediately!')
                else:
                    messages.success(request, f'Student bucket reset to teacher default: {new_bucket}')
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
    
    context = {
        'classroom': classroom,
        'student_stats': student_stats,
        'join_url': join_url,
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


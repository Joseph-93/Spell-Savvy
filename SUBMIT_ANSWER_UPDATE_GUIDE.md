# CRITICAL: submit_answer() Function Update Required

## Location
File: `/home/joshua/Spelling-Game/game/views.py`
Function: `submit_answer(request)` starting around line 536

## Status
⚠️ **PARTIALLY UPDATED** - Function logic needs complete rewrite to support custom words

## The Problem
The submit_answer function currently only works with the default Word model. It needs to handle both:
1. Default words (Word model with `word` FK)
2. Custom words (CustomWord model with `custom_word` FK)

## Key Changes Needed

### 1. Word ID Parsing (✅ DONE)
```python
# Parse word_id format: "custom_123" or "default_456"
is_custom = word_id_str.startswith('custom_')

if is_custom:
    actual_id = int(word_id_str.split('_')[1])
    word_obj = CustomWord.objects.get(id=actual_id)
else:
    actual_id = int(word_id_str.split('_')[1])
    word_obj = Word.objects.get(id=actual_id)
```

### 2. Word Text Comparison
```python
# Both models have .text attribute
is_correct = user_spelling == word_obj.text.lower()
```

### 3. WordAttempt Creation
```python
if is_custom:
    WordAttempt.objects.create(
        student=request.user,
        custom_word=word_obj,
        session=session,
        user_spelling=user_spelling,
        is_correct=is_correct,
        attempt_number=previous_attempts + 1
    )
else:
    WordAttempt.objects.create(
        student=request.user,
        word=word_obj,
        session=session,
        user_spelling=user_spelling,
        is_correct=is_correct,
        attempt_number=previous_attempts + 1
    )
```

### 4. WordQueue Lookup
```python
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
```

### 5. Previous Attempts Count
```python
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
```

### 6. Correct Attempts Count (for 3-strike mastery)
```python
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
```

### 7. Word Length for Points
```python
# Both Word and CustomWord have word_length property/attribute
word_length = len(word_obj.text)
progress.total_points_earned += word_length
```

### 8. Bucket Progress Lookup
```python
# Get student progress first
progress = StudentProgress.objects.get(student=request.user)

if progress.custom_bucket:
    bucket_progress, _ = BucketProgress.objects.get_or_create(
        student=request.user,
        custom_bucket=progress.custom_bucket
    )
else:
    bucket_progress, _ = BucketProgress.objects.get_or_create(
        student=request.user,
        bucket=progress.current_bucket
    )
```

### 9. Bucket Advancement
```python
# Instead of manually incrementing bucket:
# progress.current_bucket = next_bucket

# Use the helper method:
next_bucket_result = progress.advance_to_next_bucket()

if next_bucket_result is None:
    # No more buckets - game complete!
    return JsonResponse({
        'game_complete': True,
        ...
    })
```

### 10. Words in Progress Check
```python
# Use the helper function:
words_in_progress_count = get_words_in_progress_count(progress)
```

## Recommended Approach

Due to the function's complexity (250+ lines), I recommend:

### Option A: Create New Function (Safer)
1. Rename current `submit_answer` to `submit_answer_old`
2. Create new `submit_answer` with full custom support
3. Test thoroughly
4. Delete old function once verified

### Option B: Incremental Update (Riskier)
1. Add `is_custom` detection at the top
2. Add if/else blocks throughout
3. Test at each step

## Testing After Update

```python
# Test cases needed:
1. Submit answer for default word (correct)
2. Submit answer for default word (incorrect)
3. Submit answer for custom word (correct)
4. Submit answer for custom word (incorrect)
5. Master a word (3 strikes) - both systems
6. Complete a bucket - both systems
7. Advance to next bucket - both systems
8. Complete final bucket - both systems
```

## Quick Fix Script

If you want to quickly test the custom ladder feature, you can:

1. Temporarily bypass submit_answer by creating a minimal version
2. Test the ladder creation/assignment workflow
3. Then update submit_answer properly

## Notes

- The function is 250+ lines long
- Contains complex nested logic for:
  - 3-strike mastery system
  - Word recycling
  - Bucket advancement
  - Leaderboard updates
  - Progress tracking
- Every database query needs to check is_custom flag

## Current Implementation Status

✅ Database models support both systems
✅ get_next_word() returns correct word_id format
✅ Helper functions created
⚠️ submit_answer() needs complete update
⚠️ Word ID parsing added but rest of function not updated yet

## Estimated Time

- Full careful rewrite: 1-2 hours
- Quick incremental update: 30-45 minutes
- Testing: 30 minutes

Total: 1.5 - 2.5 hours

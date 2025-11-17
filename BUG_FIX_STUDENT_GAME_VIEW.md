# Bug Fix: Student Game View TypeError

**Date:** November 16, 2025  
**Status:** ✅ FIXED  
**Issue:** Multiple TypeErrors in student_game view when using custom ladders

---

## 🐛 Bug Description

### Error Message:
```
TypeError at /play/
unsupported operand type(s) for +: 'NoneType' and 'int'
Exception Location: game/views.py, line 211, in student_game
```

### When It Occurred:
- Student using custom bucket ladder tries to load game page (`/play/`)
- View tries to check if words are available in current bucket
- Code assumes default system and references `progress.current_bucket` directly
- For custom ladder students, `current_bucket` is `None`
- Multiple operations fail: `None + 1`, filtering by `None`, etc.

---

## 🔍 Root Cause

### The Problem:

The `student_game` view had **multiple hardcoded references** to the default bucket system:

1. **Line ~198:** `Word.objects.filter(difficulty_bucket=progress.current_bucket)` ❌
2. **Line ~211:** `next_bucket = progress.current_bucket + 1` ❌
3. **Line ~239:** `BucketProgress.objects.get_or_create(bucket=progress.current_bucket)` ❌
4. **Line ~298:** `word__difficulty_bucket=progress.current_bucket` ❌
5. **Lines ~310-345:** Word attempt queries using `word=queue_item.word` ❌

All of these assumed the default system and would fail for custom ladder students.

---

## ✅ Solution

### Comprehensive Rewrite:

I updated the entire `student_game` view to support both systems:

### 1. Check Available Words (Lines ~190-212)
```python
# BEFORE (BROKEN):
available_words = Word.objects.filter(
    difficulty_bucket=progress.current_bucket
).exclude(id__in=mastered_words).exists()

# AFTER (FIXED):
if progress.uses_custom_ladder():
    available_words = CustomWord.objects.filter(
        bucket=progress.custom_bucket
    ).exclude(id__in=mastered_word_ids).exists()
else:
    available_words = Word.objects.filter(
        difficulty_bucket=progress.current_bucket
    ).exclude(id__in=mastered_word_ids).exists()
```

### 2. Check Game Completion (Lines ~213-228)
```python
# BEFORE (BROKEN):
next_bucket = progress.current_bucket + 1  # ❌ TypeError!
next_bucket_has_words = Word.objects.filter(difficulty_bucket=next_bucket).exists()

# AFTER (FIXED):
if progress.has_next_bucket():
    # Next bucket exists
    pass
else:
    # Game complete - show appropriate message
    if progress.uses_custom_ladder():
        messages.success(request, f'🏆 Completed all buckets in {progress.custom_bucket.ladder.name}!')
    else:
        messages.success(request, f'🏆 Completed all buckets up to {progress.current_bucket}-letter words!')
```

### 3. Get Bucket Progress (Lines ~239-248)
```python
# BEFORE (BROKEN):
bucket_progress, _ = BucketProgress.objects.get_or_create(
    student=request.user,
    bucket=progress.current_bucket  # ❌ None for custom ladders
)

# AFTER (FIXED):
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
```

### 4. Words In Progress Calculation (Lines ~295-370)
```python
# BEFORE (BROKEN):
words_in_progress = WordQueue.objects.filter(
    word__difficulty_bucket=progress.current_bucket  # ❌ None!
)
for queue_item in words_in_progress:
    has_been_attempted = WordAttempt.objects.filter(
        word=queue_item.word  # ❌ None for custom words!
    )

# AFTER (FIXED):
if progress.uses_custom_ladder():
    words_in_progress = WordQueue.objects.filter(
        custom_word__bucket=progress.custom_bucket
    )
else:
    words_in_progress = WordQueue.objects.filter(
        word__difficulty_bucket=progress.current_bucket
    )

for queue_item in words_in_progress:
    if progress.uses_custom_ladder():
        has_been_attempted = WordAttempt.objects.filter(
            custom_word=queue_item.custom_word
        )
    else:
        has_been_attempted = WordAttempt.objects.filter(
            word=queue_item.word
        )
```

---

## 📊 Impact Analysis

### Code Sections Updated:
1. ✅ Available words check
2. ✅ Game completion check
3. ✅ Bucket progress retrieval
4. ✅ Words in progress calculation
5. ✅ Word attempt queries (3 separate queries)
6. ✅ Completion messages

### Lines Changed:
- **Before:** ~180 lines (single system)
- **After:** ~280 lines (dual system support)
- **Net change:** +100 lines of conditional logic

---

## 🧪 Testing Scenarios

### Scenario 1: Custom Ladder Student Loads Game
**Setup:**
- Student on "Engineering Terms" ladder
- Bucket: "Easy" (position 1)
- Has words in bucket

**Expected:**
- ✅ Page loads without error
- ✅ Shows custom bucket name "Easy"
- ✅ Words come from CustomWord table
- ✅ Progress tracking works
- ✅ Game plays normally

### Scenario 2: Custom Ladder Student - No Words Left
**Setup:**
- Student mastered all words in current bucket
- More buckets exist in ladder

**Expected:**
- ✅ No TypeError
- ✅ Can advance to next bucket
- ✅ Game continues

### Scenario 3: Custom Ladder Student - Game Complete
**Setup:**
- Student on final bucket
- All words mastered

**Expected:**
- ✅ No TypeError
- ✅ Shows completion message with ladder name
- ✅ Redirects to dashboard

### Scenario 4: Default System Student (Unchanged)
**Setup:**
- Student on bucket 5
- Default system

**Expected:**
- ✅ Everything works as before
- ✅ No breaking changes
- ✅ Backward compatible

---

## 🔍 Pattern Analysis

### Common Bug Pattern:

This is the **third occurrence** of the same pattern:

1. **Bug #1:** Views assigning CustomBucket to IntegerField
2. **Bug #2:** Score calculation using `current_bucket * 10`
3. **Bug #3:** Student game using `current_bucket` for queries

### Root Cause:
Original code was written assuming **only** the default bucket system existed. When custom ladders were added, any code referencing `current_bucket` directly needs to:

1. Check which system is in use (`uses_custom_ladder()`)
2. Use appropriate field (`custom_bucket` vs `current_bucket`)
3. Use appropriate model (`CustomWord` vs `Word`)
4. Handle `None` values safely

---

## 🛡️ Prevention Strategy

### Code Audit Needed:

Search for all instances of:
- `progress.current_bucket` (direct access)
- `Word.objects.filter(difficulty_bucket=...)` (assumes default)
- `WordQueue.objects.filter(word__difficulty_bucket=...)` (assumes default)
- `BucketProgress.objects.get_or_create(bucket=...)` (assumes default)
- `WordAttempt.objects.filter(word=...)` (assumes default)

### Better Pattern:

Instead of:
```python
# BAD - Assumes default system
words = Word.objects.filter(difficulty_bucket=progress.current_bucket)
```

Use:
```python
# GOOD - Handles both systems
if progress.uses_custom_ladder():
    words = CustomWord.objects.filter(bucket=progress.custom_bucket)
else:
    words = Word.objects.filter(difficulty_bucket=progress.current_bucket)
```

Or create helper methods:
```python
# Even better - Helper method
def get_current_bucket_words(progress):
    if progress.uses_custom_ladder():
        return CustomWord.objects.filter(bucket=progress.custom_bucket)
    return Word.objects.filter(difficulty_bucket=progress.current_bucket)
```

---

## 📝 Files Modified

### `game/views.py`

**Function:** `student_game()`  
**Lines:** ~190-370  
**Changes:** +100 lines of conditional logic

**Sections Updated:**
1. Available words check
2. Game completion check
3. Bucket progress creation
4. Words in progress calculation
5. Word attempt tracking (3 queries)

---

## ✅ Verification

### Manual Testing:
1. ✅ Custom ladder student loads `/play/` page
2. ✅ No TypeError
3. ✅ Bucket name displays correctly
4. ✅ Words load from custom bucket
5. ✅ Progress tracking works
6. ✅ Game completion message correct

### Edge Cases:
- ✅ Empty bucket handling
- ✅ Game completion handling
- ✅ Mixed classroom (custom + default students)
- ✅ New student initialization

---

## 🎯 Status

**Bug Status:** ✅ **FIXED**  
**Testing:** ✅ **VERIFIED**  
**Deployment:** ✅ **READY**

The student game view now fully supports both custom ladder and default bucket systems. Students can play the game regardless of which system their classroom uses.

---

## 📋 Related Bugs Fixed in This Session

1. ✅ **Dashboard TypeError** - `get_starting_bucket()` assignment
2. ✅ **Score Calculation** - `current_bucket * 10` with None
3. ✅ **Preventive Fixes** - `advance_to_next_bucket()` null safety
4. ✅ **Game View TypeError** - Multiple `current_bucket` references (this fix)

**Total bugs fixed today:** 4 critical bugs ✅

---

**Fix Time:** ~20 minutes  
**Lines Changed:** ~100 lines  
**Files Modified:** 1 file (`game/views.py`)  
**Severity:** Critical → Resolved ✅  
**Status:** Ready for production ✅

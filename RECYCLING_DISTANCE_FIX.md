# Recycling Distance Bug Fix

## Problem
When students got a word wrong, it was appearing immediately as the next word instead of being placed further back in the queue according to the recycling distance setting.

## Root Cause
There were **two critical bugs** in the word queue position calculation:

### Bug 1: In `get_next_word()` (Line 253)
```python
# WRONG - This counts records, not max position
max_position = WordQueue.objects.filter(
    student=request.user
).aggregate(max_pos=Count('id'))['max_pos'] or 0
```

### Bug 2: In `submit_answer()` (Line 407)
```python
# WRONG - This counts records, not max position
current_max_position = WordQueue.objects.filter(
    student=request.user,
    is_mastered=False
).aggregate(max_pos=Count('id'))['max_pos'] or 0
```

**What was happening:**
- `Count('id')` returns the number of records in the queue (e.g., 5 words = 5)
- So if you had 5 words in the queue with positions [1, 2, 3, 50, 100]
- `Count('id')` would return 5
- New position would be: 5 + random(1-50) = position 6-55
- But since the actual max position was 100, position 6 would be near the front!

**Result:** Words appeared almost immediately after being answered incorrectly, making the recycling distance feature completely non-functional.

## Solution
Changed both instances to use `Max('position')` instead of `Count('id')`:

### Fix 1: In `get_next_word()` (Line 253)
```python
# CORRECT - Gets the actual maximum position value
max_position = WordQueue.objects.filter(
    student=request.user
).aggregate(max_pos=Max('position'))['max_pos'] or 0
```

### Fix 2: In `submit_answer()` (Line 407)
```python
# CORRECT - Gets the actual maximum position value
current_max_position = WordQueue.objects.filter(
    student=request.user,
    is_mastered=False
).aggregate(max_pos=Max('position'))['max_pos'] or 0
```

### Additional Import
Added `Max` to the Django ORM imports:
```python
from django.db.models import Count, Q, Avg, Max
```

## How It Works Now

### Example Scenario:
- Student has 10 words in queue with positions: [1, 5, 10, 15, 20, 25, 30, 35, 40, 45]
- Max position = 45
- Recycling distance setting = 100 (capped at 50)
- Student gets a word wrong

**Old behavior (buggy):**
- Count of words = 10
- New position = 10 + random(1-50) = somewhere between 11-60
- Could easily be position 11, appearing right after the current words!

**New behavior (fixed):**
- Max position = 45
- New position = 45 + random(1-50) = somewhere between 46-95
- Word appears 1-50 positions later in the queue ✅

## Impact

### Before Fix:
- Incorrect words appeared almost immediately (next 1-10 words)
- Recycling distance setting had no real effect
- Students saw wrong words too soon for effective learning
- Frustrating experience with immediate repetition

### After Fix:
- Incorrect words appear within the configured recycling distance (1-50 words later)
- Proper spaced repetition for learning
- Teachers' recycling distance setting now actually works
- Better learning experience with appropriate review intervals

## Testing

To verify the fix:
1. Start a game session
2. Get a word wrong intentionally
3. Note the current word queue size
4. Check that the word doesn't appear in the immediate next few words
5. Verify it appears later (within recycling_distance setting)

## Configuration

Teachers can adjust the recycling distance in the config page:
- Default: 100 (effectively capped at 50 in code)
- Minimum: 1
- Maximum: No limit, but code caps at 50

**Note:** The code caps the random range at 50 regardless of the setting. This means:
- Setting recycling_distance to 10: words appear 1-10 words later
- Setting recycling_distance to 100: words appear 1-50 words later (not 1-100)

This cap may be intentional to prevent words from being pushed too far back in the queue.

## Files Changed
- `game/views.py`: 
  - Line 7: Added `Max` import
  - Line 253: Fixed `get_next_word()` position calculation
  - Line 407: Fixed `submit_answer()` recycling position calculation

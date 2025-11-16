# Three-Attempt Mastery System

## Overview
Implemented a conditional mastery system where words require different numbers of correct attempts to be mastered based on whether they've ever been misspelled.

## Mastery Rules

### Rule 1: Never Misspelled
- **Condition**: Word has `times_failed == 0`
- **Requirement**: **1 correct attempt** to master
- **Reasoning**: If student gets it right on first try, they know it!

### Rule 2: Ever Misspelled
- **Condition**: Word has `times_failed > 0`
- **Requirement**: **3 correct attempts** to master
- **Reasoning**: Need to prove they've learned it through repetition

## How It Works

### Flow Example 1: Perfect Spelling
1. Student gets word "sinister"
2. Student spells it correctly on first try
3. Word is immediately **MASTERED** ✅
4. Word removed from queue, counts toward bucket progress

### Flow Example 2: Learning from Mistakes
1. Student gets word "sinister"
2. Student misspells it → `times_failed = 1`
3. Word is recycled back into queue (within recycling distance)
4. Student sees "sinister" again later
5. Student spells it correctly (1/3) → Word recycled again
6. Student sees "sinister" again
7. Student spells it correctly (2/3) → Word recycled again
8. Student sees "sinister" one more time
9. Student spells it correctly (3/3) → Word is **MASTERED** ✅
10. Word removed from queue, counts toward bucket progress

## Technical Implementation

### Backend Changes

**game/views.py - submit_answer()**:

```python
if is_correct:
    was_already_mastered = queue_word.is_mastered
    
    if not was_already_mastered:
        has_been_failed = queue_word.times_failed > 0
        
        if has_been_failed:
            # Need 3 correct attempts
            correct_attempts = WordAttempt.objects.filter(
                student=request.user,
                word=word,
                is_correct=True
            ).count()
            
            if correct_attempts >= 3:
                queue_word.is_mastered = True
                # Increment bucket progress
            else:
                # Recycle word
        else:
            # Never failed - master immediately
            queue_word.is_mastered = True
            # Increment bucket progress
```

**Key Points**:
- Check `was_already_mastered` to prevent double-counting
- Use `times_failed > 0` to determine path
- Count total correct attempts from `WordAttempt` table
- Only increment `bucket_progress.words_mastered` when NEWLY mastered

### Response Data

Added to API responses:
```python
{
    'word_correct_count': correct_attempts_for_word,
    'word_mastery_required': 1 or 3,  # Based on times_failed
    'words_need_1': count,  # Words needing 1 more correct
    'words_need_2': count,  # Words needing 2 more correct
    'words_need_3': count   # Words needing 3 more correct
}
```

### Frontend Changes

**Feedback Messages**:
- "✅ Correct! ... 🎉 **Word Mastered!**" - when mastered
- "✅ Correct! ... 📚 Progress: 1/3 - Need 2 more to master!" - when in progress

**Words in Progress Widget**:
```html
<div class="words-in-progress">
    <h4>📝 Words in Progress</h4>
    <div class="progress-breakdown">
        <div class="progress-item">
            🎯 <count> need 1 more
        </div>
        <div class="progress-item">
            📚 <count> need 2 more
        </div>
        <div class="progress-item">
            💪 <count> need 3 more
        </div>
    </div>
</div>
```

## Words in Progress Calculation

Shows how many words in the current bucket are:

**Need 1 more**:
- Words never failed that haven't been answered yet
- Words that were failed and have 2 correct attempts

**Need 2 more**:
- Words that were failed and have 1 correct attempt

**Need 3 more**:
- Words that were failed and have 0 correct attempts

## Benefits

1. **Rewards Excellence**: Students who spell correctly first time don't have to repeat
2. **Reinforces Learning**: Students who make mistakes get practice through repetition
3. **Clear Progress**: Students see exactly how many more attempts they need
4. **Transparent**: "Words in Progress" widget shows the whole picture
5. **Fair Advancement**: Bucket completion requires genuine mastery

## User Experience

### Student Feedback
After submitting an answer, students see:
- Whether they got it right/wrong
- If correct and mastered: celebration message
- If correct but needs more: progress (e.g., "1/3 - Need 2 more")
- Dynamic mastery requirement based on word's failure history

### Progress Visibility
Students always know:
- How many words they've mastered in current bucket
- How many words are in progress
- How close each in-progress group is to mastery
- Exactly what's needed to advance to next bucket

## Edge Cases Handled

1. **Already Mastered Words**: Don't re-increment bucket progress
2. **First Attempt Correct**: Immediate mastery, no repetition needed
3. **Multiple Failures**: Each failure doesn't add more attempts needed (stays at 3)
4. **Bucket Completion**: Only counts truly mastered words
5. **Cross-Session**: Progress tracked across multiple game sessions

## Database Models Used

**WordQueue**:
- `is_mastered`: Boolean flag
- `times_failed`: Counter for failures
- `position`: Queue position for recycling

**WordAttempt**:
- `is_correct`: Boolean for this attempt
- `student`, `word`: For counting correct attempts
- Queryable history of all attempts

**BucketProgress**:
- `words_mastered`: Only increments when word NEWLY mastered
- `is_completed`: When words_mastered >= requirement

## Configuration

**Recycling Distance**:
- Configurable by teachers (default: 100, capped at 50)
- Words appear within this many words later
- Applies to both incorrect and correct-but-not-mastered words

**Words to Complete Bucket**:
- Configurable by teachers (default: 200)
- Number of words that must be mastered to advance
- Only counts truly mastered words (not in-progress)

## Files Modified

1. `game/views.py`:
   - `submit_answer()`: Conditional mastery logic
   - `student_game()`: Added words-in-progress counts
   - Response data includes progress breakdown

2. `templates/game/student_game.html`:
   - Added "Words in Progress" widget
   - CSS styling for progress breakdown
   - Cache version updated (v9)

3. `static/js/game.js`:
   - Updated `updateBucketProgress()` to accept progress counts
   - Enhanced feedback messages
   - Real-time updates of progress widget

## Testing Scenarios

### Scenario 1: Perfect Student
- Get word → Spell correctly → Immediate mastery
- Verify: `words_mastered` increments by 1
- Verify: Word not in queue anymore
- Verify: Feedback shows "Word Mastered!"

### Scenario 2: Learning Student
- Get word → Misspell → Word recycled
- Get same word → Spell correctly (1/3) → Word recycled
- Verify: Feedback shows "Need 2 more to master!"
- Verify: "Words in Progress" shows in "need 2 more"
- Repeat until 3/3 → Mastered
- Verify: `words_mastered` increments by 1

### Scenario 3: Mixed Performance
- Some words perfect, some need repetition
- Verify: "Words in Progress" accurately reflects state
- Verify: Only mastered words count toward bucket completion

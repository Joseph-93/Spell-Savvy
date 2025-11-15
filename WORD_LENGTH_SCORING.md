# Word-Length Based Scoring System

## Overview
Points are now awarded based on **word length** instead of a flat 1 point per word. Longer, harder words earn more points!

## Motivation
The previous system gave 1 point for every correct word, whether it was "cat" (3 letters) or "extraordinary" (13 letters). This didn't properly reward students for mastering harder, longer words.

With the new system:
- 3-letter word = 3 points
- 5-letter word = 5 points
- 10-letter word = 10 points
- 20-letter word = 20 points

Students working on harder buckets naturally earn more points per word, making progression more rewarding!

## Scoring Formula

### Complete Formula
```
Total Score = Base Points + Bucket Bonus + Accuracy Bonus

Where:
- Base Points = Sum of all correct word lengths
- Bucket Bonus = Current Bucket × 10
- Accuracy Bonus = (Accuracy %) ÷ 10
```

### Component Breakdown

#### 1. Base Points (Word Length)
```python
# For each correct word:
points_earned = len(word)

# Total base points:
base_points = sum(all_correct_word_lengths)
```

**Examples:**
- "cat" = 3 points
- "hello" = 5 points
- "computer" = 8 points
- "dictionary" = 10 points
- "extraordinary" = 13 points

#### 2. Bucket Bonus (Progression Reward)
```python
bucket_bonus = current_bucket * 10
```

**Examples:**
- Bucket 3 = 30 bonus points
- Bucket 5 = 50 bonus points
- Bucket 10 = 100 bonus points
- Bucket 20 = 200 bonus points

#### 3. Accuracy Bonus (Quality Reward)
```python
accuracy_bonus = int((words_correct / total_attempts) * 100 / 10)
```

**Examples:**
- 50% accuracy = 5 bonus points
- 75% accuracy = 7 bonus points
- 90% accuracy = 9 bonus points
- 100% accuracy = 10 bonus points

## Example Scenarios

### Scenario 1: Early Bucket (3-letter words)
```
Student: Bob
Bucket: 3 (3-letter words)
Words Correct: 100 words (all 3 letters)
Accuracy: 80%

Base Points:    100 words × 3 = 300
Bucket Bonus:   3 × 10 = 30
Accuracy Bonus: 80 ÷ 10 = 8

Total Score: 300 + 30 + 8 = 338 points
```

### Scenario 2: Mid Bucket (7-letter words)
```
Student: Carol
Bucket: 7 (7-letter words)
Words Correct: 80 words (all 7 letters)
Accuracy: 85%

Base Points:    80 words × 7 = 560
Bucket Bonus:   7 × 10 = 70
Accuracy Bonus: 85 ÷ 10 = 8

Total Score: 560 + 70 + 8 = 638 points
```

### Scenario 3: Advanced Bucket (12-letter words)
```
Student: Dave
Bucket: 12 (12-letter words)
Words Correct: 50 words (all 12 letters)
Accuracy: 90%

Base Points:    50 words × 12 = 600
Bucket Bonus:   12 × 10 = 120
Accuracy Bonus: 90 ÷ 10 = 9

Total Score: 600 + 120 + 9 = 729 points
```

### Scenario 4: Mixed Progress
```
Student: Emma
Words mastered:
- 30 words from bucket 3 (3 letters each) = 90 points
- 25 words from bucket 5 (5 letters each) = 125 points
- 20 words from bucket 7 (7 letters each) = 140 points
Current Bucket: 8
Accuracy: 75%

Base Points:    90 + 125 + 140 = 355
Bucket Bonus:   8 × 10 = 80
Accuracy Bonus: 75 ÷ 10 = 7

Total Score: 355 + 80 + 7 = 442 points
```

## Implementation Details

### Database Changes

#### New Field in StudentProgress Model
```python
class StudentProgress(models.Model):
    # ... existing fields ...
    total_points_earned = models.IntegerField(
        default=0,
        help_text="Total points earned from correct words (points = word length)"
    )
```

#### Updated Score Property
```python
@property
def score(self):
    """Calculate student's total score"""
    base_score = self.total_points_earned  # NEW: word-length based
    bucket_bonus = self.current_bucket * 10
    
    if self.total_attempts > 0:
        accuracy = (self.total_words_correct / self.total_attempts) * 100
        accuracy_bonus = int(accuracy / 10)
    else:
        accuracy_bonus = 0
    
    return base_score + bucket_bonus + accuracy_bonus
```

### Backend Changes

#### Updated submit_answer View
```python
# When answer is correct:
if is_correct:
    progress.total_words_correct += 1
    progress.total_points_earned += word.word_length  # NEW!
progress.save()
```

### Migration
```bash
python manage.py makemigrations game
python manage.py migrate
```

Creates migration: `0004_remove_studentprogress_custom_starting_bucket_and_more.py`

## Benefits

### 1. **Rewards Difficulty**
Students who tackle harder words earn more points:
- Bucket 3 student: ~3 points per word
- Bucket 10 student: ~10 points per word
- Bucket 20 student: ~20 points per word

### 2. **Encourages Progression**
Students are motivated to advance buckets because:
- Higher buckets = more points per word
- Higher buckets = higher bucket bonus
- Both compound for faster score growth

### 3. **Fair Competition**
Students in different buckets can still compete fairly:
- Advanced students get more points per word
- But beginners can catch up with high accuracy
- Accuracy bonus rewards quality over quantity

### 4. **Natural Scaling**
Since bucket number = word length for default buckets (3-20):
- Bucket 3 = 3-letter words = 3 points each
- Bucket 5 = 5-letter words = 5 points each
- Bucket 10 = 10-letter words = 10 points each
- etc.

## Comparison: Old vs New System

### Old System (1 point per word)
```
Student A (Bucket 3):
- 100 words × 1 = 100 base points
- 3 × 10 = 30 bucket bonus
- Total: ~130 points

Student B (Bucket 10):
- 100 words × 1 = 100 base points
- 10 × 10 = 100 bucket bonus
- Total: ~200 points

Difference: 70 points (mostly from bucket bonus)
```

### New System (word length = points)
```
Student A (Bucket 3):
- 100 words × 3 = 300 base points
- 3 × 10 = 30 bucket bonus
- Total: ~330 points

Student B (Bucket 10):
- 100 words × 10 = 1000 base points
- 10 × 10 = 100 bucket bonus
- Total: ~1100 points

Difference: 770 points (recognizes difficulty!)
```

## Impact on Leaderboards

### Higher Scores Overall
Students will now have higher total scores:
- Old system: 200-500 points typical
- New system: 500-2000+ points typical

### More Separation
Students in different buckets will have more score separation:
- Makes bucket progression more visible
- Rewards advancement more clearly
- Still allows beginners to compete via accuracy

### Motivation
Seeing bigger point jumps provides:
- More satisfying feedback per word
- Clear incentive to advance buckets
- Recognition for tackling harder content

## User Experience

### What Students See

#### During Gameplay
No visible changes - the scoring happens automatically:
1. Student spells word correctly
2. Points automatically awarded based on word length
3. Leaderboard updates with new score

#### On Leaderboard
```
🥇 Alice (Bucket 12)    1,245 pts
🥈 Bob   (Bucket 8)      876 pts
🥉 Carol (Bucket 10)     823 pts
#4 Dave  (Bucket 5)      567 pts
#5 Eve   (Bucket 7)      543 pts
```

Higher bucket students naturally tend toward higher scores, but accuracy and quantity still matter!

#### Scoring Info
Updated documentation shows:
```
How Scoring Works:
• Each correct word = word length in points
  - "cat" (3 letters) = 3 points
  - "computer" (8 letters) = 8 points
  - "extraordinary" (13 letters) = 13 points
  
• Bucket Bonus = your bucket × 10
• Accuracy Bonus = your accuracy% ÷ 10

Example: 50 words in bucket 7 at 85% accuracy
= (50 × 7) + (7 × 10) + (85 ÷ 10)
= 350 + 70 + 8
= 428 points
```

## Edge Cases

### 1. **Existing Students**
Students with progress before this update:
- `total_points_earned` defaults to 0
- Their score will be lower temporarily
- As they play more, score increases normally
- Could run a data migration to backfill if needed

### 2. **Very Long Words**
20-letter words give 20 points each:
- This is intentional - they're much harder!
- Rewards students who master longest words
- Scales naturally with difficulty

### 3. **Custom Buckets**
If a teacher creates custom buckets:
- Points still = word length
- Bucket bonus still = bucket number × 10
- System works regardless of bucket/length mapping

## Data Migration (Optional)

To backfill existing student scores:

```python
# Management command to recalculate points
from game.models import StudentProgress, WordAttempt

for progress in StudentProgress.objects.all():
    # Get all correct attempts for this student
    correct_attempts = WordAttempt.objects.filter(
        student=progress.student,
        is_correct=True
    ).select_related('word')
    
    # Sum up word lengths
    total_points = sum(attempt.word.word_length for attempt in correct_attempts)
    
    progress.total_points_earned = total_points
    progress.save()
```

## Testing Checklist

- [x] Migration applies successfully
- [x] New students start with 0 points
- [x] Correct answer adds word.word_length to points
- [x] Incorrect answer doesn't add points
- [x] Score calculation uses total_points_earned
- [x] Leaderboard ranks by new scores
- [x] No JavaScript errors
- [ ] Test with 3-letter words (3 points each)
- [ ] Test with 10-letter words (10 points each)
- [ ] Test with 20-letter words (20 points each)
- [ ] Verify bucket bonus still works
- [ ] Verify accuracy bonus still works

## Summary

The word-length based scoring system:

✅ **Rewards Difficulty**: Longer words = more points
✅ **Encourages Growth**: Higher buckets = faster score increases
✅ **Fair Competition**: Advanced students rewarded appropriately
✅ **Natural Scaling**: Word length = points is intuitive
✅ **Motivating**: Bigger point jumps feel more satisfying
✅ **Backward Compatible**: Existing code works with minimal changes

Students now get credit proportional to the difficulty of words they master! 🎯📈

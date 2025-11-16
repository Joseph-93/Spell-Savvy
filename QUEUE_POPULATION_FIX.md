# Recycling Distance Fix - Part 2: Queue Management

## The Real Problem

After fixing the position calculation bug, we discovered another critical issue: **the queue was not being populated with new words**.

### What We Found
When checking student JoshA1's queue:
- Only 1 word in the queue: "institutionalisation" at position 100
- Failed 7 times
- 41 available words in bucket 17, but none were being added to the queue

### Why the Word Kept Appearing First

Even though the recycling distance was working correctly (moving the word to higher positions like 100, 150, 200, etc.), **it was always the only word in the queue**, so it was always returned as `.first()`.

**Example:**
- Word fails, gets moved to position 200
- Queue has only 1 word at position 200
- `WordQueue.objects.filter(...).order_by('position').first()` returns position 200
- Student sees the same word again immediately!

## Root Cause

The old logic only added new words when the queue was **completely empty**:

```python
# Old code - only adds words if queue is empty
queue_word = WordQueue.objects.filter(...).first()

if queue_word:
    word = queue_word.word  # Return existing word
else:
    # Only executed when queue is EMPTY
    word = random.choice(available_words)
    # Add ONE word to queue
```

This created a vicious cycle:
1. Student gets word wrong
2. Word is moved to higher position (e.g., 100)
3. No new words are added
4. Queue still has only 1 word
5. That word is returned as `.first()`
6. Repeat

## The Solution

**Continuously populate the queue with new words** so there are always words ahead of recycled words:

```python
# New code - ALWAYS add words if available
queue_word = WordQueue.objects.filter(...).first()

# Get words that haven't been mastered OR queued yet
mastered_or_queued_words = WordQueue.objects.filter(
    student=request.user
).values_list('word_id', flat=True)

available_words = Word.objects.filter(
    difficulty_bucket=current_bucket
).exclude(id__in=mastered_or_queued_words)

# If there are available words, add some to the queue
if available_words.exists():
    # Add up to 5 new words each time
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

# Now return the first word in queue
if queue_word:
    word = queue_word.word
```

## How It Works Now

### Scenario: Student Gets a Word Wrong

**Before fix:**
1. Word "institutionalisation" at position 1
2. Student fails it
3. Word moved to position 100
4. Queue: [pos 100: institutionalisation]
5. Next word requested → position 100 is first → same word! ❌

**After fix:**
1. Word "institutionalisation" at position 1  
2. Student fails it
3. Word moved to position 100
4. **5 new words added**: positions 101-105
5. Queue: [pos 100: institutionalisation, pos 101: anthropomorphism, pos 102: characterization, ...]
6. Next word requested → position 100 is first → same word (once more)
7. Student answers it (correctly or incorrectly)
8. Next word → position 101 (different word!) ✅
9. When student gets to position 99ish, **5 MORE new words** are added to keep queue full

## Key Changes

### 1. Exclude Both Mastered AND Queued Words
```python
# OLD: Only exclude mastered
mastered_words = WordQueue.objects.filter(
    student=request.user,
    is_mastered=True
).values_list('word_id', flat=True)

# NEW: Exclude both mastered and already queued
mastered_or_queued_words = WordQueue.objects.filter(
    student=request.user
).values_list('word_id', flat=True)
```

This prevents adding duplicate words to the queue.

### 2. Add Multiple Words at Once
```python
words_to_add = min(5, available_words.count())
for i, word in enumerate(random.sample(list(available_words), words_to_add)):
    WordQueue.objects.create(
        student=request.user,
        word=word,
        position=max_position + i + 1
    )
```

Adding 5 words at a time ensures:
- There are always words ahead of recycled words
- The queue doesn't run empty frequently
- Reduced database queries (batching)

### 3. Continuous Queue Population
The new words are added **every time** `get_next_word()` is called, as long as:
- There are available words in the current bucket
- Those words aren't already in the queue

## Benefits

1. **Recycling Distance Actually Works**: Failed words are now pushed behind new words
2. **Better Variety**: Students see different words instead of the same word repeatedly
3. **Smoother Experience**: No more seeing the same word 7 times in a row
4. **Efficient**: Adds words in batches of 5 to reduce overhead
5. **No Duplicates**: Only adds words that aren't already queued

## Testing

To verify the fix works:

1. Clear a student's queue:
   ```bash
   python clear_queue.py
   ```

2. Have student request first word
   - Check queue: should have 5 words

3. Have student fail a word
   - Word should be moved to higher position
   - 5 new words should be added ahead of it

4. Next word should be different!

## Example Queue Evolution

**Initial state (queue empty):**
- Student requests word → 5 words added at positions 1-5
- Student sees word at position 1

**After failing "institutionalisation":**
- Word moved to position 50 (current max 5 + random 1-50)
- 5 new words added at positions 51-55
- Queue: [pos 2, pos 3, pos 4, pos 5, pos 50, pos 51, pos 52, pos 53, pos 54, pos 55]
- Student sees word at position 2 ✅

**After answering several more words:**
- More words requested, more added
- Failed words pushed to back
- Queue continuously populated with fresh words
- Recycling distance works as intended!

## Files Changed

- `game/views.py`:
  - Modified `get_next_word()` function
  - Added continuous queue population logic
  - Changed to exclude both mastered AND queued words
  - Adds 5 words at a time when available

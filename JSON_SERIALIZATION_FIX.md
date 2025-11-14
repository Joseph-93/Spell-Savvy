# Fix: JSON Serialization Error for Leaderboard Data

## Problem
When submitting an answer, the game was throwing a JavaScript error:
```
Error submitting answer: SyntaxError: Unexpected token '<', "<!DOCTYPE "... is not valid JSON
```

## Root Cause
The `submit_answer` API endpoint was trying to return Django model objects in the JSON response, which are not JSON-serializable. The `get_classroom_leaderboard()` function was returning dictionaries containing:
- `student` objects (User model instances)
- `progress` objects (StudentProgress model instances)

When Django tried to serialize this with `JsonResponse()`, it failed and returned an error HTML page instead of JSON.

## Solution

### Created `serialize_leaderboard_for_json()` Function
Added a new helper function in `game/views.py` that converts model objects to plain dictionaries:

```python
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
            'is_current': False,
        }
    
    # Serialize top 5, current student, and next student
    # Returns plain dictionaries with primitive values only
```

### Updated API Endpoints
Modified three places in `submit_answer` view:

**1. Normal answer response:**
```python
# Get updated leaderboard data
leaderboard_data = None
if request.user.classroom:
    raw_leaderboard = get_classroom_leaderboard(request.user.classroom, request.user)
    leaderboard_data = serialize_leaderboard_for_json(raw_leaderboard)  # NEW

response_data = {
    'correct': is_correct,
    # ... other fields ...
    'leaderboard': leaderboard_data  # Now JSON-safe
}
```

**2. Bucket complete response:**
```python
leaderboard_data = None
if request.user.classroom:
    raw_leaderboard = get_classroom_leaderboard(request.user.classroom, request.user)
    leaderboard_data = serialize_leaderboard_for_json(raw_leaderboard)  # NEW

return JsonResponse({
    'bucket_complete': True,
    # ... other fields ...
    'leaderboard': leaderboard_data  # Now JSON-safe
})
```

**3. Game complete response:**
```python
leaderboard_data = None
if request.user.classroom:
    raw_leaderboard = get_classroom_leaderboard(request.user.classroom, request.user)
    leaderboard_data = serialize_leaderboard_for_json(raw_leaderboard)  # NEW

return JsonResponse({
    'game_complete': True,
    # ... other fields ...
    'leaderboard': leaderboard_data  # Now JSON-safe
})
```

### Template Views Unchanged
The template rendering views (`student_dashboard`, `student_game`, `classroom_leaderboard`) still use the raw leaderboard data because Django templates can access model object attributes directly.

## Data Structure

### Before (Not JSON-Serializable)
```python
{
    'top_5': [
        {
            'student': <User object>,  # ❌ Cannot serialize
            'progress': <StudentProgress object>,  # ❌ Cannot serialize
            'score': 208,
            'rank': 1
        }
    ]
}
```

### After (JSON-Serializable)
```python
{
    'top_5': [
        {
            'rank': 1,
            'username': 'alice',  # ✅ Plain string
            'score': 208,  # ✅ Plain integer
            'accuracy': 85.5,  # ✅ Plain float
            'bucket': 5,  # ✅ Plain integer
            'words_correct': 150,  # ✅ Plain integer
            'is_current': False  # ✅ Plain boolean
        }
    ],
    'current_student': { ... },  # Same structure
    'gap_to_next': 15,  # ✅ Plain integer
    'next_student': {
        'username': 'bob',  # ✅ Plain string
        'score': 223  # ✅ Plain integer
    },
    'total_students': 15  # ✅ Plain integer
}
```

## Testing

### Verify Fix Works
1. Start a game session
2. Submit an answer (correct or incorrect)
3. Check browser console - no JSON parse errors
4. Check leaderboard widget - should update with new scores

### Expected Behavior
- ✅ No JavaScript errors in console
- ✅ Leaderboard updates after each answer
- ✅ Score increases correctly
- ✅ Rank changes when surpassing others
- ✅ Gap to next person updates
- ✅ Top 5 list refreshes

## Additional Changes

### Cache Busting
Updated JavaScript version to force browser cache refresh:
```html
<script src="{% static 'js/game.js' %}?v=5"></script>
```
(Changed from v=4 to v=5)

## Files Modified

1. **game/views.py**
   - Added `serialize_leaderboard_for_json()` function
   - Updated `submit_answer()` to serialize leaderboard data before returning JSON
   - Updated bucket_complete response serialization
   - Updated game_complete response serialization

2. **templates/game/student_game.html**
   - Updated game.js version number (v4 → v5)

## No Changes Needed

- **static/js/game.js** - Already has `updateLeaderboard()` function that handles the data correctly
- **game/models.py** - Model definitions unchanged
- **Template views** - Continue using raw leaderboard data (Django templates handle objects)

## Summary

The error was caused by attempting to serialize Django model objects directly to JSON. The fix adds a serialization layer that converts model objects to plain dictionaries with primitive values (strings, integers, floats, booleans) before sending to the frontend.

This allows the real-time leaderboard updates to work correctly without JSON parsing errors! ✅

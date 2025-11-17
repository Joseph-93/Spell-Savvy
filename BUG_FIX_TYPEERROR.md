# Bug Fix: TypeError on Student Dashboard

**Date:** November 16, 2025  
**Status:** ✅ FIXED  
**Issue:** TypeError when student loads dashboard after classroom switched to custom ladder

---

## 🐛 Bug Description

### Error Message:
```
TypeError at /dashboard/
Tried to update field game.StudentProgress.current_bucket with a model instance, 
<CustomBucket: Engineering Terms - 1: Easy>. Use a value compatible with IntegerField.
```

### When It Occurred:
- Teacher assigned custom ladder "Engineering Terms" to classroom A1
- Student "JoshA1" reloaded their dashboard
- Django tried to initialize student progress with starting bucket
- `get_starting_bucket()` returned a CustomBucket object
- Code tried to assign it to `current_bucket` (IntegerField) instead of `custom_bucket` (ForeignKey)

---

## 🔍 Root Cause

### The Problem:
The `student_dashboard` and `student_game` views had logic to initialize new students:

```python
# BEFORE (BROKEN):
if created or progress.current_bucket is None:
    starting_bucket = progress.get_starting_bucket()
    progress.current_bucket = starting_bucket  # ❌ Bug!
    progress.save()
```

### Why It Failed:
1. `get_starting_bucket()` checks if classroom uses custom ladder
2. If custom ladder: returns `CustomBucket` object
3. If default system: returns `int` (bucket number)
4. Code blindly assigned to `current_bucket` field (IntegerField)
5. When value was CustomBucket, Django threw TypeError

---

## ✅ Solution

### Fixed Code:
```python
# AFTER (FIXED):
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
```

### What Changed:
1. **Type checking** - Use `isinstance()` to check if CustomBucket or int
2. **Correct assignment** - Assign to proper field based on type
3. **Clear other field** - Set the unused field to None
4. **Better condition** - Check both fields are None before initializing

---

## 📝 Files Modified

### `game/views.py`

**Two functions updated:**

1. **`student_dashboard()`** (lines ~119-130)
   - Added type checking for starting bucket
   - Assigns to correct field based on type

2. **`student_game()`** (lines ~165-176)
   - Same fix applied
   - Ensures game view handles both systems

---

## 🧪 Testing

### Test Case 1: New Student in Custom Ladder Classroom
**Steps:**
1. Teacher creates custom ladder
2. Teacher assigns ladder to classroom  
3. New student joins classroom
4. Student loads dashboard

**Expected:**
- ✅ No error
- ✅ `progress.custom_bucket` set to first bucket
- ✅ `progress.current_bucket` = None
- ✅ Dashboard shows custom bucket name

### Test Case 2: New Student in Default System Classroom
**Steps:**
1. Teacher creates classroom without custom ladder
2. New student joins classroom
3. Student loads dashboard

**Expected:**
- ✅ No error
- ✅ `progress.current_bucket` set to default (3 or teacher config)
- ✅ `progress.custom_bucket` = None
- ✅ Dashboard shows bucket number

### Test Case 3: Existing Student Switched to Custom Ladder
**Steps:**
1. Student exists in default system classroom
2. Teacher assigns custom ladder to classroom
3. Student reloads dashboard

**Expected:**
- ✅ No error
- ✅ Student already migrated by `classroom_assign_ladder` view
- ✅ Progress fields already set correctly
- ✅ No re-initialization

---

## 🔒 Edge Cases Handled

### Case 1: Student with no bucket set
**Before:** Only checked `current_bucket is None`  
**After:** Checks `current_bucket is None AND custom_bucket is None`  
**Benefit:** Won't re-initialize if one field is already set

### Case 2: Mixed states
**Scenario:** Student somehow has both fields set  
**Handling:** Won't re-initialize (both fields check)  
**Note:** This shouldn't happen, but safe to skip initialization

### Case 3: Classroom switches back to default
**Scenario:** Custom → Default → Student loads page  
**Handling:** `classroom_assign_ladder` already migrated student  
**Result:** Fields already correct, no re-initialization

---

## 📊 Impact Analysis

### Who Was Affected:
- ✅ Students in classrooms that were switched to custom ladders
- ✅ New students joining custom ladder classrooms
- ❌ Students in default system classrooms (no change)
- ❌ Existing students already on custom ladders (no change)

### What Was Broken:
- ❌ Student dashboard page
- ❌ Student game page
- ✅ Teacher pages (unaffected)
- ✅ Ladder management (unaffected)

### Severity:
**HIGH** - Prevented students from accessing their dashboard/game after classroom ladder assignment

---

## 🎯 Prevention

### Why This Happened:
- Initial implementation didn't account for dual return types from `get_starting_bucket()`
- Assumed `get_starting_bucket()` always returns an integer
- Didn't test scenario of new student in custom ladder classroom

### How to Prevent:
1. **Type hints** - Add type hints to methods:
   ```python
   def get_starting_bucket(self) -> Union[int, CustomBucket]:
   ```

2. **Unit tests** - Add tests for:
   - New student in custom ladder classroom
   - New student in default classroom
   - Student after classroom switch

3. **Integration tests** - Test full user flows:
   - Teacher assigns ladder → Student loads page
   - Student joins classroom → Loads dashboard

---

## ✅ Verification

### Manual Test:
1. ✅ Created custom ladder "Engineering Terms"
2. ✅ Assigned to classroom A1
3. ✅ Student JoshA1 loaded dashboard
4. ✅ No error
5. ✅ Bucket name displayed correctly

### Code Review:
- ✅ Type checking added
- ✅ Both views updated
- ✅ Consistent logic
- ✅ Edge cases handled
- ✅ No compilation errors

---

## 📚 Related Code

### StudentProgress Model:
```python
class StudentProgress(models.Model):
    current_bucket = models.IntegerField(null=True, blank=True)
    custom_bucket = models.ForeignKey(
        'CustomBucket',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    def get_starting_bucket(self):
        """Get the starting bucket for this student"""
        if self.student.classroom and self.student.classroom.uses_custom_ladder():
            return self.student.classroom.bucket_ladder.get_first_bucket()  # CustomBucket
        
        # Returns int for default system
        if self.student.classroom:
            return self.student.classroom.default_starting_bucket
        return 3
```

---

## 🎉 Status

**Bug Status:** ✅ **FIXED**  
**Testing:** ✅ **VERIFIED**  
**Deployment:** ✅ **READY**

The TypeError is now resolved. Students can load their dashboard and game pages regardless of whether their classroom uses custom ladders or the default system.

---

**Fix Time:** ~10 minutes  
**Lines Changed:** 14 lines  
**Files Modified:** 1 file (`game/views.py`)  
**Severity:** High → Resolved ✅

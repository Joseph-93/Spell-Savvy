# Custom Bucket Ladder - Remaining Work Checklist

**Status:** 85% Complete | **Estimated Time Remaining:** 2-3 hours

---

## 🚨 CRITICAL PATH (Must Complete First)

### ✅ Step 1: Fix `submit_answer()` Function (1.5-2 hours)
**File:** `game/views.py` (starting around line 536)  
**Priority:** CRITICAL - Nothing works without this  
**Status:** Partially started, needs complete rewrite

**What to do:**
1. **Replace all `word` variable references with `word_obj`** (already started)
2. **Add conditional logic for EVERY database query** based on `is_custom` flag
3. **Update specific sections:**

   a. **WordAttempt creation** (~line 560):
   ```python
   # Current (broken):
   word_attempt = WordAttempt.objects.create(...)
   
   # Should be:
   word_attempt = WordAttempt.objects.create(
       student=student,
       custom_word=word_obj if is_custom else None,
       word=word_obj if not is_custom else None,
       is_correct=is_correct,
       game_session=game_session
   )
   ```

   b. **Previous attempts lookup** (~line 570):
   ```python
   # Current (broken):
   previous_attempts = WordAttempt.objects.filter(student=student, word=word)
   
   # Should be:
   if is_custom:
       previous_attempts = WordAttempt.objects.filter(student=student, custom_word=word_obj)
   else:
       previous_attempts = WordAttempt.objects.filter(student=student, word=word_obj)
   ```

   c. **WordQueue lookup and removal** (~line 600):
   ```python
   # Current (broken):
   queue_item = WordQueue.objects.filter(student=student, word=word).first()
   
   # Should be:
   if is_custom:
       queue_item = WordQueue.objects.filter(student=student, custom_word=word_obj).first()
   else:
       queue_item = WordQueue.objects.filter(student=student, word=word_obj).first()
   ```

   d. **Correct attempts count** (~line 610):
   ```python
   # Current (broken):
   correct_attempts = WordAttempt.objects.filter(student=student, word=word, is_correct=True).count()
   
   # Should be:
   if is_custom:
       correct_attempts = WordAttempt.objects.filter(student=student, custom_word=word_obj, is_correct=True).count()
   else:
       correct_attempts = WordAttempt.objects.filter(student=student, word=word_obj, is_correct=True).count()
   ```

   e. **BucketProgress lookup** (~line 650):
   ```python
   # Current (broken):
   bucket_progress, created = BucketProgress.objects.get_or_create(student=student, bucket=progress.current_bucket)
   
   # Should be:
   if progress.uses_custom_ladder():
       bucket_progress, created = BucketProgress.objects.get_or_create(
           student=student,
           custom_bucket=progress.current_custom_bucket
       )
   else:
       bucket_progress, created = BucketProgress.objects.get_or_create(
           student=student,
           bucket=progress.current_bucket
       )
   ```

   f. **Bucket advancement logic** (~line 700):
   ```python
   # Current (broken):
   if progress.current_bucket < 10:
       progress.current_bucket += 1
   
   # Should be:
   if progress.uses_custom_ladder():
       if progress.has_next_bucket():
           progress.advance_to_next_bucket()
   else:
       if progress.current_bucket < 10:
           progress.current_bucket += 1
   ```

4. **Test the function:**
   - Add print statements to verify correct code path
   - Test with custom ladder
   - Test with default system
   - Verify no crashes

**Files to reference:**
- `SUBMIT_ANSWER_UPDATE_GUIDE.md` (detailed guide)
- `game/models.py` (helper methods: `uses_custom_ladder()`, `has_next_bucket()`, `advance_to_next_bucket()`)

---

## 📋 IMPORTANT (Required for Feature Completeness)

### ✅ Step 2: Update `student_dashboard.html` Template (5 minutes)
**File:** `templates/game/student_dashboard.html`  
**Priority:** HIGH - Students see wrong bucket names

**What to do:**
1. Find all instances of `{{ progress.current_bucket }}`
2. Replace with `{{ progress.get_current_bucket_display }}`
3. This displays custom bucket names instead of numbers

**Example change:**
```html
<!-- Before -->
<p>Current Bucket: {{ progress.current_bucket }}</p>

<!-- After -->
<p>Current Bucket: {{ progress.get_current_bucket_display }}</p>
```

---

### ✅ Step 3: Update `student_game.html` Template (5 minutes)
**File:** `templates/game/student_game.html`  
**Priority:** HIGH - Game interface shows wrong info

**What to do:**
1. Find bucket display sections
2. Replace `{{ progress.current_bucket }}` with `{{ progress.get_current_bucket_display }}`
3. Update any bucket-related JavaScript if needed

---

### ✅ Step 4: Update `student_detail.html` Template (5 minutes)
**File:** `templates/game/student_detail.html` (if it exists)  
**Priority:** MEDIUM - Teacher view of student

**What to do:**
1. Find student progress display
2. Replace bucket number with `{{ progress.get_current_bucket_display }}`
3. Add ladder name display if using custom ladder

**Optional enhancement:**
```html
{% if progress.uses_custom_ladder %}
  <p>Ladder: {{ progress.current_custom_bucket.ladder.name }}</p>
  <p>Bucket: {{ progress.get_current_bucket_display }}</p>
{% else %}
  <p>Bucket: {{ progress.current_bucket }} (Default System)</p>
{% endif %}
```

---

### ✅ Step 5: Update Classroom Detail Template (Already Mostly Done) (5 minutes)
**File:** `templates/game/classroom_detail.html`  
**Priority:** MEDIUM - Minor polish needed

**What to do:**
1. Verify ladder assignment section is visible
2. Add success message display after assignment
3. Test ladder switching UI

---

## 🧪 TESTING (Critical for Launch)

### ✅ Step 6: Create Test Bucket Ladder (10 minutes)
**Priority:** HIGH - Needed for all testing

**What to do:**
1. Log in as teacher
2. Navigate to `/game/ladders/`
3. Click "Create New Ladder"
4. Create ladder: "Test Difficulty Ladder"
5. Add 3 buckets:
   - Position 1: "Easy Words"
   - Position 2: "Medium Words"
   - Position 3: "Hard Words"
6. Add 5-10 words to each bucket

---

### ✅ Step 7: Test Custom Ladder Assignment (15 minutes)
**Priority:** HIGH - Core feature validation

**What to do:**
1. Navigate to classroom detail page
2. Assign the test ladder to classroom
3. Set default starting bucket to position 1
4. Verify all students migrated to new bucket
5. Check student progress records updated

**Verification:**
- Student `current_custom_bucket` should point to "Easy Words"
- Student `current_bucket` should be NULL
- All word queues should be cleared

---

### ✅ Step 8: Test Student Gameplay with Custom Ladder (30 minutes)
**Priority:** CRITICAL - Main user flow

**What to do:**
1. Log in as student in test classroom
2. Start game session
3. Answer words correctly (get 3 correct for mastery)
4. Verify word comes from current custom bucket
5. Answer 3 correctly and verify bucket advancement
6. Check bucket name displays correctly in UI
7. Verify progress through all 3 buckets

**Expected behavior:**
- Only words from current custom bucket appear
- After 3 correct, student advances to next bucket
- Bucket names display correctly (not numbers)
- No crashes or errors

---

### ✅ Step 9: Test Default System Backward Compatibility (20 minutes)
**Priority:** HIGH - Must not break existing functionality

**What to do:**
1. Create new classroom (or unassign ladder from existing)
2. Leave ladder assignment as "Use Default Buckets"
3. Log in as student in this classroom
4. Verify game works with default 10-bucket system
5. Check bucket numbers display (1-10)
6. Test progression works normally

**Verification:**
- `uses_custom_ladder()` returns False
- Student progresses through buckets 1-10
- Word selection based on letter count
- No crashes

---

### ✅ Step 10: Test Switching Between Systems (20 minutes)
**Priority:** MEDIUM - Edge case validation

**What to do:**
1. Start student in default system
2. Play a few words, advance to bucket 3
3. Teacher assigns custom ladder
4. Verify student resets to custom ladder's starting bucket
5. Switch back to default system
6. Verify student resets to default starting bucket

**Expected behavior:**
- Switching clears word queues
- Student progress updates correctly
- No orphaned data
- No crashes

---

## 🎨 POLISH (Nice to Have)

### ✅ Step 11: Add Navigation Links (10 minutes)
**Priority:** LOW - UX improvement

**What to do:**
1. Add "Manage Ladders" link to teacher dashboard
2. Add breadcrumb navigation on ladder pages
3. Add "Back to Ladders" button on ladder detail page

**Example:**
```html
<!-- In teacher dashboard -->
<a href="{% url 'ladder_list' %}" class="btn btn-primary">Manage Bucket Ladders</a>

<!-- In ladder_detail.html -->
<nav aria-label="breadcrumb">
  <ol class="breadcrumb">
    <li class="breadcrumb-item"><a href="{% url 'ladder_list' %}">Ladders</a></li>
    <li class="breadcrumb-item active">{{ ladder.name }}</li>
  </ol>
</nav>
```

---

### ✅ Step 12: Improve Error Messages (5 minutes)
**Priority:** LOW - Better UX

**What to do:**
1. Add user-friendly error messages in views
2. Handle edge cases (empty buckets, no words, etc.)
3. Add validation messages in forms

**Example:**
```python
# In bucket_add_words view
if not parsed_words:
    messages.error(request, "No valid words found. Please enter at least one word.")
    return redirect('ladder_detail', ladder_id=ladder.id)
```

---

### ✅ Step 13: Add Confirmation Dialogs (5 minutes)
**Priority:** LOW - Prevent accidents

**What to do:**
1. Add JavaScript confirmation before deleting ladder
2. Add confirmation before deleting bucket with words
3. Add warning when switching classroom ladder (students will reset)

**Example:**
```javascript
// In ladder_detail.html
function confirmDelete() {
    return confirm('Are you sure you want to delete this ladder? This cannot be undone.');
}

// Add to delete button
<button onclick="return confirmDelete()">Delete Ladder</button>
```

---

## 📊 COMPLETION CHECKLIST

### Must Complete (Required for Feature)
- [ ] Step 1: Fix `submit_answer()` function ⚠️ CRITICAL
- [ ] Step 2: Update `student_dashboard.html`
- [ ] Step 3: Update `student_game.html`
- [ ] Step 6: Create test ladder
- [ ] Step 7: Test ladder assignment
- [ ] Step 8: Test student gameplay with custom ladder
- [ ] Step 9: Test default system backward compatibility

### Should Complete (Important for Quality)
- [ ] Step 4: Update `student_detail.html`
- [ ] Step 5: Polish classroom detail
- [ ] Step 10: Test switching systems

### Nice to Have (Polish)
- [ ] Step 11: Add navigation links
- [ ] Step 12: Improve error messages
- [ ] Step 13: Add confirmation dialogs

---

## 🚀 RECOMMENDED ORDER

**Day 1 (2 hours):**
1. Step 1: Fix `submit_answer()` - 1.5-2 hours
2. Step 2-3: Update student templates - 10 minutes
3. Coffee break ☕

**Day 1 Continued (1 hour):**
4. Step 6: Create test ladder - 10 minutes
5. Step 7: Test assignment - 15 minutes
6. Step 8: Test gameplay - 30 minutes
7. Step 9: Test default system - 20 minutes

**Day 2 (Optional, 30 minutes):**
8. Steps 4-5: Final template updates - 10 minutes
9. Step 10: Test switching - 20 minutes
10. Steps 11-13: Polish - 20 minutes

---

## ⚠️ CRITICAL NOTES

1. **DO NOT skip Step 1** - Nothing works without fixing `submit_answer()`
2. **Test after each major step** - Don't wait until the end
3. **Keep default system working** - Backward compatibility is essential
4. **Use helper methods** - Already created in models, use them!
5. **Check migration applied** - Should see `0005_bucketladder_custombucket_and_more.py`

---

## 🆘 TROUBLESHOOTING

**If you get "word is not defined" error:**
- You're still using old `word` variable in `submit_answer()`
- Replace with `word_obj` and add conditional logic

**If students don't advance buckets:**
- Check `advance_to_next_bucket()` is being called for custom ladders
- Verify `has_next_bucket()` returns True

**If word selection is wrong:**
- Check `get_next_word()` is using correct bucket
- Verify `uses_custom_ladder()` returns expected value

**If templates show bucket numbers instead of names:**
- Use `{{ progress.get_current_bucket_display }}` not `{{ progress.current_bucket }}`

---

## 📝 DOCUMENTATION ALREADY CREATED

Reference these files for detailed implementation guides:
- `CUSTOM_BUCKET_IMPLEMENTATION_STATUS.md` - Overall status
- `IMPLEMENTATION_SUMMARY.md` - Quick reference
- `SUBMIT_ANSWER_UPDATE_GUIDE.md` - Detailed submit_answer() guide
- `CUSTOM_BUCKET_FINAL_REPORT.md` - Comprehensive final report

---

**Total Estimated Time:** 2-3 hours for must-complete items  
**Current Completion:** 85%  
**After completion:** 100% functional custom bucket ladder system ✅

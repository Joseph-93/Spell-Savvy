# Classroom Join Links - Testing Checklist

## ✅ Manual Testing Guide

### Pre-Testing Setup
- [ ] Development server is running
- [ ] Database migrations are applied
- [ ] At least one teacher account exists

---

## 🧪 Test Suite 1: Classroom Creation

### Test 1.1: Create First Classroom
- [ ] Log in as teacher
- [ ] Click "📚 My Classrooms" button
- [ ] Should see empty state with "Create Classroom" button
- [ ] Click "+ Create New Classroom"
- [ ] Enter name: "Test Period 1"
- [ ] Click "Create Classroom"
- [ ] Should see success message
- [ ] Should see join code generated (format: XXX-XXX-XX)
- [ ] Should redirect to classroom detail page

**Expected:**
- Classroom created ✓
- Join code is 8 characters with hyphens ✓
- Join URL contains the code ✓

### Test 1.2: Create Multiple Classrooms
- [ ] Return to classroom list
- [ ] Create "Test Period 2"
- [ ] Create "Test Period 3"
- [ ] Should see all 3 classrooms in grid
- [ ] Each should have unique join code

**Expected:**
- Multiple classrooms shown ✓
- All join codes are unique ✓
- Student count shows 0 for each ✓

### Test 1.3: Duplicate Classroom Name
- [ ] Try to create classroom with existing name "Test Period 1"
- [ ] Should see error message
- [ ] Classroom should not be created

**Expected:**
- Error message displayed ✓
- No duplicate classroom ✓

---

## 🧪 Test Suite 2: Join Link Registration

### Test 2.1: Register with Join Link (Full URL)
- [ ] Open classroom detail page
- [ ] Copy the full join URL
- [ ] Open in incognito/private browser window
- [ ] Should see purple banner with classroom info
- [ ] Banner shows classroom name "Test Period 1"
- [ ] Banner shows teacher username
- [ ] Banner shows join code
- [ ] Fill in registration form:
  - Username: "teststudent1"
  - Password: "password123"
  - Confirm password: "password123"
- [ ] Role should default to "Student"
- [ ] Click "Register"
- [ ] Should log in automatically
- [ ] Should redirect to student dashboard

**Expected:**
- Registration successful ✓
- Student auto-enrolled in classroom ✓
- No manual teacher selection needed ✓

### Test 2.2: Verify Student in Classroom
- [ ] Log back in as teacher
- [ ] Go to "My Classrooms"
- [ ] Open "Test Period 1"
- [ ] Should see "teststudent1" in student list
- [ ] Student count should show "1 student"

**Expected:**
- Student appears in classroom ✓
- Statistics are visible ✓

### Test 2.3: Register Multiple Students
- [ ] Copy join URL again
- [ ] Register "teststudent2" (incognito)
- [ ] Register "teststudent3" (incognito)
- [ ] Check classroom detail page
- [ ] Should show "3 students"
- [ ] All 3 students should be listed

**Expected:**
- Multiple students can join ✓
- Count updates correctly ✓

---

## 🧪 Test Suite 3: Join Code Entry

### Test 3.1: Manual Join Code Entry
- [ ] Go to /register (no query parameter)
- [ ] Should see normal registration form
- [ ] Enter username: "teststudent4"
- [ ] Enter password
- [ ] Select "Student" role
- [ ] Look for join code field (might need to add this if not visible)
- [ ] Enter join code manually: "ABC-DEF-GH" (from Test Period 2)
- [ ] Register
- [ ] Should auto-enroll in Test Period 2

**Expected:**
- Manual code entry works ✓
- Student added to correct classroom ✓

---

## 🧪 Test Suite 4: Join Code Management

### Test 4.1: Copy Join Code
- [ ] Open classroom detail page
- [ ] Click 📋 button next to join code
- [ ] Should see "copied" confirmation
- [ ] Paste in notepad - verify code is correct

**Expected:**
- Copy button works ✓
- Correct code is copied ✓

### Test 4.2: Copy Join URL
- [ ] Click 📋 button next to join URL
- [ ] Should see "copied" confirmation
- [ ] Paste in notepad - verify URL is correct
- [ ] URL should contain domain + /register?join=CODE

**Expected:**
- Copy button works ✓
- Correct URL is copied ✓

### Test 4.3: Regenerate Join Code
- [ ] Note the current join code
- [ ] Click "🔄 Regenerate Code"
- [ ] Confirm regeneration
- [ ] Should see success message
- [ ] New code should be different from old code
- [ ] Format should still be XXX-XXX-XX

**Expected:**
- New code generated ✓
- Code is unique ✓
- Students already in classroom stay enrolled ✓

### Test 4.4: Old Code Becomes Invalid
- [ ] Try to register with the OLD join code
- [ ] Should see "Invalid or expired join code" error
- [ ] Should NOT be able to join classroom

**Expected:**
- Old code rejected ✓
- Security maintained ✓

---

## 🧪 Test Suite 5: Classroom Viewing

### Test 5.1: Classroom List View
- [ ] Go to "My Classrooms"
- [ ] Should see all classrooms in grid
- [ ] Each card shows:
  - Classroom name
  - Student count
  - Join code
  - "View Details" button

**Expected:**
- All classrooms visible ✓
- Information accurate ✓

### Test 5.2: Classroom Detail View
- [ ] Click "View Details" on any classroom
- [ ] Should see:
  - Classroom name in header
  - Join code section
  - Full join URL
  - Student list with stats
  - Action buttons (Regenerate, Delete)

**Expected:**
- All information displayed ✓
- Student stats accurate ✓

### Test 5.3: Empty Classroom
- [ ] Create new classroom "Empty Class"
- [ ] View its details
- [ ] Should show "No students have joined yet"
- [ ] Should show 0 students in count

**Expected:**
- Empty state displayed ✓
- No errors ✓

---

## 🧪 Test Suite 6: Classroom Deletion

### Test 6.1: Delete Classroom
- [ ] Open "Empty Class" detail page
- [ ] Click "🗑️ Delete Classroom"
- [ ] Should see confirmation dialog
- [ ] Confirm deletion
- [ ] Should redirect to classroom list
- [ ] "Empty Class" should no longer appear

**Expected:**
- Classroom deleted ✓
- Redirect successful ✓

### Test 6.2: Delete Classroom with Students
- [ ] Delete "Test Period 3" (has students)
- [ ] Confirm deletion
- [ ] Log in as one of those students
- [ ] Student account should still exist
- [ ] Student progress should be intact
- [ ] Student should not be in any classroom now

**Expected:**
- Classroom deleted ✓
- Student accounts preserved ✓
- Student data preserved ✓

---

## 🧪 Test Suite 7: Teacher Dashboard

### Test 7.1: Dashboard Shows Classrooms Button
- [ ] Go to teacher dashboard
- [ ] Should see "📚 My Classrooms" button
- [ ] Click button
- [ ] Should navigate to classroom list

**Expected:**
- Button visible ✓
- Navigation works ✓

### Test 7.2: Dashboard Shows All Students
- [ ] Return to dashboard
- [ ] Should see students from ALL classrooms
- [ ] Students from Period 1 and Period 2 both visible

**Expected:**
- All students shown ✓
- No classroom filter on main dashboard ✓

---

## 🧪 Test Suite 8: Backward Compatibility

### Test 8.1: Legacy Student Registration
- [ ] Go to /register (no join code)
- [ ] Register as "legacystudent"
- [ ] Manually select teacher from dropdown
- [ ] Should register successfully
- [ ] Check teacher dashboard - student should appear

**Expected:**
- Old registration method still works ✓
- Student assigned to teacher ✓

### Test 8.2: Legacy Student in Dashboard
- [ ] Teacher dashboard should show both:
  - Students in classrooms
  - Students with legacy teacher assignment
- [ ] Both types should be visible

**Expected:**
- Both systems work together ✓
- No data loss ✓

---

## 🧪 Test Suite 9: Edge Cases

### Test 9.1: Invalid Join Code
- [ ] Try to visit /register?join=INVALID-CODE
- [ ] Should see error message
- [ ] Should show normal registration form

**Expected:**
- Error message displayed ✓
- Graceful fallback ✓

### Test 9.2: Case Insensitive Join Code
- [ ] Use join code in lowercase: /register?join=abc-def-gh
- [ ] Should work the same as uppercase
- [ ] Banner should display code correctly

**Expected:**
- Case insensitive matching ✓
- Registration works ✓

### Test 9.3: Join Code with Extra Spaces
- [ ] Try code with spaces: " ABC-DEF-GH "
- [ ] Should be trimmed and work correctly

**Expected:**
- Whitespace handled ✓

### Test 9.4: Teacher Tries to Join Classroom
- [ ] Log in as teacher
- [ ] Try to access join link
- [ ] Should redirect or show error

**Expected:**
- Teachers can't join classrooms ✓

---

## 🧪 Test Suite 10: UI/UX

### Test 10.1: Responsive Design
- [ ] View classroom list on mobile size
- [ ] Cards should stack vertically
- [ ] All buttons should be accessible

**Expected:**
- Mobile friendly ✓

### Test 10.2: Copy Buttons
- [ ] All copy buttons should work
- [ ] Should show confirmation
- [ ] Should copy correct content

**Expected:**
- Copy functionality works ✓

### Test 10.3: Modal Behavior
- [ ] "Create Classroom" modal should:
  - Open on button click
  - Close on "Cancel"
  - Close on outside click
  - Close on Escape key

**Expected:**
- Modal works correctly ✓

---

## 📊 Testing Summary

After completing all tests, verify:

- [ ] All 10 test suites passed
- [ ] No JavaScript errors in console
- [ ] No Django errors in server logs
- [ ] No database errors
- [ ] UI is consistent and polished
- [ ] Documentation is accurate

---

## 🐛 Bug Reporting Template

If you find issues:

```
Bug: [Brief description]
Test: [Test suite and number]
Steps to reproduce:
1. 
2. 
3. 

Expected behavior:
[What should happen]

Actual behavior:
[What actually happened]

Browser: [Chrome/Firefox/Safari]
User role: [Teacher/Student]
Error messages: [Any errors]
```

---

## ✅ Acceptance Criteria

Feature is ready when:

- [ ] All test suites pass
- [ ] No critical bugs
- [ ] Documentation complete
- [ ] UI is polished
- [ ] Teacher can create classrooms
- [ ] Teacher can share join links
- [ ] Students can register via links
- [ ] Students auto-enroll correctly
- [ ] Backward compatibility confirmed

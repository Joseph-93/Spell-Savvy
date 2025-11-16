# Bulk Assignment Feature

## Overview
Added smart default bucket management and bulk student assignment features to give teachers better control over student difficulty levels.

## Features Implemented

### 1. Smart Default Bucket Changes
**Problem**: Previously, changing the default starting bucket would move ALL students to the new bucket, even those who were manually assigned to specific difficulty levels.

**Solution**: Now when a teacher changes the default starting bucket, only students currently on the old default bucket are moved to the new default.

**Example**:
- Teacher has default set to 5-letter words
- 3 students are on 5-letter words (default)
- 2 students were manually moved to 8-letter words
- Teacher changes default to 6-letter words
- Result: Only the 3 students on 5-letter words move to 6-letter words. The 2 students on 8-letter words stay where they are.

### 2. Bulk Assignment Tool
**Purpose**: Allow teachers to assign ALL students in their classroom to a specific difficulty level at once.

**Use Cases**:
- Starting a new unit and want all students at the same level
- Resetting the entire classroom to a common starting point
- Quickly adjusting difficulty for the whole class

**Features**:
- Separate form section with warning styling (yellow/orange)
- Dropdown to select target bucket (3-20 letters)
- Confirmation dialog to prevent accidental bulk changes
- Clears word queues and ends active sessions for all affected students
- Shows success message with count of students updated

## UI Changes

### Teacher Config Page (`/teacher/config/`)

**Section 1: Default Starting Bucket**
- Updated help text to show how many students are currently on the default bucket
- Message clarifies that only those students will be affected by changes

**Section 2: Bulk Student Assignment** (NEW)
- Yellow/orange warning-styled section
- Clear explanation that this affects ALL students
- Dropdown to select target bucket
- "📢 Assign All Students" button with confirmation dialog
- Warning message about the impact

## Technical Implementation

### Backend Changes

**game/views.py**:

1. **Modified `teacher_config` view**:
   ```python
   # Only update students currently on the old default
   students_to_update = StudentProgress.objects.filter(
       student__teacher=request.user,
       current_bucket=old_default_bucket
   )
   ```

2. **Added `bulk_assign_students` view**:
   - Accepts POST with `bulk_bucket` parameter
   - Updates ALL students of the teacher to specified bucket
   - Clears word queues and ends active sessions
   - Creates/updates bucket progress entries
   - Returns success message with count

**game/urls.py**:
- Added URL pattern: `teacher/config/bulk-assign/`

### Frontend Changes

**templates/game/teacher_config.html**:

1. **Updated default bucket help text**:
   - Changed variable from `students_using_default` to `students_on_default`
   - More accurate messaging about which students are affected

2. **Added bulk assignment section**:
   - Separate form posting to `bulk_assign_students` view
   - Warning-styled container (yellow background, orange border)
   - JavaScript confirmation dialog
   - Inline form layout with dropdown and button

**CSS additions**:
- `.bulk-assign-section`: Yellow warning-styled container
- `.form-inline`: Horizontal form layout
- `.btn-warning`: Orange action button
- `.help-text.warning`: Warning message styling

## Messages

### Default Bucket Changes
- **Students updated**: "✅ Configuration updated! {count} student(s) on {old}-letter words moved to {new}-letter words!"
- **No students on default**: "Configuration updated! No students were on the old default bucket."

### Bulk Assignment
- **Success**: "✅ All {count} student(s) have been assigned to {bucket}-letter words!"
- **No students**: "No students found to update."
- **Invalid bucket**: "Please select a valid bucket (3-20 letters)"

## User Flow

### Changing Default Bucket
1. Teacher goes to Config page
2. Sees count of students currently on default bucket
3. Selects new default from dropdown
4. Clicks "Save Configuration"
5. Only students on the old default are moved
6. Receives confirmation message

### Bulk Assignment
1. Teacher scrolls to "Bulk Student Assignment" section
2. Selects target bucket from dropdown
3. Clicks "📢 Assign All Students"
4. Confirms in dialog box
5. All students immediately move to selected bucket
6. Receives success message with count

## Benefits

1. **Preserves Manual Assignments**: Teachers can set individual student levels without worrying about default changes affecting them

2. **Flexible Control**: Two distinct tools for two different use cases:
   - Default bucket: For managing new students and those following the standard progression
   - Bulk assign: For class-wide difficulty adjustments

3. **Clear Communication**: Updated messages show exactly how many students were affected and why

4. **Safety Features**: Confirmation dialog prevents accidental bulk changes

5. **Immediate Effect**: Changes take effect instantly with proper cleanup (queues, sessions)

## Testing Checklist

- [ ] Change default bucket when students are on default - verify only those students move
- [ ] Change default bucket when students are on custom buckets - verify they don't move
- [ ] Use bulk assign to move all students - verify everyone moves regardless of current bucket
- [ ] Check confirmation dialog appears for bulk assign
- [ ] Verify success messages show correct counts
- [ ] Test with 0 students, 1 student, many students
- [ ] Confirm word queues are cleared after both operations
- [ ] Verify active sessions end after both operations
- [ ] Check that bucket progress entries are created

## Future Enhancements

Potential additions:
- Bulk assignment for specific classrooms (if using classroom feature)
- Preview showing which students will be affected before confirming
- Option to exclude certain students from bulk assignment
- Undo functionality for bulk operations
- Scheduled bucket changes (e.g., "Move all students to next level on Monday")

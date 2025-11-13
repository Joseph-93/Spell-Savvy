# Teacher-Student Relationship & Starting Bucket Features

## Overview
This document describes the teacher-student relationship system and customizable starting difficulty features added to the Spelling Game application.

## Key Features

### 1. Teacher-Student Relationship
- **Student Assignment**: Students must register under a specific teacher
- **Data Isolation**: Teachers can only view and modify their own students' data
- **Registration Flow**: Students select their teacher during registration

### 2. Starting Bucket Configuration
- **Default Starting Bucket**: Teachers can set a default starting difficulty (word length) for all their students
- **Per-Student Override**: Teachers can set a custom starting bucket for individual students
- **Priority System**: Custom settings override teacher defaults, which override the system default (3 letters)

## Database Changes

### User Model (`accounts/models.py`)
```python
teacher = models.ForeignKey(
    'self',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    limit_choices_to={'role': 'teacher'},
    related_name='students'
)
```
- Self-referential foreign key linking students to their teacher
- `limit_choices_to` ensures only teachers can be selected
- `SET_NULL` prevents cascade deletion of students

### GameConfiguration Model (`game/models.py`)
```python
default_starting_bucket = models.IntegerField(default=3)
```
- Stores teacher's preferred default starting difficulty
- Valid range: 3-15 (word lengths)

### StudentProgress Model (`game/models.py`)
```python
custom_starting_bucket = models.IntegerField(null=True, blank=True)

def get_starting_bucket(self):
    """Returns the starting bucket for this student"""
    if self.custom_starting_bucket:
        return self.custom_starting_bucket
    if self.student.teacher:
        config = GameConfiguration.objects.filter(teacher=self.student.teacher).first()
        if config:
            return config.default_starting_bucket
    return 3  # System default
```
- Optional per-student starting bucket override
- `get_starting_bucket()` method implements priority logic

## New Views & URLs

### Update Student Starting Bucket (`game/views.py`)
```python
@login_required
def update_student_starting_bucket(request, student_id):
    """Update a specific student's starting bucket"""
    # Permission check: must be student's teacher
    # Validates bucket is 3-15
    # IMMEDIATELY updates StudentProgress.current_bucket
    # Clears WordQueue for fresh words
    # Ends active session to force refresh
    # Creates/updates BucketProgress for new bucket
```

**URL**: `/teacher/student/<student_id>/update-bucket/`

**Key Behavior**: Changes take effect **immediately**:
- Sets `custom_starting_bucket` (or clears it)
- Updates `current_bucket` to the new value right away
- Clears the student's word queue so they get fresh words
- Ends any active game session
- Creates bucket progress entry for the new difficulty
- Student will see new difficulty on their next word request

## UI Changes

### Registration Page (`templates/accounts/register.html`)
- **Teacher Dropdown**: Shows all available teachers for student registration
- **Dynamic Display**: Teacher field only shows when "Student" role is selected
- **Required Field**: Students must select a teacher

### Teacher Configuration (`templates/game/teacher_config.html`)
- **New Field**: "Default Starting Bucket" dropdown (3-15 letters)
- **Student Count Display**: Shows how many students are using the default (no custom override)
- **Immediate Effect Warning**: Clear indication that changes affect students instantly
- **Description**: "⚡ Changes take effect immediately! Currently X student(s) are using this default setting and will be moved to the new difficulty instantly."

### Student Detail Page (`templates/game/student_detail.html`)
- **Settings Section**: New "Student Settings" panel
- **Custom Bucket Form**: Dropdown to set per-student difficulty (3-15 letters)
- **Status Display**: Shows current difficulty and whether it's custom or teacher default
- **Immediate Effect**: Changes take effect immediately - student gets new words at the selected difficulty
- **Visual Feedback**: Clear messaging that changes are instant with ⚡ icon

## Updated Logic

### Teacher Configuration Update (`game/views.py - teacher_config()`)
```python
if old_default_bucket != new_default_bucket:
    # Get all students without custom settings
    students_to_update = StudentProgress.objects.filter(
        student__teacher=request.user,
        custom_starting_bucket__isnull=True
    )
    
    for progress in students_to_update:
        progress.current_bucket = new_default_bucket
        progress.save()
        WordQueue.objects.filter(student=progress.student).delete()
        GameSession.objects.filter(student=progress.student, is_active=True).update(is_active=False)
        BucketProgress.objects.get_or_create(student=progress.student, bucket=new_default_bucket)
```
- When default bucket changes, ALL students using default are immediately updated
- Their word queues are cleared for fresh words
- Active sessions are ended for clean transition
- Bucket progress tracking is created for new difficulty
- Shows count of affected students in success message

### Student Game Initialization (`game/views.py - student_game()`)
```python
if created or progress.current_bucket is None:
    starting_bucket = progress.get_starting_bucket()
    progress.current_bucket = starting_bucket
    progress.save()
```
- Uses `get_starting_bucket()` to initialize new students
- Respects custom/teacher default/system default priority

### Teacher Dashboard (`game/views.py - teacher_dashboard()`)
```python
students = User.objects.filter(
    role='student',
    teacher=request.user
)
```
- Filtered to show only the logged-in teacher's students

### Student Detail (`game/views.py - student_detail()`)
```python
student = User.objects.get(
    id=student_id,
    role='student',
    teacher=request.user
)
```
- Permission check ensures teacher owns the student

## Demo Data

The `create_demo_users` management command now:
- Creates teacher account: `teacher/teacher123`
- Creates student account assigned to teacher: `student/student123`
- Creates admin teacher account: `admin/admin123`

## Testing the Features

### Test Immediate Default Bucket Change (NEW!)
1. Login as teacher: `teacher/teacher123`
2. Navigate to "Game Configuration"
3. Note current "Default Starting Bucket" (e.g., 3)
4. Note the count: "Currently X student(s) are using this default setting"
5. Change to different value (e.g., 6)
6. Click "Save Configuration"
7. **Result**: See message "✅ Configuration updated! X student(s) immediately moved to 6-letter words!"
8. Go to dashboard and verify students' current buckets are updated
9. Login as affected student - next word will be from new difficulty!

### Test Immediate Difficulty Change (Individual Student)
1. Login as teacher: `teacher/teacher123`
2. Click on student name in dashboard
3. Note the student's current bucket (e.g., "3-letter words")
4. In "Student Settings", select a different difficulty (e.g., "7 letters")
5. Click "Update Now"
6. **Result**: Student's current bucket changes immediately
7. Login as that student in another browser/tab
8. Click "Get Next Word" - you'll immediately get words from the new difficulty!

### Test Teacher Configuration
1. Login as teacher: `teacher/teacher123`
2. Navigate to "Game Configuration"
3. Set "Default Starting Bucket" to desired value (e.g., 5)
4. Click "Save Configuration"

### Test Per-Student Override
1. Login as teacher: `teacher/teacher123`
2. Click on student name in dashboard
3. In "Student Settings" section, select custom starting bucket
4. Click "Update"

### Test Student Registration
1. Logout
2. Click "Register"
3. Select "Student" role
4. Choose a teacher from dropdown
5. Complete registration

### Test Data Isolation
1. Create second teacher account
2. Login as second teacher
3. Verify they cannot see first teacher's students

## Migration Files

Two new migrations were created and applied:

1. `accounts/0002_user_teacher.py`
   - Adds `teacher` field to User model

2. `game/0002_gameconfiguration_default_starting_bucket_and_more.py`
   - Adds `default_starting_bucket` to GameConfiguration
   - Adds `custom_starting_bucket` to StudentProgress

## API Compatibility

All existing API endpoints remain unchanged:
- `/api/next-word/` - Works with new starting bucket logic
- `/api/submit-answer/` - No changes
- `/api/end-session/` - No changes

## Security Considerations

- **Permission Checks**: All teacher views verify ownership before displaying/modifying student data
- **Validation**: Starting bucket values validated (3-15 range)
- **SQL Injection**: ORM prevents injection attacks
- **CSRF Protection**: All forms include CSRF tokens

## Future Enhancements

Potential improvements:
- Bulk student import/assignment
- Student transfer between teachers
- Historical tracking of starting bucket changes
- Analytics on starting bucket effectiveness
- Email notifications for assignment
- Student performance recommendations based on starting bucket

## Immediate Difficulty Changes

### How It Works

When a teacher changes difficulty settings, the system applies changes **immediately**:

#### Individual Student Change
When a teacher changes a student's difficulty level (word length), the system:

1. **Updates Current Bucket**: Changes `StudentProgress.current_bucket` immediately (not just the starting bucket)
2. **Clears Word Queue**: Deletes all queued words so the student gets fresh words from the new difficulty
3. **Ends Active Session**: Closes any active game session to force a clean start
4. **Creates Bucket Progress**: Ensures the new bucket has a progress tracking entry
5. **Provides Feedback**: Shows a clear success message indicating the change is immediate

#### Default Bucket Change (Affects Multiple Students)
When a teacher changes their default starting bucket, the system:

1. **Identifies Affected Students**: Finds all students who DON'T have custom overrides (`custom_starting_bucket__isnull=True`)
2. **Updates All Current Buckets**: Changes `current_bucket` for each affected student immediately
3. **Clears All Word Queues**: Removes queued words for each affected student
4. **Ends All Active Sessions**: Closes active sessions for affected students
5. **Creates Bucket Progress**: Sets up tracking for each student at the new difficulty
6. **Reports Count**: Shows "✅ X student(s) immediately moved to Y-letter words!"

### Why This Matters

- **Real-time control**: Teachers can adjust difficulty mid-session if students are struggling or excelling
- **Bulk updates**: Change default bucket once and all non-custom students move together
- **No waiting**: Changes apply on the student's next word request, not at next login
- **Clean transition**: Old word queues are cleared to prevent mixing difficulty levels
- **Session reset**: Ends current sessions so statistics reflect the difficulty change clearly
- **Smart filtering**: Only affects students without custom settings (respects individual overrides)

### Example Scenarios

**Scenario 1: Individual Student Adjustment**
1. Student is on 3-letter words and finding them too easy
2. Teacher logs in, goes to student detail page
3. Teacher changes difficulty to 5-letter words
4. Student clicks "Get Next Word" in their active game
5. Student immediately receives a 5-letter word (not a 3-letter word from the old queue)

**Scenario 2: Class-Wide Difficulty Change**
1. Teacher has default set to 4-letter words
2. Five students are using the default (two have custom overrides at 6 and 8)
3. Teacher changes default to 5-letter words in Game Configuration
4. System immediately moves the five default students to 5-letter words
5. The two students with custom overrides stay at 6 and 8 (unaffected)
6. Success message: "✅ Configuration updated! 5 student(s) immediately moved to 5-letter words!"

This immediate behavior allows teachers to be responsive to student needs in real-time!

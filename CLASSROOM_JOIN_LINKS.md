# Classroom Join Link Feature

## Overview
Teachers can now create multiple classrooms and generate unique join links for each one. Students who register using a join link are automatically added to the corresponding classroom.

## What's New

### For Teachers

#### 1. **Multiple Classrooms**
- Teachers can create unlimited classrooms (e.g., "Period 1", "Period 2", "English 101")
- Each classroom has its own unique join code
- Students are organized by classroom

#### 2. **Join Code System**
- Each classroom gets a unique 8-character code (e.g., `ABC-DEF-GH`)
- Codes are easy to read (no confusing characters like 0, O, I, 1)
- Codes can be regenerated if needed
- Format: `XXX-XXX-XX` for easy sharing

#### 3. **Join Links**
- Full URL that automatically adds students to the classroom
- Example: `http://yoursite.com/register?join=ABC-DEF-GH`
- Students just click the link and register - they're auto-enrolled!

#### 4. **Classroom Management**
Teachers can:
- View all their classrooms
- See student count per classroom
- View detailed student stats by classroom
- Copy join codes or full links with one click
- Regenerate join codes if needed
- Delete classrooms (students aren't deleted, just unassigned)

### For Students

#### 1. **Easy Registration**
- Click join link from teacher → See classroom name and teacher
- Create account → Automatically added to classroom
- No need to manually select a teacher

#### 2. **Join Code Entry**
- If no join link, students can enter the code during registration
- System validates the code and adds them to the correct classroom

## How It Works

### Teacher Workflow

1. **Create a Classroom**
   - Go to Teacher Dashboard
   - Click "📚 My Classrooms"
   - Click "+ Create New Classroom"
   - Enter classroom name (e.g., "Period 1")
   - System generates unique join code automatically

2. **Share Join Information**
   - Option 1: Copy the full join link and share it (email, LMS, etc.)
   - Option 2: Share just the join code for students to enter manually
   - Students who use either method are auto-enrolled

3. **Manage Students**
   - View all students in each classroom
   - Track their progress individually
   - See overall classroom statistics

### Student Workflow

1. **Receive Join Link or Code from Teacher**
   - Teacher shares link or code via email, Google Classroom, etc.

2. **Register**
   - **With Link**: Click link → See classroom info → Create account → Done!
   - **With Code**: Go to register page → Enter join code → Create account → Done!

3. **Start Learning**
   - Automatically enrolled in teacher's classroom
   - Teacher can see their progress immediately

## Technical Details

### New Database Models

#### Classroom Model
```python
class Classroom(models.Model):
    name = CharField  # e.g., "Period 1"
    teacher = ForeignKey(User)
    join_code = CharField(unique=True)  # e.g., "ABC-DEF-GH"
    created_at = DateTimeField
    is_active = BooleanField
```

### Updated Models

#### User Model
- Added `classroom` field (ForeignKey to Classroom)
- Kept legacy `teacher` field for backward compatibility
- Added `get_teacher()` method to work with both systems

### URLs Added
- `/teacher/classrooms/` - List all classrooms
- `/teacher/classrooms/create/` - Create new classroom
- `/teacher/classrooms/<id>/` - View classroom details
- `/teacher/classrooms/<id>/delete/` - Delete classroom
- `/teacher/classrooms/<id>/regenerate-code/` - Get new join code
- `/register?join=<code>` - Register with join code

### Views Added
- `classroom_list` - Show all teacher's classrooms
- `classroom_create` - Create new classroom
- `classroom_detail` - View classroom with students
- `classroom_delete` - Remove classroom
- `classroom_regenerate_code` - Generate new join code

### Templates Created
- `classroom_list.html` - Classroom overview page
- `classroom_detail.html` - Individual classroom management
- Updated `register.html` - Shows join code banner when applicable
- Updated `teacher_dashboard.html` - Added "My Classrooms" button

## Backward Compatibility

✅ **Fully backward compatible!**

- Old students with direct teacher assignment still work
- Legacy `teacher` field is maintained
- New students use `classroom` field
- System works with both approaches
- Teacher dashboard shows students from both systems

## Security Features

- Join codes are unique and cryptographically random
- Codes can be regenerated to revoke access
- Only active classrooms accept new students
- Teachers can only manage their own classrooms
- Students can't see other classrooms' join codes

## UI Features

### Registration Page
- Shows beautiful banner when using join link
- Displays classroom name and teacher
- Highlights the join code being used
- Still allows manual teacher selection as fallback

### Classroom List Page
- Card-based grid layout
- Shows student count per classroom
- Easy-to-read join codes
- Quick access to classroom details
- Empty state with helpful message

### Classroom Detail Page
- Prominent join code display
- One-click copy for both code and full URL
- Student list with statistics
- Regenerate and delete options
- Link back to all classrooms

## Example Usage Scenarios

### Scenario 1: High School Teacher
Ms. Johnson teaches 5 periods:
1. Creates 5 classrooms: "Period 1" through "Period 5"
2. Shares join link in Google Classroom for each period
3. Students click, register, automatically sorted by period
4. Can view progress by period or all students combined

### Scenario 2: Elementary Teacher
Mr. Smith has one class but changes yearly:
1. Creates "Class of 2025"
2. Shares join code verbally or on paper handout
3. Students register using the code
4. Next year: creates "Class of 2026" with new code
5. Old classroom can be archived or deleted

### Scenario 3: Tutoring Center
Ms. Lee tutors multiple small groups:
1. Creates classrooms: "Morning Group", "Evening Group", "Weekend Group"
2. Emails join links to parent groups
3. Students auto-sorted by session time
4. Easy to track which group needs more help

## Testing the Feature

### As a Teacher:
1. Log in as teacher
2. Click "📚 My Classrooms" from dashboard
3. Create a test classroom
4. Copy the join link
5. Open in incognito/private window
6. Register a new student account
7. Verify student appears in classroom

### As a Student:
1. Get join link from teacher
2. Click the link
3. See classroom banner with name and code
4. Complete registration
5. Verify auto-enrollment worked

## Troubleshooting

**Q: Student says join code is invalid**
- Check if classroom is active
- Verify code was copied correctly (case-insensitive)
- Try regenerating the code

**Q: Want to revoke access to old join link**
- Go to classroom detail page
- Click "🔄 Regenerate Code"
- Share new code/link

**Q: Need to move student between classrooms**
- Currently requires admin panel
- Future feature: add "Move Student" button

**Q: Want to see all students across all classrooms**
- Teacher dashboard shows ALL students
- Individual classroom pages show per-classroom view

## Future Enhancements

Potential features for future updates:
- Bulk move students between classrooms
- Archive inactive classrooms
- Classroom-specific settings (different word requirements per period)
- Student self-service classroom switching
- Classroom join approval system
- Limited-use join codes (expires after N students)
- Time-limited join codes (expires after date)

## Migration Notes

- Migrations automatically created and applied
- Existing students retain teacher assignment
- No data loss during migration
- Teachers can gradually migrate students to classrooms
- Both systems work simultaneously

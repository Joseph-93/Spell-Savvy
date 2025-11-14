# Classroom Join Links - User Flow Diagrams

## 📚 Teacher Workflow

```
Teacher Logs In
      |
      v
Click "My Classrooms"
      |
      v
┌─────────────────────────────┐
│  Classroom List Page        │
│  ┌───────────────────────┐  │
│  │  Period 1  [3 students]│  │
│  │  Code: ABC-DEF-GH      │  │
│  │  [View Details]        │  │
│  └───────────────────────┘  │
│  ┌───────────────────────┐  │
│  │  Period 2  [5 students]│  │
│  │  Code: XYZ-123-45      │  │
│  │  [View Details]        │  │
│  └───────────────────────┘  │
│                             │
│  [+ Create New Classroom]   │
└─────────────────────────────┘
      |
      v (Click "View Details")
      |
      v
┌─────────────────────────────────────────┐
│  Period 1 - Classroom Detail            │
│  ┌─────────────────────────────────┐   │
│  │ 📎 Join Information             │   │
│  │ Join Code: ABC-DEF-GH  [📋]     │   │
│  │ Join URL: http://...   [📋]     │   │
│  │                                 │   │
│  │ [🔄 Regenerate] [🗑️ Delete]    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  👥 Students (3)                        │
│  ┌─────────────────────────────────┐   │
│  │ Alice  | Bucket 5 | 85% accuracy│   │
│  │ Bob    | Bucket 3 | 92% accuracy│   │
│  │ Carol  | Bucket 4 | 78% accuracy│   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## 👨‍🎓 Student Workflow (With Join Link)

```
Teacher Shares Link
(http://site.com/register?join=ABC-DEF-GH)
      |
      v
Student Clicks Link
      |
      v
┌──────────────────────────────────┐
│  Registration Page               │
│  ┌────────────────────────────┐  │
│  │ 🎓 You're joining:         │  │
│  │    Period 1                │  │
│  │    Teacher: Ms. Johnson    │  │
│  │    Code: ABC-DEF-GH        │  │
│  └────────────────────────────┘  │
│                                  │
│  Username: [_____________]       │
│  Password: [_____________]       │
│  Confirm:  [_____________]       │
│  Role: Student ▼                 │
│                                  │
│  [Register]                      │
└──────────────────────────────────┘
      |
      v
Student Submits Form
      |
      v
✅ Auto-enrolled in "Period 1"
      |
      v
Redirected to Student Dashboard
```

## 👨‍🎓 Student Workflow (With Join Code Only)

```
Teacher Shares Code
(ABC-DEF-GH)
      |
      v
Student Goes to Register Page
      |
      v
┌──────────────────────────────────┐
│  Registration Page               │
│                                  │
│  Username: [_____________]       │
│  Password: [_____________]       │
│  Confirm:  [_____________]       │
│  Role: Student ▼                 │
│                                  │
│  Join Code: [ABC-DEF-GH__]       │
│  (Or select teacher manually)    │
│                                  │
│  [Register]                      │
└──────────────────────────────────┘
      |
      v
Student Submits with Code
      |
      v
✅ Auto-enrolled in classroom
      |
      v
Redirected to Student Dashboard
```

## 🔄 Join Code Regeneration Flow

```
Teacher Views Classroom
      |
      v
Clicks "🔄 Regenerate Code"
      |
      v
Confirms Action
      |
      v
Old Code: ABC-DEF-GH ❌ (Invalid)
New Code: XYZ-789-AB ✅ (Active)
      |
      v
Share New Code with Students
```

## 🗑️ Classroom Deletion Flow

```
Teacher Views Classroom
      |
      v
Clicks "🗑️ Delete Classroom"
      |
      v
Confirms Deletion
      |
      v
┌─────────────────────────────┐
│  What Happens:              │
│  • Classroom deleted ✅     │
│  • Students unassigned ✅   │
│  • Student accounts kept ✅ │
│  • Student progress kept ✅ │
└─────────────────────────────┘
```

## 🔀 System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Teacher                          │
│                 (One Account)                       │
└───────────┬────────────────┬────────────────────────┘
            │                │
            │                │
     ┌──────▼──────┐  ┌─────▼───────┐
     │ Classroom 1 │  │ Classroom 2 │  (Unlimited)
     │ Period 1    │  │ Period 2    │
     │ ABC-DEF-GH  │  │ XYZ-123-45  │
     └──────┬──────┘  └─────┬───────┘
            │                │
     ┌──────┴─────┬──────┐  ├─────────┬──────┐
     │            │      │  │         │      │
  ┌──▼──┐  ┌────▼───┐ ┌▼──▼──┐ ┌────▼───┐ ┌▼──┐
  │Alice│  │  Bob   │ │Carol │ │  Dave  │ │Eve│
  │     │  │        │ │      │ │        │ │   │
  └─────┘  └────────┘ └──────┘ └────────┘ └───┘
 Student   Student    Student   Student   Student
```

## 📊 Data Relationships

```
User Table
├── id
├── username
├── role (student/teacher)
├── teacher_id (ForeignKey, legacy)
└── classroom_id (ForeignKey, new)
          │
          │
          ▼
    Classroom Table
    ├── id
    ├── name
    ├── teacher_id (ForeignKey)
    ├── join_code (unique)
    ├── is_active
    └── created_at
```

## 🎯 Feature Comparison

### Before (Legacy System)
```
Teacher → Student (Direct Link)

Problems:
❌ One teacher per student only
❌ No period/class organization
❌ Manual student assignment
❌ Hard to share enrollment info
```

### After (Classroom System)
```
Teacher → Classroom → Students

Benefits:
✅ Multiple classrooms per teacher
✅ Organized by period/class
✅ Auto-enrollment via links
✅ Easy sharing with codes
✅ Backward compatible
```

## 🔐 Security Model

```
Join Code: ABC-DEF-GH
     │
     ├─► Unique ✅ (Database constraint)
     ├─► Random ✅ (Cryptographically secure)
     ├─► Readable ✅ (No confusing chars: 0,O,I,1)
     ├─► Revocable ✅ (Can regenerate)
     └─► Scoped ✅ (Per classroom, per teacher)

Student Registration
     │
     ├─► Validates join code ✅
     ├─► Checks classroom is active ✅
     ├─► Auto-assigns to classroom ✅
     └─► Sets teacher relationship ✅
```

## 📱 Sharing Methods Comparison

```
Method 1: Full Join Link
─────────────────────────────────────
Share: http://site.com/register?join=ABC-DEF-GH
Pros:  • One click registration
       • No code entry needed
       • Works in emails, LMS, etc.
Use:   Digital sharing (email, LMS)

Method 2: Join Code Only
─────────────────────────────────────
Share: ABC-DEF-GH
Pros:  • Short and memorable
       • Easy to say verbally
       • Works on paper handouts
Use:   Physical sharing, verbal

Method 3: QR Code (Join Link)
─────────────────────────────────────
Share: [QR Code Image]
Pros:  • Scan with phone
       • No typing needed
       • Modern and quick
Use:   Classroom posters, handouts
```

## 🎓 Real-World Usage Patterns

### Elementary School
```
Ms. Smith
    └── "My Class"
         └── 25 students
```

### Middle School  
```
Mr. Jones
    ├── "Period 1 - English"
    ├── "Period 2 - English"
    ├── "Period 3 - English"
    └── "Period 4 - English"
         └── ~30 students each
```

### High School
```
Ms. Johnson
    ├── "Period 1 - AP English"  (15 students)
    ├── "Period 2 - English 10"  (28 students)
    ├── "Period 3 - English 11"  (25 students)
    ├── "Period 4 - English 10"  (27 students)
    └── "Period 5 - Remedial"    (12 students)
```

### Tutoring Center
```
Mr. Lee
    ├── "Morning Group"    (5 students)
    ├── "Afternoon Group"  (8 students)
    └── "Weekend Group"    (6 students)
```

## 📈 Scalability

```
System Limits:
├── Teachers: Unlimited
├── Classrooms per teacher: Unlimited
├── Students per classroom: Unlimited
├── Join code uniqueness: 36^8 combinations
│   (2,821,109,907,456 possible codes)
└── Database: Efficiently indexed
```

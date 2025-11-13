# Spelling Game Web Application

A comprehensive web-based spelling game for students with teacher dashboard and configurable difficulty progression.

## Features

### For Students:
- 📚 **Progressive Difficulty**: Start with 3-letter words and advance through difficulty buckets based on word length
- 🔊 **Audio Pronunciation**: Hear words spoken using browser's Text-to-Speech (Web Speech API)
- 📖 **Dictionary Integration**: Get definitions from the Free Dictionary API
- 🎯 **Smart Word Recycling**: Incorrect words return within the next 100 words (configurable)
- 💾 **Progress Saving**: Progress is automatically saved - pick up where you left off
- 📊 **Session Tracking**: See both current session score and overall progress
- 🎮 **200 Words Per Bucket**: Master 200 words to advance to the next difficulty (configurable)

### For Teachers:
- 👥 **Student Dashboard**: View all students' progress at a glance
- 📈 **Detailed Analytics**: See individual word performance, session history, and bucket progress
- ⚙️ **Configurable Parameters**: Adjust words-per-bucket and recycling distance
- 📝 **Word-by-Word Analysis**: Identify which words students struggle with

## Technology Stack

- **Backend**: Django 4.2
- **Database**: SQLite (included)
- **Frontend**: HTML, CSS, JavaScript
- **Text-to-Speech**: Web Speech API (client-side, no cost)
- **Dictionary**: Free Dictionary API (https://dictionaryapi.dev)
- **Authentication**: Django built-in with role-based access (Student/Teacher)

## Installation

1. **Python Virtual Environment** (already created):
   ```bash
   source venv/bin/activate
   ```

2. **Database** (already migrated):
   ```bash
   python manage.py migrate
   ```

3. **Load Word Database** (already loaded):
   ```bash
   python manage.py load_words
   ```

4. **Create Demo Users** (already created):
   ```bash
   python manage.py create_demo_users
   ```

## Running the Application

```bash
python manage.py runserver
```

Then open your browser to: **http://127.0.0.1:8000/**

## Demo Accounts

### Teacher Account:
- **Username**: `teacher`
- **Password**: `teacher123`

### Student Account:
- **Username**: `student`
- **Password**: `student123`

### Admin Account (for Django admin):
- **Username**: `admin`
- **Password**: `admin123`
- **Admin Panel**: http://127.0.0.1:8000/admin/

## How to Play (Student)

1. **Login** with a student account
2. Click **"Play"** to start/resume your game
3. **Listen** to the word pronunciation by clicking the 🔊 button
4. **View the definition** by clicking the 📖 button
5. **Type** the spelling in the input box
6. **Submit** your answer
7. Get **immediate feedback** (correct/incorrect)
8. Incorrect words will **reappear** later for practice
9. **Complete 200 words** in a bucket to advance to the next difficulty
10. **End session** anytime - progress is saved automatically

## Teacher Dashboard

1. **Login** with a teacher account
2. View **all students** and their overall statistics
3. Click **"View Details"** for any student to see:
   - Bucket progress
   - Session history
   - Individual word performance
   - Accuracy rates
4. Go to **"Settings"** to configure:
   - Words required per bucket (default: 200)
   - Recycling distance for incorrect words (default: 100)

## Database Schema

### Key Models:
- **User**: Extended Django user with student/teacher roles
- **Word**: 1000+ words organized by difficulty (word length)
- **StudentProgress**: Overall progress tracking
- **BucketProgress**: Progress within each difficulty bucket
- **GameSession**: Individual play sessions
- **WordAttempt**: Each word attempt with correctness tracking
- **WordQueue**: Student's current word queue with recycling
- **GameConfiguration**: Teacher-configurable game parameters

## Word Difficulty Buckets

Words are organized into buckets by length:
- Bucket 3: 3-letter words (the, and, for, etc.)
- Bucket 4: 4-letter words (that, with, have, etc.)
- Bucket 5: 5-letter words (there, would, which, etc.)
- ...up to...
- Bucket 15: 15-letter words (characterization, etc.)

Students start at **Bucket 3** and progress upward.

## Customization

### Adding More Words:
Edit `game/management/commands/load_words.py` and run:
```bash
python manage.py load_words
```

### Changing Game Parameters:
Teachers can change parameters via the Settings page, or you can modify defaults in:
- `game/models.py` → `GameConfiguration` model

## API Endpoints

- `GET /api/next-word/` - Get next word for student
- `POST /api/submit-answer/` - Submit word spelling attempt
- `POST /api/end-session/` - End current game session

## File Structure

```
Spelling-Game/
├── accounts/           # User authentication app
│   ├── models.py      # User model with roles
│   ├── views.py       # Login/register views
│   └── admin.py       # Admin configuration
├── game/              # Main game app
│   ├── models.py      # Game models
│   ├── views.py       # Game logic and teacher dashboard
│   ├── admin.py       # Admin configuration
│   └── management/
│       └── commands/
│           ├── load_words.py        # Word database loader
│           └── create_demo_users.py # Demo account creator
├── templates/
│   ├── base.html              # Base template
│   ├── accounts/              # Auth templates
│   └── game/                  # Game templates
├── static/
│   ├── css/style.css          # Main stylesheet
│   └── js/game.js             # Game JavaScript with Web Speech API
├── spelling_game/     # Django project settings
└── manage.py          # Django management script
```

## Browser Compatibility

- **Text-to-Speech**: Requires browsers with Web Speech API support (Chrome, Edge, Safari, Firefox)
- **Dictionary API**: Works in all modern browsers

## Future Enhancements

Potential improvements:
- Add multiplayer competitions
- Leaderboards
- Timed challenges
- Custom word lists
- Export student reports
- Mobile app version

## Support

For issues or questions, please check the Django documentation:
- https://docs.djangoproject.com/

## License

Educational project - free to use and modify.

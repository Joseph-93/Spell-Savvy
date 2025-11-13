# 🛠️ Common Commands Reference

## Server Management

### Start Development Server
```bash
cd /home/joshua/Spelling-Game
source venv/bin/activate
python manage.py runserver
```
**Access at:** http://127.0.0.1:8000/

### Stop Server
Press `CTRL+C` in the terminal

---

## Database Commands

### Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Load Words Database
```bash
python manage.py load_words
```

### Create Demo Users
```bash
python manage.py create_demo_users
```

### Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### Database Shell
```bash
python manage.py dbshell
```

### Django Shell
```bash
python manage.py shell
```

---

## User Management

### Create User Programmatically
```python
python manage.py shell

from accounts.models import User

# Create student
student = User.objects.create_user(
    username='newstudent',
    password='password123',
    email='student@example.com',
    role='student'
)

# Create teacher
teacher = User.objects.create_user(
    username='newteacher',
    password='password123',
    email='teacher@example.com',
    role='teacher'
)
```

### Change Password
```python
python manage.py shell

from accounts.models import User
user = User.objects.get(username='student')
user.set_password('newpassword')
user.save()
```

---

## Data Management

### Export Data
```bash
# Export all data
python manage.py dumpdata > backup.json

# Export specific app
python manage.py dumpdata game > game_backup.json
python manage.py dumpdata accounts > accounts_backup.json

# Export specific model
python manage.py dumpdata game.Word > words_backup.json
```

### Import Data
```bash
python manage.py loaddata backup.json
```

### Clear Database
```bash
# Delete database file
rm db.sqlite3

# Recreate database
python manage.py migrate
python manage.py load_words
python manage.py create_demo_users
```

---

## Development Commands

### Check for Issues
```bash
python manage.py check
```

### Create New App
```bash
python manage.py startapp appname
```

### Collect Static Files (for production)
```bash
python manage.py collectstatic
```

### Run Tests
```bash
python manage.py test
```

---

## Database Queries

### View All Students
```python
python manage.py shell

from accounts.models import User
students = User.objects.filter(role='student')
for s in students:
    print(f"{s.username}: {s.email}")
```

### View Student Progress
```python
from game.models import StudentProgress
progress = StudentProgress.objects.all()
for p in progress:
    print(f"{p.student.username}: Bucket {p.current_bucket}, {p.total_words_correct} correct")
```

### View Words by Bucket
```python
from game.models import Word
bucket_5_words = Word.objects.filter(difficulty_bucket=5)
print(f"Bucket 5 has {bucket_5_words.count()} words")
```

### View Recent Sessions
```python
from game.models import GameSession
recent = GameSession.objects.order_by('-started_at')[:10]
for session in recent:
    print(f"{session.student.username}: {session.words_correct}/{session.words_attempted}")
```

---

## Maintenance Commands

### Reset Student Progress
```python
python manage.py shell

from game.models import StudentProgress, WordQueue, BucketProgress, WordAttempt, GameSession
from accounts.models import User

student = User.objects.get(username='student')

# Delete all progress
StudentProgress.objects.filter(student=student).delete()
WordQueue.objects.filter(student=student).delete()
BucketProgress.objects.filter(student=student).delete()
WordAttempt.objects.filter(student=student).delete()
GameSession.objects.filter(student=student).delete()
```

### View Statistics
```python
python manage.py shell

from game.models import Word, StudentProgress, GameSession
from accounts.models import User

print(f"Total words: {Word.objects.count()}")
print(f"Total students: {User.objects.filter(role='student').count()}")
print(f"Total teachers: {User.objects.filter(role='teacher').count()}")
print(f"Total sessions: {GameSession.objects.count()}")
```

---

## Environment Commands

### Activate Virtual Environment
```bash
source venv/bin/activate
```

### Deactivate Virtual Environment
```bash
deactivate
```

### Install New Package
```bash
pip install package-name
pip freeze > requirements.txt
```

### Update Django
```bash
pip install --upgrade django
```

---

## Admin Panel Commands

### Access Admin
**URL:** http://127.0.0.1:8000/admin/

**Login with:**
- Username: `admin`
- Password: `admin123`

### From Admin Panel You Can:
- Add/edit/delete users
- View all database records
- Add/edit/delete words
- View student progress
- Manage sessions
- Configure game settings

---

## Debugging Commands

### View Server Logs
The terminal running `runserver` shows all requests and errors

### Django Debug
```python
python manage.py shell

# Import models
from game.models import *
from accounts.models import *

# Query data
print(User.objects.all())
print(Word.objects.all())
```

### Check URLs
```bash
python manage.py show_urls  # If django-extensions installed
```

---

## Quick Troubleshooting

### "No module named X"
```bash
pip install X
```

### "Table doesn't exist"
```bash
python manage.py migrate
```

### "Permission denied"
```bash
chmod +x manage.py
```

### "Port already in use"
```bash
# Use different port
python manage.py runserver 8080

# Or kill process on port 8000
lsof -ti:8000 | xargs kill
```

### Reset Everything
```bash
# Delete database and migrations
rm db.sqlite3
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# Recreate
python manage.py makemigrations
python manage.py migrate
python manage.py load_words
python manage.py create_demo_users
```

---

## Useful Python Snippets

### Add Multiple Words
```python
python manage.py shell

from game.models import Word

words = ['example', 'sample', 'test']
for word_text in words:
    Word.objects.create(
        text=word_text,
        word_length=len(word_text),
        difficulty_bucket=len(word_text)
    )
```

### Bulk Create Users
```python
from accounts.models import User

for i in range(1, 11):
    User.objects.create_user(
        username=f'student{i}',
        password='student123',
        email=f'student{i}@example.com',
        role='student'
    )
```

---

## Git Commands (Optional)

### Initialize Git
```bash
git init
git add .
git commit -m "Initial commit: Spelling Game complete"
```

### Create Repository
```bash
# On GitHub, create new repo, then:
git remote add origin https://github.com/yourusername/spelling-game.git
git branch -M main
git push -u origin main
```

---

## Production Deployment (Future)

### Settings to Change:
```python
# In spelling_game/settings.py

DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
SECRET_KEY = 'generate-new-secret-key'

# Use PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'spellingdb',
        'USER': 'dbuser',
        'PASSWORD': 'dbpassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

### Collect Static Files
```bash
python manage.py collectstatic
```

---

## Quick Reference Card

| Action | Command |
|--------|---------|
| Start server | `python manage.py runserver` |
| Access app | http://127.0.0.1:8000/ |
| Access admin | http://127.0.0.1:8000/admin/ |
| Create migrations | `python manage.py makemigrations` |
| Apply migrations | `python manage.py migrate` |
| Load words | `python manage.py load_words` |
| Create users | `python manage.py create_demo_users` |
| Django shell | `python manage.py shell` |
| DB shell | `python manage.py dbshell` |

---

**Keep this file handy for quick reference!** 📚

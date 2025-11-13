from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = 'Create demo users for testing'

    def handle(self, *args, **kwargs):
        # Create teacher
        teacher, created = User.objects.get_or_create(
            username='teacher',
            defaults={
                'email': 'teacher@example.com',
                'role': 'teacher'
            }
        )
        if created:
            teacher.set_password('teacher123')
            teacher.save()
            self.stdout.write(self.style.SUCCESS('Created teacher account: teacher / teacher123'))
        else:
            self.stdout.write(self.style.WARNING('Teacher account already exists'))
        
        # Create student and assign to teacher
        student, created = User.objects.get_or_create(
            username='student',
            defaults={
                'email': 'student@example.com',
                'role': 'student',
                'teacher': teacher
            }
        )
        if created:
            student.set_password('student123')
            student.save()
            self.stdout.write(self.style.SUCCESS('Created student account: student / student123'))
        else:
            # Update existing student to have teacher if they don't
            if not student.teacher:
                student.teacher = teacher
                student.save()
                self.stdout.write(self.style.SUCCESS('Assigned student to teacher'))
            self.stdout.write(self.style.WARNING('Student account already exists'))
        
        # Update admin user to be a teacher
        try:
            admin = User.objects.get(username='admin')
            admin.set_password('admin123')
            admin.role = 'teacher'
            admin.save()
            self.stdout.write(self.style.SUCCESS('Updated admin account: admin / admin123'))
        except User.DoesNotExist:
            pass
        
        self.stdout.write(self.style.SUCCESS('\nDemo accounts created successfully!'))
        self.stdout.write('Teacher: teacher / teacher123')
        self.stdout.write('Student: student / student123 (assigned to teacher)')
        self.stdout.write('Admin: admin / admin123')

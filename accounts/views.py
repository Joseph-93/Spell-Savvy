from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User


def login_view(request):
    """Login page"""
    if request.user.is_authenticated:
        if request.user.is_teacher():
            return redirect('teacher_dashboard')
        return redirect('student_game')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Redirect based on role
            if user.is_teacher():
                return redirect('teacher_dashboard')
            else:
                return redirect('student_game')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'accounts/login.html')


def register_view(request):
    """Registration page"""
    if request.user.is_authenticated:
        return redirect('home')
    
    # Check if there's a join code in the URL
    join_code = request.GET.get('join', '').strip().upper()
    classroom = None
    
    if join_code:
        try:
            from game.models import Classroom
            classroom = Classroom.objects.get(join_code=join_code, is_active=True)
        except Classroom.DoesNotExist:
            messages.error(request, f'Invalid or expired join code: {join_code}')
            join_code = None
    
    # Get all teachers for the dropdown (fallback)
    teachers = User.objects.filter(role='teacher').order_by('username')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        email = request.POST.get('email', '')
        role = request.POST.get('role', 'student')
        teacher_id = request.POST.get('teacher')
        join_code_submitted = request.POST.get('join_code', '').strip().upper()
        
        # Validate
        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        elif role == 'student' and not teacher_id and not join_code_submitted:
            messages.error(request, 'Students must select a teacher or use a join code')
        else:
            # Create user
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                role=role
            )
            
            # Handle classroom join code (preferred method)
            if role == 'student' and join_code_submitted:
                try:
                    from game.models import Classroom
                    classroom_obj = Classroom.objects.get(
                        join_code=join_code_submitted,
                        is_active=True
                    )
                    user.classroom = classroom_obj
                    user.teacher = classroom_obj.teacher  # Set legacy field too
                    user.save()
                    messages.success(
                        request,
                        f'✅ Joined {classroom_obj.name} (Teacher: {classroom_obj.teacher.username})'
                    )
                except:
                    messages.warning(request, 'Join code invalid, but account created')
            # Fallback to teacher selection (legacy)
            elif role == 'student' and teacher_id:
                try:
                    teacher = User.objects.get(id=teacher_id, role='teacher')
                    user.teacher = teacher
                    user.save()
                except User.DoesNotExist:
                    pass
            
            # Log them in
            login(request, user)
            
            messages.success(request, f'Account created successfully! Welcome, {username}!')
            
            # Redirect based on role
            if user.is_teacher():
                return redirect('teacher_dashboard')
            else:
                return redirect('student_game')
    
    context = {
        'teachers': teachers,
        'join_code': join_code,
        'classroom': classroom,
    }
    
    return render(request, 'accounts/register.html', context)


@login_required
def logout_view(request):
    """Logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('login')

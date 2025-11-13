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
    
    # Get all teachers for the dropdown
    teachers = User.objects.filter(role='teacher').order_by('username')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        email = request.POST.get('email', '')
        role = request.POST.get('role', 'student')
        teacher_id = request.POST.get('teacher')
        
        # Validate
        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        elif role == 'student' and not teacher_id:
            messages.error(request, 'Students must select a teacher')
        else:
            # Create user
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                role=role
            )
            
            # Assign teacher if student
            if role == 'student' and teacher_id:
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
    
    return render(request, 'accounts/register.html', {'teachers': teachers})


@login_required
def logout_view(request):
    """Logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('login')

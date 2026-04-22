import os
import sys
import json
import time
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django import forms
from django.core.management import execute_from_command_line

# Добавляем корневую папку проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from recommender import RecommenderEngine
from .models import Movie, UserRating

# Автоматические миграции при старте
#try:
#    execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
#except Exception:
#    pass

# Создание суперпользователя из переменных окружения
#ADMIN_USER = os.environ.get('ADMIN_USER')
#ADMIN_PASS = os.environ.get('ADMIN_PASS')
#if ADMIN_USER and ADMIN_PASS:
#    User.objects.create_superuser(ADMIN_USER, '', ADMIN_PASS)


# Глобальный экземпляр движка
_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = RecommenderEngine()
        # Путь к data/ml-latest-small относительно корневой папки проекта
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        base_path = os.path.join(project_root, 'data', 'ml-latest-small')
        _engine.fit(base_path)
    return _engine


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label='Повторите пароль')


def index(request):
    user_ratings = {}
    if request.user.is_authenticated:
        user_ratings = {ur.movie.title: ur.rating for ur in request.user.ratings.all()}
    return render(request, 'index.html', {'user_ratings': user_ratings})


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['password'] == form.cleaned_data['password2']:
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                if User.objects.filter(username=username).exists():
                    return render(request, 'register.html', {'error': 'Пользователь уже существует'})
                user = User.objects.create_user(username=username, password=password)
                login(request, user)
                return redirect('index')
            else:
                return render(request, 'register.html', {'error': 'Пароли не совпадают'})
    return render(request, 'register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('index')
        return render(request, 'login.html', {'error': 'Неверные данные'})
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('index')


@login_required
@csrf_exempt
def rate_movie(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title')
            rating = float(data.get('rating', 0))
            
            # Находим фильм по названию
            movie = Movie.objects.filter(title__icontains=title).first()
            if not movie:
                return JsonResponse({'error': 'Фильм не найден'}, status=404)
            
            # Сохраняем или обновляем оценку
            user_rating, created = UserRating.objects.update_or_create(
                user=request.user,
                movie=movie,
                defaults={'rating': rating, 'timestamp': int(time.time())}
            )
            
            return JsonResponse({'success': True, 'message': 'Оценка сохранена'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Use POST method'}, status=405)


def search_movies(request):
    """API для поиска фильмов по названию (автодополнение)"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'movies': []})
    
    movies = Movie.objects.filter(title__icontains=query)[:10]
    return JsonResponse({'movies': [{'id': m.movie_id, 'title': m.title} for m in movies]})


@login_required
@csrf_exempt
def recommend(request):
    if request.method == 'POST':
        print("RECOMMEND CALLED")
        try:
            data = json.loads(request.body)
            ratings = data.get('ratings', {})
            print("RATINGS FROM FRONT:", ratings)
            # Сохраняем оценки пользователя
            for title, rating in ratings.items():
                movie = Movie.objects.filter(title__icontains=title).first()
                if movie:
                    UserRating.objects.update_or_create(
                        user=request.user,
                        movie=movie,
                        defaults={'rating': float(rating), 'timestamp': int(time.time())}
                    )
            
            # Получаем оценки пользователя из БД для рекомендаций
            user_db_ratings = {ur.movie.title: ur.rating for ur in request.user.ratings.all()}
            print("DB RATINGS:", user_db_ratings)
            engine = get_engine()



            
            return JsonResponse({"ok": True})
            recs = engine.get_user_recommendations(user_db_ratings, n_rec=5)
            
            result = {title: float(score) for title, score in recs.items()}
            return JsonResponse({'recommendations': result})
        except Exception as e:
            print("ERROR:", e)
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Use POST method'}, status=405)

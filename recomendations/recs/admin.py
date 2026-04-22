from django.contrib import admin
from .models import Movie, UserRating


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('movie_id', 'title', 'genres')
    search_fields = ('title',)
    list_filter = ('genres',)


@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'rating', 'timestamp')
    search_fields = ('user__username', 'movie__title')
    list_filter = ('rating', 'user')
    raw_id_fields = ('user', 'movie')
    list_editable = ('rating',)

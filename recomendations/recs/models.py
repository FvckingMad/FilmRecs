from django.db import models
from django.contrib.auth.models import User


class Movie(models.Model):
    movie_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    genres = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = 'movies'

    def __str__(self):
        return self.title


class UserRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='user_ratings')
    rating = models.FloatField()
    timestamp = models.IntegerField()

    class Meta:
        db_table = 'user_ratings'
        unique_together = ('user', 'movie')

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}: {self.rating}"

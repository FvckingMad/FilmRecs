import csv
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from recs.models import Movie, UserRating


class Command(BaseCommand):
    help = 'Load movies and ratings from MovieLens dataset'

    def handle(self, *args, **options):

        # =========================
        # PATH
        # =========================
        base_path = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(
                            os.path.dirname(__file__)
                        )
                    )
                )
            ),
            'data',
            'ml-latest-small'
        )

        # =========================
        # SYSTEM USER (ВАЖНО)
        # =========================
        User = get_user_model()
        system_user, _ = User.objects.get_or_create(username="system")

        # =========================
        # LOAD MOVIES
        # =========================
        movies_path = os.path.join(base_path, 'movies.csv')
        self.stdout.write('Loading movies...')

        movies_map = {}

        with open(movies_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                movie, _ = Movie.objects.get_or_create(
                    movie_id=int(row['movieId']),
                    defaults={
                        'title': row['title'],
                        'genres': row['genres']
                    }
                )
                movies_map[int(row['movieId'])] = movie

        self.stdout.write(self.style.SUCCESS(f'Loaded {len(movies_map)} movies'))

        # =========================
        # LOAD RATINGS
        # =========================
        ratings_path = os.path.join(base_path, 'ratings.csv')
        self.stdout.write('Loading ratings...')

        ratings_batch = []
        batch_size = 1000
        ratings_count = 0

        # защита от дублей (user, movie)
        existing = set(
            UserRating.objects.values_list('user_id', 'movie_id')
        )

        with open(ratings_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:

                movie_id = int(row['movieId'])
                movie = movies_map.get(movie_id)

                if not movie:
                    continue

                key = (system_user.id, movie.id)

                if key in existing:
                    continue

                ratings_batch.append(UserRating(
                    user=system_user,   # 🔥 ВАЖНО: не user_id из CSV
                    movie=movie,
                    rating=float(row['rating']),
                    timestamp=int(row['timestamp'])
                ))

                existing.add(key)
                ratings_count += 1

                if len(ratings_batch) >= batch_size:
                    UserRating.objects.bulk_create(ratings_batch)
                    ratings_batch = []

        if ratings_batch:
            UserRating.objects.bulk_create(ratings_batch)

        self.stdout.write(
            self.style.SUCCESS(f'Loaded {ratings_count} ratings')
        )
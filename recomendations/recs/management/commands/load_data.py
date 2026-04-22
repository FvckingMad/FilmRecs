import csv
import os
from django.core.management.base import BaseCommand
from recs.models import Movie, UserRating


class Command(BaseCommand):
    help = 'Load movies and ratings from MovieLens dataset'

    def handle(self, *args, **options):
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
        # LOAD MOVIES
        # =========================
        movies_path = os.path.join(base_path, 'movies.csv')
        self.stdout.write('Loading movies...')

        movies_count = 0

        # 🔥 быстрее: один раз читаем всё
        with open(movies_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                Movie.objects.get_or_create(
                    movie_id=int(row['movieId']),
                    defaults={
                        'title': row['title'],
                        'genres': row['genres']
                    }
                )
                movies_count += 1

        self.stdout.write(self.style.SUCCESS(f'Loaded {movies_count} movies'))

        # =========================
        # PRELOAD MOVIES MAP (ускорение)
        # =========================
        movies_map = {
            m.movie_id: m
            for m in Movie.objects.all()
        }

        # =========================
        # LOAD RATINGS
        # =========================
        ratings_path = os.path.join(base_path, 'ratings.csv')
        self.stdout.write('Loading ratings...')

        ratings_batch = []
        batch_size = 1000
        ratings_count = 0

        # 🔥 защита от дублей (user_id, movie_id)
        existing = set(
            UserRating.objects.values_list('user_id', 'movie_id')
        )

        with open(ratings_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                movie_id = int(row['movieId'])
                user_id = int(row['userId'])

                movie = movies_map.get(movie_id)
                if not movie:
                    continue

                key = (user_id, movie.id)

                # 🚨 пропуск дублей
                if key in existing:
                    continue

                ratings_batch.append(UserRating(
                    user_id=user_id,
                    movie=movie,
                    rating=float(row['rating']),
                    timestamp=int(row['timestamp'])
                ))

                existing.add(key)
                ratings_count += 1

                if len(ratings_batch) >= batch_size:
                    UserRating.objects.bulk_create(ratings_batch)
                    ratings_batch = []

        # финальный batch
        if ratings_batch:
            UserRating.objects.bulk_create(ratings_batch)

        self.stdout.write(
            self.style.SUCCESS(f'Loaded {ratings_count} ratings')
        )
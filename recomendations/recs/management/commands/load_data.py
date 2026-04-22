import csv
import os
from django.core.management.base import BaseCommand
from recs.models import Movie, UserRating


class Command(BaseCommand):
    help = 'Load movies and ratings from MovieLens dataset'

    def handle(self, *args, **options):
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), 'data', 'ml-latest-small')
        
        # Load movies
        movies_path = os.path.join(base_path, 'movies.csv')
        self.stdout.write('Loading movies...')
        
        movies_count = 0
        with open(movies_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                Movie.objects.get_or_create(
                    movie_id=int(row['movieId']),
                    title=row['title'],
                    genres=row['genres']
                )
                movies_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Loaded {movies_count} movies'))

        # Load ratings
        ratings_path = os.path.join(base_path, 'ratings.csv')
        self.stdout.write('Loading ratings...')
        
        ratings_count = 0
        batch_size = 1000
        ratings_batch = []
        
        with open(ratings_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                movie = Movie.objects.filter(movie_id=int(row['movieId'])).first()
                if movie:
                    ratings_batch.append(UserRating(
                        user_id=int(row['userId']),
                        movie=movie,
                        rating=float(row['rating']),
                        timestamp=int(row['timestamp'])
                    ))
                    ratings_count += 1
                
                if len(ratings_batch) >= batch_size:
                    UserRating.objects.bulk_create(ratings_batch)
                    ratings_batch = []
        
        if ratings_batch:
            UserRating.objects.bulk_create(ratings_batch)
        
        self.stdout.write(self.style.SUCCESS(f'Loaded {ratings_count} ratings'))
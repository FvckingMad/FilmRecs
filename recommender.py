import pandas as pd
import joblib
from rapidfuzz import process, utils, fuzz
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

class RecommenderEngine:
    def __init__(self):
        self.item_similarity_df = None
        self.user_movie_matrix = None
        self.movie_titles = None
        self.content_sim_df = None
    def _refresh_engine(self):
        print("Refreshing engine weights and popularity...")
        
        rating_sim = self._calculate_similarity(self.user_movie_matrix.T)
        rating_sim_df = pd.DataFrame(
            rating_sim, index=self.user_movie_matrix.columns, columns=self.user_movie_matrix.columns
        )

        if self.content_sim_df is not None:
            common = rating_sim_df.index.intersection(self.content_sim_df.index)
            self.item_similarity_df = (rating_sim_df.loc[common, common] * 0.7 + 
                                       self.content_sim_df.loc[common, common] * 0.3)
        else:
            self.item_similarity_df = rating_sim_df

        popularity = (self.user_movie_matrix > 0).sum(axis=0)
        self.movie_titles = popularity.sort_values(ascending=False).index.intersection(self.item_similarity_df.index).tolist()
    def _calculate_similarity(self, matrix):
        """Internal method to compute similarity matrix."""
        sim_matrix = cosine_similarity(matrix)
        return sim_matrix
    def fit(self, folder_path):
        """
        Method to fully fit the model (downloading data -> processing tags -> building hybrid model)
        
        :param folder_path: path to folder with ratings.csv, movies.csv, tags.csv
        """
        print("Loading files...")
        ratings = pd.read_csv(f"{folder_path}/ratings.csv")
        movies = pd.read_csv(f"{folder_path}/movies.csv")
        tags = pd.read_csv(f"{folder_path}/tags.csv")

        full_df = pd.merge(ratings, movies[['movieId', 'title']], on='movieId')
        self.user_movie_matrix = full_df.pivot_table(index='userId', columns='title', values='rating').fillna(0)

        print("Processing tags metadata...")
        movie_content = tags.groupby('movieId')['tag'].apply(lambda x: ' '.join(x.astype(str))).reset_index()
        movie_content = pd.merge(movies, movie_content, on='movieId', how='left').fillna('')
        movie_content['metadata'] = movie_content['genres'].str.replace('|', ' ') + ' ' + movie_content['tag']
        
        tfidf = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf.fit_transform(movie_content['metadata'])
        
        c_sim = self._calculate_similarity(tfidf_matrix)
        self.content_sim_df = pd.DataFrame(c_sim, index=movie_content['title'], columns=movie_content['title'])

        self._refresh_engine()
        print(f"Fit complete. Movies: {len(self.movie_titles)}")
    def update_model(self, ratings_list):
        if not ratings_list: return
        
        print(f"Incremental update with {len(ratings_list)} records...")
        new_data_df = pd.DataFrame(ratings_list, columns=['userId', 'title', 'rating'])
        new_pivot = new_data_df.pivot_table(index='userId', columns='title', values='rating').fillna(0)

        self.user_movie_matrix = new_pivot.combine_first(self.user_movie_matrix).fillna(0)

        self._refresh_engine()
        print("Update complete.")
    def save_model(self, path="models/movie_model.joblib"):
        model_data = {
            'matrix': self.item_similarity_df,
            'source': self.user_movie_matrix,
            'titles': self.movie_titles,
            'content_sim': self.content_sim_df
        }
        joblib.dump(model_data, path)

    def load_model(self, path="models/movie_model.joblib"):
        data = joblib.load(path)
        self.item_similarity_df = data['matrix']
        self.user_movie_matrix = data['source']
        self.movie_titles = data['titles']
        self.content_sim_df = data.get('content_sim')
    def find_title(self, query):
        match = process.extractOne(
            query, 
            self.movie_titles, 
            processor=utils.default_process,
            scorer=fuzz.token_set_ratio
        )
        return match[0] if match and match[1] > 65 else None
    def get_user_recommendations(self, user_ratings, n_rec=5):
        """
        user_ratings: dict { 'Movie Title': rating_value }
        Example: {'Toy Story (1995)': 5.0, 'Aladdin (1992)': 4.0}
        """
        if not user_ratings:
            return pd.Series(1, index=self.movie_titles[:n_rec])

        sim_scores = pd.Series(dtype='float64')

        for movie, rating in user_ratings.items():
            clean_title = self.find_title(movie)
            if clean_title and clean_title in self.item_similarity_df.columns:
                weight = rating - 2.5
                similar_movies = self.item_similarity_df[clean_title] * weight
                sim_scores = sim_scores.add(similar_movies, fill_value=0)

        sim_scores = sim_scores.drop(user_ratings.keys(), errors='ignore')
        
        return sim_scores.sort_values(ascending=False).head(n_rec)
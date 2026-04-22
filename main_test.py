"""
AI generated minimalistic test pipeline
TODO: create a better well-rounded test pipeline
"""

import os
import pandas as pd
from recommender import RecommenderEngine  # Assuming your class is in recommender.py

def run_tests():
    # 1. Initialization
    engine = RecommenderEngine()
    data_path = "data/ml-latest-small"  # Path to the folder containing csv files
    
    print("--- STAGE 1: Initial Model Fit ---")
    if os.path.exists(data_path):
        # This will load ratings, movies, and tags, then build the hybrid matrix
        engine.fit(data_path)
    else:
        print(f"Error: Data folder '{data_path}' not found. Please check the path!")
        return

    # 2. Fuzzy Search Test
    print("\n--- STAGE 2: Title Search Test (Fuzzy Matching) ---")
    query = "Interstel"
    found = engine.find_title(query)
    print(f"Searching for '{query}': Found -> {found}")

    # 3. Cold Start Test (New User)
    print("\n--- STAGE 3: Cold Start Recommendations (New User) ---")
    # If the user has no ratings, the engine should return the most popular movies
    new_user_recs = engine.get_user_recommendations({}, n_rec=5)
    print("Top popular movies for a new user:")
    print(new_user_recs)

    # 4. Warm Start Test (User with preferences)
    print("\n--- STAGE 4: Personalized Recommendations ---")
    # Simulation: User liked a specific animated movie
    my_ratings = {'Toy Story (1995)': 5.0}
    recs = engine.get_user_recommendations(my_ratings, n_rec=5)
    print(f"Based on your interest in 'Toy Story', we recommend:")
    print(recs)

    # 5. Incremental Update Test (Dynamic Learning)
    print("\n--- STAGE 5: Incremental Model Update ---")
    # Simulation: A new user (ID 9999) provides high ratings for modern Sci-Fi
    new_ratings_data = [
        (9999, 'Inception (2010)', 5.0),
        (9999, 'Interstellar (2014)', 5.0)
    ]
    
    # This should trigger _refresh_engine and update the global similarity matrix
    engine.update_model(new_ratings_data)
    
    # Check if recommendations change or adapt after the update
    updated_recs = engine.get_user_recommendations({'Inception (2010)': 5.0}, n_rec=5)
    print("New recommendations after training on fresh data:")
    print(updated_recs)

    # 6. Persistence Test (Save and Load)
    print("\n--- STAGE 6: Persistence Test (Save/Load) ---")
    model_dir = "models"
    model_file = f"{model_dir}/movie_model.joblib"
    
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
    
    # Saving current state (including content-based similarity)
    engine.save_model(model_file)
    
    # Creating a brand new engine instance to test loading
    new_engine = RecommenderEngine()
    new_engine.load_model(model_file)
    
    print("Model successfully saved and reloaded.")
    print(f"Total movies in memory after reload: {len(new_engine.movie_titles)}")
    
    # Quick check on a reloaded search
    reloaded_check = new_engine.find_title("Pulp Fiction")
    print(f"Verification search after reload: {reloaded_check}")
    updated_recs = new_engine.get_user_recommendations({'Inception (2010)': 5.0}, n_rec=5)
    print("New reloaded recommendations after training on fresh data:")
    print(updated_recs)

if __name__ == "__main__":
    run_tests()
from recommender import *

engine = RecommenderEngine()

engine.fit('data\ml-latest-small')
engine.save_model()
engine.load_model()


ratings = {
    'pulp fiction':1,
    'resevoir dogs':2,
    'hangover':5
}

recs =  engine.get_user_recommendations(ratings)

print(recs)
# Trains a regression model that estimates repair cost from the description + category: python models/train_cost_model.py

import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

from text_utils import clean_text

data = pd.read_csv("data/cost_data.csv")

data["combined_text"] = data["category"] + " " + data["text"]
data["clean_text"] = data["combined_text"].apply(clean_text)

X = data["clean_text"]
y = data["cost"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = Pipeline([
    ("tfidf", TfidfVectorizer()),
    ("reg", RandomForestRegressor(n_estimators=150, random_state=42))
])

model.fit(X_train, y_train)

score = model.score(X_test, y_test)
print("Cost model R2 score on test set:", score)

joblib.dump(model, "cost_model.pkl")
print("Saved cost_model.pkl")

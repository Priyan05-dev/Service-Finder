# Trains a text classifier that predicts the service category from a problem description: python models/train_category_model.py

import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

from text_utils import clean_text

data = pd.read_csv("data/category_data.csv")
data["clean_text"] = data["text"].apply(clean_text)

X = data["clean_text"]
y = data["category"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = Pipeline([
    ("tfidf", TfidfVectorizer()),
    ("clf", MultinomialNB())
])

model.fit(X_train, y_train)

score = model.score(X_test, y_test)
print("Category model test accuracy:", score)

joblib.dump(model, "category_model.pkl")
print("Saved category_model.pkl")

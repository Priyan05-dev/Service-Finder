# Run this ONE TIME before training the models (needs internet): python download_nltk_data.py

import nltk

nltk.download("punkt")
nltk.download("punkt_tab")
nltk.download("stopwords")
nltk.download("wordnet")
nltk.download("omw-1.4")

print("nltk data downloaded")

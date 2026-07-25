# Basic text cleaning using nltk, used before feeding text into sklearn models

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()


def clean_text(text):
    text = text.lower()
    tokens = word_tokenize(text)

    cleaned = []
    for word in tokens:
        if word.isalpha() and word not in stop_words:
            lemma = lemmatizer.lemmatize(word)
            cleaned.append(lemma)

    return " ".join(cleaned)

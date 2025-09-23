from __future__ import annotations

import nltk
from nltk.data import find


def ensure_punkt():
    try:
        find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt")


def split_into_sentences(text: str):
    ensure_punkt()
    return nltk.sent_tokenize(text)

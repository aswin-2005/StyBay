# tagger.py

from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
import math
import re

# ---------------- Models ---------------- #
# Reuse the same SentenceTransformer for embeddings
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
kw_model = KeyBERT(model=model)

# ---------------- Helper Functions ---------------- #

def construct_input_text(product: dict) -> str:
    """Combine product info into a single string for keyword extraction."""
    parts = []
    if product.get("title"): 
        parts.append(product["title"])
    if product.get("description"): 
        parts.append(product["description"])
    if product.get("source"): 
        parts.append(f"Available on {product['source']}")
    if product.get("price"): 
        parts.append(f"at {product['price']}")
    return " ".join(parts)


def dynamic_top_n(text, min_n=5, max_n=20):
    """Decide how many tags to keep based on text length."""
    word_count = len(text.split())
    estimate = int(math.log2(word_count + 1) * 3)
    return max(min_n, min(estimate, max_n))


# ---------------- Session Query Tagging ---------------- #

def extract_tags_from_text(text: str):
    """
    Convert raw query string into a list of lowercase keyword tags.
    Simple NLP approach: remove non-alphabetic, lowercase, remove duplicates.
    """
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    seen = set()
    tags = []
    for w in words:
        if w not in seen:
            tags.append(w)
            seen.add(w)
    return tags


# ---------------- Product Batch Tagging ---------------- #

def batch_extract_tags(products, batch_size=50):
    """
    Extract tags for a list of product dicts in batches.
    Returns a list of tag lists in the same order as `products`.
    """
    tagged_list = []

    for i in range(0, len(products), batch_size):
        batch = products[i:i + batch_size]
        texts = [construct_input_text(p) for p in batch]

        # Compute embeddings for the whole batch at once
        embeddings = model.encode(texts, show_progress_bar=False)

        for product, text, emb in zip(batch, texts, embeddings):
            # Extract top candidate keywords
            candidates = kw_model.extract_keywords(
                text,
                keyphrase_ngram_range=(1, 1),  # single-word tags
                stop_words='english',
                top_n=50,
                use_mmr=False,
                diversity=0.7
            )

            # Clean and filter candidates
            seen, cleaned = set(), []
            for kw, _ in candidates:
                kw_clean = kw.lower()
                # only keep alphabetic words, avoid duplicates
                if kw_clean not in seen and kw_clean.replace(" ", "").isalpha():
                    cleaned.append(kw_clean)
                    seen.update(kw_clean.split())
                if len(cleaned) >= dynamic_top_n(text):
                    break

            tagged_list.append(cleaned)

    return tagged_list

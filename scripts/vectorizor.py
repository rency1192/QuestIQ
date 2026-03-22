import sqlite3
import pickle
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import (CountVectorizer, TfidfVectorizer)

class Vectorizer:

    def __init__(self, db_path: str, vectors_folder: str):
        self.db_path          = db_path
        self.vectors_folder   = Path(vectors_folder)
        self.vectors_folder.mkdir(parents=True, exist_ok=True)

        self.bow_matrix       = None
        self.tfidf_matrix     = None
        self.bow_vectorizer   = None
        self.tfidf_vectorizer = None
        self.question_ids     = []
        
        
    #Load tokens from db
    def load_tokens(self) -> tuple:
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute(""" 
            SELECT id, tokens, subject, semester, year, q_type
            FROM questions
            WHERE tokens IS NOT NULL
            ORDER BY id
                    """)
        
        rows = cur.fetchall()
        
        conn.close()
        
        ids           = []
        token_strings = []
        metadata      = []
        
        for row in rows:
            ids.append(row["id"])
            token_strings.append(row["tokens"])
            metadata.append({
                "id":       row["id"],
                "subject":  row["subject"],
                "semester": row["semester"],
                "year":     row["year"],
                "q_type":   row["q_type"],
            })
            
        print(f"  Loaded {len(ids)} questions with tokens")
        return ids, token_strings, metadata
    
     # ── BUILD BOW MATRIX ────────────────────────
    def build_bow(self, token_strings: list):
        self.bow_vectorizer = CountVectorizer(min_df=1,max_df=0.95,ngram_range=(1,2))
        self.bow_matrix = self.bow_vectorizer.fit_transform(token_strings)
        
        print(f"  BOW matrix shape : {self.bow_matrix.shape}")
        print(f"  Vocabulary size  : "
              f"{len(self.bow_vectorizer.vocabulary_)}")
        
    # ── BUILD TF-IDF MATRIX ──────────────────────
    def build_tfidf(self, token_strings: list):
        self.tfidf_vectorizer = TfidfVectorizer(min_df=1,max_df=0.95,ngram_range=(1,2),sublinear_tf=True)
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(token_strings)
        
        print(f"  TF-IDF matrix shape : {self.tfidf_matrix.shape}")
        
    # ── EXTRACT KEYWORDS ────────────────────────
    def extract_keywords(self, token_strings: list,
                          ids: list, top_n: int = 5) -> list:
        feature_names = self.tfidf_vectorizer.get_feature_names_out()
        keywords_list = []

        for i, q_id in enumerate(ids):
            row    = self.tfidf_matrix[i]
            scores = zip(
                feature_names,
                np.asarray(row.todense()).flatten()
            )
            sorted_scores = sorted(
                scores, key=lambda x: x[1], reverse=True)
            top_keywords  = [
                word for word, score in sorted_scores[:top_n]
                if score > 0
            ]
            keywords_list.append({
                "id":       q_id,
                "keywords": ", ".join(top_keywords)
            })

        return keywords_list
    
    # ── SAVE KEYWORDS TO DB ──────────────────────
    def save_keywords(self, keywords_list: list):
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for kw in keywords_list:
            cursor.execute(
        """ UPDATE questions SET keywords=? WHERE id=?
        """
           ,(kw["keywords"], kw["id"]) )
            
        conn.commit()
        conn.close()
        print(f"  Saved keywords for {len(keywords_list)} questions")
        
    # ── SAVE MATRICES TO DISK ────────────────────
    def save_vectors(self, ids: list, metadata: list):
        pickle.dump(self.tfidf_matrix,
            open(self.vectors_folder / "tfidf_matrix.pkl", "wb"))

        pickle.dump(self.bow_matrix,
            open(self.vectors_folder / "bow_matrix.pkl", "wb"))

        pickle.dump(self.tfidf_vectorizer,
            open(self.vectors_folder / "tfidf_vectorizer.pkl", "wb"))

        pickle.dump(self.bow_vectorizer,
            open(self.vectors_folder / "bow_vectorizer.pkl", "wb"))

        pickle.dump(ids,
            open(self.vectors_folder / "question_ids.pkl", "wb"))

        pickle.dump(metadata,
            open(self.vectors_folder / "metadata.pkl", "wb"))

        print(f"  Saved all vectors to: {self.vectors_folder}")

    # ── BUILD ────────────────────────────────────
    def build(self):
        print("  Loading tokens from DB...")
        ids, token_strings, metadata = self.load_tokens()

        if not token_strings:
            print("  No tokens found — run preprocessor first")
            return

        print("\n  Building BOW matrix...")
        self.build_bow(token_strings)

        print("\n  Building TF-IDF matrix...")
        self.build_tfidf(token_strings)

        print("\n  Extracting keywords...")
        keywords_list = self.extract_keywords(token_strings, ids)
        self.save_keywords(keywords_list)

        print("\n  Saving vectors to disk...")
        self.save_vectors(ids, metadata)

        print(f"\n  Vectorizer build complete!")
        print(f"  Questions vectorized : {len(ids)}")
        print(f"  Vocabulary size      : "
              f"{len(self.tfidf_vectorizer.vocabulary_)}")

    # ── PRINT SAMPLE ────────────────────────────
    def print_sample(self, n: int = 3):
        conn             = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor           = conn.cursor()

        cursor.execute("""
            SELECT id, question, keywords
            FROM questions
            WHERE keywords IS NOT NULL
            LIMIT ?
        """, (n,))
        rows = cursor.fetchall()
        conn.close()

        print(f"\n  Sample keywords:")
        for row in rows:
            print(f"\n  Q{row['id']}: {row['question'][:60]}...")
            print(f"  Keywords: {row['keywords']}")


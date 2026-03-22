import re
import sqlite3
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus   import stopwords
from nltk.stem     import WordNetLemmatizer


class TextPreprocessor:

    def __init__(self, db_path: str):
        self.db_path    = db_path
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words("english"))

        self.stop_words -= {
            'not', 'no', 'nor', 'against',
            'what', 'which', 'who', 'how', 'why', 'when'
        }
        
        # add domain stopwords — too common in exam questions
        self.stop_words |= {
            # existing ones
            'explain', 'describe', 'define', 'write',
            'discuss', 'elaborate', 'illustrate', 'state',
            'list', 'mention', 'give', 'show', 'find',
            'calculate', 'compute', 'derive', 'prove',
            'example', 'suitable', 'briefly', 'short',
            'note', 'answer', 'question', 'following',
            'given', 'using', 'based', 'compare', 'contrast',

            # add generic tech words
            'algorithm', 'method', 'approach', 'technique',
            'concept', 'model', 'system', 'process',
            'type', 'different', 'various', 'following',
            'suitable', 'proper', 'real', 'world',
            
            'diagram', 'differentiate', 'statement',
            'code', 'phase', 'number', 'one', 'new',
            'time', 'used', 'want', 'use', 'need',
            'make', 'build', 'create', 'design',
            'high', 'low', 'large', 'small',
            'first', 'second', 'third', 'last',
            'two', 'three', 'four', 'five',
            'name', 'form', 'way', 'part', 'role'
        }

    def clean(self, text: str) -> list:
        if not text:
            return []

        text   = text.lower()
        text   = re.sub(r'[^a-z\s]', ' ', text)
        tokens = word_tokenize(text)
        tokens = [
            t for t in tokens
            if t not in self.stop_words
            and len(t) > 2
        ]
        tokens = [self.lemmatizer.lemmatize(t) for t in tokens]
        return tokens

    def process_all(self) -> list:
        conn             = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row          # ← Bug 1 fix
        cursor           = conn.cursor()

        cursor.execute("""
            SELECT id, question, subject, semester,
                   year, q_type, marks
            FROM questions
            WHERE tokens IS NULL
            ORDER BY id
        """)
        rows = cursor.fetchall()
        conn.close()                            # ← Bug 3 fix

        if not rows:
            print("  No new questions to process")
            return []

        preprocessed = []                       # ← Bug 2 fix

        for row in rows:
            tokens = self.clean(row["question"])
            preprocessed.append({               # ← .append not =
                "id":       row["id"],
                "question": row["question"],
                "tokens":   tokens,
                "subject":  row["subject"],
                "semester": row["semester"],
                "year":     row["year"],
                "q_type":   row["q_type"],
                "marks":    row["marks"],
            })

        return preprocessed

    def save_tokens(self, preprocessed: list):
        conn   = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for p in preprocessed:
            cursor.execute("""
                UPDATE questions SET tokens = ?
                WHERE id = ?
            """, (" ".join(p["tokens"]), p["id"]))

        conn.commit()
        conn.close()
        print(f"  Saved tokens for {len(preprocessed)} questions")

    def print_summary(self, preprocessed: list):
        print(f"  Total processed : {len(preprocessed)}")
        print(f"\n  Sample output:")
        for p in preprocessed[:3]:
            print(f"\n  Q{p['id']}: {p['question'][:60]}...")
            print(f"  Tokens: {p['tokens'][:8]}")
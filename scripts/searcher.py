import sqlite3
import pickle
import numpy as np
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
from scripts.preprocessor import TextPreprocessor


class Searcher:

    def __init__(self, db_path: str, vectors_folder: str):
        self.db_path        = db_path
        self.vectors_folder = Path(vectors_folder)
        self.preprocessor   = TextPreprocessor(db_path)

        # loaded from disk
        self.tfidf_matrix     = None
        self.tfidf_vectorizer = None
        self.question_ids     = None
        self.metadata         = None

    # ── LOAD VECTORS ────────────────────────────
    def load(self):
        """
        Load TF-IDF matrix and vectorizer from disk.
        Called once at startup.
        """
        self.tfidf_matrix = pickle.load(
            open(self.vectors_folder / "tfidf_matrix.pkl", "rb"))

        self.tfidf_vectorizer = pickle.load(
            open(self.vectors_folder / "tfidf_vectorizer.pkl", "rb"))

        self.question_ids = pickle.load(
            open(self.vectors_folder / "question_ids.pkl", "rb"))

        self.metadata = pickle.load(
            open(self.vectors_folder / "metadata.pkl", "rb"))

        print(f"  Loaded {len(self.question_ids)} question vectors")

    # PREPROCESS QUERY 
    def preprocess_query(self, query: str) -> str:
        """
        Clean query same way as questions.
        Returns space-separated token string.

        "What is Gradient Descent?"
        → ["gradient", "descent"]
        → "gradient descent"
        """
        tokens = self.preprocessor.clean(query)
        return " ".join(tokens)

    # ── GET FILTERED IDS FROM DB ─────────────────
    def get_filtered_ids(self,
                          subject:  str  = None,
                          semester: int  = None,
                          year:     int  = None,
                          year_from:int  = None,
                          year_to:  int  = None,
                          marks:    float= None,
                          q_type:   str  = None) -> list:
        """
        SQL filter — returns list of question IDs
        that match the given filters.

        All filters are optional.
        Only provided filters are applied.
        """
        conn   = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query  = "SELECT id FROM questions WHERE 1=1"
        params = []

        if subject:
            query += " AND LOWER(subject) LIKE LOWER(?)"
            params.append(f"%{subject}%")

        if semester:
            query += " AND semester = ?"
            params.append(semester)

        if year:
            query += " AND year = ?"
            params.append(year)

        if year_from:
            query += " AND year >= ?"
            params.append(year_from)

        if year_to:
            query += " AND year <= ?"
            params.append(year_to)

        if marks:
            query += " AND marks = ?"
            params.append(marks)

        if q_type:
            query += " AND q_type = ?"
            params.append(q_type)

        cursor.execute(query, params)
        ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        return ids

    # ── GET MATRIX ROWS FOR IDS ──────────────────
    def get_matrix_rows(self, filtered_ids: list) -> tuple:
        """
        Given a list of question IDs,
        return their rows from TF-IDF matrix.

        filtered_ids = [1, 5, 23, 45]
        → find their positions in question_ids list
        → extract those rows from tfidf_matrix
        → return (matrix_subset, ids_subset)
        """
        # build index map: question_id → matrix row index
        id_to_row = {
            q_id: i
            for i, q_id in enumerate(self.question_ids)
        }

        rows    = []
        valid_ids = []

        for q_id in filtered_ids:
            if q_id in id_to_row:
                rows.append(id_to_row[q_id])
                valid_ids.append(q_id)

        if not rows:
            return None, []

        # extract those rows from full matrix
        matrix_subset = self.tfidf_matrix[rows]
        return matrix_subset, valid_ids

    # ── FETCH QUESTION DETAILS FROM DB ───────────
    def fetch_questions(self, ids: list) -> list:
        """
        Fetch full question details from DB
        for the given list of IDs.
        """
        if not ids:
            return []

        conn             = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor           = conn.cursor()

        placeholders = ",".join(["?" for _ in ids])
        cursor.execute(f"""
            SELECT id, question, subject, semester,
                   year, q_type, marks, keywords,
                   source_file
            FROM questions
            WHERE id IN ({placeholders})
        """, ids)

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # ── COSINE SEARCH ────────────────────────────
    def search(self,
               query:    str,
               subject:  str   = None,
               semester: int   = None,
               year:     int   = None,
               year_from:int   = None,
               year_to:  int   = None,
               marks:    float = None,
               q_type:   str   = None,
               top_n:    int   = 5) -> list:
        """
        Main search method.

        Steps:
        1. Preprocess query
        2. Get filtered IDs from DB (SQL)
        3. Get matrix rows for those IDs
        4. Transform query to TF-IDF vector
        5. Cosine similarity
        6. Rank and return top N
        """

        # Step 1 — preprocess
        clean_query = self.preprocess_query(query)
        if not clean_query.strip():
            print("  Query too short after preprocessing")
            return []

        # Step 2 — SQL filter
        if any([subject, semester, year,
                year_from, year_to, marks, q_type]):
            filtered_ids = self.get_filtered_ids(
                subject=subject, semester=semester,
                year=year, year_from=year_from,
                year_to=year_to, marks=marks,
                q_type=q_type
            )
            if not filtered_ids:
                print("  No questions match the filters")
                return []
            print(f"  Filtered: {len(filtered_ids)} questions")
        else:
            # no filters — search all questions
            filtered_ids = self.question_ids

        # Step 3 — get matrix rows
        matrix_subset, valid_ids = self.get_matrix_rows(
            filtered_ids)
        if matrix_subset is None:
            print("  No vectors found for filtered questions")
            return []

        # Step 4 — transform query
        query_vector = self.tfidf_vectorizer.transform(
            [clean_query])

        # Step 5 — cosine similarity
        scores = cosine_similarity(
            query_vector, matrix_subset).flatten()

        # Step 6 — rank top N
        top_indices = np.argsort(scores)[::-1][:top_n]
        top_ids     = [valid_ids[i] for i in top_indices]
        top_scores  = [scores[i] for i in top_indices]

        # filter out zero scores
        results = [
            (q_id, score)
            for q_id, score in zip(top_ids, top_scores)
            if score > 0.15
        ]

        if not results:
            print("  No similar questions found")
            return []

        # fetch full details from DB
        result_ids      = [r[0] for r in results]
        score_map       = {r[0]: r[1] for r in results}
        questions       = self.fetch_questions(result_ids)

        # add score to each question
        for q in questions:
            q["score"] = round(float(score_map[q["id"]]), 3)

        # sort by score
        questions.sort(key=lambda x: x["score"], reverse=True)

        return questions

    # ── SIMILAR QUESTION DETECTION ───────────────
    def find_similar(self, question_text: str,
                  subject: str = None,
                  top_n: int = 5) -> list:
        results = self.search(
            question_text,
            subject=subject,
            top_n=top_n
        )
        # warn if best score is too low
        if results and results[0]["score"] < 0.3:
            print("  ⚠️  Low confidence results — "
                "topic may not exist in question bank")
        return results

    # ── PRINT RESULTS ────────────────────────────
    def print_results(self, results: list):
        if not results:
            print("  No results found")
            return

        print(f"\n  Found {len(results)} results:\n")
        for i, q in enumerate(results, 1):
            print(f"  {i}. [{q['q_type']}] "
                  f"Q{q['id']} | Score: {q['score']}")
            print(f"     Subject  : {q['subject']}")
            print(f"     Semester : {q['semester']} "
                  f"| Year: {q['year']} "
                  f"| Marks: {q['marks']}")
            print(f"     Question : {q['question'][:80]}...")
            print(f"     Keywords : {q['keywords']}")
            print()
import sqlite3
import pickle
import numpy as np
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity


class Analyzer:

    def __init__(self, db_path: str, vectors_folder: str):
        self.db_path        = db_path
        self.vectors_folder = Path(vectors_folder)

        self.bow_matrix   = None
        self.bow_vectorizer = None
        self.question_ids = None

    def load(self):
        self.bow_matrix = pickle.load(
            open(self.vectors_folder / "bow_matrix.pkl", "rb"))

        self.bow_vectorizer = pickle.load(
            open(self.vectors_folder / "bow_vectorizer.pkl", "rb"))

        self.question_ids = pickle.load(
            open(self.vectors_folder / "question_ids.pkl", "rb"))

        print(f"  Loaded {len(self.question_ids)} question vectors")

    def get_questions_from_db(self,
                               subject:  str = None,
                               semester: int = None) -> list:
        import sqlite3
        conn             = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor           = conn.cursor()

        query  = """
            SELECT id, question, subject, semester,
                   year, q_type, marks, keywords, tokens
            FROM questions
            WHERE tokens IS NOT NULL
        """
        params = []

        if subject:
            query += " AND LOWER(subject) LIKE LOWER(?)"
            params.append(f"%{subject}%")

        if semester:
            query += " AND semester = ?"
            params.append(semester)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def most_repeated(self,
                       subject:  str = None,
                       semester: int = None,
                       top_n:    int = 10) -> list:

        # Step 1 — load questions
        questions = self.get_questions_from_db(
            subject=subject, semester=semester)

        if not questions:
            print("  No questions found")
            return []

        print(f"  Analyzing {len(questions)} questions...")

        # Step 2 — get BOW matrix rows
        id_to_row = {
            q_id: i
            for i, q_id in enumerate(self.question_ids)
        }

        rows     = []
        valid_qs = []

        for q in questions:
            if q["id"] in id_to_row:
                rows.append(id_to_row[q["id"]])
                valid_qs.append(q)

        if not rows:
            return []

        matrix = self.bow_matrix[rows]

        # Step 3 — cosine similarity between all questions
        sim_matrix = cosine_similarity(matrix)

        # Step 4 — group similar questions
        threshold = 0.3
        visited   = set()
        groups    = []

        for i in range(len(valid_qs)):
            if i in visited:
                continue

            group = [i]
            visited.add(i)

            for j in range(i + 1, len(valid_qs)):
                if j not in visited:
                    if sim_matrix[i][j] > threshold:
                        group.append(j)
                        visited.add(j)

            groups.append(group)

        # Step 5 — sort by size
        groups.sort(key=lambda g: len(g), reverse=True)

        # Step 6 — build results
        results = []
        for group in groups[:top_n]:
            rep_q = valid_qs[group[0]]
            results.append({
                "question":    rep_q["question"],
                "subject":     rep_q["subject"],
                "semester":    rep_q["semester"],
                "marks":       rep_q["marks"],
                "count":       len(group),
                "similar_ids": [valid_qs[i]["id"] for i in group]
            })

        return results

    def print_repeated(self, results: list):
        if not results:
            print("  No results found")
            return

        print(f"\n  Top {len(results)} repeated topics:\n")
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r['count']}x] {r['question'][:70]}...")
            print(f"     Subject  : {r['subject']}")
            print(f"     Semester : {r['semester']} "
                  f"| Marks: {r['marks']}")
            print(f"     Similar IDs: {r['similar_ids']}")
            print()
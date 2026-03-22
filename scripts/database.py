import sqlite3
from pathlib import Path


class DatabaseManager:

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = None

    # ── CONNECT ─────────────────────────────────
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        return self

    # ── DISCONNECT ───────────────────────────────
    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    # ── CREATE TABLES ────────────────────────────
    def create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS papers (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                university     TEXT,
                department     TEXT,
                subject        TEXT,
                subject_code   TEXT,
                semester       INTEGER,
                year           INTEGER,
                exam_date      TEXT,
                exam_type      TEXT,
                total_marks    INTEGER,
                duration_mins  INTEGER,
                source_file    TEXT UNIQUE,
                confidence     INTEGER,
                needs_review   INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS questions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id     INTEGER NOT NULL,
                department   TEXT,
                subject      TEXT,
                subject_code TEXT,
                semester     INTEGER,
                year         INTEGER,
                section      TEXT,
                q_type       TEXT,
                q_number     INTEGER,
                question     TEXT,
                marks        REAL,
                compulsory   INTEGER DEFAULT 1,
                source_file  TEXT,
                keywords     TEXT,
                FOREIGN KEY (paper_id) REFERENCES papers(id)
            );

            CREATE TABLE IF NOT EXISTS options (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                opt_index   INTEGER,
                opt_text    TEXT,
                FOREIGN KEY (question_id) REFERENCES questions(id)
            );
        """)
        self.conn.commit()
        print("  Tables created successfully")

        # add tokens column if not exists
        try:
            self.conn.execute(
                "ALTER TABLE questions ADD COLUMN tokens TEXT")
            self.conn.commit()
        except:
            pass

    # ── PAPER EXISTS ─────────────────────────────
    def paper_exists(self, source_file: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id FROM papers WHERE source_file = ?",
            (source_file,)
        )
        return cursor.fetchone() is not None

    # ── INSERT PAPER ─────────────────────────────
    def insert_paper(self, metadata: dict) -> int:
        cursor = self.conn.cursor()

        cursor.execute(
            "SELECT id FROM papers WHERE source_file = ?",
            (metadata["source_file"],)
        )
        existing = cursor.fetchone()
        if existing:
            return existing["id"]

        cursor.execute("""
            INSERT INTO papers (
                university, department, subject, subject_code,
                semester, year, exam_date, exam_type,
                total_marks, duration_mins, source_file,
                confidence, needs_review
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metadata["university"],
            metadata["department"],
            metadata["subject"],
            metadata["subject_code"],
            metadata["semester"],
            metadata["year"],
            metadata["exam_date"],
            metadata["exam_type"],
            metadata["total_marks"],
            metadata["duration_mins"],
            metadata["source_file"],
            metadata["confidence"],
            int(metadata["needs_review"]),
        ))
        self.conn.commit()
        return cursor.lastrowid

    # ── INSERT QUESTIONS ─────────────────────────
    def insert_questions(self, paper_id: int,
                          metadata: dict,
                          questions: list):
        cursor = self.conn.cursor()
        inserted = 0

        for q in questions:
            cursor.execute("""
                INSERT INTO questions (
                    paper_id, department, subject, subject_code,
                    semester, year, section, q_type, q_number,
                    question, marks, compulsory, source_file
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                paper_id,
                metadata["department"],
                metadata["subject"],
                metadata["subject_code"],
                metadata["semester"],
                metadata["year"],
                q["section"],
                q["q_type"],
                q["q_number"],
                q["question"],
                q["marks"],
                int(q["compulsory"]),
                metadata["source_file"],
            ))
            q_id = cursor.lastrowid

            for idx, opt_text in enumerate(q.get("options", [])):
                cursor.execute("""
                    INSERT INTO options (question_id, opt_index, opt_text)
                    VALUES (?, ?, ?)
                """, (q_id, idx, opt_text))

            inserted += 1

        self.conn.commit()
        return inserted

    # ── STORE RESULT ─────────────────────────────
    def store_result(self, result: dict):
        metadata  = result["metadata"]
        questions = result["questions"]
        paper_id  = self.insert_paper(metadata)
        inserted  = self.insert_questions(
            paper_id, metadata, questions)
        return paper_id, inserted

    # ── STATS ────────────────────────────────────
    def print_stats(self):
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM papers")
        papers = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM questions")
        questions = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM questions WHERE q_type='MCQ'")
        mcq = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM questions "
            "WHERE q_type='Descriptive'")
        desc = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM options")
        options = cursor.fetchone()[0]

        print(f"\n  Database Stats:")
        print(f"  Papers    : {papers}")
        print(f"  Questions : {questions} "
              f"(MCQ: {mcq}, Descriptive: {desc})")
        print(f"  Options   : {options}")
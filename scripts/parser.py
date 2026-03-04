import re
from pathlib import Path


# ── SUBJECT CANONICAL MAP ───────────────────────
SUBJECT_CANONICAL = {
    "Machine Learning": [
        "machine learning", "ml", "CE362", "CSE303", "IT362",
        "artificial intelligence and machine learning", "aiml",
        "ai and machine learning",
    ],
    "Advanced Web Technologies": [
        "advanced web technologies", "awt", "IT342",
        "web technologies", "CE384",
        "advanced web technology",
    ],
    "Software Engineering": [
        "software engineering", "se", "IT451",
        "CSE301", "modern software engineering", "CTUC508",
    ],
    "Data Science": [
        "data science", "IT441",
    ],
    "Database Technologies": [
        "database technologies", "dbms", "CAUC508",
        "advanced database administration", "CTUC507",
        "database management",
    ],
    "Programming Fundamentals": [
        "foundation of programming", "CAUC101",
        "introduction to programming", "CTUC101",
    ],
    "Big Data Analytics": [
        "big data analytics", "big data", "CE441",
    ],
    "Language Processors": [
        "language processors", "IT443",
    ],
    "Internet of Things": [
        "internet of things", "iot", "IT444",
    ],
    "Advanced Computing": [
        "advanced computing", "IT442",
    ],
    "Microprocessor": [
        "microprocessor architectures and assembly programming",
        "microprocessor", "assembly programming", "CE341",
    ],
    "Web Development .NET": [
        "web development using .net", "CTUC506",
        "web development",
    ],
}

SEMESTER_WORDS = {
    "first": 1, "second": 2, "third": 3, "fourth": 4,
    "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8,
    "1st": 1, "2nd": 2, "3rd": 3, "4th": 4,
    "5th": 5, "6th": 6, "7th": 7, "8th": 8,
}


class MetadataParser:

    def __init__(self):
        pass

    # ── MAIN METHOD ─────────────────────────────
    def parse(self, text: str, filename: str) -> dict:
        metadata = {
            "university":    "CHAROTAR UNIVERSITY OF SCIENCE AND TECHNOLOGY",
            "department":    None,
            "subject":       None,
            "subject_code":  None,
            "semester":      None,
            "year":          None,
            "exam_date":     None,
            "exam_type":     "Regular",
            "total_marks":   None,
            "duration_mins": None,
            "source_file":   filename,
            "confidence":    0,
            "needs_review":  False,
        }

        # Extract from filename first
        metadata = self._parse_filename(filename, metadata)

        # Then extract from text
        metadata = self._parse_subject(text, metadata)
        metadata = self._parse_semester(text, metadata)
        metadata = self._parse_year(text, metadata)
        metadata = self._parse_exam_type(text, metadata)
        metadata = self._parse_marks(text, metadata)
        metadata = self._parse_duration(text, metadata)
        metadata = self._parse_exam_date(text, metadata)

        # Set needs_review flag
        if metadata["confidence"] < 3:
            metadata["needs_review"] = True

        return metadata

    # ── PARSE FILENAME ───────────────────────────
    def _parse_filename(self, filename: str, metadata: dict) -> dict:
        name = Path(filename).stem
        # Remove (2), (3) etc
        name = re.sub(r'\s*\(\d+\)\s*$', '', name).strip()

        # Pattern: DBTECH-IT_IT342
        m = re.match(r'([A-Z]+)-([A-Z]+)_([A-Z0-9]+)', name)
        if m:
            exam_code = m.group(1)   # DBTECH / CBTECH
            metadata["department"]   = m.group(2)   # IT / CE / CS
            metadata["subject_code"] = m.group(3)   # IT342
            metadata["confidence"]  += 2

            if "DB" in exam_code:
                metadata["exam_type"] = "External"
            elif "CB" in exam_code:
                metadata["exam_type"] = "Internal"
            return metadata

        # Pattern: CAUC101, CTUC101
        m = re.match(r'([A-Z]{2,4}\d{3})', name)
        if m:
            metadata["subject_code"] = m.group(1)
            metadata["confidence"]  += 1

        return metadata

    # ── PARSE SUBJECT ────────────────────────────
    def _parse_subject(self, text: str, metadata: dict) -> dict:

        # Try subject code from text first [CE362]
        code_match = re.search(r'\[([A-Z]{2,4}\d{3})\]', text)
        if code_match:
            code = code_match.group(1)
            if not metadata["subject_code"]:
                metadata["subject_code"] = code

        # Try to find canonical subject from text
        text_lower = text.lower()
        for canonical, aliases in SUBJECT_CANONICAL.items():
            for alias in aliases:
                if alias.lower() in text_lower:
                    metadata["subject"]    = canonical
                    metadata["confidence"] += 1
                    return metadata

        # Fallback — try subject code lookup
        if metadata["subject_code"]:
            for canonical, aliases in SUBJECT_CANONICAL.items():
                if metadata["subject_code"] in aliases:
                    metadata["subject"]    = canonical
                    metadata["confidence"] += 1
                    return metadata

        return metadata

    # ── PARSE SEMESTER ───────────────────────────
    def _parse_semester(self, text: str, metadata: dict) -> dict:
        patterns = [
            r'(\w+)\s+Semester\s+(?:of\s+)?B[.\s]?Tech',
            r'Semester\s*[:\-]?\s*(\d+)',
            r'(\d+)(?:st|nd|rd|th)\s*Sem(?:ester)?',
            r'Sem(?:ester)?\s*[:\-]?\s*(\d+)',
            r'(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth)\s+Semester',
        ]

        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                val = m.group(1).strip().lower()
                if val.isdigit():
                    metadata["semester"]    = int(val)
                    metadata["confidence"] += 1
                    return metadata
                elif val in SEMESTER_WORDS:
                    metadata["semester"]    = SEMESTER_WORDS[val]
                    metadata["confidence"] += 1
                    return metadata

        return metadata

    # ── PARSE YEAR ───────────────────────────────
    def _parse_year(self, text: str, metadata: dict) -> dict:
        patterns = [
            r'(?:January|February|March|April|May|June|July|'
            r'August|September|October|November|December)\s+(20\d{2})',
            r'Year\s*[:\-]?\s*(20\d{2})',
            r'(20\d{2})',
        ]

        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                year = int(m.group(1))
                if 2015 <= year <= 2030:
                    metadata["year"]        = year
                    metadata["confidence"] += 1
                    return metadata

        return metadata

    # ── PARSE EXAM TYPE ──────────────────────────
    def _parse_exam_type(self, text: str, metadata: dict) -> dict:
        if re.search(r'supplementary', text, re.IGNORECASE):
            metadata["exam_type"] = "Supplementary"
        elif re.search(r'remedial', text, re.IGNORECASE):
            metadata["exam_type"] = "Remedial"
        elif re.search(r'internal', text, re.IGNORECASE):
            metadata["exam_type"] = "Internal"
        return metadata

    # ── PARSE MARKS ──────────────────────────────
    def _parse_marks(self, text: str, metadata: dict) -> dict:
        m = re.search(r'Marks\s*[:\-]?\s*(\d+)', text, re.IGNORECASE)
        if m:
            metadata["total_marks"] = int(m.group(1))
        return metadata

    # ── PARSE DURATION ───────────────────────────
    def _parse_duration(self, text: str, metadata: dict) -> dict:
        m = re.search(r'Duration\s*[:\-]?\s*(\d+)\s*mins?', text, re.IGNORECASE)
        if m:
            metadata["duration_mins"] = int(m.group(1))
        return metadata

    # ── PARSE EXAM DATE ──────────────────────────
    def _parse_exam_date(self, text: str, metadata: dict) -> dict:
        m = re.search(
            r'Exam Date[^:]*:\s*(\d{1,2}[-/]\w+[-/]\d{4})',
            text, re.IGNORECASE
        )
        if m:
            metadata["exam_date"] = m.group(1)
        return metadata

    # ── PRINT SUMMARY ────────────────────────────
    def print_summary(self, metadata: dict):
        print(f"    University  : {metadata['university']}")
        print(f"    Department  : {metadata['department']}")
        print(f"    Subject     : {metadata['subject']}")
        print(f"    Code        : {metadata['subject_code']}")
        print(f"    Semester    : {metadata['semester']}")
        print(f"    Year        : {metadata['year']}")
        print(f"    Exam Type   : {metadata['exam_type']}")
        print(f"    Marks       : {metadata['total_marks']}")
        print(f"    Duration    : {metadata['duration_mins']} mins")
        print(f"    Confidence  : {metadata['confidence']}/6")
        if metadata['needs_review']:
            print(f"    ⚠️  NEEDS REVIEW")
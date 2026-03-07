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
        "CSE301",
    ],
    "Data Science": [
        "data science", "IT441",
    ],
    "Data Analytics and Visualization": [
        "data analytics and visualization",
        "data analytics", "IT389",
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
        "advanced computing", "IT442", "IT405",
    ],
    "Microprocessor": [
        "microprocessor architectures and assembly programming",
        "microprocessor", "assembly programming", "CE341",
    ],
    "Web Development .NET": [
        "web development using .net", "CTUC506",
        "web development",
    ],
    "Modern Software Engineering": [
        "modern software engineering", "CTUC508",
    ],
}

SEMESTER_WORDS = {
    "first": 1, "second": 2, "third": 3, "fourth": 4,
    "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8,
    "1st": 1, "2nd": 2, "3rd": 3, "4th": 4,
    "5th": 5, "6th": 6, "7th": 7, "8th": 8,
}


# ════════════════════════════════════════════════
#  METADATA PARSER
# ════════════════════════════════════════════════
class MetadataParser:

    def __init__(self):
        pass

    # ── MAIN ────────────────────────────────────
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

        metadata = self._parse_filename(filename, metadata)
        metadata = self._parse_subject(text, metadata)
        metadata = self._parse_semester(text, metadata)
        metadata = self._parse_year(text, metadata)
        metadata = self._parse_exam_type(text, metadata)
        metadata = self._parse_marks(text, metadata)
        metadata = self._parse_duration(text, metadata)
        metadata = self._parse_exam_date(text, metadata)

        if metadata["confidence"] < 3:
            metadata["needs_review"] = True

        return metadata

    # ── FILENAME ─────────────────────────────────
    def _parse_filename(self, filename: str, metadata: dict) -> dict:
        name = Path(filename).stem
        name = re.sub(r'\s*\(\d+\)\s*$', '', name).strip()

        # Pattern: DBTECH-IT_IT342
        m = re.match(r'([A-Z]+)-([A-Z]+)_([A-Z0-9]+)', name)
        if m:
            exam_code = m.group(1)
            metadata["department"]   = m.group(2)
            metadata["subject_code"] = m.group(3)
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

    # ── SUBJECT ──────────────────────────────────
    def _parse_subject(self, text: str, metadata: dict) -> dict:

        # Step 1 — Extract code from text [CE362]
        code_match = re.search(
            r'\[([A-Z]{2,4}\d{3}(?:\.\d+)?)\]', text)
        if code_match:
            code = code_match.group(1)
            if not metadata["subject_code"]:
                metadata["subject_code"] = code

        # Step 2 — Match by subject code FIRST (most reliable)
        if metadata["subject_code"]:
            for canonical, aliases in SUBJECT_CANONICAL.items():
                if metadata["subject_code"] in aliases:
                    metadata["subject"]    = canonical
                    metadata["confidence"] += 1
                    return metadata

        # Step 3 — Fallback: match in first 10 lines only
        first_lines = '\n'.join(
            text.split('\n')[:10]).lower()
        for canonical, aliases in SUBJECT_CANONICAL.items():
            for alias in aliases:
                if alias.lower() in first_lines:
                    metadata["subject"]    = canonical
                    metadata["confidence"] += 1
                    return metadata

        return metadata

    # ── SEMESTER ─────────────────────────────────
    def _parse_semester(self, text: str, metadata: dict) -> dict:
        patterns = [
            r'(\w+)\s+Semester\s+(?:of\s+)?B[.\s]?Tech',
            r'B\.?Tech\s+\w+\s+(\d+)(?:st|nd|rd|th)\s+Semester',
            r'Semester\s*[:\-]?\s*(\d+)',
            r'(\d+)(?:st|nd|rd|th)\s*Sem(?:ester)?',
            r'Sem(?:ester)?\s*[:\-]?\s*(\d+)',
            r'(First|Second|Third|Fourth|Fifth|'
            r'Sixth|Seventh|Eighth)\s+Semester',
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

    # ── YEAR ─────────────────────────────────────
    def _parse_year(self, text: str, metadata: dict) -> dict:
        patterns = [
            r'(?:January|February|March|April|May|June|July|'
            r'August|September|October|November|December)'
            r'\s+(20\d{2})',
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

    # ── EXAM TYPE ────────────────────────────────
    def _parse_exam_type(self, text: str,
                          metadata: dict) -> dict:
        if re.search(r'supplementary', text, re.IGNORECASE):
            metadata["exam_type"] = "Supplementary"
        elif re.search(r'remedial', text, re.IGNORECASE):
            metadata["exam_type"] = "Remedial"
        elif re.search(r'backlog', text, re.IGNORECASE):
            metadata["exam_type"] = "Backlog"
        return metadata

    # ── MARKS ────────────────────────────────────
    def _parse_marks(self, text: str, metadata: dict) -> dict:
        m = re.search(
            r'Marks\s*[:\-]?\s*(\d+)', text, re.IGNORECASE)
        if m:
            metadata["total_marks"] = int(m.group(1))
        return metadata

    # ── DURATION ─────────────────────────────────
    def _parse_duration(self, text: str,
                         metadata: dict) -> dict:
        m = re.search(
            r'Duration\s*[:\-]?\s*(\d+)\s*mins?',
            text, re.IGNORECASE)
        if m:
            metadata["duration_mins"] = int(m.group(1))
        return metadata

    # ── EXAM DATE ────────────────────────────────
    def _parse_exam_date(self, text: str,
                          metadata: dict) -> dict:
        m = re.search(
            r'Exam Date[^:]*:\s*(\d{1,2}[-/]\w+[-/]\d{4})',
            text, re.IGNORECASE)
        if m:
            metadata["exam_date"] = m.group(1)
        return metadata

    # ── PRINT ────────────────────────────────────
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


# ════════════════════════════════════════════════
#  QUESTION PARSER
# ════════════════════════════════════════════════
class QuestionParser:

    SECTION_PATTERN = re.compile(
        r'((?:Section|SECTION)\s*[-–]?\s*'
        r'(?:[IVX]+|\d+)'
        r'(?:\s*[\(\-]\s*[AB]\s*\)?)?'
        r'(?:\s*[\(\-]?\s*(?:MCQ|Multiple Choice'
        r' Questions?)\s*\)?)?'
        r'|MCQs?'
        r'|I\s*[-–]\s*Multiple Choice Questions?)',
        re.IGNORECASE
    )

    def __init__(self):
        pass

    # ── MAIN ────────────────────────────────────
    def parse(self, text: str) -> list:
        questions = []
        sections  = self._split_sections(text)

        for section_name, section_text in sections.items():
            section_type = self._get_section_type(section_name)
            qs = self._extract_questions(
                section_text, section_name, section_type
            )
            questions.extend(qs)

        return questions

    # ── SPLIT SECTIONS ───────────────────────────
    def _split_sections(self, text: str) -> dict:
        sections = {}
        parts    = self.SECTION_PATTERN.split(text)

        if len(parts) <= 1:
            return {"Section I": text}

        i = 1
        while i < len(parts) - 1:
            header  = parts[i].strip()
            content = parts[i + 1] if i + 1 < len(parts) else ""
            sections[header] = content
            i += 2

        return sections

    # ── SECTION TYPE ─────────────────────────────
    def _get_section_type(self, section_name: str) -> str:
        name = section_name.upper().strip()

        mcq_keywords = ["MCQ", "MULTIPLE CHOICE", "MCQS"]
        for kw in mcq_keywords:
            if kw in name:
                return "MCQ"

        clean = re.sub(r'SECTION\s*[-–]?\s*', '', name).strip()
        if clean in ["I", "1", "- I", "-I", "- 1", "-1"]:
            return "MCQ"

        if re.match(r'^I\s*[-–]', name):
            return "MCQ"

        return "Descriptive"

    # ── EXTRACT QUESTIONS ────────────────────────
    def _extract_questions(self, text: str,
                            section_name: str,
                            section_type: str) -> list:
        questions = []

        # Join multi-line questions first
        text  = self._join_question_lines(text)
        lines = [l.strip() for l in text.split('\n')
                 if l.strip()]

        i = 0
        while i < len(lines):
            line = lines[i]

            # ── Normal format: "1 Question text (marks)" ──
            q_match = re.match(r'^(\d{1,2})\s+(.+)', line)

            if q_match:
                q_number = int(q_match.group(1))
                q_body   = q_match.group(2).strip()

                # Skip years or large numbers
                if q_number > 30:
                    i += 1
                    continue

                # Skip too short
                if len(q_body) < 5:
                    i += 1
                    continue

                # Extract marks
                marks = self._extract_marks(q_body)

                # Remove marks from text
                q_text = re.sub(
                    r'\(\d+(?:\.\d+)?\)\s*$', '', q_body
                ).strip()

                # Collect options for MCQ
                options = []
                i += 1
                if section_type == "MCQ":
                    while i < len(lines):
                        next_line = lines[i]
                        if re.match(r'^\d{1,2}\s+\S', next_line):
                            break
                        if self.SECTION_PATTERN.match(next_line):
                            break
                        if len(next_line) > 2:
                            options.extend(
                                self._split_options(next_line))
                        i += 1

                questions.append({
                    "section":    section_name,
                    "q_type":     section_type,
                    "q_number":   q_number,
                    "question":   q_text,
                    "marks":      marks,
                    "options":    options,
                    "compulsory": self._is_compulsory(
                        text, section_type)
                })
                continue

            # ── Reversed format: "Question text (marks)\n number" ──
            # CE341 style
            marks_end = re.search(
                r'\((\d+(?:\.\d+)?)\)\s*$', line)
            if marks_end and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if re.match(r'^\d{1,2}$', next_line):
                    q_number = int(next_line)
                    q_text   = re.sub(
                        r'\(\d+(?:\.\d+)?\)\s*$', '',
                        line).strip()
                    marks    = self._extract_marks(line)
                    i       += 2

                    options = []
                    while i < len(lines):
                        nl = lines[i].strip()
                        if re.match(r'^\d{1,2}$', nl):
                            break
                        if re.match(r'^\d{1,2}\s+\S', nl):
                            break
                        if nl:
                            options.extend(
                                self._split_options(nl))
                        i += 1

                    questions.append({
                        "section":    section_name,
                        "q_type":     section_type,
                        "q_number":   q_number,
                        "question":   q_text,
                        "marks":      marks,
                        "options":    options,
                        "compulsory": True
                    })
                    continue

            i += 1

        return questions

    # ── EXTRACT MARKS ────────────────────────────
    def _extract_marks(self, text: str):
        m = re.search(r'\((\d+(?:\.\d+)?)\)\s*$', text)
        if not m:
            return None
        val = float(m.group(1))
        return int(val) if val == int(val) else val

    # ── JOIN MULTI-LINE QUESTIONS ─────────────────
    def _join_question_lines(self, text: str) -> str:
        lines  = text.split('\n')
        result = []
        buffer = ""

        for line in lines:
            stripped = line.strip()

            if not stripped:
                if buffer:
                    result.append(buffer)
                    buffer = ""
                continue

            # New question starts with number + space + text
            if re.match(r'^\d{1,2}\s+\S', stripped):
                if buffer:
                    result.append(buffer)
                buffer = stripped

            # Continuation — only if question not complete yet
            elif buffer and not re.search(
                    r'\(\d+(?:\.\d+)?\)\s*$', buffer):
                # Avoid merging short option-like lines
                if (len(stripped) > 20 and
                        not re.match(r'^[A-Z]\.\s', stripped) and
                        not re.match(r'^[a-d]\)', stripped)):
                    buffer += " " + stripped
                else:
                    result.append(buffer)
                    buffer = ""
                    result.append(stripped)
            else:
                if buffer:
                    result.append(buffer)
                    buffer = ""
                result.append(stripped)

        if buffer:
            result.append(buffer)

        return '\n'.join(result)

    # ── SPLIT OPTIONS ────────────────────────────
    def _split_options(self, line: str) -> list:
        options = re.split(r'\s{2,}', line)
        options = [o.strip() for o in options if o.strip()]
        return options

    # ── IS COMPULSORY ────────────────────────────
    def _is_compulsory(self, section_text: str,
                        section_type: str) -> bool:
        if section_type == "MCQ":
            return True
        if re.search(r'answer all',
                     section_text[:300], re.IGNORECASE):
            return True
        if re.search(r'answer \d+ out of',
                     section_text[:300], re.IGNORECASE):
            return False
        return True

    # ── PRINT SUMMARY ────────────────────────────
    def print_summary(self, questions: list):
        total       = len(questions)
        mcq         = len([q for q in questions
                           if q["q_type"] == "MCQ"])
        descriptive = len([q for q in questions
                           if q["q_type"] == "Descriptive"])

        print(f"    Total questions : {total}")
        print(f"    MCQ             : {mcq}")
        print(f"    Descriptive     : {descriptive}")
        print()

        for q in questions:
            print(f"    [{q['q_type']}] "
                  f"Q{q['q_number']} "
                  f"({q['marks']} marks) "
                  f"| {q['section']}")
            print(f"    {q['question'][:80]}...")
            if q["options"]:
                print(f"    Options: {q['options'][:3]}")
            print()
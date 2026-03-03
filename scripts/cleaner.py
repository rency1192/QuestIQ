import re
from pathlib import Path


class TextCleaner:

    REMOVE_PATTERNS = [
        r'Page\s*#\d+',
        r'-----End-----',
        r'Answer all the questions\..*',
        r'Answer \d+ out of \d+ questions\..*',
        r'Section Duration:.*',
        r'\d+\.\s*Write the answer.*',
        r'\d+\.\s*Upload your answer.*',
        r'\d+\.\s*Make sure.*',
        r'\d+\.\s*if above.*',
        r'\d+\.\s*Attempt any.*',
    ]

    def __init__(self, input_folder: str, output_folder: str):
        self.input_folder  = Path(input_folder)
        self.output_folder = Path(output_folder)

    # ── Clean single text ────────────────────────
    def clean_text(self, text: str) -> str:

        # Remove unwanted patterns
        for pattern in self.REMOVE_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Remove multiple blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove trailing whitespace per line
        lines = [line.rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)

        return text.strip()

    # ── Process all txt files ────────────────────
    def run(self):
        files = list(self.input_folder.glob("*.txt"))

        if not files:
            print("No text files found to clean")
            return

        print(f"\n{'='*50}")
        print(f"STEP 2 — TEXT CLEANING")
        print(f"{'='*50}")
        print(f"Found {len(files)} text files\n")

        for file_path in files:
            print(f"  Cleaning: {file_path.name}")

            with open(file_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()

            cleaned = self.clean_text(raw_text)

            output_path = self.output_folder / file_path.name
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned)

            removed = len(raw_text) - len(cleaned)
            print(f"    Before : {len(raw_text)} chars")
            print(f"    After  : {len(cleaned)} chars")
            print(f"    Removed: {removed} chars\n")

        print(f"  Done. Cleaned files saved to: {self.output_folder}")
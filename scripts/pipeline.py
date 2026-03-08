import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from scripts.extractor import PDFExtractor
from scripts.cleaner   import TextCleaner
from scripts.parser    import MetadataParser, QuestionParser
from scripts.database  import DatabaseManager
from pathlib           import Path


class Pipeline:

    def __init__(self):
        base = r"G:\NLP_Project"

        self.paths = {
            "text_based":     f"{base}\\question_bank\\raw_papers\\text_based",
            "cleaned_text":   f"{base}\\processed\\cleaned_text",
            "extracted_data": f"{base}\\processed\\extracted_data",
            "database":       f"{base}\\database\\questions.db",
            "outputs":        f"{base}\\outputs",
            "log":            f"{base}\\logs\\extraction_log.txt",
        }

    def run(self):
        print("\n" + "="*50)
        print("  QUESTION BANK PIPELINE STARTING")
        print("="*50)

        # Step 1 — Extract text from PDFs
        extractor = PDFExtractor(
            input_folder  = self.paths["text_based"],
            output_folder = self.paths["cleaned_text"],
            log_file      = self.paths["log"]
        )
        extractor.run()

        # Step 2 — Clean extracted text
        cleaner = TextCleaner(
            input_folder  = self.paths["cleaned_text"],
            output_folder = self.paths["extracted_data"]
        )
        cleaner.run()

        # Step 3 — Parse metadata + questions
        print(f"\n{'='*50}")
        print(f"STEP 3 - PARSING METADATA & QUESTIONS")
        print(f"{'='*50}\n")

        metadata_parser = MetadataParser()
        question_parser = QuestionParser()
        files           = list(
            Path(self.paths["extracted_data"]).glob("*.txt")
        )

        all_results = []

        for file_path in files:
            print(f"  Parsing: {file_path.name}")
            print(f"  {'-'*40}")

            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            metadata  = metadata_parser.parse(text, file_path.name)
            metadata_parser.print_summary(metadata)

            questions = question_parser.parse(text)
            question_parser.print_summary(questions)

            all_results.append({
                "metadata":  metadata,
                "questions": questions
            })

        print("\n" + "="*50)
        print(f"  PARSING COMPLETE")
        print(f"  Total papers parsed: {len(all_results)}")
        print("="*50)

        # Step 4 — Store to database
        print(f"\n{'='*50}")
        print(f"STEP 4 - STORING TO DATABASE")
        print(f"{'='*50}\n")

        db = DatabaseManager(self.paths["database"])
        db.connect()
        db.create_tables()

        for result in all_results:
            paper_id, inserted = db.store_result(result)
            print(f"  Stored: {result['metadata']['source_file']}"
                  f" -> paper_id={paper_id}, questions={inserted}")

        db.print_stats()
        db.disconnect()

        return all_results
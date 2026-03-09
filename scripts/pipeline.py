import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from scripts.extractor    import PDFExtractor
from scripts.cleaner      import TextCleaner
from scripts.parser       import MetadataParser, QuestionParser
from scripts.database     import DatabaseManager
from scripts.preprocessor import TextPreprocessor
from pathlib              import Path


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

        # open DB first — single source of truth
        db = DatabaseManager(self.paths["database"])
        db.connect()
        db.create_tables()

        extractor       = PDFExtractor(
            input_folder  = self.paths["text_based"],
            output_folder = self.paths["cleaned_text"],
            log_file      = self.paths["log"]
        )
        cleaner         = TextCleaner(
            input_folder  = self.paths["cleaned_text"],
            output_folder = self.paths["extracted_data"]
        )
        metadata_parser = MetadataParser()
        question_parser = QuestionParser()

        pdfs    = list(Path(self.paths["text_based"]).glob("*.pdf"))
        new     = 0
        skipped = 0

        print(f"\n{'='*50}")
        print(f"STEPS 1-3 — EXTRACT / CLEAN / STORE")
        print(f"{'='*50}\n")

        for pdf_path in pdfs:
            txt_name = pdf_path.stem + ".txt"

            # single DB check gates all 3 steps
            if db.paper_exists(txt_name):
                print(f"  Skipping (already in DB): {pdf_path.name}")
                skipped += 1
                continue

            print(f"\n  Processing: {pdf_path.name}")
            print(f"  {'-'*40}")

            # Step 1 — Extract
            text = extractor.extract_text(pdf_path)
            if not text.strip():
                print(f"  FAILED extraction: {pdf_path.name}")
                continue
            extractor.save_text(pdf_path.name, text)
            print(f"  Extracted: {len(text)} chars")

            # Step 2 — Clean
            cleaned     = cleaner.clean_text(text)
            cleaned_out = (Path(self.paths["extracted_data"])
                           / txt_name)
            with open(cleaned_out, 'w', encoding='utf-8') as f:
                f.write(cleaned)
            print(f"  Cleaned: {len(text)} -> {len(cleaned)} chars")

            # Step 3 — Parse + Store
            metadata  = metadata_parser.parse(cleaned, txt_name)
            metadata_parser.print_summary(metadata)

            questions = question_parser.parse(cleaned)
            question_parser.print_summary(questions)

            paper_id, inserted = db.store_result({
                "metadata":  metadata,
                "questions": questions
            })
            print(f"  Stored: paper_id={paper_id},"
                  f" questions={inserted}")
            new += 1

        print(f"\n  Done: {new} new, {skipped} skipped")
        db.print_stats()
        db.disconnect()

        # Phase 2 Step 1 — Preprocessing
        print(f"\n{'='*50}")
        print(f"PHASE 2 STEP 1 - PREPROCESSING")
        print(f"{'='*50}\n")

        preprocessor = TextPreprocessor(self.paths["database"])
        processed    = preprocessor.process_all()

        if processed:
            preprocessor.save_tokens(processed)
            preprocessor.print_summary(processed)
        else:
            print("  All questions already preprocessed - skipping")
from scripts.extractor import PDFExtractor
from scripts.cleaner   import TextCleaner


class Pipeline:

    def __init__(self):
        # ── Paths ───────────────────────────────
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

        print("\n" + "="*50)
        print("  PIPELINE COMPLETE")
        print("="*50)
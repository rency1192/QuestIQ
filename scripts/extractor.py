import pdfplumber
from pathlib import Path


class PDFExtractor:

    def __init__(self, input_folder: str, output_folder: str, log_file: str):
        self.input_folder  = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.log_file      = Path(log_file)
        self.success       = 0
        self.failed        = 0

    # ── Extract text from single PDF ────────────
    def extract_text(self, pdf_path: Path) -> str:
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            self._log(f"ERROR reading {pdf_path.name}: {e}")
        return text

    # ── Save extracted text to .txt file ────────
    def save_text(self, filename: str, text: str):
        output_path = self.output_folder / filename.replace(".pdf", ".txt")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

    # ── Log messages ────────────────────────────
    def _log(self, message: str):
        print(message)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(message + "\n")

    # ── Process all PDFs in folder ──────────────
    def run(self):
        pdfs = list(self.input_folder.glob("*.pdf"))
        print(pdfs)

        if not pdfs:
            print("No PDFs found in text_based folder")
            return

        print(f"\n{'='*50}")
        print(f"STEP 1 — PDF EXTRACTION")
        print(f"{'='*50}")
        print(f"Found {len(pdfs)} PDFs\n")

        for pdf_path in pdfs:
            print(f"  Extracting: {pdf_path.name}")
            text = self.extract_text(pdf_path)

            if not text.strip():
                self._log(f"  FAILED - no text: {pdf_path.name}")
                self.failed += 1
                continue

            self.save_text(pdf_path.name, text)
            self._log(f"  SUCCESS - {pdf_path.name} - {len(text)} chars")
            self.success += 1

        print(f"\n  Done: {self.success} success, {self.failed} failed")
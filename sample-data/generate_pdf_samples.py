"""Generate small fictional PDFs used by Sprint 3 tests and demonstrations."""

from pathlib import Path

import pymupdf

ROOT = Path(__file__).parent

SAMPLES = {
    "fictional-fdf-complaint.pdf": """FICTIONAL TRAINING COMPLAINT — NOT A REAL CUSTOMER RECORD
Customer: Apollo Pharmacy (fictional example)
Product type: FDF
Product: Amoxicillin Capsules
Strength: 500 mg
Batch number: AMX-FDF-2407
Affected quantity: 18 cartons
Manufacturing date: 15 January 2026
Expiry date: 14 January 2028
Complaint: Several capsules showed brown discoloration when the cartons were opened.
""",
    "fictional-api-complaint.pdf": """FICTIONAL TRAINING COMPLAINT — NOT A REAL CUSTOMER RECORD
Customer: ABC Formulations Ltd. (fictional example)
Product type: API
Product: Metformin Hydrochloride API
Grade: IP/BP
Batch number: MET-API-77A
Affected quantity: 25 kg in one HDPE drum
Manufacturing date: 02 February 2026
Complaint: Dark foreign particles were observed in the received API material.
""",
}


def write_text_pdf(path: Path, text: str) -> None:
    with pymupdf.open() as document:
        page = document.new_page()
        page.insert_textbox(
            pymupdf.Rect(50, 50, 545, 790), text, fontsize=11, lineheight=1.4
        )
        document.save(path)


def main() -> None:
    for filename, text in SAMPLES.items():
        write_text_pdf(ROOT / filename, text)
    with pymupdf.open() as document:
        document.new_page()
        document.save(ROOT / "fictional-textless-complaint.pdf")


if __name__ == "__main__":
    main()

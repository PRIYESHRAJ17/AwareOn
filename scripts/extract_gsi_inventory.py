from pathlib import Path
import re
import pdfplumber
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

PDF_PATH = ROOT / "data/raw/landslides/gsi/Landslide Inventory (Field Validated).pdf"
OUT_DIR = ROOT / "data/processed/landslides"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RAW_TEXT_PATH = OUT_DIR / "gsi_inventory_raw.txt"
CSV_PATH = OUT_DIR / "gsi_inventory_extracted.csv"

rows = []

with pdfplumber.open(PDF_PATH) as pdf:
    print(f"Total pages: {len(pdf.pages)}")

    for page_no, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""

        with RAW_TEXT_PATH.open("a", encoding="utf-8") as f:
            f.write(f"\n\n===== PAGE {page_no} =====\n")
            f.write(text)

        lines = [line.strip() for line in text.splitlines() if line.strip()]

        # Keep lines containing coordinate-like values.
        for line in lines:
            coords = re.findall(r"-?\d+\.\d{3,}", line)

            if len(coords) >= 2:
                rows.append(
                    {
                        "page": page_no,
                        "raw_line": line,
                    }
                )

        if page_no % 50 == 0:
            print(f"Processed {page_no} pages...")

df = pd.DataFrame(rows)

df.to_csv(CSV_PATH, index=False, encoding="utf-8")

print("\nExtraction finished.")
print("Candidate rows:", len(df))
print("Raw text:", RAW_TEXT_PATH)
print("CSV:", CSV_PATH)

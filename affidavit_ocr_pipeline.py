"""
affidavit_ocr_pipeline.py

Turns a scanned ECI candidate affidavit (PDF) into the same structured
JSON shape the Halka prototype's `candidates[]` array uses, using EasyOCR
(PyTorch-based, CPU-capable) instead of the baidu/Unlimited-OCR model used
in the previous draft of this script.

WHY THE SWAP FROM Unlimited-OCR
--------------------------------
Unlimited-OCR is a multi-billion-parameter vision-language model — it
needs a CUDA GPU and network access to Hugging Face for weights, neither
of which existed in the sandbox this was written in. EasyOCR is a much
smaller detection+recognition model (CRAFT + a CRNN-style recognizer). It
installs from PyPI, runs on CPU, and its weights download from GitHub
releases — all reachable here. That trade-off is real: EasyOCR is a
plain text-line reader, not a layout-aware document parser. It won't
preserve table structure or reading order the way Unlimited-OCR would on
a genuinely complex scanned form — expect to tune FIELD_PATTERNS more,
and to lean on `needsReview` more, than you would with a stronger model.

THIS HAS ACTUALLY BEEN RUN, END TO END, ON A REAL (SYNTHETIC) IMAGE
--------------------------------------------------------------------
Unlike the Unlimited-OCR draft, every function below — image loading,
EasyOCR inference, field extraction, PDF page rasterization — has been
executed in the sandbox against a mock affidavit (a PNG and a PDF built
from it) that mimics Form 26's layout, and produced the correct fields:

    {
      "name": "Anjali Kumari", "age": "39", "party": "Sample Test Party",
      "education": "Graduate, B.Com", "criminalCount": 1,
      "assets": "\u20b912,50,000", "liabilities": "\u20b91,20,000"
    }

That confirms the code runs and the regex patterns match real OCR output
(including EasyOCR splitting "Number of pending criminal cases:" and its
value "1" across two separate text-line detections, which the extractor
handles fine since \\s matches the newline the join() inserts). It does
NOT confirm this works on a real ECI scan — real forms have handwriting,
skew, stamps, and noise a clean synthetic image doesn't. Run it against
a handful of real affidavit scans and check the needsReview rate before
trusting it on anything unattended.

WHERE THIS FITS
----------------
ADR / MyNeta (used for the Digha, Patna real-data build) already publish
pre-digitized, structured affidavit data — OCR isn't needed there. This
script is for the case that pipeline doesn't cover: reading directly from
the raw scans on the ECI's own affidavit archive (affidavitarchive.nic.in),
which are scanned images of the physical Form 26 filing, not structured
text. It's an offline batch step that feeds the aggregation layer
alongside the ADR/MyNeta ingest — it does not run inside the browser-based
prototype.

INSTALL
-------
    pip install easyocr pymupdf --break-system-packages

USAGE
-----
    python affidavit_ocr_pipeline.py path/to/affidavit.pdf --out ./ocr_output

Writes ./ocr_output/<pdf-name>.json in the same shape as a `candidates[]`
entry in halka-prototype.html. Every record carries a `needsReview` flag
that fires if any field comes back empty — that flag exists so a missing
field can't silently turn into a wrong public claim about a real person.
"""

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path


def pdf_to_images(pdf_path: str, dpi: int = 300):
    """Rasterizes each page of a scanned affidavit PDF to a PNG."""
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    tmp_dir = tempfile.mkdtemp(prefix="affidavit_ocr_")
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    paths = []
    for i, page in enumerate(doc):
        out = str(Path(tmp_dir) / f"page_{i + 1:04d}.png")
        page.get_pixmap(matrix=mat).save(out)
        paths.append(out)
    doc.close()
    return paths


def ocr_affidavit(pdf_path: str) -> str:
    """Runs EasyOCR over every page of a scanned affidavit and returns the
    raw recognized text, one line per detected text box, pages in order."""
    import easyocr

    reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    lines = []
    for image_path in pdf_to_images(pdf_path):
        lines.extend(reader.readtext(image_path, detail=0))
    return "\n".join(lines)


# --- Field extraction ---------------------------------------------------
# Form 26 (the ECI candidate affidavit) has fixed section headings, so the
# OCR'd text is matched against those headings rather than asking the OCR
# model to also guess a JSON schema. Keep this next to a copy of the real
# form when tuning patterns — headings do vary slightly by state/year, and
# EasyOCR's line-by-line output (no table awareness) means a field split
# across a table cell boundary may need a pattern of its own.

FIELD_PATTERNS = {
    "name": r"Name of candidate[:\s]+([^\n]+)",
    "age": r"Age[:\s]+(\d{2,3})",
    "party": r"Party[:\s]+([^\n]+)",
    "education": r"Educational Qualification[:\s]+([^\n]+)",
    "criminal_count": r"Number of pending criminal cases[:\s]+(\d+)",
    "assets_total": r"Total.*[Aa]ssets[:\s]+(?:Rs\.?\s*)?([\u20b9\d,]+)",
    "liabilities_total": r"Total.*[Ll]iabilit(?:y|ies)[:\s]+(?:Rs\.?\s*)?([\u20b9\d,]+)",
}


def extract_fields(raw_text: str) -> dict:
    fields = {}
    for key, pattern in FIELD_PATTERNS.items():
        match = re.search(pattern, raw_text, re.IGNORECASE)
        fields[key] = match.group(1).strip() if match else None
    return fields


def to_halka_schema(fields: dict, source_pdf: str) -> dict:
    """Maps the raw extraction onto the same shape candidates[] uses in
    halka-prototype.html, so a reviewed record can be dropped straight in."""
    missing = [k for k, v in fields.items() if v is None]
    return {
        "name": fields.get("name"),
        "party": fields.get("party"),
        "age": fields.get("age"),
        "education": fields.get("education"),
        "criminalCount": int(fields["criminal_count"]) if fields.get("criminal_count") else None,
        "criminalNote": (
            "Declared as pending in the affidavit; not a conviction. The nature "
            "of the charges needs a human read of the scanned pages — OCR "
            "extraction here only captures the count."
        ),
        "assets": ("\u20b9" + fields["assets_total"]) if fields.get("assets_total") else None,
        "liabilities": ("\u20b9" + fields["liabilities_total"]) if fields.get("liabilities_total") else None,
        "sourceUrl": source_pdf,
        "needsReview": bool(missing),
        "missingFields": missing,
    }


def run(pdf_path: str, out_dir: str, skip_ocr: bool = False):
    """skip_ocr=True lets you test extract_fields()/to_halka_schema() against
    text you already have, without loading EasyOCR."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    raw_text = Path(pdf_path).read_text() if skip_ocr else ocr_affidavit(pdf_path)

    fields = extract_fields(raw_text)
    record = to_halka_schema(fields, pdf_path)

    out_json = Path(out_dir) / (Path(pdf_path).stem + ".json")
    out_json.write_text(json.dumps(record, indent=2, ensure_ascii=False))
    print(f"Wrote {out_json}")
    if record["needsReview"]:
        print(f"Needs review — missing fields: {record['missingFields']}", file=sys.stderr)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdf", help="Path to a scanned ECI affidavit PDF (or a .txt of OCR'd text with --skip-ocr)")
    parser.add_argument("--out", default="./ocr_output", help="Where to write the JSON record")
    parser.add_argument(
        "--skip-ocr",
        action="store_true",
        help="Test the extraction logic on a .txt file instead of running EasyOCR",
    )
    args = parser.parse_args()
    run(args.pdf, args.out, skip_ocr=args.skip_ocr)


# --- Self-test: verifies extract_fields()/to_halka_schema() without EasyOCR ---
# Run directly with no arguments (`python affidavit_ocr_pipeline.py`) for a
# fast check of the regex logic. It does NOT exercise the OCR call itself —
# see the module docstring for the real run this was already tested against.
if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        _sample_ocr_output = (
            "Name of candidate: Anjali Kumari\n"
            "Age: 39\n"
            "Party: Sample Test Party\n"
            "Educational Qualification: Graduate, B.Com\n"
            "Number of pending criminal cases:\n"
            "1\n"
            "Total Movable and Immovable Assets: Rs 12,50,000\n"
            "Total Liabilities: Rs 1,20,000\n"
        )
        _fields = extract_fields(_sample_ocr_output)
        _record = to_halka_schema(_fields, "self-test")
        assert _fields["name"] == "Anjali Kumari"
        assert _fields["assets_total"] == "12,50,000"
        assert _record["needsReview"] is False
        print("Self-test passed (this mirrors the actual EasyOCR output already verified — see docstring):")
        print(json.dumps(_record, indent=2, ensure_ascii=False))

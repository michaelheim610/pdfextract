#!/usr/bin/env python3
"""
Label Splitter - A4 Etiketten-PDFs aufteilen
---------------------------------------------
Nimmt PDFs und extrahiert nur Seiten die ein Versandetikett enthalten.
Erkennt automatisch Label-Seiten anhand von Schluesselwoertern
(DHL, Sendungsnr, Leitcode, Barcode, etc.).
Seiten ohne Etikett (z.B. Lieferscheine) werden uebersprungen.

Nutzung:
    # PDFs in den 'import' Ordner legen, dann:
    python split_labels.py
"""

import shutil
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter

# Projektverzeichnis (dort wo das Skript liegt)
SCRIPT_DIR = Path(__file__).resolve().parent
IMPORT_DIR = SCRIPT_DIR / "import"
OUTPUT_DIR = SCRIPT_DIR / "output"
DONE_DIR = SCRIPT_DIR / "verarbeitet"

# Schluesselwoerter die ein Versandetikett identifizieren
LABEL_KEYWORDS = [
    "sendungsnr",
    "leitcode",
    "routingcode",
    "tracking",
    "paket",
    "kleinpaket",
    "dhl",
    "dpd",
    "hermes",
    "gls",
    "ups",
    "dpdhl",
    "deutsche post",
    "common label",
]


def is_label_page(page) -> bool:
    """Prueft ob eine Seite ein Versandetikett enthaelt."""
    try:
        text = page.extract_text().lower()
    except Exception:
        return False

    # Leerzeichen zwischen Buchstaben entfernen (manche PDFs haben
    # "D H L  K L E I N P A K E T" statt "DHL KLEINPAKET")
    text_compact = text.replace(" ", "")

    # In beiden Varianten suchen
    matches = sum(
        1 for kw in LABEL_KEYWORDS
        if kw in text or kw.replace(" ", "") in text_compact
    )
    # Mindestens 2 Schluesselwoerter muessen gefunden werden
    return matches >= 2


def crop_to_label(page):
    """Schneidet eine A4-Seite auf den Label-Bereich zu (1:1, keine Skalierung)."""
    media_box = page.mediabox
    page_width = float(media_box.width)
    page_height = float(media_box.height)

    # Label-Bereich: linke ~58% Breite, obere ~50% Hoehe
    content_width = page_width * 0.58
    content_height = page_height * 0.50

    page.mediabox.lower_left = (
        float(media_box.left),
        page_height - content_height,
    )
    page.mediabox.upper_right = (
        float(media_box.left) + content_width,
        float(media_box.top),
    )
    return page


def split_pdf(input_path: Path, output_dir: Path) -> int:
    """Extrahiert nur Label-Seiten aus einem PDF."""
    reader = PdfReader(input_path)
    count = 0
    skipped = 0

    for i, page in enumerate(reader.pages, start=1):
        if not is_label_page(page):
            print(f"  Seite {i}: Kein Etikett erkannt - uebersprungen")
            skipped += 1
            continue

        page = crop_to_label(page)

        writer = PdfWriter()
        writer.add_page(page)

        if len(reader.pages) == 1:
            output_path = output_dir / input_path.name
        else:
            output_path = output_dir / f"{input_path.stem}_label{count + 1}.pdf"

        with open(output_path, "wb") as f:
            writer.write(f)

        print(f"  Seite {i}: Label {count + 1} extrahiert")
        count += 1

    if skipped > 0:
        print(f"  ({skipped} Seite(n) ohne Etikett uebersprungen)")

    return count


def main():
    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DONE_DIR.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(IMPORT_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"Keine PDF-Dateien im Import-Ordner gefunden:")
        print(f"  {IMPORT_DIR}")
        print(f"\nBitte PDFs dort ablegen und erneut starten.")
        sys.exit(1)

    print(f"=== Label Splitter ===")
    print(f"Erkennt und extrahiert nur Etikett-Seiten.\n")
    print(f"Verarbeite   {len(pdf_files)} PDF(s)...")
    print(f"Import:      {IMPORT_DIR}")
    print(f"Output:      {OUTPUT_DIR}")
    print(f"Verarbeitet: {DONE_DIR}\n")

    count = 0
    for pdf_file in pdf_files:
        print(f"\n{pdf_file.name}:")
        result = split_pdf(pdf_file, OUTPUT_DIR)
        if result > 0:
            shutil.move(str(pdf_file), DONE_DIR / pdf_file.name)
            count += result

    print(f"\n{count} Label(s) extrahiert.")
    if count > 0:
        print(f"Originale verschoben nach: {DONE_DIR}")


if __name__ == "__main__":
    main()

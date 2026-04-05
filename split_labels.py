#!/usr/bin/env python3
"""
Label Splitter - A4 Etiketten-PDFs aufteilen
---------------------------------------------
Nimmt PDFs die nur Etiketten enthalten (jede Seite = ein Etikett auf A4)
und schneidet jede Seite auf den Label-Bereich zu.
Jedes Etikett wird als einzelnes PDF gespeichert.

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
    """Teilt ein PDF auf: jede Seite wird zugeschnitten und einzeln gespeichert."""
    reader = PdfReader(input_path)
    count = 0

    for i, page in enumerate(reader.pages, start=1):
        page = crop_to_label(page)

        writer = PdfWriter()
        writer.add_page(page)

        if len(reader.pages) == 1:
            # Nur eine Seite: gleicher Dateiname
            output_path = output_dir / input_path.name
        else:
            # Mehrere Seiten: mit Seitennummer
            output_path = output_dir / f"{input_path.stem}_label{i}.pdf"

        with open(output_path, "wb") as f:
            writer.write(f)

        print(f"  OK: {input_path.name} -> Label {i}")
        count += 1

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
    print(f"Schneide jede Seite auf Etikett-Groesse zu.\n")
    print(f"Verarbeite   {len(pdf_files)} PDF(s)...")
    print(f"Import:      {IMPORT_DIR}")
    print(f"Output:      {OUTPUT_DIR}")
    print(f"Verarbeitet: {DONE_DIR}\n")

    count = 0
    for pdf_file in pdf_files:
        result = split_pdf(pdf_file, OUTPUT_DIR)
        if result > 0:
            shutil.move(str(pdf_file), DONE_DIR / pdf_file.name)
            count += result

    print(f"\n{count} Label(s) erstellt.")
    if count > 0:
        print(f"Originale verschoben nach: {DONE_DIR}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Whatnot Label Extractor
-----------------------
Extrahiert das Versandetikett (letzte Seite) aus Whatnot-PDF-Dokumenten
und speichert es als eigenes PDF.

Nutzung:
    # PDFs in den 'import' Ordner legen, dann einfach starten:
    python extract_label.py

    # Die Labels landen im 'output' Ordner mit dem gleichen Dateinamen.
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

# DIN A6 Hochkant in PDF-Punkten (1 Punkt = 1/72 Zoll)
# 105mm x 148mm
A6_WIDTH = 297.64
A6_HEIGHT = 419.53


def extract_label(input_path: Path, output_dir: Path) -> Path | None:
    """Extrahiert die letzte Seite eines PDFs und speichert sie als Label."""
    reader = PdfReader(input_path)

    if len(reader.pages) < 2:
        print(f"  Uebersprungen: {input_path.name} (nur {len(reader.pages)} Seite)")
        return None

    last_page = reader.pages[-1]

    media_box = last_page.mediabox
    page_width = float(media_box.width)
    page_height = float(media_box.height)

    # Label-Inhalt: linke ~58% Breite, obere ~50% Hoehe
    content_width = page_width * 0.58
    content_height = page_height * 0.50

    # Crop auf den Label-Bereich (PDF-Koordinaten: 0,0 = unten links)
    last_page.mediabox.lower_left = (
        float(media_box.left),
        page_height - content_height,
    )
    last_page.mediabox.upper_right = (
        float(media_box.left) + content_width,
        float(media_box.top),
    )

    # Auf A6 skalieren (fuellend)
    last_page.scale_to(A6_WIDTH, A6_HEIGHT)

    writer = PdfWriter()
    writer.add_page(last_page)

    output_dir.mkdir(parents=True, exist_ok=True)
    # Gleicher Dateiname wie das Original
    output_path = output_dir / input_path.name

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"  OK: {input_path.name}")
    return output_path


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

    print(f"Verarbeite {len(pdf_files)} PDF(s)...")
    print(f"Import:      {IMPORT_DIR}")
    print(f"Output:      {OUTPUT_DIR}")
    print(f"Verarbeitet: {DONE_DIR}\n")

    count = 0
    for pdf_file in pdf_files:
        result = extract_label(pdf_file, OUTPUT_DIR)
        if result:
            # Original-PDF in den verarbeitet-Ordner verschieben
            shutil.move(str(pdf_file), DONE_DIR / pdf_file.name)
            count += 1

    print(f"\n{count} Label(s) extrahiert.")
    if count > 0:
        print(f"Originale verschoben nach: {DONE_DIR}")


if __name__ == "__main__":
    main()

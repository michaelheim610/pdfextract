#!/usr/bin/env python3
"""
Whatnot Label Extractor
-----------------------
Extrahiert das Versandetikett (letzte Seite) aus Whatnot-PDF-Dokumenten
und speichert es als eigenes PDF in einen Unterordner.

Nutzung:
    # Einzelne Datei:
    python extract_label.py /pfad/zur/datei.pdf

    # Alle PDFs in einem Ordner:
    python extract_label.py /pfad/zum/ordner/

    # Mit benutzerdefiniertem Ausgabeordner:
    python extract_label.py /pfad/zur/datei.pdf -o /pfad/zum/ausgabeordner/
"""

import argparse
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter


# DIN A6 Hochkant in PDF-Punkten (1 Punkt = 1/72 Zoll)
# 105mm x 148mm = 297.64 x 419.53 Punkte
A6_WIDTH_PT = 297.64
A6_HEIGHT_PT = 419.53


def extract_label(input_path: Path, output_dir: Path, crop: bool = True) -> Path | None:
    """Extrahiert die letzte Seite eines PDFs und speichert sie als Label."""
    reader = PdfReader(input_path)

    if len(reader.pages) < 2:
        print(f"  Uebersprungen: {input_path.name} (nur {len(reader.pages)} Seite)")
        return None

    last_page = reader.pages[-1]

    if crop:
        # Seite auf den bedruckten Bereich (obere Haelfte) zuschneiden
        media_box = last_page.mediabox
        page_width = float(media_box.width)
        page_height = float(media_box.height)

        # Label-Bereich: oberer Teil der Seite, volle Breite
        # Das DHL-Label nimmt ca. die obere 50% der A4-Seite ein
        label_height = page_height * 0.50

        # Crop: untere Grenze anheben (PDF-Koordinaten: 0,0 = unten links)
        last_page.mediabox.lower_left = (
            float(media_box.left),
            page_height - label_height,
        )
        last_page.mediabox.upper_right = (
            float(media_box.right),
            float(media_box.top),
        )

    writer = PdfWriter()
    writer.add_page(last_page)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"label_{input_path.stem}.pdf"

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"  OK: {input_path.name} -> {output_path.name}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Extrahiert Versandetiketten aus Whatnot-PDFs"
    )
    parser.add_argument(
        "input",
        help="PDF-Datei oder Ordner mit PDFs",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Ausgabeordner (Standard: 'labels' im Eingabeordner)",
    )
    parser.add_argument(
        "--no-crop",
        action="store_true",
        help="Letzte Seite nicht zuschneiden (ganze A4-Seite behalten)",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()

    if input_path.is_file():
        pdf_files = [input_path]
        default_output = input_path.parent / "labels"
    elif input_path.is_dir():
        pdf_files = sorted(input_path.glob("*.pdf"))
        if not pdf_files:
            print(f"Keine PDF-Dateien in {input_path} gefunden.")
            sys.exit(1)
        default_output = input_path / "labels"
    else:
        print(f"Pfad nicht gefunden: {input_path}")
        sys.exit(1)

    output_dir = Path(args.output).resolve() if args.output else default_output

    print(f"Verarbeite {len(pdf_files)} PDF(s)...")
    print(f"Ausgabe: {output_dir}\n")

    count = 0
    for pdf_file in pdf_files:
        # Labels-Ordner selbst nicht verarbeiten
        if output_dir in pdf_file.parents:
            continue
        result = extract_label(pdf_file, output_dir, crop=not args.no_crop)
        if result:
            count += 1

    print(f"\n{count} Label(s) extrahiert.")


if __name__ == "__main__":
    main()

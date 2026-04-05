#!/usr/bin/env python3
"""
Label Splitter - A4 Etiketten-PDFs aufteilen
---------------------------------------------
Nimmt PDFs und extrahiert nur Seiten die ein Versandetikett enthalten.

Erkennt zwei Typen:
  1) Text-Labels (DHL etc.) - erkannt anhand Schluesselwoertern
  2) Bild-Labels (Deutsche Post/GoGreen) - erkannt als eingebettete Bilder

Seiten ohne Etikett werden uebersprungen.

Nutzung:
    # PDFs in den 'import' Ordner legen, dann:
    python split_labels.py
"""

import shutil
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter, Transformation

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


def has_label_text(page) -> bool:
    """Prueft ob eine Seite Label-Text enthaelt."""
    try:
        text = page.extract_text().lower()
    except Exception:
        return False

    if not text.strip():
        return False

    # Leerzeichen zwischen Buchstaben entfernen (manche PDFs haben
    # "D H L  K L E I N P A K E T" statt "DHL KLEINPAKET")
    text_compact = text.replace(" ", "")

    matches = sum(
        1 for kw in LABEL_KEYWORDS
        if kw in text or kw.replace(" ", "") in text_compact
    )
    return matches >= 2


def has_label_image(page) -> bool:
    """Prueft ob eine Seite ein eingebettetes Bild-Label enthaelt
    (z.B. Deutsche Post/GoGreen - kein extrahierbarer Text)."""
    try:
        resources = page.get("/Resources", {})
        xobjects = resources.get("/XObject", {})

        for _, obj in xobjects.items():
            resolved = obj.get_object()
            # Form XObject mit eingebettetem Bild (typisch fuer Bild-Labels)
            if resolved.get("/Subtype") == "/Form":
                form_res = resolved.get("/Resources", {})
                form_xobj = form_res.get("/XObject", {})
                for _, fobj in form_xobj.items():
                    fresolved = fobj.get_object()
                    if fresolved.get("/Subtype") == "/Image":
                        return True
            # Direkt eingebettetes Bild
            if resolved.get("/Subtype") == "/Image":
                return True
    except Exception:
        return False

    return False


def detect_label_type(page) -> str | None:
    """Erkennt ob und welcher Typ Label auf der Seite ist.
    Returns: 'text', 'image', oder None"""
    if has_label_text(page):
        return "text"
    if has_label_image(page):
        return "image"
    return None


def crop_text_label(page):
    """Schneidet ein Text-Label (DHL etc.) auf den Label-Bereich zu."""
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


def crop_and_rotate_image_label(page):
    """Schneidet ein Bild-Label zu und dreht es ins Hochformat."""
    media_box = page.mediabox
    page_width = float(media_box.width)
    page_height = float(media_box.height)

    # Bild-Label: obere ~62% Hoehe (Bild ist 508px von ~791px Seitenhoehe)
    content_height = page_height * 0.62

    page.mediabox.lower_left = (
        float(media_box.left),
        page_height - content_height,
    )

    # Um 90 Grad drehen -> Hochformat
    page.rotate(90)

    return page


def split_pdf(input_path: Path, output_dir: Path) -> int:
    """Extrahiert nur Label-Seiten aus einem PDF."""
    reader = PdfReader(input_path)
    count = 0
    skipped = 0

    for i, page in enumerate(reader.pages, start=1):
        label_type = detect_label_type(page)

        if label_type is None:
            print(f"  Seite {i}: Kein Etikett erkannt - uebersprungen")
            skipped += 1
            continue

        if label_type == "text":
            page = crop_text_label(page)
            type_info = "DHL/Text"
        else:
            page = crop_and_rotate_image_label(page)
            type_info = "Bild (Deutsche Post/GoGreen)"

        writer = PdfWriter()
        writer.add_page(page)

        if len(reader.pages) == 1:
            output_path = output_dir / input_path.name
        else:
            output_path = output_dir / f"{input_path.stem}_label{count + 1}.pdf"

        with open(output_path, "wb") as f:
            writer.write(f)

        print(f"  Seite {i}: Label {count + 1} extrahiert [{type_info}]")
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
    print(f"Erkennt und extrahiert Etikett-Seiten (Text + Bild).\n")
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

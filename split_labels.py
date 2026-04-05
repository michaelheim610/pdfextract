#!/usr/bin/env python3
"""
Label Splitter - A4 Etiketten-PDFs aufteilen
---------------------------------------------
Nimmt PDFs und extrahiert nur Seiten die ein Versandetikett enthalten.

Erkennt zwei Typen:
  1) Text-Labels (DHL etc.) - erkannt anhand Schluesselwoertern
  2) Bild-Labels (Deutsche Post/GoGreen) - erkannt als eingebettete Bilder
     -> werden auf 36x89mm Hochformat zugeschnitten

Seiten ohne Etikett werden uebersprungen.

Nutzung:
    # PDFs in den 'import' Ordner legen, dann:
    python split_labels.py
"""

import shutil
import sys
import tempfile
from pathlib import Path

import pikepdf
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

# Bild-Label Konstanten
SCALE_FACTOR = 0.4800504  # Standard-Skalierung in Whatnot-PDFs
IMG_FORM_X = 136           # Bild-Position im Form XObject
IMG_FORM_Y = 1172
IMG_FORM_W = 793           # 753 + 40 Rand oben (wird nach Rotation zum oberen Rand)
IMG_FORM_H = 381

# 36x89mm in PDF-Punkten
TARGET_W_PT = 102.05
TARGET_H_PT = 252.28


def has_label_text(page) -> bool:
    """Prueft ob eine Seite Label-Text enthaelt."""
    try:
        text = page.extract_text().lower()
    except Exception:
        return False

    if not text.strip():
        return False

    text_compact = text.replace(" ", "")

    matches = sum(
        1 for kw in LABEL_KEYWORDS
        if kw in text or kw.replace(" ", "") in text_compact
    )
    return matches >= 2


def has_label_image(page) -> bool:
    """Prueft ob eine Seite ein eingebettetes Bild-Label enthaelt."""
    try:
        resources = page.get("/Resources", {})
        xobjects = resources.get("/XObject", {})

        for _, obj in xobjects.items():
            resolved = obj.get_object()
            if resolved.get("/Subtype") == "/Form":
                form_res = resolved.get("/Resources", {})
                form_xobj = form_res.get("/XObject", {})
                for _, fobj in form_xobj.items():
                    fresolved = fobj.get_object()
                    if fresolved.get("/Subtype") == "/Image":
                        return True
            if resolved.get("/Subtype") == "/Image":
                return True
    except Exception:
        return False

    return False


def detect_label_type(page) -> str | None:
    """Erkennt ob und welcher Typ Label auf der Seite ist."""
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


def save_image_label(input_path: Path, page_index: int, output_path: Path):
    """Extrahiert ein Bild-Label mit pikepdf: Crop + Skalierung + 270° Rotation auf 36x89mm."""
    pdf = pikepdf.open(input_path)
    page = pdf.pages[page_index]

    # Bild-Koordinaten auf der Seite
    img_left = IMG_FORM_X * SCALE_FACTOR
    img_bottom = IMG_FORM_Y * SCALE_FACTOR
    img_width = IMG_FORM_W * SCALE_FACTOR
    img_height = IMG_FORM_H * SCALE_FACTOR

    # Skalierungsfaktoren: Querformat -> 36x89mm Hochformat
    # Nach 270° Rotation: visuelle Breite = mediabox_height, visuelle Hoehe = mediabox_width
    sx = TARGET_H_PT / img_width    # Breite -> Hoehe
    sy = TARGET_W_PT / img_height   # Hoehe -> Breite

    # Skalierte Mediabox
    new_left = img_left * sx
    new_bottom = img_bottom * sy
    new_right = (img_left + img_width) * sx
    new_top = (img_bottom + img_height) * sy

    page.mediabox = [new_left, new_bottom, new_right, new_top]
    page.cropbox = page.mediabox

    # Content Stream mit Skalierung vorschalten
    raw = page.obj["/Contents"].read_bytes()
    scaled = f"q {sx:.6f} 0 0 {sy:.6f} 0 0 cm\n".encode() + raw + b"\nQ"
    page.obj["/Contents"] = pdf.make_stream(scaled)

    # 270° Rotation -> Hochformat
    page.Rotate = 270

    out = pikepdf.new()
    out.pages.append(page)
    out.save(output_path)
    pdf.close()


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

        if len(reader.pages) == 1:
            output_path = output_dir / input_path.name
        else:
            output_path = output_dir / f"{input_path.stem}_label{count + 1}.pdf"

        if label_type == "text":
            page = crop_text_label(page)
            writer = PdfWriter()
            writer.add_page(page)
            with open(output_path, "wb") as f:
                writer.write(f)
            type_info = "DHL/Text"
        else:
            save_image_label(input_path, i - 1, output_path)
            type_info = "Bild 36x89mm (Deutsche Post/GoGreen)"

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

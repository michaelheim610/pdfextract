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

import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional

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
IMG_FORM_W = 753
IMG_FORM_H = 381

# Raender in pt (nach Rotation: oben/links vom sichtbaren Label)
MARGIN_TOP = 60   # Rand oben (~21mm)
MARGIN_LEFT = 20  # Rand links (~7mm)

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


def extract_alias(page) -> Optional[str]:
    """Extrahiert den Whatnot-Alias des Kaeufers aus einem DHL-Label.

    Struktur: ... An: / Name / Alias / Strasse ...
    Der Alias steht in der Zeile nach dem Empfaengernamen.
    """
    try:
        text = page.extract_text()
    except Exception:
        return None
    if not text:
        return None

    lines = [l.replace(" ", "") for l in text.split("\n") if l.strip()]

    # "An:" oder "To:" finden, dann: Name, Alias, Strasse
    for idx, line in enumerate(lines):
        if line.lower() in ("an:", "to:") and idx + 2 < len(lines):
            alias = lines[idx + 2]  # Zeile nach dem Namen
            # Pruefen ob es eine Strasse ist (Strassenname + Hausnummer)
            street_patterns = (
                r"(?:stra[sß]e|str\.|weg|gasse|platz|allee|ring|damm|"
                r"ufer|hof|steig|berg|feld|grund|park|markt)\s*\d"
            )
            if re.search(street_patterns, alias, re.IGNORECASE):
                return None
            # Sicherheitscheck: kein Land, keine reine Nummer
            if alias.upper() == "GERMANY" or alias.isdigit():
                return None
            return alias
    return None


def sanitize_filename(name: str) -> str:
    """Bereinigt einen String fuer die Nutzung als Dateiname."""
    # Nur Buchstaben, Zahlen, Bindestrich, Unterstrich behalten
    clean = re.sub(r"[^\w\-]", "_", name)
    clean = re.sub(r"_+", "_", clean).strip("_")
    return clean[:60] if clean else "label"


def detect_label_type(page) -> Optional[str]:
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
    """Extrahiert ein Bild-Label mit pikepdf auf 36x89mm Hochformat mit Raendern."""
    pdf = pikepdf.open(input_path)
    page = pdf.pages[page_index]

    # Bild-Koordinaten auf der Original-Seite
    img_left = IMG_FORM_X * SCALE_FACTOR
    img_bottom = IMG_FORM_Y * SCALE_FACTOR
    img_width = IMG_FORM_W * SCALE_FACTOR
    img_height = IMG_FORM_H * SCALE_FACTOR

    # Skalierung: Querformat-Bild -> 36x89mm Hochformat
    sx = TARGET_H_PT / img_width    # Bildbreite -> Seitenhoehe
    sy = TARGET_W_PT / img_height   # Bildhoehe -> Seitenbreite

    # Endgueltige Seitengroesse (Hochformat) mit Raendern
    page_w = TARGET_W_PT + MARGIN_LEFT
    page_h = TARGET_H_PT + MARGIN_TOP

    # Content-Stream-Transformation (von innen nach aussen gelesen):
    # 1. Bild zum Ursprung verschieben (-img_left, -img_bottom)
    # 2. Skalieren (sx, sy) -> Bild ist jetzt (TARGET_H_PT x TARGET_W_PT) Querformat
    # 3. 270° im Uhrzeigersinn drehen (= 90° gegen UZS) -> Hochformat
    # 4. In Endposition verschieben (mit Rand links, Rand oben bleibt frei)
    raw = page.obj["/Contents"].read_bytes()
    new_content = (
        f"q\n"
        f"1 0 0 1 {MARGIN_LEFT + TARGET_W_PT:.6f} 0 cm\n"
        f"0 1 -1 0 0 0 cm\n"
        f"{sx:.6f} 0 0 {sy:.6f} 0 0 cm\n"
        f"1 0 0 1 {-img_left:.6f} {-img_bottom:.6f} cm\n"
    ).encode() + raw + b"\nQ"

    page.obj["/Contents"] = pdf.make_stream(new_content)
    page.mediabox = [0, 0, page_w, page_h]

    # Alle Box-Attribute und Rotation entfernen
    for box in ["/CropBox", "/TrimBox", "/BleedBox", "/ArtBox"]:
        if box in page.obj:
            del page.obj[box]
    if "/Rotate" in page.obj:
        del page.obj["/Rotate"]

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

        # Alias als Dateiname versuchen (nur bei DHL/Text moeglich)
        alias = extract_alias(page) if label_type == "text" else None

        if alias:
            safe_name = sanitize_filename(alias)
            output_path = output_dir / f"{safe_name}.pdf"
            # Bei Duplikaten Nummer anhaengen
            n = 2
            while output_path.exists():
                output_path = output_dir / f"{safe_name}_{n}.pdf"
                n += 1
        elif len(reader.pages) == 1:
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

        alias_info = f" -> {alias}" if alias else ""
        print(f"  Seite {i}: Label {count + 1} extrahiert [{type_info}]{alias_info}")
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

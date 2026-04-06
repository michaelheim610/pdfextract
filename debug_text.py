#!/usr/bin/env python3
"""Diagnose-Skript: Zeigt wie pypdf den Text aus den PDFs extrahiert."""

import os
from pathlib import Path
from pypdf import PdfReader
import pypdf

SCRIPT_DIR = Path(__file__).resolve().parent

print(f"Python pypdf Version: {pypdf.__version__}")
print()

# PDF finden
pdf_path = None
for d in [SCRIPT_DIR / "import", SCRIPT_DIR / "verarbeitet", SCRIPT_DIR]:
    if d.exists():
        for f in sorted(d.glob("*.pdf")):
            pdf_path = f
            break
    if pdf_path:
        break

if not pdf_path:
    print("Keine PDF gefunden! Bitte eine PDF in den import/ Ordner legen.")
    exit(1)

reader = PdfReader(pdf_path)
print(f"Datei: {pdf_path.name} ({len(reader.pages)} Seiten)")
print()

# Erste 3 Seiten mit Text anzeigen
shown = 0
for i, page in enumerate(reader.pages):
    text = page.extract_text()
    if not text or not text.strip():
        print(f"=== Seite {i+1}: (kein Text) ===")
        print()
        shown += 1
    else:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        print(f"=== Seite {i+1}: {len(lines)} Zeilen ===")
        for j, line in enumerate(lines[:15]):
            compact = line.replace(" ", "")
            print(f"  {j:2}: [{compact}]")
        print()
        shown += 1
    if shown >= 4:
        break

input("Druecke Enter zum Schliessen...")

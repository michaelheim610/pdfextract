#!/bin/bash
# Whatnot Label Splitter mit OCR - Alias-Erkennung auch fuer Deutsche Post Labels

# Ins Skript-Verzeichnis wechseln
cd "$(dirname "$0")"

echo "====================================="
echo "  Whatnot Label Splitter (mit OCR)"
echo "  (Jede Seite = ein Label)"
echo "  (Alias als Dateiname)"
echo "====================================="
echo ""

# Pruefen ob Python3 installiert ist
if ! command -v python3 &> /dev/null; then
    echo "FEHLER: Python3 ist nicht installiert."
    echo "Bitte installiere Python3: https://www.python.org/downloads/"
    echo ""
    read -p "Druecke Enter zum Schliessen..."
    exit 1
fi

# Pruefen ob Tesseract installiert ist
if ! command -v tesseract &> /dev/null; then
    echo "FEHLER: Tesseract ist nicht installiert (wird fuer OCR benoetigt)."
    echo ""
    echo "Installation:"
    echo "  brew install tesseract tesseract-lang"
    echo ""
    read -p "Druecke Enter zum Schliessen..."
    exit 1
fi

# Pruefen ob Abhaengigkeiten installiert sind
python3 -c "import pypdf; import pytesseract; import PIL" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installiere Abhaengigkeiten..."
    pip3 install -r requirements.txt pytesseract Pillow
    echo ""
fi

# Import-Ordner im Finder oeffnen falls leer
mkdir -p import output verarbeitet
if [ -z "$(ls import/*.pdf 2>/dev/null)" ]; then
    echo "Der Import-Ordner ist leer."
    echo "Lege deine PDFs mit Etiketten in diesen Ordner:"
    echo "  $(pwd)/import"
    echo ""
    open import
    read -p "Druecke Enter wenn die PDFs im Ordner liegen..."
    echo ""
fi

# Skript ausfuehren
python3 split_labels_ocr.py

echo ""

# Output-Ordner oeffnen
open output

echo "Fertig! Der Output-Ordner wurde geoeffnet."
echo ""
read -p "Druecke Enter zum Schliessen..."

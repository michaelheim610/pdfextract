# Whatnot Label Tools

Werkzeuge zum Extrahieren von Versandetiketten aus PDF-Dokumenten.

## Das Problem

- **Whatnot-PDFs** enthalten Lieferschein + Etikett - das Label muss manuell ausgeschnitten werden
- **Etiketten-PDFs** enthalten mehrere Labels auf A4-Seiten - muessen einzeln zugeschnitten werden

Bei vielen Bestellungen ist das sehr zeitaufwendig.

## Die Werkzeuge

### 1. Label Extractor (`extract_label.py`)
Fuer **Whatnot-PDFs** (Lieferschein + Etikett): Extrahiert die letzte Seite (das Etikett) und schneidet den Leerraum weg.

### 2. Label Splitter (`split_labels.py`)
Fuer **PDFs die nur Etiketten enthalten**: Jede Seite wird auf den Label-Bereich zugeschnitten und als einzelnes PDF gespeichert. Dateiname = Whatnot-Alias des Kaeufers (bei DHL-Labels).

### 3. Label Splitter OCR (`split_labels_ocr.py`)
Wie Label Splitter, aber mit **OCR-Erkennung**: Liest auch bei Deutsche Post/GoGreen Bild-Labels den Whatnot-Alias per Texterkennung aus. Damit haben **alle** Labels den Alias als Dateiname.

## Voraussetzungen

### 1. Homebrew installieren (Mac Paketmanager)

Terminal oeffnen und diesen Befehl ausfuehren:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Nach der Installation die angezeigte Anleitung befolgen (PATH einrichten). Meistens:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Pruefen ob es funktioniert:

```bash
brew --version
```

### 2. Python installieren

```bash
brew install python
```

Pruefen:

```bash
python3 --version
pip3 --version
```

### 3. Tesseract installieren (fuer OCR-Version)

```bash
brew install tesseract tesseract-lang
```

### 4. Projekt klonen und Abhaengigkeiten installieren

```bash
git clone https://github.com/michaelheim610/pdfextract.git
cd pdfextract
pip3 install -r requirements.txt
```

## Schnellinstallation (alles auf einmal)

Fuer einen neuen Mac - alles in einem Rutsch:

```bash
# Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# Python + Tesseract
brew install python tesseract tesseract-lang

# Projekt
git clone https://github.com/michaelheim610/pdfextract.git
cd pdfextract
pip3 install -r requirements.txt
```

## Nutzung

### Mac (einfachste Variante)

PDFs in den `import/` Ordner legen, dann Doppelklick auf:

| Datei | Funktion |
|---|---|
| **`Label Extractor.command`** | Whatnot-PDFs: nur das Etikett (letzte Seite) |
| **`Label Splitter.command`** | Jede Seite einzeln als Label-PDF (Alias bei DHL) |
| **`Label Splitter OCR.command`** | Wie oben + OCR fuer Deutsche Post Alias |

### Terminal

```bash
# Whatnot-PDFs: Etikett extrahieren
python3 extract_label.py

# Etiketten-PDFs: alle Seiten einzeln zuschneiden
python3 split_labels.py

# Mit OCR (auch Deutsche Post Alias-Erkennung)
python3 split_labels_ocr.py
```

## Ordnerstruktur

```
pdfextract/
├── import/                        # PDFs hier ablegen
├── output/                        # Fertige Labels
├── verarbeitet/                   # Originale nach Verarbeitung
├── extract_label.py               # Whatnot-Etikett extrahieren
├── split_labels.py                # Etiketten-PDF aufteilen
├── split_labels_ocr.py            # Aufteilen mit OCR-Alias
├── Label Extractor.command        # Mac Doppelklick-Start
├── Label Splitter.command         # Mac Doppelklick-Start
├── Label Splitter OCR.command     # Mac Doppelklick-Start (mit OCR)
├── requirements.txt
└── LICENSE
```

## Ablauf

1. PDFs in `import/` legen (beliebig viele)
2. Passendes Werkzeug starten
3. Fertige Labels landen in `output/` (Dateiname = Whatnot-Alias)
4. Originale werden nach `verarbeitet/` verschoben
5. `import/` ist leer und bereit fuer die naechste Runde

## Lizenz

MIT License - siehe [LICENSE](LICENSE)

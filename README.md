# Whatnot Label Tools

Zwei Werkzeuge zum Extrahieren von Versandetiketten aus PDF-Dokumenten.

## Das Problem

- **Whatnot-PDFs** enthalten Lieferschein + Etikett - das Label muss manuell ausgeschnitten werden
- **Etiketten-PDFs** enthalten mehrere Labels auf A4-Seiten - muessen einzeln zugeschnitten werden

Bei vielen Bestellungen ist das sehr zeitaufwendig.

## Die Werkzeuge

### 1. Label Extractor (`extract_label.py`)
Fuer **Whatnot-PDFs** (Lieferschein + Etikett): Extrahiert die letzte Seite (das Etikett) und schneidet den Leerraum weg.

### 2. Label Splitter (`split_labels.py`)
Fuer **PDFs die nur Etiketten enthalten**: Jede Seite wird auf den Label-Bereich zugeschnitten und als einzelnes PDF gespeichert.

## Voraussetzungen

- Python 3.10 oder neuer
- macOS, Windows oder Linux

## Installation

```bash
git clone https://github.com/michaelheim610/pdfextract.git
cd pdfextract
pip install -r requirements.txt
```

## Nutzung

### Mac (einfachste Variante)

PDFs in den `import/` Ordner legen, dann Doppelklick auf:

| Datei | Funktion |
|---|---|
| **`Label Extractor.command`** | Whatnot-PDFs: nur das Etikett (letzte Seite) |
| **`Label Splitter.command`** | Jede Seite einzeln als Label-PDF |

### Terminal

```bash
# Whatnot-PDFs: Etikett extrahieren
python3 extract_label.py

# Etiketten-PDFs: alle Seiten einzeln zuschneiden
python3 split_labels.py
```

## Ordnerstruktur

```
pdfextract/
├── import/                    # PDFs hier ablegen
├── output/                    # Fertige Labels
├── verarbeitet/               # Originale nach Verarbeitung
├── extract_label.py           # Whatnot-Etikett extrahieren
├── split_labels.py            # Etiketten-PDF aufteilen
├── Label Extractor.command    # Mac Doppelklick-Start
├── Label Splitter.command     # Mac Doppelklick-Start
├── requirements.txt
└── LICENSE
```

## Ablauf

1. PDFs in `import/` legen (beliebig viele)
2. Passendes Werkzeug starten
3. Fertige Labels landen in `output/`
4. Originale werden nach `verarbeitet/` verschoben
5. `import/` ist leer und bereit fuer die naechste Runde

## Lizenz

MIT License - siehe [LICENSE](LICENSE)

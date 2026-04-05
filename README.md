# Whatnot Label Extractor

Extrahiert automatisch Versandetiketten (DHL, etc.) aus Whatnot-PDF-Dokumenten und speichert sie als druckfertige DIN A6 PDFs.

## Das Problem

Whatnot liefert PDF-Dokumente mit Lieferschein + Versandetikett. Um das Etikett zu drucken, muss man es manuell per Screenshot ausschneiden. Bei vielen Bestellungen ist das sehr zeitaufwendig.

## Die Loesung

Dieses Skript extrahiert automatisch das Etikett (letzte Seite) aus allen PDFs, schneidet es auf den Label-Bereich zu und skaliert es auf **DIN A6 Hochkant (105 x 148 mm)** - druckfertig.

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

1. Doppelklick auf **`Label Extractor.command`**
2. PDFs in den geoeffneten `import/` Ordner legen
3. Enter druecken
4. Fertige Labels erscheinen im `output/` Ordner

### Terminal

```bash
# PDFs in den import/ Ordner kopieren, dann:
python3 extract_label.py
```

## Ordnerstruktur

```
pdfextract/
├── import/          # PDFs hier ablegen
├── output/          # Extrahierte Labels (DIN A6)
├── verarbeitet/     # Originale nach Verarbeitung
├── extract_label.py
├── Label Extractor.command
└── requirements.txt
```

## Ablauf

1. PDFs in `import/` legen (beliebig viele)
2. Skript starten
3. Fuer jede PDF wird das Etikett von der **letzten Seite** extrahiert
4. Label wird auf **DIN A6 Hochkant** zugeschnitten und skaliert
5. Fertiges Label landet in `output/` (gleicher Dateiname)
6. Original wird nach `verarbeitet/` verschoben

## Lizenz

MIT License - siehe [LICENSE](LICENSE)

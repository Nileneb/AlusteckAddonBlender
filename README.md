# 🏗️ ALUSTECK BUILDER - Blender Addon

> **Parametrisches CAD-System für Alusteck Stecksysteme mit AI-Integration**

[![Blender](https://img.shields.io/badge/Blender-4.0%2B-orange)](https://www.blender.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🎯 Vision

Ein **intelligentes Baukastensystem** direkt in Blender, das:

- Exakte Alusteck-Komponenten mit echten Maßen bereitstellt
- Automatisches Snapping mit physikalisch korrekten Verbindungen ermöglicht
- Per **Chat oder Skizze** komplette 3D-Strukturen generiert
- Stücklisten und Kostenkalkulationen exportiert

---

## 📐 System-Architektur

```mermaid
┌─────────────────────────────────────────────────────────────────────────┐
│                        ALUSTECK BUILDER v2.0                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │   20mm      │    │   25mm      │    │   30mm      │                 │
│  │  SYSTEM     │    │  SYSTEM     │    │  SYSTEM     │   DATENBANK    │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘   (JSON/SQLite) │
│         │                  │                  │                         │
│         └──────────────────┼──────────────────┘                         │
│                            │                                            │
│                            ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    KOMPONENTEN-REGISTRY                          │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐             │   │
│  │  │ Profile │  │Verbinder│  │ Zubehör │  │  Stege  │             │   │
│  │  │(Hollow) │  │(2-6Way) │  │(Kappen) │  │(A/B/C)  │             │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                            │                                            │
│                            ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      SNAP ENGINE                                 │   │
│  │                                                                  │   │
│  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │   │
│  │   │ Verbindungs- │    │  Kollisions- │    │    Steg-     │      │   │
│  │   │   Regeln     │───▶│   Prüfung    │───▶│  Kompatibil. │      │   │
│  │   └──────────────┘    └──────────────┘    └──────────────┘      │   │
│  │                                                                  │   │
│  │   • Max. Anschlüsse pro Verbinder                               │   │
│  │   • Zapfen-Einstecktiefe validieren                             │   │
│  │   • Überlappungen verhindern                                    │   │
│  │   • Steg-Richtung beachten                                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                            │                                            │
│                            ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    AI INTEGRATION                                │   │
│  │                                                                  │   │
│  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │   │
│  │   │    Chat      │    │   Skizzen-   │    │    Best      │      │   │
│  │   │   Input      │───▶│   Analyse    │───▶│   Practice   │      │   │
│  │   └──────────────┘    └──────────────┘    └──────────────┘      │   │
│  │                                                                  │   │
│  │   "Baue ein Regal 2m x 0.5m x 1.8m"  ──▶  🧊 3D-Modell          │   │
│  │   [Skizze hochladen]                  ──▶  🧊 3D-Modell          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                            │                                            │
│                            ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                       EXPORT                                     │   │
│  │                                                                  │   │
│  │   📋 Stückliste    💰 Kalkulation    📦 3D-Export    🛒 Shop    │   │
│  │      (CSV/PDF)        (Excel)         (GLTF/STL)      (Link)    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Projektstruktur

```
alusteck_builder/
│
├── __init__.py                 # Blender Addon Entry Point
├── manifest.toml               # Blender 4.2+ Extension Manifest
│
├── core/
│   ├── __init__.py
│   ├── database.py             # Datenbank-Loader (JSON/SQLite)
│   ├── registry.py             # Komponenten-Registry
│   └── constants.py            # Globale Konstanten & Maße
│
├── components/
│   ├── __init__.py
│   ├── profile.py              # Profil-Mesh-Generator
│   ├── connector.py            # Verbinder-Mesh-Generator
│   ├── accessory.py            # Zubehör-Generator
│   └── materials.py            # Material-Definitionen
│
├── snap/
│   ├── __init__.py
│   ├── engine.py               # Snap-Engine Hauptlogik
│   ├── rules.py                # Verbindungsregeln
│   ├── collision.py            # Kollisionsprüfung
│   └── validation.py           # Konstruktions-Validierung
│
├── ai/
│   ├── __init__.py
│   ├── chat_interface.py       # Chat-Panel in Blender
│   ├── prompt_builder.py       # Prompt-Engineering
│   ├── structure_generator.py  # Text → 3D Struktur
│   └── sketch_analyzer.py      # Skizze → Struktur (Optional)
│
├── ui/
│   ├── __init__.py
│   ├── panels.py               # Sidebar Panels
│   ├── menus.py                # Add-Menüs
│   ├── operators.py            # Alle Blender Operators
│   └── preferences.py          # Addon-Einstellungen
│
├── export/
│   ├── __init__.py
│   ├── bom.py                  # Bill of Materials (Stückliste)
│   ├── cost_calc.py            # Kostenberechnung
│   └── shop_link.py            # Direktlink zum Alusteck-Shop
│
├── data/
│   ├── alusteck_database.json  # Alle Komponenten-Daten
│   ├── snap_rules.json         # Snap-Regeln
│   └── presets/                # Vorgefertigte Strukturen
│       ├── regal_basic.json
│       ├── tisch_standard.json
│       └── rahmen_modular.json
│
└── tools/
    ├── scraper.py              # Web-Scraper für Produktdaten
    └── db_updater.py           # Datenbank-Aktualisierung
```

---

## 🔧 Komponenten-Datenbank

### Struktur (JSON Schema)

```json
{
  "meta": {
    "version": "2.0",
    "source": "alusteck.de",
    "last_updated": "2025-01-15"
  },

  "systems": {
    "20mm": { ... },
    "25mm": {
      "profile": {
        "outer_mm": 25.0,
        "wall_mm": 1.5,
        "inner_mm": 22.0,

        "variants": [
          {
            "id": "VK25-STD",
            "name": "Standard Vierkantrohr",
            "steg": null,
            "price_per_m": 5.90
          },
          {
            "id": "VK25-2SI",
            "name": "2 Stege Innenwinkel",
            "steg": {
              "count": 2,
              "type": "single",
              "position": "inner_corner",
              "height_mm": 15.0,
              "blocks_directions": ["+X", "+Y"]
            },
            "price_per_m": 13.77
          }
        ],

        "schnittbilder": {
          "A": {"name": "Gerade", "surcharge": 0.48},
          "B": {"name": "45° Gehrung", "surcharge": 0.48},
          "C": {"name": "Doppel-Gehrung", "surcharge": 0.69}
        }
      },

      "connectors": [
        {
          "id": "2D25K",
          "name": "Verbinder gerade",
          "type": "straight",
          "ways": 2,
          "socket_depth_mm": 25.0,
          "price": 1.50,
          "ports": [
            {"direction": [0, 0, 1], "offset": [0, 0, 12.5]},
            {"direction": [0, 0, -1], "offset": [0, 0, -12.5]}
          ]
        },
        {
          "id": "3E25K",
          "name": "Eckverbinder 3-Wege",
          "type": "corner_3",
          "ways": 3,
          "socket_depth_mm": 25.0,
          "cube_size_mm": 25.0,
          "price": 2.50,
          "ports": [
            {"direction": [1, 0, 0], "offset": [12.5, 0, 0]},
            {"direction": [0, 1, 0], "offset": [0, 12.5, 0]},
            {"direction": [0, 0, 1], "offset": [0, 0, 12.5]}
          ]
        }
      ],

      "accessories": [ ... ]
    },
    "30mm": { ... }
  },

  "snap_rules": {
    "socket_tolerance_mm": 0.5,
    "auto_align": true,
    "steg_compatibility": {
      "inner_corner": {
        "compatible_connectors": ["corner_3", "corner_4"],
        "blocked_ports": ["+X", "+Y"]
      }
    }
  }
}
```

---

## 🧲 Snap-Engine

### Funktionsweise

```
   PROFIL                    VERBINDER                    PROFIL
     │                          │                           │
     │    ┌──────────────┐      │      ┌──────────────┐     │
     │    │              │      │      │              │     │
═════╪════╡   ZAPFEN     ╞══════╪══════╡   ZAPFEN     ╞═════╪═════
     │    │   (22mm)     │      │      │   (22mm)     │     │
     │    └──────────────┘      │      └──────────────┘     │
     │                          │                           │
     │◄────── 25mm ──────►│◄─25─►│◄────── 25mm ──────►│
     │    Einstecktiefe        Würfel      Einstecktiefe    │
```

### Snap-Regeln

| Verbinder-Typ | Max. Ports | Richtungen | Kollisionsprüfung |
| ------------- | ---------- | ---------- | ----------------- |
| Gerade (2D)   | 2          | ±Z         | Nein              |
| Winkel (2W)   | 2          | +X, +Y     | Ja                |
| T-Stück (3T)  | 3          | ±X, +Y     | Ja                |
| Ecke (3E)     | 3          | +X,+Y,+Z   | Ja                |
| Kreuz (4K)    | 4          | ±X, ±Y     | Ja                |
| Würfel (6W)   | 6          | ±X,±Y,±Z   | Ja                |

### Steg-Kompatibilität

```
   INNENWINKEL-STEG              GEGENÜBER-STEG

      ┌─────┐                       ┌─────┐
      │█████│ ← Steg                │█│ │█│ ← Stege
      │█   █│                       │█│ │█│
      │█████│ ← Steg                │█│ │█│
      └─────┘                       └─────┘

   Blockiert: +X, +Y            Blockiert: ±X
   Erlaubt: -X, -Y, ±Z          Erlaubt: ±Y, ±Z
```

---

## 🤖 AI-Integration

### Chat-Interface

```python
# Beispiel-Prompts → 3D-Struktur

"Baue ein Regal mit 3 Böden, 80cm breit, 40cm tief, 180cm hoch"
    ↓
┌────────────────────────────────────────┐
│  AI analysiert:                        │
│  • Breite: 800mm → 32 Rastereinheiten  │
│  • Tiefe: 400mm → 16 Rastereinheiten   │
│  • Höhe: 1800mm → 72 Rastereinheiten   │
│  • Böden: 3 → Abstände berechnen       │
│  • System: 25mm (Standard)             │
├────────────────────────────────────────┤
│  Generiert:                            │
│  • 4x Eckverbinder 3-Wege (oben)       │
│  • 4x Eckverbinder 3-Wege (unten)      │
│  • 8x T-Verbinder (Zwischenböden)      │
│  • 4x Profile 1800mm (Stützen)         │
│  • 12x Profile 800mm (Querstreben)     │
│  • 12x Profile 400mm (Tiefenstreben)   │
└────────────────────────────────────────┘
    ↓
🧊 Fertiges 3D-Modell in Blender
```

### Prompt-Schema für Claude API

```json
{
  "system": "Du bist ein CAD-Assistent für Alusteck-Konstruktionen...",
  "context": {
    "available_systems": ["20mm", "25mm", "30mm"],
    "snap_rules": { ... },
    "best_practices": [
      "Vertikale Stützen alle 60-80cm",
      "Horizontale Verstrebungen für Stabilität",
      "Stellfüße für Bodenausgleich"
    ]
  },
  "output_format": {
    "type": "construction_plan",
    "components": [...],
    "connections": [...]
  }
}
```

---

## 🚀 Roadmap

### Phase 1: Foundation ✅

- [x] Basis-Addon Struktur
- [x] Profil-Mesh-Generator (Hohlkörper)
- [x] Verbinder-Mesh-Generator (2-6 Wege)
- [x] Material-System

### Phase 2: Datenbank 🔄

- [ ] JSON-Schema definieren
- [ ] Scraper für Produktdaten
- [ ] Alle 3 Systeme (20/25/30mm) erfassen
- [ ] Steg-Varianten integrieren
- [ ] Schnittbild-Optionen

### Phase 3: Snap-Engine ✅

- [x] Port-basiertes Snap-System
- [x] Kollisionserkennung
- [x] Steg-Kompatibilitätsprüfung
- [x] Visuelle Snap-Vorschau (Highlighting)

### Phase 4: Export & Polish 📋

- [ ] Stücklisten-Export (CSV/PDF)
- [ ] Kostenberechnung
- [ ] Direktlink zum Alusteck-Warenkorb
- [ ] Preset-Bibliothek

### Phase 5: AI-Integration 📋

- [ ] Chat-Panel in Blender Sidebar
- [ ] Claude API Integration
- [ ] Text → Struktur Konvertierung
- [ ] Best-Practice Vorschläge

---

## 🛠️ Installation

```bash
# 1. Repository klonen
git clone https://github.com/user/alusteck-builder.git

# 2. In Blender installieren
#    Edit > Preferences > Add-ons > Install
#    Wähle: alusteck_builder/__init__.py

# 3. Addon aktivieren
#    Häkchen bei "Alusteck Builder"

# 4. (Optional) API-Key für AI-Features
#    Addon-Preferences > Claude API Key eingeben
```

---

## 📖 Verwendung

### Komponenten hinzufügen

```
Shift+A > Mesh > Alusteck > [System wählen] > [Komponente]
```

### Snap-Modus

```
1. Verbinder platzieren
2. Profil auswählen
3. G (Grab) + Mausbewegung
4. Automatischer Snap an freie Ports
```

### AI-Konstruktion

```
1. Sidebar (N) > Alusteck > AI Builder
2. Beschreibung eingeben oder Skizze hochladen
3. "Generieren" klicken
4. Vorschlag akzeptieren/anpassen
```

---

## 🤝 Contributing

Contributions welcome! Besonders gesucht:

- Produktdaten-Vervollständigung
- Snap-Algorithmus-Optimierung
- UI/UX Verbesserungen
- Preset-Bibliothek erweitern

---

## 📄 Lizenz

MIT License - Siehe [LICENSE](LICENSE)

---

## 🔗 Links

- [Alusteck Shop](https://www.alusteck.de/)
- [Blender](https://www.blender.org/)
- [Claude API](https://www.anthropic.com/)

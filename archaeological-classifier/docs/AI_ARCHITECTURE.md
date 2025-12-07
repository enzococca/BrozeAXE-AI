# AI Architecture - Archaeological Classifier System

Questo documento descrive come l'intelligenza artificiale (Claude) viene utilizzata nel sistema di classificazione archeologica.

## Panoramica

Il sistema utilizza **Claude 4.5 Sonnet** (Anthropic) per l'analisi e l'interpretazione di artefatti archeologici, in particolare asce dell'età del bronzo di tipo Savignano.

## Dove viene usata l'AI

### 1. Classificazione Artefatti (`ai_assistant.py`)

**Scopo:** Analizzare features morfometriche e suggerire classificazioni tipologiche.

**Configurazione:**
```python
model = "claude-sonnet-4-5-20250929"
temperature = 0.3  # Bassa per risposte più deterministiche
max_tokens = 2000
```

**Input fornito all'AI:**
- ID artefatto
- Features morfometriche estratte (lunghezza, larghezza, rapporti, ecc.)
- Features Savignano specifiche (tipo tallone, bordi, sezione, ecc.)
- Classi tipologiche esistenti per confronto
- Contesto archeologico opzionale

**Output:**
- Suggerimento di classificazione
- Confronti tipologici
- Note metodologiche

### 2. Interpretazione Savignano (`routes.py`)

**Endpoint:** `/web/savignano-ai-interpretation/<artifact_id>`

**Configurazione:**
```python
temperature = 0.1  # Molto bassa per massima coerenza
max_tokens = 600
```

**Input:**
- Features morfometriche complete dell'ascia
- Dati dimensionali
- Caratteristiche tipologiche

**Output salvato in cache:** `savignano_interpretation`

### 3. Analisi Tecnologica (`routes.py`)

**Endpoint:** `/artifact/<id>/tech-analysis`

**Scopo:** Analisi delle tecniche di produzione (martellatura, fusione).

**Output salvato in cache:** `tech_analysis`

### 4. Q&A Archeologico (`archaeological_qa.py`)

**Scopo:** Rispondere a domande specifiche sugli artefatti.

**Configurazione:**
```python
model = "claude-sonnet-4-5-20250929"
max_tokens = variabile (600-2000)
```

---

## Come l'AI prende decisioni

### Criteri di Classificazione

L'AI utilizza un prompt strutturato che include:

1. **Ruolo definito:** "Esperto archeologo specializzato in asce dell'età del bronzo"
2. **Dati oggettivi:** Solo features estratte algoritmicamente dalla mesh 3D
3. **Framework tipologico:** Riferimento a tipologie note (Savignano I-IV, varianti regionali)
4. **Vincoli di risposta:** Formato strutturato per evitare divagazioni

### Esempio di Prompt

```
You are an expert archaeological AI assistant specializing in
Bronze Age artifact classification, particularly bronze axes.

Analyze the following artifact and provide classification insights:

**Artifact ID:** SAV_001

**Morphometric Features:**
- Length: 152.3 mm
- Width: 45.2 mm
- Thickness: 28.1 mm
...

Based on these features, provide:
1. Typological classification
2. Production technique analysis
3. Comparative notes
```

---

## Come vengono estratti i dati

### Pipeline di Estrazione

```
Mesh 3D (.obj)
    │
    ▼
┌─────────────────────────┐
│ Morphometric Extractor  │  ← Algoritmi geometrici
│ (morphometric.py)       │
└─────────────────────────┘
    │
    ▼
Features numeriche
(lunghezza, area, volume, rapporti)
    │
    ▼
┌─────────────────────────┐
│ Savignano Extractor     │  ← Analisi specifica tipo
│ (morphometric_extractor.py)
└─────────────────────────┘
    │
    ▼
Features Savignano
(tipo_tallone, margini, sezione)
    │
    ▼
┌─────────────────────────┐
│ AI Analysis             │  ← Claude interpreta
│ (ai_assistant.py)       │
└─────────────────────────┘
    │
    ▼
Interpretazione testuale
```

### Dati MAI inventati dall'AI

L'AI **NON inventa** dati numerici. Tutti i dati quantitativi provengono da:

1. **Estrazione geometrica** dalla mesh 3D (trimesh)
2. **Calcoli matematici** (PCA, clustering, distanze)
3. **Database** (features precedentemente estratte)

L'AI si limita a:
- **Interpretare** i dati esistenti
- **Classificare** in base a tipologie note
- **Confrontare** con altri artefatti
- **Descrivere** in linguaggio naturale

---

## Configurazione Temperature

| Endpoint | Temperature | Motivo |
|----------|-------------|--------|
| Classificazione | 0.3 | Bilanciamento creatività/coerenza |
| Interpretazione Savignano | 0.1 | Massima coerenza/ripetibilità |
| Analisi Tecnologica | 0.2 | Bassa creatività, focus tecnico |
| Q&A Generale | 0.3 | Permette risposte più elaborate |

**Nota:** Temperature basse (0.1-0.3) riducono significativamente il rischio di "hallucination" mantenendo le risposte ancorate ai dati forniti.

---

## Sistema di Cache

Per evitare rigenerazione costosa e garantire coerenza:

```
┌─────────────────────────────────────┐
│           ai_cache table            │
├─────────────────────────────────────┤
│ artifact_id | cache_type | content  │
│ SAV_001     | savignano_interpretation | {...} │
│ SAV_001     | hammering_analysis | {...} │
│ SAV_002     | tech_analysis | {...} │
└─────────────────────────────────────┘
```

**Tipi di cache:**
- `savignano_interpretation` - Interpretazione tipologica
- `tech_analysis` - Analisi tecnologica
- `hammering_analysis` - Analisi martellatura
- `casting_analysis` - Analisi fusione
- `comprehensive_report` - Report completo

**Vantaggi:**
1. ✅ Risparmio token (costo API)
2. ✅ Risposte immediate per dati già analizzati
3. ✅ Coerenza nelle risposte ripetute
4. ✅ Possibilità di aggregare/ricercare interpretazioni

---

## Rischi e Mitigazioni

### Hallucination (Invenzione dati)

**Rischio:** L'AI potrebbe inventare dati non presenti nei features.

**Mitigazioni:**
1. Temperature bassa (0.1-0.3)
2. Prompt strutturati con dati espliciti
3. Richiesta di citare solo dati forniti
4. Validazione post-hoc dei riferimenti numerici

### Bias Tipologico

**Rischio:** L'AI potrebbe favorire classificazioni note.

**Mitigazioni:**
1. Inclusione di categorie "incerto" o "atipico"
2. Richiesta esplicita di evidenziare anomalie
3. Confronto con database esistente

### Inconsistenza

**Rischio:** Risposte diverse per lo stesso artefatto.

**Mitigazioni:**
1. Sistema di cache per riutilizzo
2. Temperature bassa
3. Prompt deterministici

---

## Schema Architetturale

```
┌─────────────────────────────────────────────────────────────┐
│                    WEB INTERFACE                            │
│  (Templates: viewer3d.html, morphometric.html, etc.)       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    ROUTES (routes.py)                       │
│  Endpoints: /artifact/*, /savignano-*, /run-pca, etc.      │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│  MORPHOMETRIC     │ │  AI ASSISTANT     │ │  DATABASE         │
│  ANALYZER         │ │  (Claude API)     │ │  (SQLite)         │
│                   │ │                   │ │                   │
│ - PCA             │ │ - Classify        │ │ - artifacts       │
│ - Clustering      │ │ - Interpret       │ │ - features        │
│ - Similarity      │ │ - Analyze Tech    │ │ - ai_cache        │
└───────────────────┘ └───────────────────┘ └───────────────────┘
            │                 │                       │
            └─────────────────┼───────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    MESH PROCESSING                          │
│  Savignano Extractor → Features → Storage                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    STORAGE (Dropbox)                        │
│  Mesh files (.obj), Backups, Reports                       │
└─────────────────────────────────────────────────────────────┘
```

---

## API Reference

### AIClassificationAssistant

```python
from acs.core.ai_assistant import AIClassificationAssistant

ai = AIClassificationAssistant()

# Analisi singola
result = ai.analyze_artifact(
    artifact_id="SAV_001",
    features=features_dict,
    existing_classes=taxonomy_classes,
    context="Ritrovamento nella zona X"
)

# Analisi streaming
for chunk in ai.analyze_artifact_stream(artifact_id, features):
    print(chunk, end='')
```

### Database Cache

```python
from acs.core.database import get_database

db = get_database()

# Salvare interpretazione
db.save_ai_cache(
    artifact_id="SAV_001",
    cache_type="savignano_interpretation",
    content=interpretation_text,
    model="claude-sonnet-4-5-20250929"
)

# Recuperare interpretazione cached
cached = db.get_ai_cache("SAV_001", "savignano_interpretation")
if cached:
    print(cached['content'])
```

---

## Conclusioni

L'AI nel sistema ACS è configurata per:

1. **Essere trasparente:** Tutti i dati di input sono visibili e verificabili
2. **Essere coerente:** Temperature basse e cache riducono variabilità
3. **Non inventare:** L'AI interpreta solo dati forniti algoritmicamente
4. **Essere tracciabile:** Ogni interpretazione è salvata con metadata

Per domande o problemi: aprire una issue su GitHub.

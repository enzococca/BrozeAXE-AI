## Sistema Completo di Analisi Archeologica per le Asce di Savignano sul Panaro

**Archaeological Classifier System - Savignano Module**
**Versione:** 1.0.0
**Data:** Novembre 2025

---

## Indice

1. [Introduzione](#introduzione)
2. [Domande Archeologiche Affrontate](#domande-archeologiche-affrontate)
3. [Architettura del Sistema](#architettura-del-sistema)
4. [Installazione e Setup](#installazione-e-setup)
5. [Utilizzo del Sistema](#utilizzo-del-sistema)
6. [Parametri Morfometrici Estratti](#parametri-morfometrici-estratti)
7. [Analisi Matrici e Fusioni](#analisi-matrici-e-fusioni)
8. [Interpretazione AI con Claude](#interpretazione-ai-con-claude)
9. [Output e Risultati](#output-e-risultati)
10. [Esempi Pratici](#esempi-pratici)
11. [Troubleshooting](#troubleshooting)
12. [Riferimenti Bibliografici](#riferimenti-bibliografici)

---

## Introduzione

Questo sistema fornisce un'analisi archeologica completa e automatizzata delle 96 asce in bronzo del ripostiglio di Savignano sul Panaro (Modena, Italia), datato al Bronzo Medio-Recente (ca. 1600-1300 BCE).

### Cosa Fa il Sistema

Il sistema combina:
- **Analisi morfometrica 3D automatica** - estrae parametri dettagliati dalle scansioni 3D
- **Clustering machine learning** - identifica matrici di fusione e raggruppa asce simili
- **Interpretazione AI (Claude Sonnet 4.5)** - fornisce risposte archeologiche contestualizzate
- **Visualizzazioni scientifiche** - genera grafici, dendrogrammi, PCA

### Output Finale

- Identificazione numero matrici usate e loro caratteristiche
- Stima fusioni per ogni matrice
- Analisi trattamenti post-fusione (martellatura, rifinitura)
- Interpretazione funzione incavo tallone
- Valutazione intensità d'uso
- Report archeologico completo in Markdown

---

## Domande Archeologiche Affrontate

Il sistema risponde a **6 domande chiave** sul ripostiglio di Savignano:

### 1. Matrici di Fusione

**Domanda:** Quante matrici sono state usate? Quali sono gli aspetti tecnici e formali (mono/bivalva, incisione margini, preparazione tallone/incavo)?

**Metodologia:**
- Clustering gerarchico su parametri morfometrici
- Silhouette score per numero ottimale cluster
- Analisi variabilità intra-cluster per tipo matrice

**Output:**
- Numero matrici identificate
- Tipo matrice (bivalva/monovalva)
- Caratteristiche distintive per matrice
- Qualità produttiva (CV dimensionale)

### 2. Fusioni per Matrice

**Domanda:** Quante fusioni sono state eseguite per ciascuna matrice?

**Metodologia:**
- Assunzione: 1 ascia = 1 fusione distinta
- Giustificazione: variabilità micro-dimensionale incompatibile con fusioni multiple identiche

**Output:**
- N. fusioni per matrice
- Range pesi per matrice
- Distribuzione produttiva

### 3. Trattamenti Post-Fusione

**Domanda:** Che tipo di trattamento è stato apportato (martellatura, barra centrale, tallone)?

**Metodologia:**
- Analisi margini rialzati (proxy barra centrale)
- Analisi tallone (incavo predisposto vs post-fusione)
- Stima martellatura da letteratura

**Output:**
- % asce con margini rialzati
- % asce con incavo tallone
- Tipologie trattamento

### 4. Rifinitura Finale

**Domanda:** Aspetti tecnici della rifinitura finale (tagliente e tallone)?

**Metodologia:**
- Analisi forme tagliente (arco ribassato/semicircolare/lunato)
- Rapporto arco/corda
- Consistenza dimensionale tallone

**Output:**
- Distribuzione forme tagliente
- Statistiche rifinitura
- Confronto tagliente vs tallone (variabilità)

### 5. Funzione Incavo Tallone

**Domanda:** Perché l'incavo nel tallone? Quale funzione?

**Metodologia:**
- Analisi correlazioni incavo con altre features
- Classificazione profili (circolare/rettangolare)
- Confronto letteratura archeologica

**Output:**
- Ipotesi funzionali (immanicatura/rinforzo/fusione)
- Evidenze a supporto
- Confronti tipologici

### 6. Intensità Uso

**Domanda:** Quanto (e se) sono state usate le asce?

**Metodologia:**
- Analisi usura (se dati disponibili)
- Contestualizzazione deposito (fonditoriale/rituale)
- Indicatori morfometrici indiretti

**Output:**
- Scenario deposizionale prevalente
- Stima uso (nullo/limitato/intenso)
- Raccomandazioni analisi ulteriori

---

## Architettura del Sistema

### Moduli Principali

```
archaeological-classifier/
├── acs/
│   ├── savignano/
│   │   ├── morphometric_extractor.py    # Estrazione parametri morfometrici
│   │   ├── matrix_analyzer.py           # Identificazione matrici/fusioni
│   │   ├── archaeological_qa.py         # Risposte domande archeologiche
│   │   └── __init__.py
│   │
│   └── database/
│       └── savignano_schema.sql         # Schema DB espanso
│
├── savignano_complete_workflow.py        # SCRIPT PRINCIPALE
│
└── SAVIGNANO_SYSTEM_GUIDE.md            # Questa guida
```

### Flusso Dati

```
Mesh 3D (.obj, .stl, .ply)
           ↓
[SavignanoMorphometricExtractor]
           ↓
Features DataFrame (CSV/JSON)
           ↓
[MatrixAnalyzer] → Clustering → Matrici identificate
           ↓
[SavignanoArchaeologicalQA] → Analisi + AI → Risposte + Report
           ↓
Output completo (JSON, CSV, MD, visualizzazioni)
```

---

## Installazione e Setup

### Requisiti

- Python 3.8+
- Dipendenze Python (installare con pip)

```bash
cd /Users/enzo/Documents/BrozeAXE-AI/archaeological-classifier

# Attiva virtual environment
source ../.venv/bin/activate

# Installa dipendenze
pip install numpy pandas scikit-learn scipy matplotlib seaborn trimesh anthropic python-docx
```

### Setup API Key Anthropic (Opzionale ma Raccomandato)

Per interpretazione AI completa:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Oppure passa come argomento:
```bash
--anthropic-api-key YOUR_KEY
```

### Verifica Installazione

```bash
python -c "from acs.savignano import SavignanoMorphometricExtractor; print('✓ OK')"
```

---

## Utilizzo del Sistema

### Workflow Completo (Raccomandato)

```bash
cd /Users/enzo/Documents/BrozeAXE-AI/archaeological-classifier

python savignano_complete_workflow.py \
    --meshes /path/to/meshes/ \
    --output /path/to/output/ \
    --weights-docx "/Users/enzo/Desktop/rif savignano/Note scansioni Artec asce Savignano.docx" \
    --anthropic-api-key YOUR_KEY
```

### Parametri Script

| Parametro | Descrizione | Obbligatorio |
|-----------|-------------|--------------|
| `--meshes` | Directory con file mesh 3D (.obj, .stl, .ply) | ✓ |
| `--output` | Directory output risultati | ✓ |
| `--weights` | File JSON con pesi `{inventory_num: weight_g}` | ✗ |
| `--weights-docx` | File DOCX note scansioni (estrae pesi automaticamente) | ✗ |
| `--anthropic-api-key` | API key Anthropic (o usa env var `ANTHROPIC_API_KEY`) | ✗ |

### Esempio Completo

```bash
python savignano_complete_workflow.py \
    --meshes ~/Desktop/savignano_meshes/ \
    --output ~/Desktop/savignano_analysis_results/ \
    --weights-docx "~/Desktop/rif savignano/Note scansioni Artec asce Savignano.docx"
```

**Tempo stimato:** 15-30 minuti per 96 asce (dipende da complessità mesh)

---

## Parametri Morfometrici Estratti

### Tallone (Butt)

| Parametro | Unità | Descrizione |
|-----------|-------|-------------|
| `tallone_larghezza` | mm | Larghezza tallone |
| `tallone_spessore` | mm | Spessore tallone |
| `incavo_presente` | boolean | Presenza incavo |
| `incavo_larghezza` | mm | Larghezza incavo |
| `incavo_profondita` | mm | Profondità incavo |
| `incavo_profilo` | text | 'rettangolare', 'circolare', 'assente' |

### Margini Rialzati (Raised Edges)

| Parametro | Unità | Descrizione |
|-----------|-------|-------------|
| `margini_rialzati_presenti` | boolean | Presenza margini rialzati |
| `margini_rialzati_lunghezza` | mm | Lunghezza margini |
| `margini_rialzati_spessore_max` | mm | Spessore massimo margini |

### Corpo (Body)

| Parametro | Unità | Descrizione |
|-----------|-------|-------------|
| `larghezza_minima` | mm | Larghezza minima corpo |
| `spessore_massimo_con_margini` | mm | Spessore max includendo margini |
| `spessore_massimo_senza_margini` | mm | Spessore max corpo senza margini |

### Tagliente (Blade)

| Parametro | Unità | Descrizione |
|-----------|-------|-------------|
| `tagliente_larghezza` | mm | Larghezza tagliente |
| `tagliente_forma` | text | 'arco_ribassato', 'semicircolare', 'lunato' |
| `tagliente_arco_misura` | mm | Misurazione arco (se curvo) |
| `tagliente_corda_misura` | mm | Misurazione corda |
| `tagliente_espanso` | boolean | Tagliente espanso rispetto a corpo |

### Generali

| Parametro | Unità | Descrizione |
|-----------|-------|-------------|
| `length` | mm | Lunghezza totale ascia |
| `width` | mm | Larghezza totale |
| `thickness` | mm | Spessore totale |
| `peso` | g | Peso ascia |
| `inventory_number` | text | Numero inventario (es: "974") |

**Totale:** ~25 parametri morfometrici per ascia

---

## Analisi Matrici e Fusioni

### Metodo Clustering

**Algoritmo:** Hierarchical Clustering (Ward linkage)

**Features usate per clustering:**
- Dimensioni (length, width, thickness)
- Tallone (larghezza, spessore, incavo)
- Tagliente (larghezza, forma)
- Peso
- Features booleane (incavo_presente, margini_rialzati_presenti, tagliente_espanso)

**Standardizzazione:** Z-score normalization

### Determinazione Numero Matrici

**Metodo automatico:** Silhouette score maximization

- Testa k=2 a k=15
- Seleziona k con massimo silhouette score
- Validazione con Davies-Bouldin score

**Interpretazione Silhouette:**
- > 0.50: Clustering molto buono
- 0.30-0.50: Clustering accettabile
- < 0.30: Clustering debole (rivedere features/metodo)

### Caratteristiche Matrici

Per ogni matrice identificata:

**Centroide:** Valori medi features
- `avg_length`, `avg_width`, `avg_thickness`
- `avg_weight`, `avg_butt_width`, `avg_socket_width`

**Variabilità:** Coefficiente variazione (CV)
- CV < 0.03: Produzione ALTA qualità (bivalva precisa)
- CV 0.03-0.07: Produzione MEDIA qualità
- CV > 0.07: Produzione BASSA qualità (monovalva/usura)

**Tipo:** Inferito da variabilità e caratteristiche
- Bivalva: CV basso, simmetria, incavo definito
- Monovalva: CV alto, variabilità, caratteristiche meno consistenti

### Output Matrix Analysis

```json
{
  "MAT_A": {
    "matrix_id": "MAT_A",
    "artifacts_count": 23,
    "type": "bivalva",
    "avg_length": 118.5,
    "avg_weight": 395.2,
    "has_socket": true,
    "socket_profile": "circolare",
    "avg_socket_width": 8.2,
    "avg_socket_depth": 12.5,
    "weight_cv": 0.028,
    "production_quality": "ALTA",
    "description": "Matrice A, tipo bivalva con incavo circolare..."
  },
  ...
}
```

---

## Interpretazione AI con Claude

### Modello

**Model:** `claude-sonnet-4-5-20250929`
**Temperature:** 0.1 (bassa → output deterministico)
**Max Tokens:** 6000

### System Prompt

Il prompt sistema configura Claude come:
> "Archeologo specializzato nell'Età del Bronzo con expertise in metallurgia antica,
> tipologia asce metalliche, cultura Terramare (Italia settentrionale)"

### Input per AI

Claude riceve:
1. Tutti i dati quantitativi estratti
2. Risultati clustering matrici
3. Statistiche morfometriche
4. Risposte preliminari alle 6 domande
5. Contesto archeologico (letteratura, cronologia, cultura)

### Output AI

**Interpretazione strutturata** con:
- Organizzazione produttiva (artigiano singolo vs workshop)
- Funzione ripostiglio (fonditoriale/commerciale vs rituale)
- Contesto culturale (cronologia, affinità, confronti)
- Significato tecnologico (innovazioni, livello qualitativo)
- Domande aperte e ricerche future

**Formato:** Markdown con sezioni chiare

### Validazione Output

- Basato ESCLUSIVAMENTE su dati forniti
- Distingue certezze vs ipotesi vs speculazioni
- Cita letteratura pertinente (Bianco Peroni, De Marinis, Carancini)
- Evidenzia pattern statisticamente significativi

---

## Output e Risultati

### Struttura Directory Output

```
savignano_analysis_results/
│
├── features/
│   ├── savignano_morphometric_features.csv    # Tutti i parametri estratti
│   └── savignano_morphometric_features.json   # Stesso in JSON
│
├── matrices/
│   ├── matrices_summary.json                  # Info dettagliate matrici
│   ├── matrix_assignments.csv                 # Quale ascia → quale matrice
│   └── fusions_per_matrix.json                # Fusioni per matrice
│
├── archaeological_qa/
│   ├── archaeological_questions_answers.json  # Risposte 6 domande (JSON)
│   └── SAVIGNANO_ARCHAEOLOGICAL_REPORT.md     # ⭐ REPORT FINALE COMPLETO
│
├── visualizations/
│   ├── matrices_dendrogram.png                # Dendrogram clustering
│   └── matrices_pca_clusters.png              # PCA 2D visualization
│
├── ANALYSIS_SUMMARY.json                      # Summary generale
└── README.md                                  # Indice risultati
```

### File Principali da Consultare

1. **`archaeological_qa/SAVIGNANO_ARCHAEOLOGICAL_REPORT.md`**
   - Report archeologico completo in Markdown
   - Tutte le domande con risposte dettagliate
   - Interpretazione AI contestualizzata
   - **QUESTO È IL FILE PIÙ IMPORTANTE**

2. **`matrices/matrices_summary.json`**
   - Dettagli tecnici matrici identificate
   - Parametri medi, CV, tipo matrice
   - Asce appartenenti a ciascuna matrice

3. **`features/savignano_morphometric_features.csv`**
   - Dataset completo parametri morfometrici
   - Importabile in Excel, R, Python per analisi custom

4. **`visualizations/matrices_dendrogram.png`**
   - Dendrogram gerarchico
   - Visualizza relazioni tra asce
   - Identifica gruppi/matrici

---

## Esempi Pratici

### Esempio 1: Analisi Completa Base

```bash
# Setup
cd /Users/enzo/Documents/BrozeAXE-AI/archaeological-classifier
source ../.venv/bin/activate

# Esegui workflow
python savignano_complete_workflow.py \
    --meshes ~/meshes_savignano/ \
    --output ~/results_savignano/ \
    --weights-docx "~/Desktop/rif savignano/Note scansioni Artec asce Savignano.docx"

# Controlla risultati
cat ~/results_savignano/archaeological_qa/SAVIGNANO_ARCHAEOLOGICAL_REPORT.md
```

### Esempio 2: Solo Estrazione Features (No AI)

```python
from acs.savignano import batch_extract_savignano_features
import json

# Estrai features
features = batch_extract_savignano_features(
    mesh_directory='/path/to/meshes/',
    weights_dict={'974': 387.0, '942': 413.0, ...}
)

# Salva
with open('features.json', 'w') as f:
    json.dump(features, f, indent=2)
```

### Esempio 3: Analisi Matrici Standalone

```python
import pandas as pd
from acs.savignano import MatrixAnalyzer

# Carica features già estratte
features_df = pd.read_csv('savignano_morphometric_features.csv')

# Analizza matrici
analyzer = MatrixAnalyzer(features_df)
result = analyzer.identify_matrices(method='hierarchical')

print(f"Identificate {result['n_matrices']} matrici")
print(f"Silhouette score: {result['silhouette_score']:.3f}")

# Esporta
analyzer.export_results('./matrices_output/')
analyzer.plot_dendrogram('./dendrogram.png')
```

### Esempio 4: Domande Archeologiche Custom

```python
from acs.savignano import SavignanoArchaeologicalQA
import pandas as pd

# Carica dati
features_df = pd.read_csv('features.csv')
matrices_info = {...}  # Da MatrixAnalyzer

# Inizializza QA
qa = SavignanoArchaeologicalQA(
    matrices_info=matrices_info,
    features_df=features_df,
    anthropic_api_key='your-key'
)

# Rispondi a tutte le domande
answers = qa.answer_all_questions()

# Export report
qa.generate_report('SAVIGNANO_REPORT.md', format='markdown')
```

---

## Troubleshooting

### Problema: "ModuleNotFoundError: No module named 'acs'"

**Soluzione:**
```bash
cd /Users/enzo/Documents/BrozeAXE-AI/archaeological-classifier
export PYTHONPATH=$(pwd):$PYTHONPATH
```

### Problema: Mesh troppo piccole/grandi

**Sintomo:** Features estratte con valori strani (es: length=0.12 invece di 120mm)

**Causa:** Mesh in metri invece di millimetri

**Soluzione:** Il sistema converte automaticamente, ma verifica:
```python
import trimesh
mesh = trimesh.load('axe.obj')
print(f"Bounding box: {mesh.bounds}")
# Se max dimension < 1.0 → mesh in metri, viene scalata automaticamente
```

### Problema: Claude API non disponibile

**Sintomo:** `'status': 'unavailable', 'reason': 'Claude API not configured'`

**Soluzione 1:** Imposta API key
```bash
export ANTHROPIC_API_KEY="your-key"
```

**Soluzione 2:** Passa come argomento
```bash
--anthropic-api-key YOUR_KEY
```

**Nota:** Senza API key, il sistema fornisce analisi quantitativa completa ma senza interpretazione AI narrativa.

### Problema: Clustering identifica troppe/poche matrici

**Sintomo:** Silhouette score < 0.30 o numero matrici non realistico

**Soluzione:** Forza numero cluster:
```python
analyzer.identify_matrices(method='hierarchical', n_clusters=8)
```

Oppure usa K-Means:
```python
analyzer.identify_matrices(method='kmeans', n_clusters=8)
```

### Problema: Dendrogram troppo affollato

**Soluzione:** Plotta con subset asce:
```python
# Filtra top 30 asce per visualizzazione
subset_df = features_df.head(30)
analyzer_subset = MatrixAnalyzer(subset_df)
analyzer_subset.identify_matrices()
analyzer_subset.plot_dendrogram('dendrogram_subset.png')
```

---

## Riferimenti Bibliografici

### Tipologia e Metallurgia

- **Bianco Peroni, V.** (1994). *I pugnali nell'Italia continentale*. Prähistorische Bronzefunde, IV, 1. Stuttgart.

- **De Marinis, R.C.** (1977). "Il ripostiglio della Baragalla (Bibbiano, Reggio Emilia) e i ripostigli del Bronzo Finale iniziale nell'Italia settentrionale". *Preistoria Alpina*, 13, 7-36.

- **Carancini, G.L.** (1984). *Le asce nell'Italia continentale II*. Prähistorische Bronzefunde, IX, 12. München.

### Cultura Terramare

- **Bernabò Brea, M., Cardarelli, A., Cremaschi, M.** (Eds.) (1997). *Le Terramare: la più antica civiltà padana*. Milano: Electa.

### Metodologia Analisi 3D

- **Grosman, L., Karasik, A., Harush, O., Smilanski, U.** (2014). "Archaeology in three dimensions: Computer-based methods in archaeological research". *Journal of Eastern Mediterranean Archaeology & Heritage Studies*, 2(1), 48-64.

### Clustering Archeologico

- **Baxter, M.J.** (2003). *Statistics in Archaeology*. Arnold, London.

---

## Citazione Sistema

Se usi questo sistema per pubblicazioni scientifiche, cita come:

```
Archaeological Classifier System - Savignano Module (2025).
Sistema di analisi archeologica quantitativa per asce in bronzo
dell'Età del Bronzo. Version 1.0.0.
https://github.com/anthropics/archaeological-classifier-savignano
```

---

## Contatti e Supporto

Per domande, bug reports, o collaborazioni:

- **Email:** [inserire email]
- **GitHub Issues:** [inserire link repository]

---

## Licenza

[Inserire licenza appropriata - es: MIT, CC-BY-SA, etc.]

---

**Ultima revisione:** Novembre 2025
**Versione documento:** 1.0.0
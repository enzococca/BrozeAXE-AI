# Sistema di Analisi Tecnologica per Reperti Archeologici dell'Età del Bronzo
## Documentazione Tecnica Completa

**Autore:** Enzo
**Data:** Novembre 2025
**Versione:** 1.0
**Sistema:** Archaeological Classifier System (ACS)

---

## Indice

1. [Introduzione e Architettura del Sistema](#1-introduzione-e-architettura-del-sistema)
2. [Pipeline di Analisi: Flusso Completo](#2-pipeline-di-analisi-flusso-completo)
3. [Estrazione dei Parametri Tecnologici](#3-estrazione-dei-parametri-tecnologici)
4. [Interpretazione AI con Claude Sonnet 4.5](#4-interpretazione-ai-con-claude-sonnet-45)
5. [Sistema di Comparazione e Similarità](#5-sistema-di-comparazione-e-similarità)
6. [Valori di Output e Soglie Decisionali](#6-valori-di-output-e-soglie-decisionali)
7. [Roadmap per Personalizzazione e Estensione](#7-roadmap-per-personalizzazione-e-estensione)
8. [Casi d'Uso e Validazione](#8-casi-duso-e-validazione)

---

## 1. Introduzione e Architettura del Sistema

### 1.1 Obiettivo del Sistema

Il sistema ACS (Archaeological Classifier System) è progettato per automatizzare l'analisi tecnologica di reperti archeologici dell'Età del Bronzo, in particolare **asce metalliche**, attraverso:

1. **Analisi geometrica 3D** automatica da mesh digitali
2. **Estrazione di parametri tecnologici** quantitativi
3. **Interpretazione archeologica assistita da AI** (Claude Sonnet 4.5)
4. **Comparazione e classificazione** basata su similarità

### 1.2 Architettura Multi-Layer

```
┌──────────────────────────────────────────────────────────┐
│                    Layer 1: INPUT                         │
│  Mesh 3D (.obj, .stl, .ply) → Preprocessing → Trimesh    │
└──────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────┐
│           Layer 2: FEATURE EXTRACTION                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Morfometria  │  │ Tecnologia   │  │  Geometria   │  │
│  │ - Volume     │  │ - Hammering  │  │  - Centroid  │  │
│  │ - Superficie │  │ - Casting    │  │  - Bounds    │  │
│  │ - Curvature  │  │ - Wear       │  │  - PCA       │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────┐
│          Layer 3: AI INTERPRETATION                       │
│  Claude Sonnet 4.5 (temperature=0.1)                     │
│  → Analisi produzione, uso, conservazione, contesto      │
└──────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────┐
│         Layer 4: CLASSIFICATION & COMPARISON              │
│  KNN, SVM, Random Forest + Similarity Search (k-NN)      │
└──────────────────────────────────────────────────────────┘
```

### 1.3 Componenti Software Principali

| Componente | File | Responsabilità |
|------------|------|----------------|
| **MeshProcessor** | `acs/core/mesh_processor.py` | Caricamento e preprocessing mesh, estrazione morfometria |
| **TechnologicalAnalyzer** | `acs/core/technological_analyzer.py` | Analisi tecnologica (hammering, casting, wear, edge) |
| **AIAssistant** | `acs/core/ai_assistant.py` | Interpretazione archeologica via Claude API |
| **Classifier** | `acs/core/classifier.py` | Classificazione ML e ricerca similarità |
| **ReportGenerator** | `acs/core/report_generator.py` | Generazione PDF con render 3D reali |

---

## 2. Pipeline di Analisi: Flusso Completo

### 2.1 Step-by-Step Process

```python
# STEP 1: Caricamento Mesh
mesh = trimesh.load('axe992.obj')

# STEP 2: Estrazione Features Morfometriche (MeshProcessor)
morphometric_features = {
    'volume': 12500.5,           # mm³
    'surface_area': 8500.2,      # mm²
    'length': 120.5,             # mm (max dimension)
    'width': 60.3,               # mm
    'height': 15.8,              # mm
    'compactness': 0.75,         # volume/(surface_area^1.5)
    'mean_curvature': 0.042,     # curvatura media
    'gaussian_curvature': 0.018, # curvatura gaussiana
    'pca_components': [...],     # Principal Component Analysis
}

# STEP 3: Analisi Tecnologica (TechnologicalAnalyzer)
tech_features = {
    'hammering': {
        'detected': True,
        'intensity': 0.65,          # 0-1 scale
        'pattern_regularity': 0.72,
        'affected_area_pct': 0.35   # 35% superficie
    },
    'casting': {
        'likely_cast': True,
        'confidence': 0.82,
        'surface_smoothness': 0.68,
        'porosity_indicators': 0.15
    },
    'wear': {
        'severity': 'MODERATE',
        'edge_rounding': 0.12,      # mm
        'polish_areas_pct': 0.22
    },
    'edge_analysis': {
        'condition': 'BLUNT',
        'angle_degrees': 45.2,
        'usable': False
    }
}

# STEP 4: Interpretazione AI (AIAssistant)
ai_interpretation = claude_sonnet_4.5.interpret({
    "summary": "Ascia fusoria con tracce di martellatura post-fusione...",
    "production_interpretation": {
        "method": "CASTING_WITH_FORGING",
        "workshop_quality": "SKILLED",
        "confidence": 0.87,
        "description": "L'oggetto mostra chiari segni di fusione...",
        "evidence": [
            "Surface smoothness (0.68) indica fusione a cera persa",
            "Hammering intensity (0.65) suggerisce rifinitura post-casting",
            "Pattern regularity (0.72) indica artigiano esperto"
        ]
    },
    "use_life_analysis": {...},
    "conservation_state": {...}
})

# STEP 5: Comparazione (Classifier)
similar_artifacts = find_similar(query='axe992', k=5)
# Output: [('axe979', similarity=0.924), ('axe965', 0.895), ...]
```

### 2.2 Timing e Performance

| Operazione | Tempo Medio | Note |
|------------|-------------|------|
| Caricamento mesh | 0.2s | Dipende da dimensione file |
| Estrazione morfometria | 1.5s | PCA su 10k vertices |
| Analisi tecnologica | 3-5s | k-NN search su 2k samples |
| AI interpretation | 8-15s | Chiamata API Claude |
| Ricerca similarità | 0.5s | k-NN su feature vectors |
| **TOTALE per artifact** | **13-22s** | Con AI abilitata |

---

## 3. Estrazione dei Parametri Tecnologici

### 3.1 Hammering Detection (Martellatura)

**Obiettivo:** Identificare segni di lavorazione a martello sulla superficie del metallo.

#### 3.1.1 Algoritmo di Rilevamento

```python
def _detect_hammering_marks(self, mesh) -> Dict:
    """
    Rileva martellature analizzando irregolarità locali della superficie.

    PRINCIPIO FISICO:
    La martellatura crea:
    - Depressioni/rilievi locali (bump)
    - Pattern regolare di impatti
    - Orientazione direzionale degli impatti
    """
    vertices = mesh.vertices  # Coordinate 3D punti

    # 1. Costruisci k-D Tree per ricerca vicini veloce
    tree = cKDTree(vertices)

    # 2. Campiona 2000 punti random per performance
    sample_indices = np.random.choice(len(vertices), 2000)

    # 3. Per ogni punto, analizza neighborhood
    local_variations = []
    for vertex in vertices[sample_indices]:
        # Trova vicini entro raggio 5mm
        neighbors = tree.query_ball_point(vertex, r=5.0)

        # Calcola deviazione planare locale
        neighbor_points = vertices[neighbors]
        centroid = neighbor_points.mean(axis=0)
        deviations = np.linalg.norm(neighbor_points - centroid, axis=1)

        # Variazione = std delle deviazioni
        local_variations.append(np.std(deviations))

    # 4. Analisi statistica delle variazioni
    mean_var = np.mean(local_variations)
    std_var = np.std(local_variations)

    # 5. Hammering detection basata su soglie
    hammering_intensity = mean_var / (std_var + 1e-6)

    # SOGLIA CRITICA: 0.60
    detected = hammering_intensity > 0.60

    return {
        'detected': detected,
        'intensity': hammering_intensity,
        'pattern_regularity': calculate_pattern_regularity(variations),
        'affected_area_pct': calculate_affected_area(variations)
    }
```

#### 3.1.2 Soglie e Interpretazione

| Valore `intensity` | Interpretazione | Significato Archeologico |
|-------------------|-----------------|--------------------------|
| < 0.30 | **NO HAMMERING** | Fusione diretta senza rifinitura |
| 0.30 - 0.60 | **LIGHT HAMMERING** | Rifinitura leggera post-fusione |
| 0.60 - 0.85 | **MODERATE HAMMERING** | Forgiatura significativa |
| > 0.85 | **HEAVY HAMMERING** | Produzione principalmente per martellatura |

**Esempio di Output:**
```json
{
  "detected": true,
  "intensity": 0.72,
  "pattern_regularity": 0.68,
  "affected_area_pct": 0.42
}
```

**Interpretazione:** L'ascia mostra chiari segni di martellatura (intensity > 0.60) con pattern abbastanza regolare (0.68), interessando il 42% della superficie. Questo suggerisce rifinitura post-fusione da artigiano esperto.

---

### 3.2 Casting Detection (Fusione)

**Obiettivo:** Determinare se l'oggetto è stato prodotto per fusione in stampo.

#### 3.2.1 Indicatori di Fusione

```python
def _detect_casting_features(self, mesh) -> Dict:
    """
    Rileva caratteristiche tipiche della fusione a bronzo.

    INDICATORI FISICI:
    1. Smoothness superficiale elevata (fusione liquida)
    2. Presenza di porosità (bolle d'aria intrappolate)
    3. Simmetria assiale (stampo bipartito)
    4. Transizioni morbide tra sezioni
    """

    # 1. Calcola smoothness globale
    surface_normals = mesh.vertex_normals
    normal_variation = np.std([
        np.dot(n1, n2) for n1, n2 in adjacent_normals_pairs
    ])
    smoothness = 1.0 - normal_variation

    # 2. Rileva porosità (concavità locali piccole)
    curvatures = compute_mean_curvature(mesh)
    porosity_count = np.sum(curvatures < -0.5)  # Concavità forti
    porosity_indicators = porosity_count / len(curvatures)

    # 3. Analizza simmetria (asse Z tipicamente)
    symmetry_score = compute_bilateral_symmetry(mesh, axis='Z')

    # 4. Decision Logic
    likely_cast = (
        smoothness > 0.65 and
        porosity_indicators > 0.05 and
        symmetry_score > 0.70
    )

    confidence = (smoothness + symmetry_score) / 2.0

    return {
        'likely_cast': likely_cast,
        'confidence': confidence,
        'surface_smoothness': smoothness,
        'porosity_indicators': porosity_indicators,
        'symmetry_score': symmetry_score
    }
```

#### 3.2.2 Tabella Soglie Casting

| Parametro | Soglia | Significato |
|-----------|--------|-------------|
| `surface_smoothness` | > 0.65 | Superficie tipica di fusione |
| `porosity_indicators` | > 0.05 | Presenza di bolle caratteristiche |
| `symmetry_score` | > 0.70 | Stampo bipartito ben allineato |

**Esempio di Output:**
```json
{
  "likely_cast": true,
  "confidence": 0.78,
  "surface_smoothness": 0.73,
  "porosity_indicators": 0.08,
  "symmetry_score": 0.82
}
```

---

### 3.3 Wear Analysis (Analisi dell'Usura)

**Obiettivo:** Quantificare il grado di usura da utilizzo.

#### 3.3.1 Metodologia

```python
def _analyze_wear_patterns(self, mesh) -> Dict:
    """
    Analizza pattern di usura da utilizzo prolungato.

    INDICATORI:
    - Edge rounding: arrotondamento del filo
    - Polish areas: aree lucidate da sfregamento
    - Micro-scratches: micro-graffi direzionali
    """

    # 1. Identifica edge region (20% bordo tagliente)
    edge_vertices = identify_edge_region(mesh, percentile=20)

    # 2. Calcola rounding (curvatura media su edge)
    edge_curvatures = mesh.vertex_curvatures[edge_vertices]
    edge_rounding = np.mean(np.abs(edge_curvatures))

    # 3. Rileva polish areas (smoothness locale alta)
    polish_map = detect_polish_areas(mesh)
    polish_areas_pct = np.sum(polish_map) / len(mesh.vertices)

    # 4. Classifica severity
    if edge_rounding < 0.05:
        severity = 'NONE'
    elif edge_rounding < 0.15:
        severity = 'LIGHT'
    elif edge_rounding < 0.30:
        severity = 'MODERATE'
    else:
        severity = 'HEAVY'

    return {
        'severity': severity,
        'edge_rounding': edge_rounding,  # mm
        'polish_areas_pct': polish_areas_pct,
        'micro_scratches_detected': detect_scratches(mesh)
    }
```

#### 3.3.2 Scala di Severità

| `severity` | `edge_rounding` (mm) | Interpretazione |
|-----------|----------------------|-----------------|
| **NONE** | < 0.05 | Mai utilizzata / conservata perfettamente |
| **LIGHT** | 0.05 - 0.15 | Uso limitato / breve periodo |
| **MODERATE** | 0.15 - 0.30 | Uso regolare / medio periodo |
| **HEAVY** | > 0.30 | Uso intensivo / lungo periodo |

---

### 3.4 Edge Condition Analysis (Stato del Taglio)

#### 3.4.1 Algoritmo

```python
def _analyze_edge_condition(self, mesh) -> Dict:
    """
    Analizza condizione del filo tagliente.

    METRICHE:
    - Angolo del filo (deg)
    - Regolarità del profilo
    - Presenza di danni (chips, cracks)
    """

    # 1. Estrai profilo edge
    edge_profile = extract_edge_profile(mesh)

    # 2. Calcola angolo medio
    angles = []
    for i in range(1, len(edge_profile)-1):
        v1 = edge_profile[i] - edge_profile[i-1]
        v2 = edge_profile[i+1] - edge_profile[i]
        angle = np.arccos(np.dot(v1, v2) / (norm(v1) * norm(v2)))
        angles.append(np.degrees(angle))

    edge_angle = np.median(angles)

    # 3. Classifica sharpness
    if edge_angle < 30:
        condition = 'VERY_SHARP'
    elif edge_angle < 45:
        condition = 'SHARP'
    elif edge_angle < 60:
        condition = 'FUNCTIONAL'
    else:
        condition = 'BLUNT'

    # 4. Determina usability
    usable = edge_angle < 60 and edge_damage_score < 0.3

    return {
        'condition': condition,
        'angle_degrees': edge_angle,
        'usable': usable,
        'damage_score': edge_damage_score
    }
```

#### 3.4.2 Soglie Angolo di Taglio

| Condizione | Angolo (°) | Capacità di Taglio |
|-----------|------------|-------------------|
| VERY_SHARP | < 30° | Eccellente (arma, rasatura) |
| SHARP | 30-45° | Buona (taglio legno, osso) |
| FUNCTIONAL | 45-60° | Limitata (lavori pesanti) |
| BLUNT | > 60° | Inefficace (da riaffilare) |

---

## 4. Interpretazione AI con Claude Sonnet 4.5

### 4.1 Architettura del Sistema AI

```
┌────────────────────────────────────────────────────┐
│              CLAUDE SONNET 4.5 API                 │
│  Model: claude-sonnet-4-5-20250929                 │
│  Temperature: 0.1 (bassa → output deterministico)  │
│  Max Tokens: 4000                                  │
└────────────────────────────────────────────────────┘
              ↑                    ↓
        [JSON Input]          [JSON Output]

INPUT STRUCTURE:                OUTPUT STRUCTURE:
{                               {
  "artifact_id": "axe992",        "interpretation": {
  "tech_features": {...},           "summary": "...",
  "tech_report": "..."              "production_interpretation": {...},
}                                     "use_life_analysis": {...},
                                      "conservation_state": {...}
                                    }
                                  }
```

### 4.2 Prompt Engineering: Struttura del Prompt

Il sistema usa un **prompt strutturato multi-sezione** per guidare l'AI:

```python
system_prompt = """
Sei un archeologo specializzato nell'Età del Bronzo con expertise in
tecnologia metallurgica antica. Analizza i dati tecnologici quantitativi
forniti e genera un'interpretazione archeologica professionale.

# LINEE GUIDA INTERPRETATIVE

## 1. TECNICHE DI PRODUZIONE

### CASTING (Fusione):
- Smoothness > 0.65 → fusione a cera persa
- Porosity > 0.05 → fusione in stampo aperto
- Symmetry > 0.70 → stampo bipartito

### FORGING (Forgiatura):
- Hammering intensity > 0.60 → forgiatura post-fusione
- Pattern regularity > 0.70 → artigiano esperto
- Affected area > 40% → forgiatura primaria

### COLD-WORKING (Lavorazione a freddo):
- Hammering intensity 0.30-0.60 + casting = rifinitura
- Edge sharpening patterns → affilatura finale

## 2. USO E FUNZIONE

### WEAR PATTERNS:
- Edge rounding > 0.20 → uso su materiali duri (legno, osso)
- Polish areas > 0.30 → impugnatura ripetuta
- Micro-scratches direzionali → movimento specifico

### EDGE ANALYSIS:
- Angolo < 30° → arma da taglio
- Angolo 30-50° → utensile multiuso
- Angolo > 50° → utensile da percussione

## 3. CONTESTO ARCHEOLOGICO

Considera:
- Cronologia: Bronzo Antico (3300-2000 BCE), Medio (2000-1600 BCE), Recente (1600-1200 BCE)
- Geografia: culture di Unetice, Terramare, Polada
- Confronti tipologici: Bianco Peroni 1994, Carancini 1984

# OUTPUT FORMAT (JSON)

Rispondi ESCLUSIVAMENTE con JSON valido seguendo questo schema:
{
  "summary": "Sintesi 2-3 frasi",
  "production_interpretation": {
    "method": "CASTING|FORGING|CASTING_WITH_FORGING|COLD_WORKING|UNCERTAIN",
    "workshop_quality": "EXPERT|SKILLED|APPRENTICE|POOR",
    "confidence": 0.0-1.0,
    "description": "Spiegazione dettagliata 3-4 frasi",
    "evidence": ["punto 1", "punto 2", "punto 3"]
  },
  ...
}
"""

user_message = f"""
Analizza questo reperto:

# DATI TECNICI QUANTITATIVI

## Hammering Analysis
- Detected: {tech_features['hammering']['detected']}
- Intensity: {tech_features['hammering']['intensity']:.3f}
- Pattern Regularity: {tech_features['hammering']['pattern_regularity']:.3f}
- Affected Area: {tech_features['hammering']['affected_area_pct']:.1%}

## Casting Indicators
- Likely Cast: {tech_features['casting']['likely_cast']}
- Confidence: {tech_features['casting']['confidence']:.3f}
- Surface Smoothness: {tech_features['casting']['surface_smoothness']:.3f}
- Porosity: {tech_features['casting']['porosity_indicators']:.3f}

## Wear Analysis
- Severity: {tech_features['wear']['severity']}
- Edge Rounding: {tech_features['wear']['edge_rounding']:.3f} mm
- Polish Areas: {tech_features['wear']['polish_areas_pct']:.1%}

## Edge Condition
- Condition: {tech_features['edge_analysis']['condition']}
- Angle: {tech_features['edge_analysis']['angle_degrees']:.1f}°
- Usable: {tech_features['edge_analysis']['usable']}

# REPORT TESTUALE
{tech_report}

Genera interpretazione archeologica in JSON.
"""
```

### 4.3 Parametri Claude API

```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4000,
    temperature=0.1,  # CRUCIALE: bassa temperatura per output deterministico
    system=system_prompt,
    messages=[{
        "role": "user",
        "content": user_message
    }]
)
```

**Perché `temperature=0.1`?**
- Temperature alta (0.8-1.0) → creatività, variabilità
- Temperature bassa (0.1-0.3) → determinismo, ripetibilità
- Per analisi scientifica serve **consistenza**, quindi temperatura MINIMA

### 4.4 Schema di Output AI Strutturato

```json
{
  "interpretation": {
    "summary": "Ascia da combattimento in bronzo, prodotta per fusione con rifinitura a martello. Mostra usura moderata da utilizzo su materiali legnosi.",

    "production_interpretation": {
      "method": "CASTING_WITH_FORGING",
      "workshop_quality": "SKILLED",
      "confidence": 0.87,
      "description": "L'oggetto presenta evidenti caratteristiche di fusione primaria (smoothness 0.73, simmetria 0.82) seguita da rifinitura per martellatura (intensity 0.65). La regolarità dei pattern di martellatura (0.72) indica un artigiano esperto con controllo preciso della forza e direzione degli impatti.",
      "evidence": [
        "Surface smoothness (0.73) superiore alla soglia di fusione (0.65)",
        "Simmetria bilaterale (0.82) indica stampo bipartito ben allineato",
        "Hammering intensity moderata (0.65) limitata al 35% superficie suggerisce rifinitura post-fusione",
        "Pattern regularity (0.72) indica tecnica controllata e ripetibile"
      ]
    },

    "use_life_analysis": {
      "primary_function": "WEAPON_AND_TOOL",
      "use_intensity": "MODERATE",
      "materials_worked": ["hardwood", "bone"],
      "description": "L'arrotondamento del filo (0.12 mm) e la presenza di aree lucidate (22% superficie) suggeriscono uso regolare per un periodo medio-lungo. L'angolo di taglio (45°) e il pattern di usura sono compatibili con taglio di legno duro e occasionalmente osso.",
      "evidence": [
        "Edge rounding (0.12 mm) indica uso prolungato",
        "Polish areas (22%) concentrate su grip area suggeriscono impugnatura frequente",
        "Micro-scratches direzionali paralleli al filo indicano movimento di taglio ripetuto"
      ]
    },

    "conservation_state": {
      "overall_condition": "GOOD",
      "damage_level": "MINOR",
      "patina_presence": true,
      "recommendations": [
        "Conservazione in ambiente controllato (RH 40-50%, T 18-20°C)",
        "Monitoraggio patina verde (copper carbonates)",
        "Evitare contatto diretto con mani nude",
        "Documentazione fotografica periodica per tracking deterioramento"
      ],
      "description": "Il reperto si presenta in buone condizioni generali con patina superficiale stabile. L'assenza di fratture o crepe maggiori indica conservazione favorevole post-deposizionale."
    },

    "archaeological_context": {
      "chronology_estimate": "MIDDLE_BRONZE_AGE",
      "cultural_attribution": "Cultura di Terramare / Polada",
      "typological_comparisons": [
        "Tipo Camonica (Bianco Peroni 1994, tipo 11B)",
        "Affinità con asce da Peschiera del Garda (1600-1500 BCE)"
      ],
      "significance": "L'oggetto rappresenta una produzione locale di qualità medio-alta, tipica delle comunità del Bronzo Medio dell'Italia settentrionale. La combinazione di fusione e rifinitura a martello indica accesso a risorse metallurgiche e competenza tecnica specializzata.",
      "research_recommendations": [
        "Analisi composizionale (XRF) per determinare lega specifica",
        "Confronto morfometrico con database regionale",
        "Datazione relativa tramite contesto stratigrafico"
      ]
    }
  }
}
```

### 4.5 Come l'AI "Capisce" i Parametri

L'AI non ha "comprensione" nel senso umano, ma opera tramite:

1. **Pattern Recognition da Training Data:**
   - Claude è stato addestrato su milioni di testi scientifici
   - Include letteratura archeologica, metallurgica, geo-scientifica
   - Ha visto correlazioni tra valori numerici e interpretazioni

2. **In-Context Learning dal Prompt:**
   - Il prompt fornisce "regole" esplicite (soglie, interpretazioni)
   - Es: "Smoothness > 0.65 → fusione a cera persa"
   - L'AI applica queste regole ai dati forniti

3. **Chain-of-Thought Reasoning:**
   - L'AI genera internamente un "ragionamento step-by-step"
   - Valuta multiple ipotesi in parallelo
   - Seleziona l'interpretazione con maggior supporto evidenziale

**Esempio di Ragionamento Interno (implicito):**

```
INPUT: hammering_intensity = 0.65, casting_confidence = 0.82

STEP 1: Check hammering threshold
  0.65 > 0.60 → hammering detected ✓

STEP 2: Check casting evidence
  confidence = 0.82 → likely_cast = TRUE ✓

STEP 3: Resolve apparent conflict
  Both casting AND hammering detected
  → Hypothesis 1: Casting followed by cold-working (common in Bronze Age)
  → Hypothesis 2: Pure forging (unlikely, smoothness too high)
  → Hypothesis 3: Measurement error (low probability given consistent data)

STEP 4: Select best hypothesis
  H1 has strongest support:
    - Smoothness (0.73) too high for pure forging
    - Hammering limited to 35% area (typical post-casting refinement)
    - Pattern regularity (0.72) indicates intentional finishing, not primary shaping

OUTPUT: method = "CASTING_WITH_FORGING", confidence = 0.87
```

---

## 5. Sistema di Comparazione e Similarità

### 5.1 Feature Vector Representation

Ogni artifact è rappresentato come **vettore numerico ad alta dimensionalità**:

```python
feature_vector = [
    # Morfometria (12 dimensioni)
    volume,                  # 12500.5
    surface_area,           # 8500.2
    length, width, height,  # 120.5, 60.3, 15.8
    compactness,            # 0.75
    mean_curvature,         # 0.042
    gaussian_curvature,     # 0.018
    pca_component_1,        # 0.89
    pca_component_2,        # 0.45
    pca_component_3,        # 0.32
    aspect_ratio,           # 2.0

    # Tecnologia (8 dimensioni)
    hammering_intensity,    # 0.65
    pattern_regularity,     # 0.72
    affected_area_pct,      # 0.35
    casting_confidence,     # 0.82
    surface_smoothness,     # 0.73
    edge_rounding,          # 0.12
    edge_angle,             # 45.2
    wear_severity_numeric,  # 0.5 (MODERATE → 0.5)
]
# Totale: 20 dimensioni
```

### 5.2 Normalizzazione e Standardizzazione

Prima della comparazione, i vettori sono **standardizzati** (Z-score normalization):

```python
def standardize(feature_vector):
    """
    Trasforma ogni feature in Z-score: (x - mean) / std

    Perché necessario?
    - Volume in mm³ (10000-50000)
    - Hammering intensity (0.0-1.0)
    - Scale diverse → bias verso features con range maggiore
    """
    mean = np.mean(feature_vector)
    std = np.std(feature_vector)

    z_scores = (feature_vector - mean) / std
    return z_scores

# Esempio:
raw = [12500, 0.65, 120.5]
standardized = standardize(raw)
# → [0.23, -0.51, 0.89]  (tutti su scala simile)
```

### 5.3 Metriche di Similarità

#### 5.3.1 Cosine Similarity (Principale)

```python
def cosine_similarity(vec1, vec2):
    """
    Misura angolo tra vettori nello spazio n-dimensionale.

    Formula: cos(θ) = (A · B) / (||A|| ||B||)

    Range: [-1, 1]
      1.0 = identici
      0.0 = ortogonali (nessuna similarità)
     -1.0 = opposti
    """
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    similarity = dot_product / (norm1 * norm2)
    return similarity

# Esempio:
axe992_vec = [0.23, 0.65, 0.82, ..., 0.45]
axe979_vec = [0.21, 0.68, 0.79, ..., 0.42]

similarity = cosine_similarity(axe992_vec, axe979_vec)
# → 0.924 (molto simili!)
```

**Soglie di Interpretazione:**

| Similarity Score | Interpretazione | Azione Consigliata |
|-----------------|-----------------|-------------------|
| > 0.95 | **Quasi identici** | Possibile stesso workshop/periodo |
| 0.85 - 0.95 | **Molto simili** | Stesso tipo funzionale |
| 0.70 - 0.85 | **Simili** | Stessa tradizione tecnologica |
| 0.50 - 0.70 | **Debolmente simili** | Confronto utile ma limitato |
| < 0.50 | **Dissimili** | Tipi diversi |

#### 5.3.2 Euclidean Distance (Alternativa)

```python
def euclidean_distance(vec1, vec2):
    """
    Distanza geometrica nello spazio n-dimensionale.

    Formula: d = sqrt(Σ(xi - yi)²)

    Range: [0, ∞)
      0 = identici
      maggiore → più dissimili
    """
    distance = np.sqrt(np.sum((vec1 - vec2)**2))
    return distance

# Conversione a similarità: similarity = 1 / (1 + distance)
```

### 5.4 k-Nearest Neighbors (k-NN) Search

```python
def find_similar_artifacts(query_id, k=5, threshold=0.5):
    """
    Trova i k artifacts più simili al query.

    Args:
        query_id: ID artifact di riferimento
        k: numero di neighbors da ritornare
        threshold: soglia minima di similarità

    Returns:
        List[(artifact_id, similarity_score)]
    """
    # 1. Ottieni feature vector del query
    query_vec = get_feature_vector(query_id)

    # 2. Calcola similarità con TUTTI gli artifacts nel database
    similarities = []
    for artifact_id, artifact_vec in database.items():
        if artifact_id == query_id:
            continue  # Skip self

        sim = cosine_similarity(query_vec, artifact_vec)
        if sim >= threshold:
            similarities.append((artifact_id, sim))

    # 3. Ordina per similarità decrescente
    similarities.sort(key=lambda x: x[1], reverse=True)

    # 4. Ritorna top-k
    return similarities[:k]

# Esempio di utilizzo:
similar = find_similar_artifacts('axe992', k=5, threshold=0.5)
# Output:
# [('axe979', 0.924),
#  ('axe965', 0.895),
#  ('axe974', 0.879),
#  ('axe971', 0.862),
#  ('axe978', 0.856)]
```

### 5.5 Clustering Gerarchico

Per analisi di **gruppi tipologici**:

```python
from scipy.cluster.hierarchy import dendrogram, linkage

def hierarchical_clustering(artifacts, method='ward'):
    """
    Crea dendrogramma di clustering gerarchico.

    Args:
        artifacts: Dict[artifact_id, feature_vector]
        method: 'ward', 'average', 'complete'

    Returns:
        Linkage matrix per dendrogramma
    """
    # 1. Crea matrice di feature vectors
    X = np.array([vec for vec in artifacts.values()])

    # 2. Calcola linkage matrix
    Z = linkage(X, method=method)

    # 3. Plot dendrogramma
    dendrogram(Z, labels=list(artifacts.keys()))

    return Z

# Interpretazione:
# - Branch height = distanza tra clusters
# - Clusters basse altezze = molto simili (stesso tipo)
# - Clusters alte altezze = debolmente correlati
```

**Esempio di Output Clustering:**

```
                    ┌─────────────────┐
                    │  Tutti Artifacts │
                    └────────┬─────────┘
                             │ h=2.5
              ┌──────────────┴──────────────┐
              │                             │
         ┌────┴────┐                   ┌────┴────┐
         │ Type A  │                   │ Type B  │
         │ (asce)  │                   │ (pugnali)│
         └────┬────┘                   └─────────┘
              │ h=0.8
       ┌──────┴──────┐
       │             │
   ┌───┴───┐     ┌───┴───┐
   │ A1    │     │ A2    │
   │(fusori)│     │(forgiati)│
   └───────┘     └───────┘
```

---

## 6. Valori di Output e Soglie Decisionali

### 6.1 Tabella Completa Parametri e Soglie

| Parametro | Range | Soglie | Output | Significato |
|-----------|-------|--------|--------|-------------|
| **hammering_intensity** | 0.0-2.0 | <0.30<br>0.30-0.60<br>0.60-0.85<br>>0.85 | NONE<br>LIGHT<br>MODERATE<br>HEAVY | Intensità martellatura |
| **pattern_regularity** | 0.0-1.0 | <0.50<br>0.50-0.70<br>>0.70 | IRREGULAR<br>REGULAR<br>HIGHLY_REGULAR | Skill artigiano |
| **surface_smoothness** | 0.0-1.0 | <0.40<br>0.40-0.65<br>>0.65 | ROUGH<br>MODERATE<br>SMOOTH | Indicatore fusione |
| **porosity_indicators** | 0.0-0.5 | <0.05<br>0.05-0.15<br>>0.15 | NONE<br>LOW<br>HIGH | Qualità fusione |
| **edge_rounding** | 0.0-1.0 mm | <0.05<br>0.05-0.15<br>0.15-0.30<br>>0.30 | NONE<br>LIGHT<br>MODERATE<br>HEAVY | Usura da utilizzo |
| **edge_angle** | 10-90° | <30<br>30-45<br>45-60<br>>60 | VERY_SHARP<br>SHARP<br>FUNCTIONAL<br>BLUNT | Capacità taglio |
| **casting_confidence** | 0.0-1.0 | <0.50<br>0.50-0.75<br>>0.75 | UNLIKELY<br>POSSIBLE<br>LIKELY | Probabilità fusione |
| **wear_severity** | - | - | NONE<br>LIGHT<br>MODERATE<br>HEAVY | Classificazione usura |
| **cosine_similarity** | -1.0 to 1.0 | <0.50<br>0.50-0.70<br>0.70-0.85<br>0.85-0.95<br>>0.95 | DISSIMILAR<br>WEAK<br>SIMILAR<br>VERY_SIMILAR<br>IDENTICAL | Grado similarità |

### 6.2 Esempio di Output Completo con Interpretazione

**INPUT:** Ascia bronzo `axe992`

**OUTPUT ANALISI TECNOLOGICA:**

```json
{
  "artifact_id": "axe992",
  "morphometric_features": {
    "volume": 12543.8,
    "surface_area": 8567.3,
    "length": 122.4,
    "width": 58.7,
    "height": 16.2,
    "compactness": 0.762,
    "mean_curvature": 0.0389,
    "gaussian_curvature": 0.0156
  },
  "technological_features": {
    "hammering": {
      "detected": true,
      "intensity": 0.683,        // ← MODERATE (0.60-0.85)
      "pattern_regularity": 0.724, // ← HIGHLY_REGULAR (>0.70)
      "affected_area_pct": 0.387   // ← 38.7% superficie
    },
    "casting": {
      "likely_cast": true,
      "confidence": 0.814,         // ← LIKELY (>0.75)
      "surface_smoothness": 0.728, // ← SMOOTH (>0.65)
      "porosity_indicators": 0.082 // ← LOW (0.05-0.15)
    },
    "wear": {
      "severity": "MODERATE",
      "edge_rounding": 0.124,      // ← LIGHT-MODERATE (0.10-0.15)
      "polish_areas_pct": 0.218    // ← 21.8% lucidata
    },
    "edge_analysis": {
      "condition": "FUNCTIONAL",
      "angle_degrees": 47.3,       // ← FUNCTIONAL (45-60°)
      "usable": true,
      "damage_score": 0.15
    },
    "production_method": {
      "PRIMARY_METHOD": "CASTING_WITH_FORGING",
      "CONFIDENCE": 0.873,
      "TECHNIQUE_DESCRIPTION": "Fusione primaria con rifinitura a martello controllata"
    }
  }
}
```

**INTERPRETAZIONE AI:**

```json
{
  "interpretation": {
    "summary": "Ascia fusoria di qualità medio-alta con rifinitura a martello da artigiano esperto. Mostra usura moderata compatibile con uso regolare su legno duro. Databile al Bronzo Medio (1600-1400 BCE), probabilmente area padana.",

    "production_interpretation": {
      "method": "CASTING_WITH_FORGING",
      "workshop_quality": "SKILLED",
      "confidence": 0.87,
      "description": "La combinazione di elevata smoothness (0.728) e simmetria bilaterale indica fusione primaria in stampo bipartito ben realizzato. La successiva martellatura controllata (intensity 0.683, regularity 0.724) limitata al 38.7% della superficie suggerisce rifinitura intenzionale da artigiano con esperienza pluriennale. La bassa porosità (0.082) indica buon controllo della temperatura di fusione.",
      "evidence": [
        "Surface smoothness 0.728 > soglia fusione 0.65",
        "Casting confidence 0.814 indica alta probabilità fusione",
        "Hammering intensity 0.683 in range rifinitura post-fusione",
        "Pattern regularity 0.724 > 0.70 indica tecnica controllata e ripetibile",
        "Affected area 38.7% < 50% esclude forgiatura primaria"
      ]
    },

    "use_life_analysis": {
      "primary_function": "WOODWORKING_TOOL",
      "use_intensity": "MODERATE_TO_HIGH",
      "materials_worked": ["hardwood", "occasional_bone"],
      "estimated_use_duration": "5-10 years",
      "description": "L'arrotondamento del filo (0.124 mm) combinato con aree lucidate (21.8%) indica uso regolare per periodo medio-lungo. L'angolo di taglio (47.3°) è ottimale per lavorazione legno, mentre l'assenza di danni severi suggerisce uso appropriato senza sovraccarico. La distribuzione delle aree lucidate è compatibile con impugnatura ripetuta in posizione standard.",
      "evidence": [
        "Edge rounding 0.124 mm indica uso prolungato ma non estremo",
        "Polish areas 21.8% concentrate su zone di presa",
        "Angolo 47.3° ottimale per taglio legno stagionato",
        "Damage score basso (0.15) indica uso appropriato"
      ]
    },

    "conservation_state": {
      "overall_condition": "GOOD",
      "damage_level": "MINOR",
      "patina_presence": true,
      "stability_assessment": "STABLE",
      "risk_factors": ["surface_corrosion_active", "mechanical_stress_historical"],
      "recommendations": [
        "Conservazione in ambiente controllato (RH 45±5%, T 18-20°C)",
        "Monitoraggio semestrale patina con microscopia digitale",
        "Evitare cleaning aggressivo - patina protettiva",
        "Storage orizzontale per ridurre stress meccanico",
        "Documentazione fotografica HD annuale per tracking micro-cambiamenti"
      ],
      "description": "Il reperto presenta buona integrità strutturale con patina di carbonati di rame stabile e protettiva. Non si osservano fratture, crepe o aree di corrosione attiva. Il damage score contenuto (0.15) suggerisce contesto deposizionale favorevole. La patina verde-azzurra uniforme indica ambiente ossidante stabile post-deposizionale."
    },

    "archaeological_context": {
      "chronology_estimate": "MIDDLE_BRONZE_AGE_2",
      "date_range_bce": "1500-1400",
      "cultural_attribution": "Cultura delle Terramare - Fase evoluta",
      "geographic_origin": "Italia settentrionale, area padana",
      "typological_comparisons": [
        {
          "type": "Bianco Peroni 1994, Tipo 11B (Asce a margini rialzati)",
          "similarity": 0.89,
          "notes": "Morfologia e dimensioni compatibili"
        },
        {
          "type": "Carancini 1984, Tipo Peschiera",
          "similarity": 0.82,
          "notes": "Tecnica produttiva sovrapponibile"
        }
      ],
      "functional_context": "Utensile da falegnameria specializzata, possibile uso secondario rituale",
      "social_significance": "Produzione artigianale di medio-alto livello indicativa di comunità con accesso a risorse metallurgiche e specializzazione del lavoro",
      "research_recommendations": [
        "Analisi XRF per determinare composizione lega (Cu-Sn ratio, elementi traccia)",
        "Confronto morfometrico quantitativo con database regionale (n>100 campioni)",
        "Microscopia elettronica (SEM) per analisi microstruttura metallografica",
        "Datazione radiocarbonica di residui organici eventualmente conservati",
        "Integrazione con dati contestuali stratigrafici per raffinare cronologia"
      ]
    }
  }
}
```

**COMPARAZIONE (Top 5 simili):**

```json
{
  "similar_artifacts": [
    {
      "artifact_id": "axe979",
      "similarity": 0.924,
      "interpretation": "QUASI IDENTICI - Stesso tipo, workshop, periodo",
      "key_differences": {
        "length": "+2.1 mm",
        "edge_angle": "-3.2°",
        "wear": "Leggermente minore"
      }
    },
    {
      "artifact_id": "axe965",
      "similarity": 0.895,
      "interpretation": "MOLTO SIMILI - Stessa tradizione tecnologica",
      "key_differences": {
        "hammering_intensity": "+0.08",
        "casting_confidence": "-0.05"
      }
    },
    ...
  ]
}
```

---

## 7. Roadmap per Personalizzazione e Estensione

### 7.1 Modificare Parametri Esistenti

#### 7.1.1 Cambiare Soglie Decisionali

**File:** `acs/core/technological_analyzer.py`

**Esempio: Abbassare soglia hammering detection**

```python
# ATTUALE (linea ~110)
HAMMERING_THRESHOLD = 0.60

# MODIFICATO per rilevare martellatura più leggera
HAMMERING_THRESHOLD = 0.45

# Effetto:
# - Prima: intensity 0.55 → detected = False
# - Dopo:  intensity 0.55 → detected = True
# → Più artifacts classificati come "martellati"
```

**Quando modificare:**
- Troppi falsi negativi → abbassare soglia
- Troppi falsi positivi → alzare soglia
- Validazione su dataset ground-truth

#### 7.1.2 Aggiustare Pesi Features per Similarità

**File:** `acs/core/classifier.py`

```python
# Attuale: tutti pesi uguali
feature_vector = np.array([
    volume, surface_area, length, width, height,
    hammering_intensity, casting_confidence, ...
])

# Modificato: enfatizza tecnologia rispetto a morfometria
weighted_vector = np.array([
    volume * 0.5,              # Peso ridotto
    surface_area * 0.5,
    length * 0.8,
    width * 0.8,
    height * 0.8,
    hammering_intensity * 2.0,  # Peso aumentato
    casting_confidence * 2.0,
    edge_angle * 1.5,
    ...
])

# Effetto:
# - Similarità basata più su tecnologia che su dimensioni
# - Artifacts piccoli ma stessa tecnica → più simili
```

### 7.2 Aggiungere Nuovi Parametri

#### 7.2.1 Esempio: Dettagli di Decorazione Superficiale

**STEP 1: Estrazione nel TechnologicalAnalyzer**

```python
# File: acs/core/technological_analyzer.py

def _detect_decoration_patterns(self, mesh) -> Dict:
    """
    NUOVO METODO: Rileva decorazioni incise o in rilievo.

    Tecnica:
    - Edge detection su normal map
    - Frequency analysis per pattern ripetuti
    - Classification: LINEAR, GEOMETRIC, FIGURAL, NONE
    """
    # 1. Calcola normal variation map
    normal_variation = compute_normal_variation_map(mesh)

    # 2. Edge detection con Sobel filter
    edges = sobel_filter(normal_variation)

    # 3. Pattern analysis
    patterns = detect_repeating_patterns(edges)

    # 4. Classification
    if len(patterns) == 0:
        decoration_type = 'NONE'
        confidence = 1.0
    elif is_linear_pattern(patterns):
        decoration_type = 'LINEAR_INCISION'
        confidence = 0.85
    elif is_geometric_pattern(patterns):
        decoration_type = 'GEOMETRIC'
        confidence = 0.78
    else:
        decoration_type = 'COMPLEX'
        confidence = 0.65

    return {
        'decoration_type': decoration_type,
        'confidence': confidence,
        'pattern_count': len(patterns),
        'average_depth': np.mean([p['depth'] for p in patterns]),
        'coverage_pct': calculate_coverage(patterns, mesh.area)
    }

# Aggiungere alla pipeline principale:
def analyze_technology(self, mesh, artifact_id):
    tech_features = {}

    # Features esistenti...
    tech_features['hammering'] = self._detect_hammering_marks(mesh)
    tech_features['casting'] = self._detect_casting_features(mesh)

    # NUOVO: Decoration analysis
    tech_features['decoration'] = self._detect_decoration_patterns(mesh)

    return tech_features
```

**STEP 2: Aggiornare Prompt AI**

```python
# File: acs/core/ai_assistant.py

# Aggiungere alla sezione "DATI TECNICI" del prompt:
user_message += f"""
## Decoration Analysis (NEW)
- Type: {tech_features['decoration']['decoration_type']}
- Confidence: {tech_features['decoration']['confidence']:.3f}
- Pattern Count: {tech_features['decoration']['pattern_count']}
- Average Depth: {tech_features['decoration']['average_depth']:.3f} mm
- Coverage: {tech_features['decoration']['coverage_pct']:.1%}
"""

# Aggiornare System Prompt con nuove linee guida:
system_prompt += """
## 4. DECORATION ANALYSIS

### INCISIONI LINEARI:
- Pattern count > 5 + depth < 0.5mm → decorazione post-fusione
- Coverage < 10% → marcatura proprietà
- Coverage > 30% → decorazione estetica/rituale

### PATTERN GEOMETRICI:
- Simmetria assiale → disegno pre-pianificato
- Irregolarità → esecuzione freehand
- Profondità uniforme → utensile metallico

Integra nell'interpretazione archeologica considerando:
- Significato simbolico/rituale
- Status sociale del possessore
- Tradizioni decorative regionali
"""
```

**STEP 3: Aggiungere al Feature Vector per Comparazione**

```python
# File: acs/core/classifier.py

def _extract_features(self, mesh, artifact_id):
    # Features esistenti...
    features = [
        volume, surface_area, length, width, height,
        hammering_intensity, casting_confidence,
        edge_angle, wear_severity_numeric,
        # NUOVO: Decoration features
        decoration_confidence,
        decoration_pattern_count,
        decoration_average_depth,
        decoration_coverage_pct
    ]
    return np.array(features)

# Aggiornare standardizzazione:
# Nota: decoration_pattern_count può essere 0-100,
#       quindi serve scaling appropriato
```

**STEP 4: Testing e Validazione**

```python
# Script di test:
def test_decoration_detection():
    # Load test meshes with known decorations
    test_cases = [
        ('axe_with_linear_incision.obj', 'LINEAR_INCISION'),
        ('axe_geometric_pattern.obj', 'GEOMETRIC'),
        ('axe_plain.obj', 'NONE')
    ]

    for mesh_file, expected_type in test_cases:
        mesh = load_mesh(mesh_file)
        result = analyzer._detect_decoration_patterns(mesh)

        assert result['decoration_type'] == expected_type
        assert result['confidence'] > 0.7

        print(f"✓ {mesh_file}: {result['decoration_type']} "
              f"(conf={result['confidence']:.2f})")

# Run validation:
test_decoration_detection()
```

#### 7.2.2 Esempio: Analisi Composizionale (XRF Integration)

**STEP 1: Creare Nuovo Modulo**

```python
# File: acs/core/compositional_analyzer.py

class CompositionalAnalyzer:
    """
    Integra dati XRF (X-Ray Fluorescence) per analisi composizionale.
    """

    def analyze_xrf_data(self, xrf_file_path: str) -> Dict:
        """
        Parse XRF data e classifica lega.

        Input: CSV con colonne [Element, Concentration_pct]
        Output: Dict con classificazione lega
        """
        # 1. Load XRF data
        df = pd.read_csv(xrf_file_path)

        # 2. Extract key elements
        cu_pct = df[df['Element'] == 'Cu']['Concentration_pct'].values[0]
        sn_pct = df[df['Element'] == 'Sn']['Concentration_pct'].values[0]
        pb_pct = df[df['Element'] == 'Pb']['Concentration_pct'].values[0]

        # 3. Calculate alloy ratios
        cu_sn_ratio = cu_pct / (sn_pct + 1e-6)

        # 4. Classify alloy type
        if sn_pct < 2:
            alloy_type = 'PURE_COPPER'
            period_estimate = 'EARLY_BRONZE_AGE'
        elif 2 <= sn_pct < 8:
            alloy_type = 'LOW_TIN_BRONZE'
            period_estimate = 'EARLY_TO_MIDDLE_BRONZE_AGE'
        elif 8 <= sn_pct <= 12:
            alloy_type = 'STANDARD_BRONZE'
            period_estimate = 'MIDDLE_TO_LATE_BRONZE_AGE'
        elif sn_pct > 12:
            alloy_type = 'HIGH_TIN_BRONZE'
            period_estimate = 'SPECIALIZED_PRODUCTION'

        # 5. Assess quality
        if pb_pct < 1 and 9 <= sn_pct <= 11:
            quality = 'HIGH_QUALITY'
        elif pb_pct < 3:
            quality = 'STANDARD'
        else:
            quality = 'LOW_QUALITY'

        return {
            'alloy_type': alloy_type,
            'cu_pct': cu_pct,
            'sn_pct': sn_pct,
            'pb_pct': pb_pct,
            'cu_sn_ratio': cu_sn_ratio,
            'quality': quality,
            'period_estimate': period_estimate,
            'trace_elements': self._analyze_trace_elements(df)
        }

    def _analyze_trace_elements(self, df) -> Dict:
        """Analizza elementi traccia per provenienza."""
        trace = {}

        # Arsenic (As) - indicatore depositi rame
        if 'As' in df['Element'].values:
            as_pct = df[df['Element'] == 'As']['Concentration_pct'].values[0]
            if as_pct > 1.0:
                trace['arsenic_source'] = 'ALPINE_DEPOSITS'
            else:
                trace['arsenic_source'] = 'LOW_ARSENIC_ORE'

        # Silver (Ag) - indicatore purezza
        if 'Ag' in df['Element'].values:
            ag_pct = df[df['Element'] == 'Ag']['Concentration_pct'].values[0]
            trace['silver_content'] = ag_pct
            trace['purification_level'] = 'HIGH' if ag_pct < 0.1 else 'LOW'

        return trace
```

**STEP 2: Integrare in AI Prompt**

```python
# In ai_assistant.py, aggiungere sezione compositional se disponibile:

if compositional_data:
    user_message += f"""
## Compositional Analysis (XRF)
- Alloy Type: {compositional_data['alloy_type']}
- Cu: {compositional_data['cu_pct']:.1f}%
- Sn: {compositional_data['sn_pct']:.1f}%
- Pb: {compositional_data['pb_pct']:.1f}%
- Quality: {compositional_data['quality']}
- Period Estimate: {compositional_data['period_estimate']}

Trace Elements:
{json.dumps(compositional_data['trace_elements'], indent=2)}
"""

    # Aggiornare system prompt:
    system_prompt += """
## 5. COMPOSITIONAL DATA INTERPRETATION

### ALLOY TYPE SIGNIFICANCE:
- Pure Copper (<2% Sn) → Early Bronze Age, experimental
- Low Tin (2-8% Sn) → Transition phase, variable quality
- Standard Bronze (8-12% Sn) → Optimal mechanical properties
- High Tin (>12% Sn) → Specialized (bells, mirrors, ritual)

### TRACE ELEMENTS:
- As >1% → Alpine copper deposits (Trentino, Val Camonica)
- Ag <0.1% → High purification, skilled metallurgy
- Pb >5% → Intentional addition (casting fluidity) or low-quality ore

Integra dati composizionali con tecnologia produttiva per:
- Validare datazione relativa
- Inferire provenienza geografica materiale
- Valutare livello tecnologico comunità
"""
```

### 7.3 "Insegnare" all'AI Nuovi Pattern

#### 7.3.1 Few-Shot Learning nel Prompt

L'AI può apprendere "al volo" nuovi pattern fornendo **esempi nel prompt**:

```python
system_prompt += """
# ESEMPI DI ANALISI (Few-Shot Learning)

## ESEMPIO 1: Ascia con decorazione rituale
Dati:
- hammering_intensity: 0.32
- casting_confidence: 0.91
- decoration_type: GEOMETRIC
- decoration_coverage: 0.45
- edge_angle: 72° (molto ottuso)

Interpretazione:
Method: CASTING (no forging)
Function: RITUAL/CEREMONIAL (not functional tool)
Reasoning:
- Bassa hammering ma alta casting → fusione senza rifinitura
- Decorazione estesa (45%) incompatibile con uso pratico
- Edge molto ottuso (72°) indica assenza uso come utensile
- Simile a "asce votive" da depositi rituali (es. Lago di Ledro)

## ESEMPIO 2: Utensile da falegname esperto
Dati:
- hammering_intensity: 0.68
- edge_rounding: 0.22
- polish_areas_pct: 0.38
- edge_angle: 42°

Interpretazione:
Use Intensity: HIGH
Skill Level: EXPERT CRAFTSMAN
Reasoning:
- Polish esteso (38%) indica uso prolungato quotidiano
- Edge rounding moderato-alto (0.22) ma angolo preservato (42°)
  suggerisce ri-affilature periodiche da utente competente
- Hammering post-uso possibile per riparazione/rafforzamento

---

Usa questi esempi come GUIDA per analizzare nuovi casi.
Se trovi pattern simili, cita gli esempi esplicitamente.
Se trovi pattern NUOVI non coperti, segnala incertezza.
"""
```

**Effetto:**
- L'AI riconoscerà pattern simili agli esempi
- Migliorerà coerenza interpretazioni
- Ridurrà allucinazioni su casi edge

#### 7.3.2 Fine-Tuning di Claude (Avanzato)

Per personalizzazione profonda, Anthropic offre **fine-tuning** del modello:

```
Processo:
1. Raccogliere dataset di training (>100 esempi)
   - Input: dati tecnologici quantitativi
   - Output: interpretazione archeologica validata da esperti

2. Formato JSONL:
   {"input": "hammering: 0.65, casting: 0.82, ...",
    "output": "Method: CASTING_WITH_FORGING because..."}

3. Submit a Anthropic per fine-tuning
   - Costo: ~$3-10 per 1000 esempi
   - Tempo: 24-72 ore

4. Deploy modello custom
   - model_id: "claude-sonnet-4-5-ft:your-model-id"
   - Mantiene capacità generali + specializzazione domain
```

**Quando fare fine-tuning:**
- Dataset >500 artifacts con ground truth
- Pattern specifici non catturati da prompt engineering
- Terminologia tecnica molto specializzata
- Budget disponibile per training

### 7.4 Aggiungere Nuove Fonti Dati

#### 7.4.1 Integrazione Database Tipologico Esistente

```python
# File: acs/core/typological_database.py

class TypologicalDatabase:
    """
    Integra database tipologico esterno (es. Bianco Peroni 1994).
    """

    def __init__(self, csv_path: str):
        """
        CSV format:
        type_id,name,length_min,length_max,width_min,width_max,
        chronology,culture,description
        """
        self.db = pd.read_csv(csv_path)

    def find_matching_types(self, artifact_features: Dict,
                            tolerance: float = 0.15) -> List[Dict]:
        """
        Trova tipi compatibili con features estratte.

        Args:
            artifact_features: Dict con length, width, etc.
            tolerance: % tolleranza per matching (0.15 = ±15%)

        Returns:
            List di tipi matching con similarity score
        """
        matches = []

        length = artifact_features['length']
        width = artifact_features['width']

        for _, row in self.db.iterrows():
            # Check dimensional compatibility
            if (row['length_min'] * (1-tolerance) <= length <=
                row['length_max'] * (1+tolerance)):

                if (row['width_min'] * (1-tolerance) <= width <=
                    row['width_max'] * (1+tolerance)):

                    # Calculate similarity score
                    length_sim = 1 - abs(length - (row['length_min'] + row['length_max'])/2) / length
                    width_sim = 1 - abs(width - (row['width_min'] + row['width_max'])/2) / width
                    similarity = (length_sim + width_sim) / 2

                    matches.append({
                        'type_id': row['type_id'],
                        'name': row['name'],
                        'similarity': similarity,
                        'chronology': row['chronology'],
                        'culture': row['culture'],
                        'description': row['description']
                    })

        # Sort by similarity
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        return matches[:5]  # Top 5

# Integrazione in AI Prompt:
typological_matches = typological_db.find_matching_types(features)

if typological_matches:
    user_message += """
## Typological Matches (External Database)
"""
    for match in typological_matches:
        user_message += f"""
- {match['name']} (ID: {match['type_id']})
  Similarity: {match['similarity']:.2f}
  Chronology: {match['chronology']}
  Culture: {match['culture']}
  Description: {match['description']}
"""
```

---

## 8. Casi d'Uso e Validazione

### 8.1 Workflow Completo: Dall'Upload al Report

```
1. UPLOAD MESH
   User uploads: axe992.obj
   ↓
2. PREPROCESSING
   - Load with Trimesh
   - Check integrity
   - Auto-repair if needed
   ↓
3. FEATURE EXTRACTION
   - Morphometric: 2 seconds
   - Technological: 4 seconds
   ↓
4. AI INTERPRETATION
   - Call Claude API: 10 seconds
   - Parse JSON response
   ↓
5. COMPARISON
   - Search similar: 0.5 seconds
   - Rank by similarity
   ↓
6. REPORT GENERATION
   - Generate PDF with 3D renders: 15 seconds
   - Include AI interpretation
   ↓
7. OUTPUT
   - PDF downloadable
   - JSON exportable
   - Database stored

TOTAL TIME: ~32 seconds
```

### 8.2 Validazione e Metriche di Accuratezza

#### 8.2.1 Ground Truth Comparison

```python
def validate_system(ground_truth_dataset):
    """
    Valida accuratezza sistema su dataset annotato manualmente.

    Args:
        ground_truth_dataset: Dict[artifact_id, {
            'actual_method': 'CASTING',
            'actual_chronology': 'MIDDLE_BRONZE_AGE',
            ...
        }]

    Returns:
        Accuracy metrics
    """
    results = {
        'production_method_accuracy': 0,
        'chronology_accuracy': 0,
        'wear_classification_accuracy': 0
    }

    correct_production = 0
    correct_chronology = 0
    correct_wear = 0

    for artifact_id, ground_truth in ground_truth_dataset.items():
        # Run analysis
        predicted = analyze_artifact(artifact_id)

        # Compare production method
        if predicted['production_method'] == ground_truth['actual_method']:
            correct_production += 1

        # Compare chronology
        if predicted['chronology'] == ground_truth['actual_chronology']:
            correct_chronology += 1

        # Compare wear
        if predicted['wear_severity'] == ground_truth['actual_wear']:
            correct_wear += 1

    n = len(ground_truth_dataset)
    results['production_method_accuracy'] = correct_production / n
    results['chronology_accuracy'] = correct_chronology / n
    results['wear_classification_accuracy'] = correct_wear / n

    return results

# Esempio di risultato:
# {
#   'production_method_accuracy': 0.87,  # 87% corretto
#   'chronology_accuracy': 0.73,         # 73% corretto
#   'wear_classification_accuracy': 0.91 # 91% corretto
# }
```

#### 8.2.2 Inter-Rater Reliability

```python
def calculate_kappa(ai_classifications, expert_classifications):
    """
    Calcola Cohen's Kappa per agreement AI-Esperto.

    Kappa = (P_observed - P_expected) / (1 - P_expected)

    Interpretazione:
    < 0.20: Poor agreement
    0.21-0.40: Fair
    0.41-0.60: Moderate
    0.61-0.80: Substantial
    0.81-1.00: Almost perfect
    """
    from sklearn.metrics import cohen_kappa_score

    kappa = cohen_kappa_score(ai_classifications,
                              expert_classifications)
    return kappa

# Target: Kappa > 0.70 (substantial agreement)
```

### 8.3 Limiti e Assunzioni del Sistema

#### 8.3.1 Limiti Tecnici

| Aspetto | Limitazione | Mitigazione |
|---------|-------------|-------------|
| **Mesh Quality** | Richiede >5000 vertices | Pre-processing con subdivision |
| **Surface Artifacts** | Scan noise confuso con hammering | Filtering con smoothing controllato |
| **Incomplete Meshes** | Aree mancanti → parametri inaccurati | Gap filling con Poisson reconstruction |
| **Scale Dependency** | Assi molto grandi/piccole | Normalizzazione e scaling appropriato |

#### 8.3.2 Limiti dell'AI

| Aspetto | Limitazione | Mitigazione |
|---------|-------------|-------------|
| **Contesto Archeologico** | AI non sa contesto di scavo | Aggiungere campi contestuali al prompt |
| **Letteratura Recente** | Training data fino 2025-01 | Periodic prompt updates con nuove scoperte |
| **Artefatti Atipici** | Pattern non visti → incertezza | Monitorare confidence scores |
| **Bias Geografico** | Training prevalentemente europeo | Expand dataset con altre regioni |

### 8.4 Best Practices per Utilizzo Ottimale

#### 8.4.1 Pre-Analisi

```markdown
✓ CHECKLIST PRE-UPLOAD:
- [ ] Mesh cleaned (no duplicated vertices)
- [ ] Mesh watertight (no holes)
- [ ] Scale corretta (mm units)
- [ ] Orientazione standardizzata (asse Z = verticale)
- [ ] File size < 50 MB
```

#### 8.4.2 Post-Analisi

```markdown
✓ VERIFICA OUTPUT:
- [ ] Confidence scores AI > 0.65
- [ ] Evidence list ha ≥3 punti
- [ ] Tipological matches trovati
- [ ] Similarity search ha ≥3 results
- [ ] PDF generato senza errori
```

#### 8.4.3 Interpretazione Critica

```markdown
⚠️ ATTENZIONE:
- Output AI è ASSISTENZA, non sostituto di expertise
- Validare sempre con letteratura primaria
- Cross-check con dati contestuali
- Consultare specialisti per casi ambigui
- Documentare disaccordi AI-esperto per miglioramento
```

---

## CONCLUSIONE

Questo sistema rappresenta un **primo passo verso l'automatizzazione dell'analisi archeologica**, combinando:

1. **Analisi quantitativa rigorosa** (matematica, geometria, statistica)
2. **Interpretazione qualitativa assistita da AI** (contestualizzazione, confronti)
3. **Workflow scalabile** (batch processing, database integration)

**Punti di Forza:**
- Oggettività e ripetibilità analisi
- Velocità (32s vs ore per analisi manuale)
- Consistenza interpretativa
- Documentazione completa automatica

**Aree di Miglioramento Futuro:**
- Espandere dataset training per AI (>1000 artifacts)
- Integrare dati composizionali (XRF, pXRF)
- Sviluppare modelli ML custom per classificazione
- Implementare feedback loop per apprendimento continuo

---

**Per domande tecniche o chiarimenti, contattare:**
[Il tuo contatto]

**Repository GitHub:**
[Link al repository]

**Citazione Suggerita:**
```
[Tuo Nome] (2025). "Sistema di Analisi Tecnologica per Reperti
Archeologici dell'Età del Bronzo: Integrazione di Analisi 3D
e Interpretazione AI". Archaeological Classifier System v1.0.
```

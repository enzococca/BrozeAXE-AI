-- ============================================================================
-- SAVIGNANO AXES ANALYSIS - EXPANDED DATABASE SCHEMA
-- ============================================================================
-- Schema per analisi approfondita delle asce del ripostiglio di Savignano
-- Include parametri morfometrici specifici, analisi matrici, e risposte
-- alle domande archeologiche chiave
-- ============================================================================

-- Tabella 1: Parametri morfometrici specifici per asce Savignano
CREATE TABLE IF NOT EXISTS savignano_morphometrics (
    artifact_id TEXT PRIMARY KEY,

    -- Dati generali
    inventory_number TEXT UNIQUE,  -- Es: "974", "942", "965", etc.
    peso REAL,  -- Peso in grammi
    scan_date TEXT,  -- Data scansione

    -- TALLONE (top end)
    tallone_larghezza REAL,  -- Larghezza tallone (mm)
    tallone_spessore REAL,  -- Spessore tallone (mm)

    -- INCAVO nel tallone (caratteristica distintiva Savignano)
    incavo_presente INTEGER DEFAULT 0,  -- Boolean: 0=no, 1=yes
    incavo_larghezza REAL,  -- Larghezza incavo (mm)
    incavo_profondita REAL,  -- Profondità incavo (mm)
    incavo_profilo TEXT,  -- 'rettangolare', 'circolare', 'assente'

    -- MARGINI RIALZATI (raised edges)
    margini_rialzati_presenti INTEGER DEFAULT 0,
    margini_rialzati_lunghezza REAL,  -- Lunghezza margini (mm)
    margini_rialzati_spessore_max REAL,  -- Spessore massimo margini (mm)

    -- CORPO ascia
    larghezza_minima REAL,  -- Larghezza minima corpo (mm)
    spessore_massimo_con_margini REAL,  -- Spessore max includendo margini (mm)
    spessore_massimo_senza_margini REAL,  -- Spessore max corpo senza margini (mm)

    -- TAGLIENTE (cutting edge)
    tagliente_larghezza REAL,  -- Larghezza tagliente (mm)
    tagliente_forma TEXT,  -- 'arco_ribassato', 'semicircolare', 'lunato'
    tagliente_arco_misura REAL,  -- Misurazione arco (mm)
    tagliente_corda_misura REAL,  -- Misurazione corda (mm)
    tagliente_espanso INTEGER DEFAULT 0,  -- Boolean: tagliente espanso

    -- Metadati
    extraction_date TEXT DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,  -- Note aggiuntive

    FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id) ON DELETE CASCADE
);

-- Tabella 2: Matrici identificate (molds analysis)
CREATE TABLE IF NOT EXISTS savignano_matrices (
    matrix_id TEXT PRIMARY KEY,
    matrix_name TEXT NOT NULL,  -- Es: "Matrice A", "Matrice B", etc.

    -- Caratteristiche distintive matrice
    type TEXT,  -- 'monovalva', 'bivalva'
    incisione_margini INTEGER DEFAULT 0,  -- Presenza incisione margini
    tallone_preparation TEXT,  -- Tipo preparazione tallone

    -- Parametri medi matrice (centroide)
    avg_length REAL,
    avg_width REAL,
    avg_thickness REAL,
    avg_weight REAL,
    avg_incavo_width REAL,
    avg_incavo_depth REAL,

    -- Statistiche
    artifacts_count INTEGER DEFAULT 0,  -- N. asce da questa matrice
    confidence_score REAL,  -- Confidenza clustering (0-1)
    variability_coefficient REAL,  -- Coefficiente variazione intra-matrice

    -- Caratteristiche dettagliate (JSON)
    characteristics_json TEXT,  -- JSON con caratteristiche morfologiche

    -- Metadati
    identified_date TEXT DEFAULT CURRENT_TIMESTAMP,
    identification_method TEXT,  -- 'clustering_kmeans', 'hierarchical', 'manual'

    UNIQUE(matrix_name)
);

-- Tabella 3: Associazione asce-matrici
CREATE TABLE IF NOT EXISTS savignano_matrix_artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id TEXT NOT NULL,
    matrix_id TEXT NOT NULL,

    -- Metriche associazione
    similarity_to_matrix_center REAL,  -- Similarità al centroide (0-1)
    distance_from_center REAL,  -- Distanza euclidea dal centroide
    assignment_confidence REAL,  -- Confidenza assegnazione (0-1)

    -- Numero fusione stimato per questa matrice
    estimated_fusion_number INTEGER,  -- Es: 1a, 2a, 3a fusione da matrice X

    -- Metadati
    assignment_date TEXT DEFAULT CURRENT_TIMESTAMP,
    assignment_method TEXT,  -- 'automatic', 'validated', 'manual'
    validator_notes TEXT,

    FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id) ON DELETE CASCADE,
    FOREIGN KEY (matrix_id) REFERENCES savignano_matrices(matrix_id) ON DELETE CASCADE,
    UNIQUE(artifact_id, matrix_id)
);

-- Tabella 4: Analisi tecnologica specifica Savignano
CREATE TABLE IF NOT EXISTS savignano_technological_analysis (
    artifact_id TEXT PRIMARY KEY,

    -- MARTELLATURA (hammering)
    martellatura_presente INTEGER DEFAULT 0,
    martellatura_intensita REAL,  -- 0-1 scale
    martellatura_pattern TEXT,  -- 'regolare', 'irregolare', 'assente'
    martellatura_aree TEXT,  -- JSON: zone con martellatura

    -- BARRA CENTRALE (central bar/ridge)
    barra_centrale_presente INTEGER DEFAULT 0,
    barra_centrale_altezza REAL,  -- Altezza barra (mm)
    barra_centrale_larghezza REAL,  -- Larghezza barra (mm)

    -- TRATTAMENTO TALLONE
    tallone_trattamento TEXT,  -- 'levigato', 'martellato', 'grezzo'
    tallone_incavo_funzione TEXT,  -- Interpretazione funzione incavo

    -- RIFINITURA TAGLIENTE
    tagliente_rifinitura TEXT,  -- 'affilato', 'smussato', 'non_rifinito'
    tagliente_affilatura_tecnica TEXT,  -- 'martellatura', 'abrasione', 'mista'
    tagliente_simmetria REAL,  -- Simmetria tagliente (0-1)

    -- TRACCE D'USO
    uso_presente INTEGER DEFAULT 0,  -- Boolean: tracce uso visibili
    uso_intensita TEXT,  -- 'nullo', 'leggero', 'moderato', 'intenso'
    uso_tipo TEXT,  -- 'legno', 'osso', 'pietra', 'metallo', 'misto', 'indeterminato'
    uso_pattern TEXT,  -- Descrizione pattern usura

    -- CONSERVAZIONE
    conservazione_stato TEXT,  -- 'ottimo', 'buono', 'discreto', 'scarso'
    conservazione_patina TEXT,  -- Descrizione patina
    conservazione_danni TEXT,  -- JSON: descrizione danni

    -- Metadati
    analysis_date TEXT DEFAULT CURRENT_TIMESTAMP,
    analyzer TEXT,  -- Chi ha fatto analisi
    notes TEXT,

    FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id) ON DELETE CASCADE
);

-- Tabella 5: Risposte alle domande archeologiche
CREATE TABLE IF NOT EXISTS archaeological_questions_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_date TEXT DEFAULT CURRENT_TIMESTAMP,
    dataset_size INTEGER,  -- N. asce analizzate

    -- DOMANDA 1: Numero matrici e caratteristiche
    question_1_matrices_count INTEGER,
    question_1_details_json TEXT,  -- JSON dettagliato matrici
    -- Struttura JSON:
    -- {
    --   "matrices": [
    --     {
    --       "id": "MAT_A",
    --       "name": "Matrice A - Bivalva con incavo rettangolare",
    --       "type": "bivalva",
    --       "artifacts_count": 23,
    --       "characteristics": {...}
    --     },
    --     ...
    --   ],
    --   "summary": "Identificate X matrici distinte..."
    -- }

    -- DOMANDA 2: Fusioni per matrice
    question_2_fusions_per_matrix_json TEXT,
    -- Struttura JSON:
    -- {
    --   "MAT_A": {
    --     "estimated_fusions": 23,
    --     "artifacts": ["974", "942", ...],
    --     "confidence": 0.87,
    --     "notes": "Basato su micro-variazioni morfometriche..."
    --   },
    --   ...
    -- }

    -- DOMANDA 3: Trattamenti post-fusione
    question_3_treatments_json TEXT,
    -- Struttura JSON:
    -- {
    --   "hammering_statistics": {
    --     "present": 62,
    --     "absent": 34,
    --     "average_intensity": 0.65,
    --     ...
    --   },
    --   "central_bar_usage": {...},
    --   "butt_treatments": {...}
    -- }

    -- DOMANDA 4: Rifinitura finale
    question_4_finishing_json TEXT,
    -- Dettagli rifinitura tagliente e tallone

    -- DOMANDA 5: Funzione incavo tallone
    question_5_incavo_analysis_json TEXT,
    -- Analisi funzionale incavo

    -- DOMANDA 6: Intensità uso
    question_6_usage_analysis_json TEXT,
    -- Analisi tracce d'uso

    -- Interpretazione AI completa
    ai_interpretation_json TEXT,
    -- Interpretazione archeologica completa da Claude

    -- Metadati
    analysis_version TEXT,  -- Versione software
    confidence_overall REAL,  -- Confidenza complessiva (0-1)
    validated INTEGER DEFAULT 0,  -- Se validato da archeologo
    validator_name TEXT,
    validator_notes TEXT
);

-- Tabella 6: Dati scansione 3D (metadati tecnici)
CREATE TABLE IF NOT EXISTS savignano_scan_metadata (
    artifact_id TEXT PRIMARY KEY,

    -- Dati scansione
    scan_date TEXT,
    scanner_model TEXT DEFAULT 'Artec',
    scan_resolution REAL DEFAULT 0.15,  -- mm

    -- Parametri scansione
    num_scans INTEGER DEFAULT 4,  -- Numero riprese (fronte, retro, bordo1, bordo2)
    registration_type TEXT,  -- 'separate', 'collective'
    outlier_removal_level REAL,  -- Valore outlier removal usato
    fusion_resolution REAL,  -- Max mesh resolution (mm)

    -- Qualità scansione
    mesh_quality TEXT,  -- 'ottima', 'buona', 'sufficiente', 'scarsa'
    problematic_areas TEXT,  -- JSON: aree critiche (es. tagliente, tallone)

    -- File output
    mesh_file_path TEXT,
    texture_file_path TEXT,

    -- Note tecniche
    technical_notes TEXT,
    scanned_by TEXT,  -- Operatore

    FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id) ON DELETE CASCADE
);

-- ============================================================================
-- INDICI per performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_savignano_morpho_inventory ON savignano_morphometrics(inventory_number);
CREATE INDEX IF NOT EXISTS idx_savignano_morpho_peso ON savignano_morphometrics(peso);
CREATE INDEX IF NOT EXISTS idx_savignano_morpho_incavo ON savignano_morphometrics(incavo_presente);

CREATE INDEX IF NOT EXISTS idx_matrices_artifacts_count ON savignano_matrices(artifacts_count);
CREATE INDEX IF NOT EXISTS idx_matrices_confidence ON savignano_matrices(confidence_score);

CREATE INDEX IF NOT EXISTS idx_matrix_artifacts_artifact ON savignano_matrix_artifacts(artifact_id);
CREATE INDEX IF NOT EXISTS idx_matrix_artifacts_matrix ON savignano_matrix_artifacts(matrix_id);
CREATE INDEX IF NOT EXISTS idx_matrix_artifacts_similarity ON savignano_matrix_artifacts(similarity_to_matrix_center);

CREATE INDEX IF NOT EXISTS idx_tech_analysis_uso ON savignano_technological_analysis(uso_presente);
CREATE INDEX IF NOT EXISTS idx_tech_analysis_martellatura ON savignano_technological_analysis(martellatura_presente);

CREATE INDEX IF NOT EXISTS idx_scan_meta_date ON savignano_scan_metadata(scan_date);
CREATE INDEX IF NOT EXISTS idx_scan_meta_quality ON savignano_scan_metadata(mesh_quality);

-- ============================================================================
-- VIEWS utili per query veloci
-- ============================================================================

-- View 1: Vista completa per ogni ascia
CREATE VIEW IF NOT EXISTS v_savignano_complete AS
SELECT
    a.artifact_id,
    a.mesh_path,
    sm.inventory_number,
    sm.peso,
    sm.tallone_larghezza,
    sm.tallone_spessore,
    sm.incavo_presente,
    sm.incavo_larghezza,
    sm.incavo_profondita,
    sm.incavo_profilo,
    sm.tagliente_larghezza,
    sm.tagliente_forma,
    sta.martellatura_presente,
    sta.martellatura_intensita,
    sta.uso_intensita,
    sta.uso_tipo,
    ma.matrix_id,
    ma.similarity_to_matrix_center,
    ssm.scan_date,
    ssm.mesh_quality
FROM artifacts a
LEFT JOIN savignano_morphometrics sm ON a.artifact_id = sm.artifact_id
LEFT JOIN savignano_technological_analysis sta ON a.artifact_id = sta.artifact_id
LEFT JOIN savignano_matrix_artifacts ma ON a.artifact_id = ma.artifact_id
LEFT JOIN savignano_scan_metadata ssm ON a.artifact_id = ssm.artifact_id;

-- View 2: Statistiche per matrice
CREATE VIEW IF NOT EXISTS v_matrix_statistics AS
SELECT
    m.matrix_id,
    m.matrix_name,
    m.type,
    m.artifacts_count,
    m.confidence_score,
    AVG(sm.peso) as avg_weight,
    STDEV(sm.peso) as weight_stddev,
    AVG(sm.tallone_larghezza) as avg_butt_width,
    AVG(sm.incavo_profondita) as avg_socket_depth,
    COUNT(CASE WHEN sta.uso_presente = 1 THEN 1 END) as axes_with_use_traces,
    COUNT(CASE WHEN sta.martellatura_presente = 1 THEN 1 END) as axes_with_hammering
FROM savignano_matrices m
LEFT JOIN savignano_matrix_artifacts ma ON m.matrix_id = ma.matrix_id
LEFT JOIN savignano_morphometrics sm ON ma.artifact_id = sm.artifact_id
LEFT JOIN savignano_technological_analysis sta ON ma.artifact_id = sta.artifact_id
GROUP BY m.matrix_id;

-- View 3: Asce con incavo
CREATE VIEW IF NOT EXISTS v_axes_with_socket AS
SELECT
    sm.artifact_id,
    sm.inventory_number,
    sm.peso,
    sm.incavo_larghezza,
    sm.incavo_profondita,
    sm.incavo_profilo,
    sta.tallone_incavo_funzione,
    ma.matrix_id
FROM savignano_morphometrics sm
LEFT JOIN savignano_technological_analysis sta ON sm.artifact_id = sta.artifact_id
LEFT JOIN savignano_matrix_artifacts ma ON sm.artifact_id = ma.artifact_id
WHERE sm.incavo_presente = 1;

-- ============================================================================
-- TRIGGER per mantenere consistenza
-- ============================================================================

-- Trigger: Aggiorna conteggio artifacts in savignano_matrices
CREATE TRIGGER IF NOT EXISTS update_matrix_count_insert
AFTER INSERT ON savignano_matrix_artifacts
BEGIN
    UPDATE savignano_matrices
    SET artifacts_count = (
        SELECT COUNT(*)
        FROM savignano_matrix_artifacts
        WHERE matrix_id = NEW.matrix_id
    )
    WHERE matrix_id = NEW.matrix_id;
END;

CREATE TRIGGER IF NOT EXISTS update_matrix_count_delete
AFTER DELETE ON savignano_matrix_artifacts
BEGIN
    UPDATE savignano_matrices
    SET artifacts_count = (
        SELECT COUNT(*)
        FROM savignano_matrix_artifacts
        WHERE matrix_id = OLD.matrix_id
    )
    WHERE matrix_id = OLD.matrix_id;
END;

-- ============================================================================
-- COMMENTI E DOCUMENTAZIONE
-- ============================================================================

-- Questo schema supporta:
-- 1. Analisi morfometrica dettagliata secondo standard Savignano
-- 2. Identificazione e tracking matrici di fusione
-- 3. Analisi tecnologica approfondita (martellatura, rifinitura, uso)
-- 4. Risposte strutturate alle 6 domande archeologiche chiave
-- 5. Metadati scansione 3D per tracciabilità

-- Per uso:
-- 1. Importare schema: sqlite3 database.db < savignano_schema.sql
-- 2. Popolare dati con script Python di estrazione features
-- 3. Eseguire analisi matrici con clustering algorithms
-- 4. Generare risposte archeologiche con AI (Claude)
-- 5. Validare risultati con archeologo esperto
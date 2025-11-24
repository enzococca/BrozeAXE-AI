# BrozeAXE-AI: Workflow Semplificato

**Versione:** 2.0 - Semplificato
**Data:** 24 Novembre 2025

---

## 🎯 Workflow in 6 Passi

```
1. Login → 2. Scegli Progetto → 3. Upload File → 4. Genera Report → 5. Visualizza/Compara → 6. Training (Auto)
```

---

## 📖 Guida Passo-Passo

### **Passo 1: Login**
```
URL: http://localhost:5001/web/login
Credenziali: admin / admin123
```

### **Passo 2: Scegli o Crea Progetto**
```
Dashboard → Projects (📁)
→ Click su progetto esistente
OPPURE
→ Click "+" per creare nuovo progetto
```

**Creare Progetto:**
- Project ID: `Savignano2025` (identificativo unico)
- Nome: `Asce di Savignano`
- Descrizione: opzionale

### **Passo 3: Upload File 3D**
```
Dalla pagina progetto → Click "📤 Upload"
OPPURE
Dashboard → Upload Artifact
```

**Formati supportati:** `.obj`, `.stl`, `.ply`
**Limite:** 100MB per file (web), 500MB (API)

**Cosa succede automaticamente:**
- ✅ File salvato nel database
- ✅ 36+ features estratte (volume, dimensioni, ecc.)
- ✅ Features Savignano specifiche (angolo filo, simmetria, ecc.)
- ✅ Dati pronti per analisi

### **Passo 4: Genera Report Completo**
```
Dalla pagina progetto → Click "📊 Report"
OPPURE
Dashboard → Savignano Comprehensive Report
```

**Configurazione Report:**
1. **Seleziona Artifacts:** Spunta quali asce includere nel report
2. **API Key Claude:** Inserisci se vuoi analisi AI (opzionale)
3. **Lingua:** Italiano (default)
4. **Opzioni:**
   - ✅ PCA e Clustering
   - ✅ Hammering Analysis
   - ✅ Casting Analysis
5. Click "Generate Report"

**Output PDF Include:**
- 📊 Analisi AI delle caratteristiche tecnologiche
- 📈 PCA (Principal Component Analysis) + grafico
- 🌳 Clustering gerarchico (dendrogramma)
- 🔨 Analisi martellatura (hammering patterns)
- 🔥 Analisi fusione (casting marks)
- 📐 Visualizzazioni 3D
- 📋 Tabella comparativa features
- 📊 Statistiche descrittive

**Sistema Salva Automaticamente:**
- Classificazioni AI → tabella `classifications`
- Features → tabella `features`
- Analisi → tabella `stylistic_features`

### **Passo 5: Visualizza e Compara**
```
Dashboard → 3D Viewer
OPPURE
Dashboard → Savignano Compare
```

**Funzioni:**
- 👀 Visualizza modelli 3D interattivi
- ⚖️ Compara 2+ artifacts side-by-side
- 📊 Overlay grafici differenze
- 📐 Misure comparative

### **Passo 6: Training ML (Automatico)**
```
Sistema fa training automatico quando:
- Hai 20+ artifacts classificati
- Hai validato le classificazioni
```

**Cosa fa il sistema:**
1. Raccoglie tutti gli artifacts validati
2. Estrae feature vectors
3. Training modello ML (PCA + Classifier)
4. Valida con cross-validation
5. Deploy modello per auto-classificazione

**Puoi monitorare:**
```
Data Explorer → Training Data
→ Vedi samples usati per training
→ Controlla accuracy modello
```

---

## 🗂️ Struttura Progetti

### Come Funzionano i Progetti

**Progetto = Contenitore logico per artifacts correlati**

Esempio:
```
Progetto: "Savignano2025"
├── axe_001.obj
├── axe_002.obj
├── axe_003.obj
└── axe_007.obj
```

**Benefici:**
- ✅ Organizzazione: tutti gli artifacts insieme
- ✅ Report per progetto: analisi solo artifacts del progetto
- ✅ Comparazioni: confronti all'interno dello stesso contesto
- ✅ Gestione: facile archiviazione/eliminazione

### Gestione Progetti

**Visualizza tutti i progetti:**
```
Dashboard → Projects (📁)
```

**Ogni progetto mostra:**
- 📊 Numero artifacts
- ✅ Classificazioni totali
- ✔️ Classificazioni validate
- 📅 Data creazione

**Azioni progetto:**
- 📤 Upload → Carica nuovi file nel progetto
- 📊 Report → Genera report per il progetto
- 🗑️ Delete → Elimina progetto (e tutti gli artifacts)

---

## 🔍 Dove Trovare i Dati

### **Data Explorer (Tutto in un posto)**
```
URL: http://localhost:5001/web/data-explorer
```

**6 Sezioni:**

#### 1. **Overview**
- Statistiche sistema
- Link rapidi a tutte le funzioni

#### 2. **Artifacts**
- Lista paginata (20/pagina)
- Ricerca per ID/filename
- Filtro per progetto
- Click artifact → Vedi features

#### 3. **Features**
- Visualizza tutte le features estratte
- Morfometriche + Savignano
- Valori precisi per ogni parametro

#### 4. **Training Data**
- Samples usati per ML
- Artifacts con classificazione validata
- Gestione training set

#### 5. **Reports**
- Links ai generatori
- Guida step-by-step

#### 6. **Users** (solo Admin)
- Gestione utenti
- Cambio ruoli

---

## 📊 Report Generator - Dettagli

### Selezione Artifacts

**Il Report Generator adesso permette di:**
1. ✅ Vedere SOLO gli artifacts del progetto corrente
2. ✅ Selezionare quali includere nel report
3. ✅ Generare report parziale (solo alcuni artifacts)
4. ✅ Generare report completo (tutti)

**Come funziona:**
```
1. Apri Report Generator dal progetto
2. Vedi lista artifacts del progetto
3. Checkbox per ogni artifact
4. Click "Select All" o seleziona manualmente
5. Generate Report
```

---

## 🔄 Workflow Completo - Esempio Reale

### **Scenario: Nuovo Studio Asce Savignano**

**Step 1: Setup (2 min)**
```
1. Login: admin/admin123
2. Dashboard → Projects → "+"
3. Crea: "Savignano2025"
```

**Step 2: Upload Dati (5 min)**
```
1. Dalla pagina progetto → Upload
2. Seleziona 7 file .obj
3. Upload automatico
4. Sistema estrae features
```

**Step 3: Verifica Dati (5 min)**
```
1. Data Explorer → Artifacts
2. Filtra per "Savignano2025"
3. Click su ogni artifact → Verifica features OK
```

**Step 4: Genera Report (10 min)**
```
1. Torna al progetto → Report
2. Seleziona tutti 7 artifacts
3. Inserisci Claude API key (se hai)
4. Enable tutte le analisi
5. Generate Report
```

**Step 5: Analizza PDF (20 min)**
```
1. Download PDF generato
2. Leggi:
   - Analisi AI: tipologia, periodo, tecnica
   - PCA: raggruppamenti naturali
   - Clustering: relazioni tra artifacts
   - Hammering: tecniche di lavorazione
   - Casting: segni di fusione
```

**Step 6: Compara (10 min)**
```
1. Dashboard → Savignano Compare
2. Seleziona 2 artifacts simili dal PCA
3. Visualizza differenze morfologiche
4. Conferma o correggi clustering
```

**Step 7: Validazione (5 min)**
```
1. Data Explorer → Artifacts
2. Per ogni artifact: verifica classificazione AI
3. Se corretta: già salvata e validata
4. Se sbagliata: correggi manualmente
```

**Step 8: Usa Training (Auto)**
```
Sistema in background:
- Raccoglie 7 samples validati
- (Se ne aggiungi altri 13+ artifacts)
- Training automatico modello ML
- Prossimi upload → classificazione automatica
```

**Tempo Totale:** ~57 minuti
**Output:** PDF completo 50+ pagine con tutte le analisi

---

## 🎓 Best Practices

### Upload
- ✅ Usa nomi file significativi: `axe_savignano_001.obj`
- ✅ Gruppo artifacts per progetto
- ✅ Verifica qualità mesh prima upload
- ✅ Dimensioni ragionevoli (<100MB)

### Report
- ✅ Usa API key Claude per analisi AI completa
- ✅ Seleziona solo artifacts rilevanti
- ✅ Enable tutte le analisi per report completo
- ✅ Genera lingua appropriata per pubblicazione

### Progetti
- ✅ Un progetto per studio/pubblicazione
- ✅ Nome descrittivo (es. "Savignano2025", "BronzeAgePo")
- ✅ Descrizione dettagliata per riferimento futuro
- ✅ Archivia progetti completati (non eliminare subito)

### Classificazione
- ✅ Valida sempre classificazioni AI
- ✅ Aggiungi note archeologiche
- ✅ Usa nomenclatura consistente
- ✅ Minimo 20 samples per classe per ML training

---

## ❓ FAQ

**Q: Dove sono i dati estratti?**
**A:** Data Explorer → Artifacts → Click artifact → Features

**Q: Come genero report solo per alcuni artifacts?**
**A:** Report Generator → Checkbox seleziona quali includere

**Q: Il report include artifacts di altri progetti?**
**A:** NO. Se apri report da un progetto, vedi SOLO quelli del progetto.

**Q: Posso comparare artifacts di progetti diversi?**
**A:** Sì, usa Savignano Compare (seleziona manualmente)

**Q: Come funziona training automatico?**
**A:** Sistema monitora artifacts validati. Con 20+ samples, training automatico.

**Q: Posso eliminare artifacts?**
**A:** Sì: Data Explorer → Artifacts → Click artifact → 🗑️ Delete

**Q: Dove vedo classificazioni AI?**
**A:** Nel PDF report (sezione AI Analysis) e in Data Explorer → Artifacts

**Q: Come aggiungo utenti?**
**A:** Data Explorer → Users (solo admin) → Add User

---

## 🔗 Link Rapidi

| Funzione | URL |
|----------|-----|
| **Login** | `http://localhost:5001/web/login` |
| **Dashboard** | `http://localhost:5001/web/dashboard` |
| **Projects** | `http://localhost:5001/web/projects-page` |
| **Data Explorer** | `http://localhost:5001/web/data-explorer` |
| **Upload** | `http://localhost:5001/web/upload` |
| **Report Generator** | `http://localhost:5001/web/savignano-comprehensive-report` |
| **3D Viewer** | `http://localhost:5001/web/viewer` |
| **Compare** | `http://localhost:5001/web/savignano-compare` |

---

## 📞 API Endpoints Essenziali

### Projects
```bash
GET  /web/api/projects              # Lista progetti
POST /web/api/projects              # Crea progetto
GET  /web/api/projects/<id>         # Dettagli progetto
```

### Artifacts
```bash
POST /api/mesh/upload               # Upload singolo
GET  /api/mesh/artifacts            # Lista (paginata)
GET  /api/mesh/artifacts/<id>       # Dettagli + features
DELETE /api/mesh/artifacts/<id>     # Elimina
```

### Authentication
```bash
POST /api/auth/login                # Login
GET  /api/auth/users                # Lista utenti (admin)
```

### System
```bash
GET /api/system/health              # Health check
GET /api/system/status              # System stats
```

---

## 🎯 Conclusione

**Workflow Semplificato = 6 Passi:**
1. Login
2. Scegli/Crea Progetto
3. Upload File
4. Genera Report (seleziona quali)
5. Visualizza/Compara
6. Training (automatico)

**Tutto il resto è automatico!** 🚀

---

**Versione:** 2.0
**Autore:** BrozeAXE-AI Team
**Aggiornato:** 24 Novembre 2025

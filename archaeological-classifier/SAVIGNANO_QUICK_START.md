# Savignano Quick Start Guide
## Come Inserire i Pesi delle Asce

**Versione:** 3.0
**Data:** 9 Novembre 2025

---

## 📝 5 Modi per Inserire i Pesi

### 🔵 Opzione 1: No Weights (Default)

**Quando usarlo:** Peso non disponibile o non rilevante

**Procedura:**
1. Vai su `/web/savignano-analysis`
2. Step 1: Upload 3D Meshes
3. Seleziona i file mesh (.obj, .stl, .ply)
4. Sezione "Weights Data (Optional)"
5. ⚪ Lascia selezionato **"No weights (peso = 0)"** (default)
6. Click "📤 Upload & Start Analysis"

**Risultato:**
- Features Savignano estratte ✓
- Campo `peso` = 0.0 per tutte le asce
- Tutte le altre features (tallone, incavo, tagliente) funzionano normalmente ✓

---

### 🟢 Opzione 2: Manual Input

**Quando usarlo:** Upload di 1-10 asce con pesi noti

**Procedura:**
1. Vai su `/web/savignano-analysis`
2. Step 1: Upload 3D Meshes
3. Seleziona i file mesh delle asce (.obj, .stl, .ply)
4. Sezione "Weights Data (Optional)"
5. ⚪ Seleziona radio button **"Manual input (type weight for each file)"**
6. **IMPORTANTE**: Appaiono campi peso per ogni file selezionato
7. Inserisci il peso in grammi per ogni ascia (es: `387.0`)
8. Lascia vuoti i campi per pesi non noti (peso = 0)
9. Click "📤 Upload & Start Analysis"

**Screenshot Workflow:**
```
┌─────────────────────────────────────────────────────┐
│ Weights Data (Optional):                            │
│  ( ) No weights (peso = 0)                          │
│  (•) Manual input (type weight for each file)       │
│  ( ) Upload Excel/CSV file                          │
│  ( ) Upload DOCX scan notes (auto-extract)          │
│  ( ) Upload JSON file                               │
└─────────────────────────────────────────────────────┘

Enter weight (grams) for each axe:
┌─────────────────────────────────────────────────────┐
│ 📄 axe974.obj                        [387.0    ]    │
│ 📄 axe942.obj                        [413.0    ]    │
│ 📄 axe936.obj                        [401.5    ]    │
└─────────────────────────────────────────────────────┘
```

**Risultato:**
- Mesh caricata ✓
- Features Savignano estratte ✓
- Peso salvato nel campo `peso` ✓

---

### 🟡 Opzione 3: File Excel/CSV (Batch)

**Quando usarlo:** Upload di 10+ asce, pesi già in tabella Excel

**Procedura:**
1. Prepara file Excel/CSV (`pesi_asce.xlsx` o `pesi_asce.csv`):
   ```
   | artifact_id | weight |
   |-------------|--------|
   | axe974      | 387.0  |
   | axe942      | 413.0  |
   | axe936      | 401.5  |
   ```

   **IMPORTANTE:**
   - `artifact_id` deve corrispondere al nome del file (senza estensione)
   - Esempio: file `axe974.obj` → artifact_id = `axe974`

2. Vai su `/web/savignano-analysis`
3. Step 1: Upload 3D Meshes
4. Seleziona TUTTI i file mesh
5. Sezione "Weights Data (Optional)"
6. ⚪ Seleziona radio button **"Upload Excel/CSV file"**
7. Click su "Choose File" e seleziona `pesi_asce.xlsx` (o `.csv`)
8. Click "📤 Upload & Start Analysis"

**Auto-matching:**
Il sistema matcha automaticamente:
```
File mesh: axe974.obj  →  artifact_id: axe974  →  peso: 387.0 ✓
File mesh: axe942.obj  →  artifact_id: axe942  →  peso: 413.0 ✓
```

**Formati Supportati:**
- **Excel**: `.xlsx`, `.xls`
- **CSV**: `.csv`
- **JSON**: `.json` formato `{"axe974": 387.0, "axe942": 413.0}`
- **DOCX**: `.docx` con pattern "974: 387g" nel testo

---

### 🟠 Opzione 4: DOCX Scan Notes (Auto-Extract)

**Quando usarlo:** Hai un documento Word con note di scavo/catalogazione contenenti i pesi

**Procedura:**
1. Vai su `/web/savignano-analysis`
2. Step 1: Upload 3D Meshes
3. Seleziona i file mesh
4. Sezione "Weights Data (Optional)"
5. ⚪ Seleziona radio button **"Upload DOCX scan notes (auto-extract)"**
6. Click su "Choose File" e seleziona il file `.docx`
7. Click "📤 Upload & Start Analysis"

**Formato Supportato:**
Il sistema cerca pattern come:
- `974: 387g`
- `axe942 - peso 413g`
- `ID 936: weight 401.5 grams`

**Risultato:**
- Pesi estratti automaticamente dal testo ✓
- Matching automatico con nomi file ✓

---

### 🔴 Opzione 5: JSON File

**Quando usarlo:** Hai già un file JSON con i pesi (da sistemi automatici)

**Procedura:**
1. Prepara file JSON (`pesi_asce.json`):
   ```json
   {
     "axe974": 387.0,
     "axe942": 413.0,
     "axe936": 401.5
   }
   ```

2. Vai su `/web/savignano-analysis`
3. Step 1: Upload 3D Meshes
4. Seleziona i file mesh
5. Sezione "Weights Data (Optional)"
6. ⚪ Seleziona radio button **"Upload JSON file"**
7. Click su "Choose File" e seleziona `pesi_asce.json`
8. Click "📤 Upload & Start Analysis"

**Risultato:**
- Pesi caricati dal JSON ✓
- Formato semplice dizionario artifact_id → peso ✓

---

## ⚙️ Configurazione API Key (Già Esistente)

**IMPORTANTE:** L'API key è già configurata nel progetto!

**Verifica configurazione:**
1. Vai sulla dashboard `/web/`
2. Sezione "🤖 AI Assistant"
3. Controlla "API Key: ✓ Configured"

**Se non configurata:**
1. Vai su `/web/` (dashboard)
2. Sezione AI Assistant
3. Click "Configure API Key"
4. Inserisci la tua Anthropic API key
5. Salva

**Il sistema Savignano usa automaticamente questa API key** - non serve configurazione separata!

---

## 🎯 Workflow Completo: Esempio Pratico

### Scenario: 3 Asce con Pesi Noti

**Hai:**
- `ascia_974.obj` (387g)
- `ascia_942.obj` (413g)
- `ascia_936.obj` (401.5g)

**Opzione A - Manuale:**
```
1. Upload → Seleziona 3 file .obj
2. ✅ Enable Savignano Analysis
3. (•) Manual input
4. Lista file:
   ascia_974.obj  Peso: [387]   ← inserisci
   ascia_942.obj  Peso: [413]   ← inserisci
   ascia_936.obj  Peso: [401.5] ← inserisci
5. Upload → Fatto! ✓
```

**Opzione B - Excel:**
```
1. Crea pesi.xlsx:
   artifact_id | weight
   ascia_974   | 387
   ascia_942   | 413
   ascia_936   | 401.5

2. Upload → Seleziona 3 file .obj
3. ✅ Enable Savignano Analysis
4. (•) From file
5. Carica pesi.xlsx
6. Upload → Fatto! ✓ (auto-matching)
```

---

## 🔍 Verifica Pesi Caricati

**Dopo l'upload:**

1. Vai su `/web/artifacts`
2. Click su un'ascia (es: `ascia_974`)
3. Sezione **"🗡️ Savignano Morphometric Analysis"**
4. Card **"⚖️ Peso"**:
   ```
   ┌─────────────────┐
   │ ⚖️ Peso        │
   │                 │
   │   387.0 g      │ ← Peso corretto!
   └─────────────────┘
   ```

---

## ❌ Troubleshooting Pesi

### Problema: Peso = 0 dopo upload

**Causa 1:** Radio button "Manual input" non selezionato
- ✅ Soluzione: Assicurati di selezionare "Manual input" PRIMA di inserire i pesi

**Causa 2:** Excel - artifact_id non corrisponde al filename
```
File: axe974.obj
Excel artifact_id: "974"  ✗ Mismatch!
```
- ✅ Soluzione: Excel deve essere `axe974` (uguale al filename)

**Causa 3:** Campo peso lasciato vuoto
- ✅ Soluzione: Inserisci almeno un valore (può essere 0)

### Problema: Input manuale peso non appare

**Causa:** Radio button "Manual input" non selezionato

**Soluzione:**
1. Seleziona file PRIMA
2. ✅ Enable Savignano Analysis
3. Click radio "Manual input"
4. I campi peso appaiono nella lista file

---

## 📊 Comparazione Asce

**Dopo aver caricato le asce con pesi:**

1. Vai su `/web/savignano-compare`
2. Dropdown "Axe 1": Mostra `ascia_974 (387.0g)` ← peso visibile!
3. Dropdown "Axe 2": Seleziona un'altra ascia
4. Click "Compare Selected Axes"
5. Vedi:
   - Score similarità
   - Confronto peso: `387.0g vs 413.0g`
   - AI interpretation

---

## 🚀 Link Rapidi

Dalla dashboard `/web/`:
- **Analisi Savignano**: `/web/savignano-analysis`
- **Comparazione**: `/web/savignano-compare`
- **AI Assistant** → "🗡️ Savignano Axes Analysis"
- **Quick Actions** → "🗡️ Savignano Compare"

---

## 💡 Best Practices

### ✅ DO:
- Usa nomi file consistenti (`axe974.obj`, `axe942.obj`, etc.)
- Per 1-10 asce con pesi noti: usa "Manual input"
- Per 10+ asce con Excel/CSV: usa "Upload Excel/CSV file"
- Verifica pesi dopo analisi completata (scarica risultati)
- Lascia campi peso vuoti se non noti (peso = 0 automatico)

### ❌ DON'T:
- Non cambiare nomi file dopo aver preparato Excel/CSV
- Non dimenticare di selezionare il radio button corretto per i pesi
- Non usare `/web/upload` per Savignano (usa `/web/savignano-analysis`)
- Non aspettarti rilevamento automatico peso dalla mesh (non possibile)

---

## 📞 Quick Reference

**1. No Weights (Default):**
```
/web/savignano-analysis → Select files → (•) No weights → Upload
```

**2. Manual Input:**
```
/web/savignano-analysis → Select files → (•) Manual input → [387.0, 413.0, ...] → Upload
```

**3. Excel/CSV:**
```
Excel/CSV ready → /web/savignano-analysis → Files → (•) Excel/CSV → Choose file → Upload
```

**4. DOCX Auto-Extract:**
```
DOCX ready → /web/savignano-analysis → Files → (•) DOCX → Choose file → Upload
```

**5. JSON:**
```
JSON ready → /web/savignano-analysis → Files → (•) JSON → Choose file → Upload
```

---

**Ultimo Aggiornamento:** 9 Novembre 2025
**Versione Sistema:** 3.0

**Novità Versione 3.0:**
- ✅ Aggiunte 5 opzioni peso (prima solo 3)
- ✅ Manual input ora disponibile nell'UI
- ✅ Artifacts salvati automaticamente nel database principale
- ✅ Comparazione e 3D viewer ora funzionano con file caricati
- ✅ Rilevamento incavo migliorato (soglie più sensibili)

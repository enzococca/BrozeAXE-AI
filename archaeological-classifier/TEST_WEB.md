# 🧪 Test Web Interface

## Quick Test

Il problema della pagina bianca è stato risolto! Il CSS non veniva caricato correttamente.

### Fix Applicato

**Problema:** `static_url_path` nel blueprint causava conflitti
**Soluzione:** Rimosso `static_url_path='/web/static'` da `web_bp`

### Verifica Funzionamento

```bash
# Test automatico
python -c "
from acs.api.app import create_app
app = create_app()
with app.test_client() as client:
    print('Test Homepage:', client.get('/web/').status_code)
    print('Test CSS:', client.get('/web/static/css/style.css').status_code)
    print('✅ Se entrambi 200, funziona!')
"
```

Expected output:
```
Test Homepage: 200
Test CSS: 200
✅ Se entrambi 200, funziona!
```

## Riavvia Server

**Se il server è ancora in esecuzione:**

1. Ferma con `Ctrl+C`
2. Riavvia con `python run_web.py`

**Oppure in un nuovo terminale:**

```bash
cd archaeological-classifier
python run_web.py
```

## Apri Browser

**URL:** http://localhost:5000/web/

Dovresti vedere:

```
┌────────────────────────────────────────┐
│ 🏛️ Archaeological Classifier          │
├────────────────────────────────────────┤
│ Dashboard  Upload  Artifacts  ...      │
├────────────────────────────────────────┤
│                                         │
│  Dashboard                              │
│  Overview of your archaeological...    │
│                                         │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  │
│  │ 📦  │  │ 📊  │  │ 🏷️  │  │ ✓  │  │
│  │  0  │  │  0  │  │  0  │  │  0 │  │
│  └─────┘  └─────┘  └─────┘  └─────┘  │
└────────────────────────────────────────┘
```

## Checklist Visiva

Quando apri la pagina, verifica:

- [ ] **Navbar blu/viola** visibile in alto
- [ ] **Logo 🏛️** e titolo "Archaeological Classifier"
- [ ] **Menu navigation** (Dashboard, Upload, Artifacts, Analysis, Taxonomy)
- [ ] **4 card statistiche** con gradiente blu-viola
- [ ] **Pulsanti colorati** (blue, purple)
- [ ] **Footer** in basso con copyright
- [ ] **Stile moderno** (no pagina bianca!)

## Se Ancora Bianca

### 1. Verifica Console Browser

Premi `F12` → Tab "Console"

Se vedi errori tipo:
```
Failed to load resource: net::ERR_FILE_NOT_FOUND
.../static/css/style.css
```

### 2. Hard Refresh

- **Windows/Linux:** `Ctrl+Shift+R`
- **Mac:** `Cmd+Shift+R`

### 3. Verifica File CSS

```bash
ls -la acs/web/static/css/style.css
# Dovrebbe mostrare ~10KB
```

### 4. Controlla Logs Server

Nel terminale dove hai avviato il server, cerca errori tipo:
```
127.0.0.1 - - [04/Nov/2024 08:00:00] "GET /web/static/css/style.css HTTP/1.1" 200 -
```

Il `200` indica successo. Se vedi `404`, c'è un problema.

## Test Funzionalità Base

### 1. Navigation

Click su ogni voce menu:
- Dashboard → `/web/`
- Upload → `/web/upload`
- Artifacts → `/web/artifacts`
- Analysis → `/web/morphometric`
- Taxonomy → `/web/taxonomy`

Tutte dovrebbero caricare senza errori.

### 2. Upload Page

Vai a `/web/upload`

Dovresti vedere:
- Zona upload con bordo tratteggiato
- Icona 📦
- Testo "Drag and drop files here"
- Pulsante "Choose Files"

### 3. Dashboard Actions

Torna a `/web/`

Click "Export Data" → dovrebbe aprire prompt

## Troubleshooting Avanzato

### Cache Browser

Cancella cache:

**Chrome:**
1. F12
2. Right-click sul reload button
3. "Empty Cache and Hard Reload"

**Firefox:**
1. F12
2. Network tab
3. Click cestino (clear cache)

### Reload Python Module

Se modifichi codice mentre server è attivo:

```bash
# Ctrl+C per fermare
# Poi riavvia
python run_web.py
```

### Verifica Template Rendering

```python
from acs.api.app import create_app
app = create_app()

with app.test_client() as client:
    response = client.get('/web/')
    print(response.data.decode()[:500])
    # Dovresti vedere HTML con <!DOCTYPE html>
```

## Success Indicators

✅ **Funziona se:**
- Vedi stile colorato (blu, viola)
- Navbar in alto con logo
- Card statistiche con gradiente
- Pulsanti blu con hover effect
- Footer in basso
- Nessun testo bianco su bianco

❌ **Non funziona se:**
- Tutto bianco/grigio
- Solo testo senza stile
- Console browser mostra errori 404
- Navbar è solo testo semplice

## Dopo il Fix

Se tutto funziona:

1. ✅ Carica qualche file OBJ test
2. ✅ Prova analisi PCA
3. ✅ Definisci una classe test
4. ✅ Esplora tutte le pagine

---

**Fix applicato!** 🎉
Riavvia il server e dovresti vedere l'interfaccia completa con tutti gli stili!

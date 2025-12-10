# Google Drive Storage Setup

Questo documento spiega come configurare Google Drive per archiviare file 3D e database su BrozeAXE-AI.

## 🎯 Vantaggi
- ✅ **15GB gratuiti** (espandibili a 100GB+ a pagamento)
- ✅ **Storage persistente** (Railway cancella file al redeploy)
- ✅ **Backup automatico** con versioning
- ✅ **File grandi supportati** (fino a 5TB per file)
- ✅ **Costo zero** per piccoli progetti

---

## 📋 Step 1: Creare Progetto Google Cloud

1. Vai su [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuovo progetto:
   - Nome: `BrozeAXE-AI-Storage`
   - Clicca **CREA**

---

## 🔧 Step 2: Abilitare Google Drive API

1. Nel menu di sinistra: **API e servizi** → **Libreria**
2. Cerca "Google Drive API"
3. Clicca su **Google Drive API**
4. Clicca **ABILITA**

---

## 🔑 Step 3: Creare Credenziali OAuth2

1. Nel menu: **API e servizi** → **Credenziali**
2. Clicca **+ CREA CREDENZIALI** → **ID client OAuth**
3. Se richiesto, configura la schermata del consenso:
   - Tipo: **Esterno**
   - Nome app: `BrozeAXE-AI`
   - Email assistenza: `tua-email@esempio.com`
   - Ambiti: Aggiungi `../auth/drive.file` (accesso ai file creati dall'app)
   - Salva

4. Torna a **Credenziali** → **+ CREA CREDENZIALI** → **ID client OAuth**
   - Tipo applicazione: **Applicazione web**
   - Nome: `BrozeAXE-AI-Railway`
   - URI di reindirizzamento autorizzati:
     - `http://localhost:8080/`  (per testing locale)
     - `https://your-app.railway.app/oauth2callback` (sostituisci con URL Railway)
   - Clicca **CREA**

5. **Scarica JSON** delle credenziali
   - Clicca sull'icona download ⬇️
   - Salva come `client_secrets.json`

---

## 🔐 Step 4: Generare Token di Accesso

### Opzione A: Manualmente (Locale)

```bash
cd archaeological-classifier

# Installa PyDrive2
pip install PyDrive2

# Crea script temporaneo
cat > setup_gdrive.py << 'EOF'
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# Autenticazione
gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # Apre browser per login

# Salva credenziali
gauth.SaveCredentialsFile("mycreds.txt")

print("✅ Credenziali salvate in mycreds.txt")
print("📋 Carica questo file su Railway come variabile d'ambiente")
EOF

# Esegui script
python setup_gdrive.py
```

Questo:
1. Apre il browser
2. Ti chiede di fare login con Google
3. Salva il token in `mycreds.txt`

### Opzione B: Service Account (Produzione)

Per produzione senza interazione umana:

1. In **Google Cloud Console** → **API e servizi** → **Credenziali**
2. **+ CREA CREDENZIALI** → **Account di servizio**
3. Nome: `brozeaxe-storage-service`
4. Clicca **CREA E CONTINUA**
5. Ruolo: **Editor** (o personalizza permessi)
6. Clicca **FINE**
7. Clicca sull'account di servizio creato
8. Tab **CHIAVI** → **AGGIUNGI CHIAVE** → **Crea nuova chiave**
9. Tipo: **JSON**
10. **CREA** → Scarica JSON

---

## ⚙️ Step 5: Configurare Railway

### 5.1 Aggiungi Variabili d'Ambiente

Su Railway, vai su **Variables** e aggiungi:

```bash
# Storage Configuration
STORAGE_BACKEND=gdrive

# Google Drive Credentials (incolla contenuto JSON come stringa)
GOOGLE_DRIVE_CREDENTIALS={"type":"service_account","project_id":"...","private_key":"..."}

# Oppure path a file (se caricato su Railway)
# GOOGLE_DRIVE_CREDENTIALS_PATH=/app/credentials.json

# Folder structure on Google Drive
GDRIVE_FOLDER_ARTIFACTS=BrozeAXE/artifacts
GDRIVE_FOLDER_DATABASE=BrozeAXE/database
GDRIVE_FOLDER_UPLOADS=BrozeAXE/uploads
```

### 5.2 Carica Credenziali (se usi file)

Se usi file invece di variabile JSON:

1. Railway Dashboard → **Settings** → **Volumes**
2. Crea volume: `/app/credentials`
3. Carica `client_secrets.json` nel volume

---

## 🧪 Step 6: Test Locale

```bash
# Installa dipendenze
pip install -r requirements.txt

# Configura environment
export STORAGE_BACKEND=gdrive
export GOOGLE_DRIVE_CREDENTIALS_PATH=./client_secrets.json

# Avvia server
python -m acs.api.app

# Test upload
curl -X POST http://localhost:5001/api/mesh/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.obj" \
  -F "project_id=TestProject"
```

Se funziona, vedrai:
```
✅ Google Drive storage initialized
✅ Uploaded test.obj to Google Drive
```

---

## 📁 Struttura File su Google Drive

```
My Drive/
└── BrozeAXE/
    ├── database/
    │   └── acs_artifacts.db
    ├── artifacts/
    │   ├── Savignano2025/
    │   │   ├── axe936.obj
    │   │   ├── axe992.obj
    │   │   └── ...
    │   └── TestProject/
    │       └── ...
    └── uploads/
        ├── drawings/
        └── reports/
```

---

## 🔒 Sicurezza

### Best Practices:

1. **Non committare credenziali** nel repository
   ```bash
   # Aggiungi a .gitignore
   echo "client_secrets.json" >> .gitignore
   echo "mycreds.txt" >> .gitignore
   ```

2. **Usa Service Account** in produzione (non OAuth2 user)

3. **Limita permessi** all'account di servizio:
   - Solo Google Drive API
   - Solo cartelle specifiche (se possibile)

4. **Ruota chiavi regolarmente** (ogni 90 giorni)

5. **Monitora utilizzo** nella Google Cloud Console

---

## 🔄 Migrazione Dati Esistenti

Se hai già file locali:

```python
from acs.core.storage import get_storage

# Setup storage
storage = get_storage('gdrive', credentials_path='client_secrets.json')

# Upload database
storage.upload_file('acs_artifacts.db', 'BrozeAXE/database/acs_artifacts.db')

# Upload artifacts
import os
for root, dirs, files in os.walk('savignano_meshes'):
    for file in files:
        if file.endswith('.obj'):
            local_path = os.path.join(root, file)
            remote_path = f'BrozeAXE/artifacts/{file}'
            storage.upload_file(local_path, remote_path)
            print(f'✅ Uploaded {file}')
```

---

## ❓ Troubleshooting

### Errore: "Authentication required"
- Verifica che le credenziali siano valide
- Rigenera token: `python setup_gdrive.py`

### Errore: "Quota exceeded"
- Controlla spazio Drive: [drive.google.com/settings/storage](https://drive.google.com/settings/storage)
- Upgrade a Google One se necessario

### File non trovati
- Verifica struttura cartelle su Drive
- Controlla variabili `GDRIVE_FOLDER_*`

### Upload lento
- Normale per file >100MB
- Google Drive ha rate limits
- Considera chunked upload per file giganti

---

## 💰 Costi

### Free Tier (15GB)
- ✅ Sufficiente per ~150 modelli 3D (100MB ciascuno)
- ✅ Database fino a 1GB

### Google One (se serve più spazio)
- **100GB**: €1.99/mese
- **200GB**: €2.99/mese
- **2TB**: €9.99/mese

Molto più economico di storage dedicato Railway/AWS!

---

## 📚 Risorse

- [PyDrive2 Documentation](https://docs.iterative.ai/PyDrive2/)
- [Google Drive API Reference](https://developers.google.com/drive/api/v3/reference)
- [Google Cloud Console](https://console.cloud.google.com/)

---

**Prossimi step:**
1. Segui questa guida
2. Configura credenziali
3. Testa in locale
4. Deploy su Railway
5. Verifica che file vengano salvati su Drive

🎉 **Done!** Il tuo storage è ora su cloud persistente!

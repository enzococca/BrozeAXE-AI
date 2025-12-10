# Configurazione Dropbox Storage per BrozeAXE-AI

Questa guida ti aiuterà a configurare Dropbox come backend di storage per i tuoi file 3D mesh su Railway.

## Vantaggi di Dropbox

✅ **Gratuito** - Account base con 2GB di spazio (espandibile con referral)
✅ **Semplice** - Solo un access token, nessuna configurazione complessa
✅ **Backup automatico** - I file sono sincronizzati con il tuo account Dropbox
✅ **File grandi** - Supporto automatico per file > 150MB con chunked upload

---

## Passo 1: Crea un'app Dropbox

1. **Vai su Dropbox App Console:**
   ```
   https://www.dropbox.com/developers/apps
   ```

2. **Clicca "Create app"** (o "Crea app")

3. **Scegli le impostazioni:**
   - **API:** Scoped access
   - **Type of access:** Full Dropbox (accesso completo)
   - **Name your app:** `BrozeAXE-Railway` (o un nome a tua scelta, deve essere unico)

4. **Clicca "Create app"**

---

## Passo 2: Configura i permessi

Nella pagina dell'app appena creata:

1. **Vai alla tab "Permissions"**

2. **Abilita i seguenti permessi:**
   - ✅ `files.metadata.write` - Scrivere metadati dei file
   - ✅ `files.metadata.read` - Leggere metadati dei file
   - ✅ `files.content.write` - Scrivere contenuti dei file
   - ✅ `files.content.read` - Leggere contenuti dei file

3. **Clicca "Submit"** in fondo alla pagina per salvare

---

## Passo 3: Genera l'Access Token

1. **Vai alla tab "Settings"** (o torna alla pagina principale dell'app)

2. **Scorri fino a "OAuth 2" section**

3. **Trova "Generated access token"**

4. **Clicca "Generate"**

5. **Copia il token generato** (apparirà qualcosa tipo: `sl.B1234...`)

   ⚠️ **IMPORTANTE:** Salva questo token in un posto sicuro! Non verrà mostrato di nuovo.

---

## Passo 4: Configura Railway

1. **Vai al tuo progetto Railway:** https://railway.app/

2. **Clicca sul tuo progetto BrozeAXE-AI**

3. **Vai su "Variables"** (tab variabili ambiente)

4. **Aggiungi/modifica queste variabili:**

   ```bash
   # Cambia backend da 'local' a 'dropbox'
   STORAGE_BACKEND=dropbox

   # Incolla il token generato al passo 3
   DROPBOX_ACCESS_TOKEN=sl.B1234xxxxxxxxxxxxxxxxxxxxx
   ```

5. **Clicca "Add" o "Save"**

6. **Railway farà il redeploy automaticamente**

---

## Passo 5: Verifica il funzionamento

Dopo il redeploy di Railway:

1. **Carica un file 3D mesh** dalla tua applicazione

2. **Controlla i log di Railway**, dovresti vedere:
   ```
   ✅ Dropbox storage initialized
   ✅ Uploaded to Dropbox: meshes/axeITAL001/axeITAL001.obj
   ```

3. **Apri il tuo Dropbox** (web o app desktop)

4. **Verifica che i file siano stati caricati** nella struttura:
   ```
   /meshes/
     └── axeITAL001/
         └── axeITAL001.obj
   ```

---

## Struttura dei file su Dropbox

L'applicazione organizza i file in questa struttura:

```
/ (root Dropbox)
├── meshes/
│   ├── artifact_id_1/
│   │   ├── artifact_id_1.obj
│   │   └── artifact_id_1.mtl
│   ├── artifact_id_2/
│   │   └── artifact_id_2.obj
│   └── ...
├── backups/
│   └── database/
│       ├── acs_artifacts_backup_20231206_120000.db
│       └── acs_artifacts_backup_20231207_120000.db
└── exports/
    ├── artifact_export_20231206.pdf
    └── ...
```

---

## Troubleshooting

### Errore: "Invalid access token"

**Problema:** Il token è scaduto o non valido

**Soluzione:**
1. Torna alla Dropbox App Console
2. Genera un nuovo access token
3. Aggiorna `DROPBOX_ACCESS_TOKEN` in Railway

---

### Errore: "Insufficient permissions"

**Problema:** I permessi dell'app non sono configurati correttamente

**Soluzione:**
1. Vai alla tab "Permissions" nella Dropbox App Console
2. Verifica che tutti i permessi `files.*` siano abilitati
3. Clicca "Submit" per salvare
4. **IMPORTANTE:** Dopo aver modificato i permessi, devi **rigenerare il token**
5. Aggiorna `DROPBOX_ACCESS_TOKEN` in Railway con il nuovo token

---

### Errore: "Path not found"

**Problema:** La cartella non esiste

**Soluzione:** Non serve fare nulla, l'applicazione crea automaticamente le cartelle necessarie

---

### I file vengono salvati in locale invece che su Dropbox

**Problema:** `STORAGE_BACKEND` non è impostato su `dropbox`

**Verifica in Railway:**
```bash
STORAGE_BACKEND=dropbox  # NON 'local'
```

---

## Passare da Google Drive a Dropbox

Se stavi provando Google Drive prima:

1. **In Railway, modifica le variabili:**
   ```bash
   # Cambia backend
   STORAGE_BACKEND=dropbox

   # Aggiungi token Dropbox
   DROPBOX_ACCESS_TOKEN=sl.B1234...

   # Puoi rimuovere (opzionale):
   GOOGLE_DRIVE_CREDENTIALS  ← rimuovi
   GOOGLE_DRIVE_FOLDER_ID    ← rimuovi
   ```

2. **Salva e attendi il redeploy**

3. **I nuovi upload andranno su Dropbox**

⚠️ **Nota:** I file già caricati su Google Drive (se ce ne sono) non vengono migrati automaticamente.

---

## Limiti di spazio

**Account Dropbox gratuito:** 2GB

**Se hai bisogno di più spazio:**
- Dropbox Plus: €11.99/mese - 2TB
- Dropbox Professional: €19.99/mese - 3TB
- Oppure ottieni spazio gratis invitando amici (500MB per referral)

**Stima spazio per mesh 3D:**
- Mesh 3D ad alta risoluzione: 10-50 MB ciascuno
- Con 2GB puoi archiviare circa **40-200 mesh 3D**

---

## Backup del database

L'applicazione può anche fare backup automatici del database su Dropbox.

**Per abilitare:**
```bash
# In Railway, aggiungi:
DB_BACKUP_ENABLED=true
DB_BACKUP_INTERVAL_HOURS=24
```

I backup verranno salvati in `/backups/database/` con timestamp.

---

## Supporto

Se hai problemi:
1. Controlla i log di Railway per errori specifici
2. Verifica che il token sia valido
3. Assicurati che i permessi dell'app siano corretti
4. Apri una issue su GitHub se il problema persiste

---

**Fatto!** 🎉

Ora il tuo BrozeAXE-AI usa Dropbox per archiviare i file 3D mesh in modo sicuro e persistente!

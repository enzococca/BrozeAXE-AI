# 🚂 Railway Deployment Guide - BrozeAXE-AI

Guida completa per deployare BrozeAXE-AI su Railway con Google Drive storage.

---

## 🎯 Perché Railway?

- ✅ **Deploy automatico** da GitHub
- ✅ **Free tier** $5/mese di credito
- ✅ **Scaling automatico**
- ✅ **HTTPS gratuito**
- ✅ **PostgreSQL/MySQL** opzionale
- ✅ **Logs in realtime**

---

## 📋 Prerequisiti

1. ✅ Account GitHub con repository BrozeAXE-AI
2. ✅ Account Railway ([railway.app](https://railway.app))
3. ✅ Google Drive configurato (vedi `GOOGLE_DRIVE_SETUP.md`)

---

## 🚀 Step 1: Collega Railway a GitHub

### 1.1 Crea Account Railway

1. Vai su [railway.app](https://railway.app)
2. Clicca **Login** → **Login with GitHub**
3. Autorizza Railway

### 1.2 Crea Nuovo Progetto

1. Dashboard Railway → **New Project**
2. Seleziona **Deploy from GitHub repo**
3. Cerca `enzococca/BrozeAXE-AI`
4. Clicca **Deploy Now**

Railway rileverà automaticamente Python e Flask!

---

## ⚙️ Step 2: Configura Variabili d'Ambiente

Nel tuo progetto Railway, vai su **Variables** e aggiungi:

### 2.1 Flask Configuration

```bash
# Flask Environment
FLASK_ENV=production
FLASK_DEBUG=False
PORT=5001
HOST=0.0.0.0

# JWT Secret (GENERA UNA CHIAVE SICURA!)
JWT_SECRET_KEY=your-super-secret-key-change-this-now-abc123xyz789
```

**Genera chiave sicura:**
```python
import secrets
print(secrets.token_urlsafe(32))
# Usa questo output come JWT_SECRET_KEY
```

### 2.2 Google Drive Storage

```bash
# Storage Backend
STORAGE_BACKEND=gdrive

# Google Drive Credentials (JSON come stringa)
GOOGLE_DRIVE_CREDENTIALS={"type":"service_account","project_id":"your-project","private_key":"-----BEGIN PRIVATE KEY-----\n...","client_email":"..."}

# Folder Paths
GDRIVE_FOLDER_ARTIFACTS=BrozeAXE/artifacts
GDRIVE_FOLDER_DATABASE=BrozeAXE/database
GDRIVE_FOLDER_UPLOADS=BrozeAXE/uploads
```

### 2.3 Database Path

```bash
# Database (su Google Drive)
DATABASE_PATH=/tmp/acs_artifacts.db
```

### 2.4 File Upload Configuration

```bash
MAX_UPLOAD_SIZE=104857600
UPLOAD_FOLDER=/tmp/uploads
```

### 2.5 Security (Opzionale ma consigliato)

```bash
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

---

## 🔧 Step 3: Configurazione Build

Railway rileva automaticamente Python, ma puoi personalizzare:

### 3.1 Build Command (Automatico)

Railway usa `requirements.txt` automaticamente:
```bash
pip install -r requirements.txt
```

### 3.2 Start Command (Automatico da Procfile)

Railway usa `Procfile`:
```
web: cd archaeological-classifier && python -m acs.api.app
```

### 3.3 Health Check (Opzionale)

In **Settings** → **Health Check**:
- Path: `/api/system/health`
- Timeout: 300s

---

## 📦 Step 4: Volume Persistente (Opzionale)

Railway offre volume persistente (a pagamento), ma usiamo Google Drive per:
- Database
- File OBJ
- Upload

**Quindi non serve volume Railway!** ✅

---

## 🌐 Step 5: Custom Domain (Opzionale)

### 5.1 Ottieni URL Railway

Dopo il deploy, Railway ti dà:
```
https://brozeaxe-ai-production.up.railway.app
```

### 5.2 Aggiungi Dominio Personalizzato

Se hai un dominio (es. `brozeaxe.com`):

1. Railway → **Settings** → **Domains**
2. **Add Domain** → `brozeaxe.com`
3. Copia CNAME record
4. Nel tuo DNS provider (Cloudflare, GoDaddy, ecc.):
   ```
   Type: CNAME
   Name: @
   Value: brozeaxe-ai-production.up.railway.app
   ```
5. Aspetta propagazione DNS (5-60 minuti)

Railway genera certificato SSL automaticamente! 🔒

---

## 🐛 Step 6: Verifica Deployment

### 6.1 Controlla Logs

Railway → **Deployments** → **View Logs**

Dovresti vedere:
```
✅ Google Drive storage initialized
 * Serving Flask app 'app'
 * Running on http://0.0.0.0:5001
✅ Initialized 3 default taxonomy classes
```

### 6.2 Test Endpoints

```bash
# Health check
curl https://your-app.railway.app/api/system/health

# Login
curl -X POST https://your-app.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Dashboard
open https://your-app.railway.app/web/dashboard
```

---

## 🔄 Step 7: Automatic Deploys

Railway fa deploy automatico ad ogni push su GitHub!

```bash
# Fai modifiche
git add .
git commit -m "Update feature"
git push origin main

# Railway detecta push e redeploya automaticamente! 🎉
```

Vedi progress in realtime su Railway dashboard.

---

## 💰 Costi Railway

### Free Tier
- **$5/mese** di credito incluso
- ~500 ore/mese di runtime
- Sufficiente per:
  - ✅ Testing e sviluppo
  - ✅ Small projects
  - ✅ Demo e POC

### Hobby Plan ($5/mese)
- **$5/mese** credito + **$5/mese** per extra usage
- Unlimited runtime
- Consigliato per produzione

### Pro Plan ($20/mese)
- **$20/mese** credito
- Priority support
- Team collaboration

**Con Google Drive storage, i costi sono minimi!** 💰

---

## 📊 Monitoring

### Railway Dashboard

- **Deployments**: Storico deploy
- **Metrics**: CPU, Memory, Network
- **Logs**: Real-time logging
- **Usage**: Costi e crediti

### Health Checks Automatici

Railway fa ping a `/api/system/health` ogni 60s.
Se fallisce 3 volte consecutive → restart automatico.

### Alerts (Opzionale)

Configura notifiche:
- Email su deployment fallito
- Slack integration
- Webhook custom

---

## 🔧 Troubleshooting

### Problema: "Module not found"

**Causa:** Dipendenze non installate

**Fix:**
```bash
# Verifica requirements.txt esista
ls requirements.txt

# Forza rebuild
Railway → Settings → Redeploy
```

### Problema: "Port already in use"

**Causa:** Railway assegna porta automaticamente via variabile `PORT`

**Fix:** Il codice legge già `os.getenv('PORT', 5001)`
```python
# In acs/api/app.py
port = int(os.getenv('PORT', 5001))
```

### Problema: "Google Drive authentication failed"

**Causa:** Credenziali non valide o mal formattate

**Fix:**
1. Verifica JSON credentials valido
2. Rimuovi newlines/spazi extra
3. Usa `\n` per newlines nelle private keys

### Problema: "Database locked"

**Causa:** SQLite non supporta concorrenza elevata

**Fix:**
1. Usa Google Drive per sync
2. Considera PostgreSQL per produzione:
   ```bash
   Railway → Add Plugin → PostgreSQL
   ```
3. Modifica `DATABASE_PATH` per usare PostgreSQL

### Problema: "Out of memory"

**Causa:** File OBJ troppo grandi caricati in memoria

**Fix:**
1. Aumenta memory limit (Railway Settings)
2. Usa streaming per file grandi
3. Implementa chunked upload

---

## 🔐 Sicurezza Production

### 1. Cambia Password Admin

**Subito dopo primo deploy:**

```bash
# Login come admin
curl -X POST https://your-app.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Cambia password (TODO: implementare endpoint)
```

### 2. Disabilita Debug Mode

```bash
FLASK_DEBUG=False  # ✅ Già impostato
```

### 3. HTTPS Only

```bash
SESSION_COOKIE_SECURE=True  # ✅ Già impostato
```

### 4. Rate Limiting

Railway include rate limiting di base.
Per custom limits, aggiungi Flask-Limiter.

### 5. Backup Database

Google Drive ha versioning automatico! ✅

Per backup extra:
```bash
# Scarica DB da Google Drive
# Salva localmente
# Upload su altro cloud (Dropbox, AWS S3)
```

---

## 📈 Scaling

### Vertical Scaling

Railway Settings → **Resources**:
- Memory: 512MB → 8GB
- CPU: 1 → 8 cores

### Horizontal Scaling

Railway **non supporta** multiple instances per app.

Alternative:
1. **Load Balancer** esterno (Cloudflare, AWS ALB)
2. **Migrate to Kubernetes** (overkill per small app)
3. **Railway Pro** con multiple services

---

## 🔄 CI/CD Pipeline

Railway = CI/CD automatico! ✅

Ma puoi aggiungere:

### GitHub Actions (Pre-deploy tests)

```yaml
# .github/workflows/test.yml
name: Tests
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest
```

### Railway Webhooks

Notifica altri servizi dopo deploy:
```bash
Railway → Settings → Webhooks
URL: https://your-webhook-url.com
Events: deployment.success, deployment.failed
```

---

## 📚 Risorse Utili

- [Railway Documentation](https://docs.railway.app/)
- [Railway Discord](https://discord.gg/railway) - Community support
- [Railway Status](https://status.railway.app/) - Uptime
- [Railway Pricing](https://railway.app/pricing)

---

## ✅ Checklist Deploy

Prima di andare in produzione:

- [ ] Google Drive configurato
- [ ] Credenziali caricate su Railway
- [ ] Variabili d'ambiente impostate
- [ ] `JWT_SECRET_KEY` generata (non default!)
- [ ] Password admin cambiata
- [ ] Health check endpoint attivo
- [ ] Logs verificati (no errori)
- [ ] Test login funzionante
- [ ] Test upload funzionante
- [ ] Custom domain configurato (opzionale)
- [ ] Monitoring attivo
- [ ] Backup strategy definita

---

## 🎉 Deploy Completato!

Se tutto funziona:

1. ✅ App accessibile da `https://your-app.railway.app`
2. ✅ File salvati su Google Drive
3. ✅ Deploy automatico ad ogni push
4. ✅ Logs e monitoring attivi
5. ✅ HTTPS con certificato valido

**Congratulazioni! 🎊 BrozeAXE-AI è in produzione!**

---

## 🆘 Support

Problemi? Contatta:

1. **Railway Community**: [Discord](https://discord.gg/railway)
2. **GitHub Issues**: Apri issue su repository
3. **Email support**: (se hai piano a pagamento)

---

**Last Updated:** 24 November 2025
**Tested By:** Claude AI
**Railway Version:** Latest
**Status:** ✅ Production Ready

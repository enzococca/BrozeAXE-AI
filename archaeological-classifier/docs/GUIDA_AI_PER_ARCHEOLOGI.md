# Guida all'Intelligenza Artificiale per Archeologi

## Sistema di Analisi AI per le Asce di Savignano sul Panaro

---

## Introduzione

Questa guida spiega come utilizzare le funzionalità di Intelligenza Artificiale del sistema Archaeological Classifier. Il sistema è stato progettato per assistere gli archeologi nell'analisi del ripostiglio di asce dell'Età del Bronzo di Savignano sul Panaro (Modena), ma può essere applicato ad altri contesti.

**Non è richiesta alcuna competenza informatica** per utilizzare queste funzionalità.

---

## Accesso al Sistema

1. Apri il browser e vai all'indirizzo dell'applicazione
2. Inserisci le credenziali:
   - **Username**: il tuo nome utente
   - **Password**: la tua password

> **Per aggiungere screenshot**: Cattura la schermata di login (`/web/login`) e salvala come `screenshots/login.png`

---

## Funzionalità AI Disponibili

Il sistema offre diverse funzionalità basate sull'intelligenza artificiale:

### 1. Analisi Automatica delle Asce

Il sistema può analizzare automaticamente le caratteristiche morfometriche di ogni ascia caricata, identificando:

- **Dimensioni**: lunghezza, larghezza, spessore
- **Peso** (se disponibile dai dati di scavo)
- **Forma del tagliente**: a ventaglio, rettilineo, convesso
- **Presenza dell'incavo**: caratteristica tipica delle asce a margini rialzati
- **Tracce di martellatura**: evidenze di lavorazione post-fusione

> **Per aggiungere screenshot**: Cattura la pagina Artifacts (`/web/artifacts`) e salvala come `screenshots/artifacts_dashboard.png`

---

### 2. Identificazione delle Matrici di Fusione

Una delle domande archeologiche fondamentali è: **quante matrici (stampi) sono state usate per produrre le 96 asce del ripostiglio?**

Il sistema utilizza algoritmi di **clustering** (raggruppamento) per identificare gruppi di asce probabilmente prodotte dalla stessa matrice, basandosi su:

- Somiglianza morfometrica
- Dimensioni compatibili
- Caratteristiche tecniche comuni

#### Come funziona:

1. Vai alla pagina **"Savignano Analysis"** dal menu
2. Seleziona **"Da Progetto"** per scegliere artefatti esistenti
3. Seleziona le asce da analizzare (spunta le caselle)
4. Se vuoi inserire i pesi manualmente, seleziona **"Inserimento manuale"**
5. Clicca su **"Start Analysis"**
6. Il sistema identificherà automaticamente i gruppi (matrici)

> **Per aggiungere screenshot**: Cattura la pagina Savignano Analysis (`/web/savignano-analysis`) con artefatti selezionati e salvala come `screenshots/savignano_analysis.png`

#### Risultati:

Il sistema mostra:
- **Numero di matrici identificate**: quanti stampi diversi sono stati usati
- **Numero stimato di fusioni per matrice**: quante asce per ogni stampo
- **Punteggio di qualità** (silhouette score): da 0 a 1, più alto = migliore raggruppamento
- **Visualizzazioni grafiche**: dendrogramma e PCA

> **Per aggiungere screenshot**: Dopo un'analisi completata, cattura la sezione risultati e salvala come `screenshots/analysis_results.png`

---

### 3. Visualizzazioni Grafiche

#### Dendrogramma
Il **dendrogramma** mostra come le asce si raggruppano in base alla loro somiglianza. È un grafico ad albero dove:
- Le asce più simili sono collegate da rami vicini
- L'altezza dei collegamenti indica il grado di differenza
- I colori indicano le matrici identificate

> **Per aggiungere screenshot**: Dal visualizzatore risultati, cattura il dendrogramma e salvalo come `screenshots/dendrogram.png`

#### PCA (Analisi delle Componenti Principali)
Il grafico **PCA** proietta le asce su un piano bidimensionale, dove:
- Ogni punto rappresenta un'ascia
- Asce vicine = morfologicamente simili
- Colori diversi = matrici diverse
- I cluster (gruppi) visibili indicano gruppi produttivi distinti

> **Per aggiungere screenshot**: Dal visualizzatore risultati, cattura il grafico PCA e salvalo come `screenshots/pca_clusters.png`

---

### 4. Ricerca Semantica (RAG)

Il sistema include una **ricerca intelligente** che comprende il significato delle domande, non solo le parole chiave. Questo significa che puoi fare domande in italiano naturale.

#### Come usarla:

1. Vai alla **Cache Dashboard** dal menu
2. Nella sezione "Ricerca Globale AI", scrivi una domanda, ad esempio:
   - *"Quali asce mostrano tracce di martellatura intensa?"*
   - *"Confronta SAV_001 con SAV_015"*
   - *"Quali sono le asce più grandi del ripostiglio?"*
   - *"Quante matrici sono state identificate?"*
3. Spunta **"Genera risposta AI"** per ottenere un'interpretazione dettagliata
4. Clicca **"Cerca"**

> **Per aggiungere screenshot**: Cattura la Cache Dashboard (`/web/cache-dashboard`) con una ricerca attiva e salvala come `screenshots/rag_search.png`

#### La risposta AI include:

- **Sintesi**: riassunto in 2-3 frasi
- **Analisi dettagliata**: spiegazione approfondita con interpretazione archeologica
- **Punti chiave**: lista dei risultati principali
- **Artefatti citati**: elenco delle asce menzionate nella risposta
- **Suggerimento visualizzazione**: se utile, il sistema può generare un grafico

La risposta usa **temperatura 0.1**, che significa che l'AI fornisce risposte fattuali e coerenti, basate solo sui dati disponibili.

> **Per aggiungere screenshot**: Dopo una ricerca con risposta AI, cattura la risposta formattata e salvala come `screenshots/rag_answer.png`

---

### 5. Confronto tra Asce

È possibile confrontare due asce per valutarne la somiglianza morfometrica:

1. Vai alla pagina **"Savignano Compare"** dal menu
2. Seleziona la prima ascia dal menu a tendina
3. Seleziona la seconda ascia
4. Clicca **"Confronta"**

Il sistema mostrerà:
- **Percentuale di somiglianza**: quanto sono simili (0-100%)
- **Differenze principali**: quali misure differiscono di più
- **Interpretazione AI**: analisi delle differenze
- **Possibilità dalla stessa matrice**: valutazione se provengono dallo stesso stampo

> **Per aggiungere screenshot**: Cattura la pagina Compare (`/web/savignano-compare`) con un confronto e salvala come `screenshots/compare_axes.png`

---

### 6. Report PDF

Dopo un'analisi, puoi esportare i risultati in formato PDF professionale:

1. Completa l'analisi Savignano
2. Clicca **"Export PDF"** (pulsante rosso)
3. Il sistema genera un report che include:
   - Titolo e data di generazione
   - Sintesi dei risultati (numero matrici, fusioni, qualità)
   - Tabella dettagliata delle matrici identificate
   - Grafici (dendrogramma, PCA)
   - Risposte alle domande archeologiche

Il PDF è pronto per essere allegato a pubblicazioni o rapporti di scavo.

> **Per aggiungere screenshot**: Cattura i pulsanti Export PDF e View Detailed Report e salva come `screenshots/pdf_export.png`

---

### 7. Visualizzatore Risultati Formattato

Invece di leggere dati grezzi, puoi visualizzare i risultati in modo leggibile:

1. Dopo l'analisi, clicca **"View Detailed Report"** (pulsante blu)
2. Si apre una finestra modale con:
   - **Riepilogo metriche**: asce analizzate, matrici, fusioni, punteggio qualità
   - **Dettagli matrici**: schede per ogni matrice con statistiche
   - **Visualizzazioni**: dendrogramma e PCA integrati
   - **Domande & Risposte**: interpretazioni archeologiche strutturate

Questa vista è progettata per essere comprensibile senza conoscenze tecniche.

> **Per aggiungere screenshot**: Apri il visualizzatore risultati e cattura la finestra modale, salva come `screenshots/results_viewer.png`

---

## Domande Archeologiche Affrontate

Il sistema risponde automaticamente a 6 domande fondamentali sull'analisi delle asce:

| # | Domanda | Come risponde il sistema |
|---|---------|--------------------------|
| 1 | **Quante matrici sono state usate?** | Clustering morfometrico delle asce |
| 2 | **Quante fusioni per matrice?** | Conteggio asce per cluster |
| 3 | **Quali trattamenti post-fusione?** | Analisi tracce di martellatura |
| 4 | **Come è stata rifinita la lama?** | Analisi forma del tagliente |
| 5 | **A cosa serviva l'incavo?** | Interpretazione funzionale |
| 6 | **Quanto sono state usate le asce?** | Analisi tracce d'usura |

---

## Cache e Dati Salvati

Tutte le analisi AI vengono salvate automaticamente nel database. Questo significa che:

- **Non devi ripetere le analisi**: i risultati sono sempre disponibili
- **Puoi confrontare analisi nel tempo**: traccia l'evoluzione dell'interpretazione
- **I dati sono al sicuro**: backup automatico su cloud (Dropbox)

### Dashboard Cache

La **Cache Dashboard** mostra le statistiche del sistema:

| Statistica | Significato |
|------------|-------------|
| **Interpretazioni AI** | Numero di analisi AI salvate |
| **Comparazioni** | Confronti tra artefatti effettuati |
| **Artefatti con Features** | Quanti hanno dati morfometrici (totale) |
| **Con Features Savignano** | Quanti hanno l'analisi specifica Savignano |
| **Analisi (PCA/Clustering)** | Risultati di analisi statistiche salvate |
| **Totale Artefatti** | Numero totale di artefatti nel database |

> **Per aggiungere screenshot**: Cattura la Cache Dashboard con le statistiche visibili e salva come `screenshots/cache_dashboard.png`

---

## Suggerimenti per l'Uso

### Per ottenere risultati migliori:

1. **Carica dati completi**: più informazioni fornisci (peso, dimensioni esatte), migliore sarà l'analisi
2. **Usa la ricerca naturale**: scrivi domande come le faresti a un collega archeologo
3. **Confronta sempre i risultati**: l'AI è uno strumento di supporto, non sostituisce l'interpretazione umana
4. **Esporta i report**: documenta le analisi per pubblicazioni e archivi di scavo

### Limiti da considerare:

- L'AI si basa sui dati disponibili: se mancano informazioni, i risultati saranno meno accurati
- Il clustering è statistico: asce simili potrebbero provenire da matrici diverse (usura, riparazioni, riutilizzo stampi)
- Le interpretazioni AI sono suggerimenti basati sui dati, richiedono sempre validazione archeologica da parte dell'esperto

---

## Glossario

| Termine | Significato per l'archeologo |
|---------|------------------------------|
| **Clustering** | Raggruppamento automatico di oggetti simili - il sistema identifica quali asce "vanno insieme" |
| **Dendrogramma** | Grafico ad albero che mostra le relazioni di somiglianza tra asce |
| **PCA** | Tecnica per visualizzare dati complessi su un piano - ogni punto è un'ascia |
| **Silhouette Score** | Misura della qualità del raggruppamento (0-1), più alto significa gruppi più distinti |
| **RAG** | Sistema di ricerca intelligente che capisce le domande in linguaggio naturale |
| **Matrice** | Stampo bivalve usato per la fusione del bronzo |
| **Features** | Caratteristiche misurabili di un artefatto (dimensioni, forma, peso) |
| **Cache** | Memoria dove vengono salvate le analisi per riutilizzarle |
| **Temperatura (AI)** | Parametro che controlla quanto l'AI è "creativa" - bassa = risposte più fattuali |

---

## Come Aggiungere gli Screenshot

Per completare questa guida con le immagini:

1. Accedi all'applicazione con le tue credenziali
2. Naviga alle pagine indicate
3. Usa lo strumento di cattura schermo del tuo computer:
   - **Windows**: `Win + Shift + S` o Strumento di cattura
   - **Mac**: `Cmd + Shift + 4`
   - **Linux**: `gnome-screenshot` o `scrot`
4. Salva le immagini nella cartella `docs/screenshots/` con i nomi indicati
5. Le immagini saranno automaticamente visualizzate nella guida

---

## Supporto

Per assistenza:
- **Email**: admin@brozeaxe.com
- **Segnalazione problemi**: https://github.com/anthropics/claude-code/issues

---

*Documento aggiornato: Dicembre 2025*
*Versione: 2.0 - Guida per Archeologi*

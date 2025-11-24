# Problema: Analisi Martellatura e Fusione Vuote nel PDF

## Stato Attuale
Le pagine PDF di analisi martellatura (hammering) e fusione (casting) mostrano solo i titoli/intestazioni ma **NON i dati effettivi**.

## Sintomo
Nel PDF generato si vede solo:
```
ANALISI MARTELLATURA
Artefatto: axe936
ANALISI MARTELLAMENTO (Cold-working)
Rugosità superficiale (deviazione standard delle normali):

ANALISI FUSIONE
Artefatto: axe936
ANALISI TECNICA DI FUSIONE
1. ANALISI SIMMETRIA
```

Mancano tutti i dati numerici e le interpretazioni.

## Evidenze dai Log
I log di debug mostrano che **i dati VENGONO generati correttamente**:

```
INFO:acs.savignano.comprehensive_report:=== HAMMERING ANALYSIS DEBUG ===
INFO:acs.savignano.comprehensive_report:Analysis text length: 772 characters
INFO:acs.savignano.comprehensive_report:Analysis text lines: 22 lines
INFO:acs.savignano.comprehensive_report:First 200 chars: ANALISI MARTELLAMENTO (Cold-working)

Rugosità superficiale (deviazione standard delle normali):
  - Tallone: σ = 0.5092
  - Corpo: σ = 0.5016
  - Tagliente: σ = 0.4855
...
INFO:acs.savignano.comprehensive_report:Wrapped lines count: 22
INFO:acs.savignano.comprehensive_report:Total pages needed: 1
```

```
INFO:acs.savignano.comprehensive_report:=== CASTING ANALYSIS DEBUG ===
INFO:acs.savignano.comprehensive_report:Analysis text length: 1832 characters
INFO:acs.savignano.comprehensive_report:Analysis text lines: 44 lines
INFO:acs.savignano.comprehensive_report:First 200 chars: ANALISI TECNICA DI FUSIONE

1. ANALISI SIMMETRIA
   Simmetria bilaterale: 98.9%
...
INFO:acs.savignano.comprehensive_report:Wrapped lines count: 47
INFO:acs.savignano.comprehensive_report:Total pages needed: 2
```

## Conclusione
**I dati ci sono!** Le funzioni `_analyze_hammering()` e `_analyze_casting()` generano correttamente 772 e 1832 caratteri di testo. Il problema è che questo testo **non viene renderizzato visibilmente nel PDF**.

## Tentativi di Fix Eseguiti

### 1. ✅ Aggiunto Logging
- Sostituito `print()` con `logger.info()` per visibilità nei log
- **Risultato**: Confermato che i dati vengono generati

### 2. ✅ Aggiunto Colore Nero Esplicito
```python
ax.text(0.08, current_y, line, ha='left', va='top',
       fontsize=9, family='monospace', color='black')
```
- **Risultato**: Nessun cambiamento, dati ancora mancanti

### 3. ✅ Preservata Indentazione
Problema identificato: `textwrap.wrap()` rimuove gli spazi iniziali. Fix:
```python
# Preserve leading spaces for indentation
leading_spaces = len(paragraph) - len(paragraph.lstrip())
indent = ' ' * leading_spaces
stripped = paragraph.lstrip()
if len(stripped) > 95:
    wrapped = textwrap.wrap(stripped, width=95 - leading_spaces, break_long_words=False)
    wrapped_lines.extend([indent + line for line in wrapped])
else:
    wrapped_lines.append(paragraph)
```
- **Risultato**: ANCORA nessun cambiamento

## Possibili Cause da Investigare

### 1. Font Monospace Non Disponibile
Il codice usa `family='monospace'` che potrebbe non essere disponibile su tutti i sistemi. Se il font non esiste, matplotlib potrebbe fallire silenziosamente il rendering.

**Test da fare:**
```python
# Prova senza specifica del font
ax.text(0.08, current_y, line, ha='left', va='top',
       fontsize=9, color='black')
```

### 2. Coordinate Y Fuori Vista
Le coordinate potrebbero uscire dalla vista della pagina.

**Debug da aggiungere:**
```python
logger.info(f"Rendering line {i}: y={current_y}, text='{line[:50]}'")
```

### 3. Problema con Caratteri Speciali
Il carattere sigma (σ) potrebbe causare problemi di encoding.

**Test da fare:**
```python
# Test con solo ASCII
hammer_text = hammer_text.encode('ascii', 'ignore').decode('ascii')
```

### 4. PDF Non Salva Correttamente il Contenuto
Le chiamate `pdf.savefig(fig)` potrebbero non includere il testo.

**Test da fare:**
```python
# Prova con bbox_inches
pdf.savefig(fig, bbox_inches='tight')
```

### 5. Figure Axis Non Configurato Correttamente
```python
ax.axis('off')  # Questo potrebbe nascondere anche il testo?
```

**Test da fare:**
```python
# Non disabilitare l'axis per vedere se il testo appare
# ax.axis('off')  # Commentare temporaneamente
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
```

## Codice Rilevante

### File: `acs/savignano/comprehensive_report.py`

**Funzione problematica (linee 1568-1635):**
```python
def _create_hammering_analysis_page(self, pdf):
    """Create dedicated Hammering Analysis page - multiple A4 pages if needed."""
    import textwrap

    hammer_text = self._analyze_hammering()

    # DEBUG logs (funzionano - mostrano dati corretti)
    logger.info(f"\n=== HAMMERING ANALYSIS DEBUG ===")
    logger.info(f"Analysis text length: {len(hammer_text)} characters")
    # ...

    # Wrapping con preservazione indentazione
    wrapped_lines = []
    for paragraph in hammer_text.split('\n'):
        if paragraph.strip():
            leading_spaces = len(paragraph) - len(paragraph.lstrip())
            indent = ' ' * leading_spaces
            stripped = paragraph.lstrip()
            if len(stripped) > 95:
                wrapped = textwrap.wrap(stripped, width=95 - leading_spaces, break_long_words=False)
                wrapped_lines.extend([indent + line for line in wrapped])
            else:
                wrapped_lines.append(paragraph)
        else:
            wrapped_lines.append('')

    # Rendering del testo
    for page_num in range(total_pages):
        fig = plt.figure(figsize=(8.27, 11.69))  # A4 portrait
        ax = fig.add_subplot(111)
        ax.axis('off')  # ← Possibile problema?

        # ... titoli ...

        # Rendering linee
        current_y = text_start_y  # 0.91
        line_height = 0.018

        for line in page_lines:
            if line.strip():
                ax.text(0.08, current_y, line, ha='left', va='top',
                       fontsize=9, family='monospace', color='black')  # ← Non funziona
            current_y -= line_height

        pdf.savefig(fig)  # ← Il testo non viene salvato
        plt.close(fig)
```

## Test Diagnostico Proposto

Creare una pagina di test semplificata:

```python
def _test_text_rendering(self, pdf):
    """Test if basic text rendering works"""
    fig = plt.figure(figsize=(8.27, 11.69))
    ax = fig.add_subplot(111)
    ax.axis('off')

    # Test vari tipi di testo
    test_texts = [
        (0.5, 0.9, "Test 1: Simple text", {}),
        (0.5, 0.8, "Test 2: With monospace", {'family': 'monospace'}),
        (0.5, 0.7, "Test 3: Tallone: σ = 0.5092", {}),
        (0.5, 0.6, "  Test 4: Indented text", {}),
    ]

    for x, y, text, kwargs in test_texts:
        ax.text(x, y, text, ha='center', va='top',
               fontsize=10, color='black', **kwargs)
        logger.info(f"Rendered: {text}")

    pdf.savefig(fig)
    plt.close(fig)
```

Chiamare all'inizio di `generate_complete_report()` per verificare se il rendering di base funziona.

## Dati di Esempio Completi

**Hammering text che dovrebbe apparire:**
```
ANALISI MARTELLAMENTO (Cold-working)

Rugosità superficiale (deviazione standard delle normali):
  - Tallone: σ = 0.5092
  - Corpo: σ = 0.5016
  - Tagliente: σ = 0.4855

SPIEGAZIONE METRICA (σ roughness):
La deviazione standard (σ) delle normali superficiali misura
quanto la superficie si discosta da un piano ideale.

  σ < 0.02: superficie molto liscia (levigatura o fusione pulita)
  σ = 0.02-0.05: rugosità moderata (martellatura leggera)
  σ > 0.05: superficie irregolare (martellatura intensa)

INTERPRETAZIONE: La rugosità elevata nel tagliente...
[continua per 22 righe totali]
```

**Casting text che dovrebbe apparire:**
```
ANALISI TECNICA DI FUSIONE

1. ANALISI SIMMETRIA
   Simmetria bilaterale: 98.9%

   SPIEGAZIONE METRICA:
   La simmetria è calcolata confrontando le distribuzioni geometriche
   della metà sinistra e destra dell'ascia (specchiate).
   100% = perfettamente simmetrica, 0% = completamente asimmetrica
[continua per 44 righe totali]
```

## Prossimi Passi

1. **Test font**: Rimuovere `family='monospace'` e usare font di default
2. **Test axis**: Commentare `ax.axis('off')` per vedere se il testo appare
3. **Test semplificato**: Creare `_test_text_rendering()` per isolare il problema
4. **Test encoding**: Sostituire caratteri speciali con ASCII
5. **Verificare matplotlib version**: Controllare se c'è un bug noto con text rendering
6. **Test con altro backend**: Provare con backend diverso da Agg

## File Modificati
- `acs/savignano/comprehensive_report.py`: Aggiunto logging, color='black', preservazione indentazione
- `acs/api/blueprints/savignano.py`: Streaming con preview analisi

## Log Server
Monitorare stderr di Flask per vedere output debug durante generazione PDF.

---

**Commit**: `a69b697`
**Data**: 2025-11-24
**Branch**: main

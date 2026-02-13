// ============================================================================
// CAPITOLO 4: GESTIONE DEGLI ERRORI
// ============================================================================
// Rust non ha eccezioni. Usa due meccanismi:
// - panic! per errori irrecuperabili (il programma si ferma)
// - Result<T, E> per errori recuperabili (il chiamante decide cosa fare)
//
// Questo approccio ti OBBLIGA a gestire gli errori, rendendo il codice
// piu robusto e prevedibile.
//
// Esegui con: cargo run --example cap04_errori
// ============================================================================

use std::fmt;
use std::num::ParseIntError;

fn main() {
    println!("╔══════════════════════════════════════════════╗");
    println!("║   CAPITOLO 4: GESTIONE DEGLI ERRORI          ║");
    println!("╚══════════════════════════════════════════════╝\n");

    // ========================================================================
    // 4.1 - PANIC! (ERRORI IRRECUPERABILI)
    // ========================================================================
    println!("--- 4.1 panic! ---\n");

    // panic! ferma il programma immediatamente. Usalo solo per:
    // - Bug nel codice (situazioni che non dovrebbero mai accadere)
    // - Prototipi rapidi dove non vuoi ancora gestire gli errori

    // Esempio: accesso a indice fuori range causa panic
    let v = vec![1, 2, 3];
    // v[99]; // PANIC! "index out of bounds"

    // Modo sicuro:
    match v.get(99) {
        Some(valore) => println!("Trovato: {}", valore),
        None => println!("Indice 99 fuori range (gestito senza panic)"),
    }

    // Puoi anche creare un panic esplicito (commentato per non bloccare l'esempio):
    // panic!("Qualcosa e andato terribilmente storto!");

    println!();

    // ========================================================================
    // 4.2 - RESULT<T, E> (ERRORI RECUPERABILI)
    // ========================================================================
    println!("--- 4.2 Result<T, E> ---\n");

    // Result e un enum con due varianti:
    // enum Result<T, E> {
    //     Ok(T),   // successo, contiene il valore
    //     Err(E),  // errore, contiene l'errore
    // }

    // Esempio: parsing di un numero da stringa
    let numero_ok: Result<i32, ParseIntError> = "42".parse();
    let numero_err: Result<i32, ParseIntError> = "abc".parse();

    println!("Parse \"42\":  {:?}", numero_ok);   // Ok(42)
    println!("Parse \"abc\": {:?}", numero_err);   // Err(...)

    // Gestione con match
    match numero_ok {
        Ok(n) => println!("Numero valido: {}", n),
        Err(e) => println!("Errore: {}", e),
    }

    match numero_err {
        Ok(n) => println!("Numero valido: {}", n),
        Err(e) => println!("Errore di parsing: {}", e),
    }

    println!();

    // ========================================================================
    // 4.3 - UNWRAP E EXPECT
    // ========================================================================
    println!("--- 4.3 unwrap() e expect() ---\n");

    // unwrap(): estrae il valore Ok, oppure fa panic se e Err
    // DA USARE SOLO in prototipi o quando sei SICURO che non puo fallire
    let n: i32 = "100".parse().unwrap();
    println!("unwrap: {}", n);

    // expect(): come unwrap ma con un messaggio di errore personalizzato
    let n: i32 = "200".parse().expect("Doveva essere un numero!");
    println!("expect: {}", n);

    // ATTENZIONE: in produzione, NON usare unwrap/expect su dati esterni!
    // "abc".parse::<i32>().unwrap(); // PANIC!

    // Metodi piu sicuri:
    let con_default = "abc".parse::<i32>().unwrap_or(0);
    println!("unwrap_or: {}", con_default);  // 0

    let con_closure = "abc".parse::<i32>().unwrap_or_else(|e| {
        println!("  (errore gestito: {})", e);
        -1
    });
    println!("unwrap_or_else: {}", con_closure);  // -1

    println!();

    // ========================================================================
    // 4.4 - L'OPERATORE ? (PROPAGAZIONE ERRORI)
    // ========================================================================
    println!("--- 4.4 Operatore ? ---\n");

    // L'operatore ? e zucchero sintattico per propagare gli errori.
    // Funziona SOLO in funzioni che restituiscono Result o Option.

    // Senza ?:
    // match operazione() {
    //     Ok(val) => { ... }
    //     Err(e) => return Err(e),
    // }

    // Con ?:
    // let val = operazione()?;  // se Err, ritorna subito l'errore

    match leggi_eta("3200") {
        Ok(eta) => println!("Eta letta: {} anni", eta),
        Err(e) => println!("Errore: {}", e),
    }

    match leggi_eta("-5") {
        Ok(eta) => println!("Eta letta: {} anni", eta),
        Err(e) => println!("Errore: {}", e),
    }

    match leggi_eta("abc") {
        Ok(eta) => println!("Eta letta: {} anni", eta),
        Err(e) => println!("Errore: {}", e),
    }

    println!();

    // ========================================================================
    // 4.5 - ERRORI PERSONALIZZATI
    // ========================================================================
    println!("--- 4.5 Errori Personalizzati ---\n");

    // Puoi creare i tuoi tipi di errore con enum

    let test_cases = vec![
        ("Ascia", "Bronzo", "350.5", "2019"),    // OK
        ("", "Bronzo", "350.5", "2019"),          // nome vuoto
        ("Spada", "Bronzo", "-10", "2019"),       // peso negativo
        ("Pugnale", "Bronzo", "abc", "2019"),     // peso non numerico
        ("Fibula", "Bronzo", "50", "futuro"),     // anno non valido
    ];

    for (nome, materiale, peso, anno) in test_cases {
        match valida_reperto(nome, materiale, peso, anno) {
            Ok(info) => println!("  OK: {}", info),
            Err(e) => println!("  ERRORE: {}", e),
        }
    }

    println!();

    // ========================================================================
    // 4.6 - COMBINATORI DI RESULT
    // ========================================================================
    println!("--- 4.6 Combinatori ---\n");

    // map: trasforma il valore Ok
    let risultato: Result<i32, ParseIntError> = "10".parse();
    let raddoppiato = risultato.map(|n| n * 2);
    println!("map: {:?}", raddoppiato);  // Ok(20)

    // and_then (flatmap): concatena operazioni che possono fallire
    let risultato = "5"
        .parse::<i32>()
        .and_then(|n| {
            if n > 0 {
                Ok(n * 10)
            } else {
                // Creiamo un errore di parsing come esempio
                "non_valido".parse::<i32>()
            }
        });
    println!("and_then: {:?}", risultato);  // Ok(50)

    // or_else: prova un'alternativa in caso di errore
    let risultato: Result<i32, _> = "abc"
        .parse::<i32>()
        .or_else(|_| "42".parse::<i32>());
    println!("or_else: {:?}", risultato);  // Ok(42)

    // map_err: trasforma l'errore
    let risultato: Result<i32, String> = "abc"
        .parse::<i32>()
        .map_err(|e| format!("Parsing fallito: {}", e));
    println!("map_err: {:?}", risultato);

    println!();

    // ========================================================================
    // 4.7 - GESTIRE ERRORI MULTIPLI
    // ========================================================================
    println!("--- 4.7 Errori Multipli ---\n");

    // Quando una funzione puo produrre errori di tipo diverso,
    // puoi usare un enum che li raggruppa (vedi AnalisiErrore sopra)
    // oppure Box<dyn Error> per semplicita

    let risultati = vec![
        analizza_dato("42"),
        analizza_dato("3.14"),
        analizza_dato("abc"),
        analizza_dato("-999"),
    ];

    for (i, r) in risultati.iter().enumerate() {
        match r {
            Ok(msg) => println!("  Dato {}: {}", i + 1, msg),
            Err(e) => println!("  Dato {}: ERRORE - {}", i + 1, e),
        }
    }

    println!();

    // ========================================================================
    // 4.8 - PATTERN: EARLY RETURN
    // ========================================================================
    println!("--- 4.8 Pattern: Early Return ---\n");

    // Un pattern comune: validare tutto all'inizio e fare "early return" degli errori.
    // Questo mantiene il codice "felice" (il percorso di successo) non indentato.

    match processa_scavo("Savignano", 2019, 47) {
        Ok(report) => println!("{}", report),
        Err(e) => println!("Errore: {}", e),
    }

    match processa_scavo("", 2019, 47) {
        Ok(report) => println!("{}", report),
        Err(e) => println!("Errore: {}", e),
    }

    match processa_scavo("Savignano", 1800, 47) {
        Ok(report) => println!("{}", report),
        Err(e) => println!("Errore: {}", e),
    }

    println!();

    // ========================================================================
    // 4.9 - OPTION E RESULT INSIEME
    // ========================================================================
    println!("--- 4.9 Option e Result insieme ---\n");

    // Convertire tra Option e Result
    let opt: Option<i32> = Some(42);
    let res: Result<i32, &str> = opt.ok_or("Valore mancante");
    println!("Option -> Result: {:?}", res);

    let opt_none: Option<i32> = None;
    let res_none: Result<i32, &str> = opt_none.ok_or("Valore mancante");
    println!("None -> Result: {:?}", res_none);

    // Result -> Option
    let res_ok: Result<i32, &str> = Ok(42);
    let opt_ok: Option<i32> = res_ok.ok();
    println!("Result -> Option: {:?}", opt_ok);

    // Collezioni di Result -> Result di collezione
    let numeri_str = vec!["1", "2", "3", "4", "5"];
    let numeri: Result<Vec<i32>, _> = numeri_str.iter().map(|s| s.parse::<i32>()).collect();
    println!("Collect Result: {:?}", numeri);  // Ok([1, 2, 3, 4, 5])

    let numeri_str = vec!["1", "2", "abc", "4", "5"];
    let numeri: Result<Vec<i32>, _> = numeri_str.iter().map(|s| s.parse::<i32>()).collect();
    println!("Collect con errore: {:?}", numeri);  // Err(...)

    // Filtrare solo i valori Ok
    let numeri_str = vec!["1", "abc", "3", "def", "5"];
    let solo_validi: Vec<i32> = numeri_str
        .iter()
        .filter_map(|s| s.parse::<i32>().ok())
        .collect();
    println!("Solo validi: {:?}", solo_validi);  // [1, 3, 5]

    println!("\n✅ Capitolo 4 completato!");
}

// ============================================================================
// TIPI DI ERRORE PERSONALIZZATI
// ============================================================================

/// Enum per errori del catalogo archeologico
#[derive(Debug)]
enum ErroreReperto {
    NomeVuoto,
    PesoNonValido(String),
    PesoNegativo(f64),
    AnnoNonValido(String),
}

// Implementiamo Display per mostrare messaggi leggibili
impl fmt::Display for ErroreReperto {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ErroreReperto::NomeVuoto => write!(f, "Il nome del reperto non puo essere vuoto"),
            ErroreReperto::PesoNonValido(s) => write!(f, "Peso non numerico: '{}'", s),
            ErroreReperto::PesoNegativo(p) => write!(f, "Il peso non puo essere negativo: {}", p),
            ErroreReperto::AnnoNonValido(s) => write!(f, "Anno non valido: '{}'", s),
        }
    }
}

// Conversione automatica da ParseIntError a ErroreReperto
impl From<ParseIntError> for ErroreReperto {
    fn from(e: ParseIntError) -> Self {
        ErroreReperto::AnnoNonValido(e.to_string())
    }
}

// ============================================================================
// FUNZIONI
// ============================================================================

/// Legge e valida un'eta (deve essere un numero positivo)
fn leggi_eta(input: &str) -> Result<i32, String> {
    // L'operatore ? propaga l'errore convertendolo in String
    let eta: i32 = input.parse().map_err(|e: ParseIntError| e.to_string())?;

    if eta < 0 {
        return Err(format!("L'eta non puo essere negativa: {}", eta));
    }

    Ok(eta)
}

/// Valida i dati di un reperto
fn valida_reperto(
    nome: &str,
    materiale: &str,
    peso_str: &str,
    anno_str: &str,
) -> Result<String, ErroreReperto> {
    // Valida nome
    if nome.is_empty() {
        return Err(ErroreReperto::NomeVuoto);
    }

    // Valida peso (puo fallire nel parsing)
    let peso: f64 = peso_str
        .parse()
        .map_err(|_| ErroreReperto::PesoNonValido(peso_str.to_string()))?;

    if peso < 0.0 {
        return Err(ErroreReperto::PesoNegativo(peso));
    }

    // Valida anno (usa From<ParseIntError> implementato sopra)
    let _anno: i32 = anno_str.parse()?;

    Ok(format!("{} ({}) - {}g", nome, materiale, peso))
}

/// Analizza un dato con possibili errori diversi
fn analizza_dato(input: &str) -> Result<String, String> {
    // Prima prova come intero
    if let Ok(n) = input.parse::<i32>() {
        if n < 0 {
            return Err(format!("Valore negativo non ammesso: {}", n));
        }
        return Ok(format!("Intero valido: {}", n));
    }

    // Poi prova come float
    if let Ok(f) = input.parse::<f64>() {
        return Ok(format!("Decimale valido: {:.2}", f));
    }

    Err(format!("'{}' non e un numero valido", input))
}

/// Processa i dati di uno scavo con validazione early-return
fn processa_scavo(sito: &str, anno: u32, reperti: u32) -> Result<String, String> {
    // Validazioni con early return
    if sito.is_empty() {
        return Err("Il nome del sito non puo essere vuoto".to_string());
    }

    if anno < 1900 || anno > 2030 {
        return Err(format!("Anno fuori range (1900-2030): {}", anno));
    }

    if reperti == 0 {
        return Err("Nessun reperto trovato".to_string());
    }

    // Percorso felice - tutto validato
    let densita = reperti as f64 / (2030 - anno + 1) as f64;
    Ok(format!(
        "Scavo '{}' ({}): {} reperti, densita {:.1}/anno",
        sito, anno, reperti, densita
    ))
}

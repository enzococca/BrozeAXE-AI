// ============================================================================
// CAPITOLO 1: LE BASI DI RUST
// ============================================================================
// Questo file copre tutti i fondamenti del linguaggio Rust.
// Esegui con: cargo run --example cap01_basi
// ============================================================================

fn main() {
    println!("╔══════════════════════════════════════════════╗");
    println!("║   CAPITOLO 1: LE BASI DI RUST               ║");
    println!("╚══════════════════════════════════════════════╝\n");

    // ========================================================================
    // 1.1 - VARIABILI E IMMUTABILITA
    // ========================================================================
    println!("--- 1.1 Variabili e Immutabilita ---\n");

    // In Rust, le variabili sono IMMUTABILI per default.
    // Questo e un design deliberato: ti costringe a dichiarare esplicitamente
    // quando vuoi che un valore possa cambiare.
    let x = 5;
    println!("x = {} (immutabile)", x);
    // x = 6; // ERRORE! Decommenta per vedere il messaggio del compilatore

    // Per rendere una variabile mutabile, usa `mut`
    let mut y = 10;
    println!("y = {} (mutabile, prima)", y);
    y = 20;
    println!("y = {} (mutabile, dopo)", y);

    // SHADOWING: puoi ridichiarare una variabile con lo stesso nome.
    // Non e la stessa cosa di `mut` - crea una NUOVA variabile.
    let z = 5;
    let z = z + 1;      // z e ora 6 (nuova variabile)
    let z = z * 2;      // z e ora 12 (un'altra nuova variabile)
    println!("z dopo shadowing = {}", z);

    // Lo shadowing permette anche di cambiare tipo!
    let spazi = "   ";           // &str (stringa)
    let spazi = spazi.len();     // usize (numero)
    println!("Numero di spazi: {}\n", spazi);

    // ========================================================================
    // 1.2 - TIPI DI DATO
    // ========================================================================
    println!("--- 1.2 Tipi di Dato ---\n");

    // INTERI
    let intero_8: i8 = -128;           // da -128 a 127
    let intero_16: i16 = -32_768;      // gli underscore migliorano la leggibilita
    let intero_32: i32 = 2_147_483_647;// tipo di default per interi
    let intero_64: i64 = 9_000_000_000_000;
    let intero_senza_segno: u32 = 42;  // solo positivi: da 0 a 4_294_967_295
    let intero_architettura: usize = 100; // dimensione dipende dalla CPU (32 o 64 bit)

    println!("i8:    {}", intero_8);
    println!("i16:   {}", intero_16);
    println!("i32:   {}", intero_32);
    println!("i64:   {}", intero_64);
    println!("u32:   {}", intero_senza_segno);
    println!("usize: {}", intero_architettura);

    // FLOAT (numeri decimali)
    let pi: f64 = 3.14159265358979;    // 64 bit - precisione doppia (default)
    let pi_corto: f32 = 3.14;          // 32 bit - precisione singola
    println!("pi (f64): {}", pi);
    println!("pi (f32): {}", pi_corto);

    // BOOLEANI
    let vero: bool = true;
    let falso = false;  // il tipo e inferito
    println!("vero: {}, falso: {}", vero, falso);

    // CARATTERI - Rust usa Unicode! Un char e 4 byte.
    let lettera = 'a';
    let emoji = '🦀';      // Si, anche le emoji!
    let ideogramma = '漢';
    println!("lettera: {}, emoji: {}, ideogramma: {}", lettera, emoji, ideogramma);

    // STRINGHE - Due tipi principali:
    let stringa_letterale: &str = "Sono una string slice";  // &str - immutabile, nello stack
    let stringa_owned: String = String::from("Sono una String"); // String - mutabile, nell'heap
    println!("{}", stringa_letterale);
    println!("{}\n", stringa_owned);

    // ========================================================================
    // 1.3 - COSTANTI
    // ========================================================================
    println!("--- 1.3 Costanti ---\n");

    // Le costanti sono SEMPRE immutabili (non puoi usare mut).
    // DEVONO avere il tipo annotato esplicitamente.
    // Convenzione: SCREAMING_SNAKE_CASE
    const VELOCITA_LUCE: u64 = 299_792_458;       // metri al secondo
    const PI_GRECO: f64 = 3.14159265358979;
    const MAX_REPERTI: usize = 10_000;

    println!("Velocita della luce: {} m/s", VELOCITA_LUCE);
    println!("Pi greco: {}", PI_GRECO);
    println!("Max reperti: {}\n", MAX_REPERTI);

    // ========================================================================
    // 1.4 - TUPLE E ARRAY
    // ========================================================================
    println!("--- 1.4 Tuple e Array ---\n");

    // TUPLE: raggruppano valori di tipi DIVERSI. Dimensione fissa.
    let reperto: (i32, f64, &str) = (1, 3.5, "Ascia di bronzo");

    // Accesso per posizione (destructuring)
    let (id, peso, nome) = reperto;
    println!("Reperto: id={}, peso={}kg, nome={}", id, peso, nome);

    // Accesso per indice con il punto
    println!("Primo elemento: {}", reperto.0);
    println!("Secondo elemento: {}", reperto.1);
    println!("Terzo elemento: {}", reperto.2);

    // ARRAY: tutti gli elementi dello STESSO tipo. Dimensione fissa.
    let mesi: [&str; 4] = ["Gennaio", "Febbraio", "Marzo", "Aprile"];
    println!("\nPrimo mese: {}", mesi[0]);
    println!("Terzo mese: {}", mesi[2]);

    // Array inizializzato con lo stesso valore
    let zeri = [0; 5]; // [0, 0, 0, 0, 0]
    println!("Array di zeri: {:?}\n", zeri);

    // ========================================================================
    // 1.5 - FUNZIONI
    // ========================================================================
    println!("--- 1.5 Funzioni ---\n");

    // Chiamata a funzioni definite sotto
    saluta("Archeologo");

    let somma = somma(15, 27);
    println!("15 + 27 = {}", somma);

    let area = area_rettangolo(5.0, 3.0);
    println!("Area rettangolo 5x3 = {:.1}", area);

    // Funzione che ritorna una tupla
    let (minimo, massimo) = trova_min_max(42, 17);
    println!("Min: {}, Max: {}", minimo, massimo);

    // In Rust, l'ultima espressione SENZA punto e virgola e il valore di ritorno.
    // Questo e un concetto importante: Rust e un linguaggio "expression-based".
    let risultato = {
        let a = 10;
        let b = 20;
        a + b  // NESSUN punto e virgola = questa e l'espressione restituita dal blocco
    };
    println!("Risultato del blocco: {}\n", risultato);

    // ========================================================================
    // 1.6 - CONTROLLO DI FLUSSO
    // ========================================================================
    println!("--- 1.6 Controllo di Flusso ---\n");

    // IF/ELSE - Le condizioni NON hanno parentesi (a differenza di C/Java)
    let temperatura = 25;
    if temperatura > 30 {
        println!("Fa caldo!");
    } else if temperatura > 20 {
        println!("Temperatura piacevole: {}°C", temperatura);
    } else {
        println!("Fa fresco!");
    }

    // IF come espressione (come il ternario in altri linguaggi)
    let stato = if temperatura > 20 { "caldo" } else { "freddo" };
    println!("Stato: {}", stato);

    // MATCH - Molto piu potente di switch/case
    let giorno = 3;
    let nome_giorno = match giorno {
        1 => "Lunedi",
        2 => "Martedi",
        3 => "Mercoledi",
        4 => "Giovedi",
        5 => "Venerdi",
        6 | 7 => "Weekend!",       // Pattern multipli con |
        _ => "Giorno non valido",   // _ = tutti gli altri casi (obbligatorio!)
    };
    println!("Giorno {}: {}", giorno, nome_giorno);

    // Match con range
    let voto = 85;
    let giudizio = match voto {
        90..=100 => "Eccellente",
        80..=89 => "Ottimo",
        70..=79 => "Buono",
        60..=69 => "Sufficiente",
        _ => "Insufficiente",
    };
    println!("Voto {}: {}\n", voto, giudizio);

    // ========================================================================
    // 1.7 - CICLI
    // ========================================================================
    println!("--- 1.7 Cicli ---\n");

    // LOOP - ciclo infinito (si interrompe con break)
    let mut contatore = 0;
    let risultato = loop {
        contatore += 1;
        if contatore == 5 {
            break contatore * 2;  // loop puo restituire un valore con break!
        }
    };
    println!("Risultato del loop: {}", risultato);

    // WHILE
    let mut n = 3;
    print!("Conto alla rovescia: ");
    while n > 0 {
        print!("{}... ", n);
        n -= 1;
    }
    println!("Via!");

    // FOR - il modo piu comune e sicuro per iterare
    print!("Numeri da 1 a 5: ");
    for i in 1..=5 {   // ..= include l'ultimo valore (range inclusivo)
        print!("{} ", i);
    }
    println!();

    // FOR su un array
    let reperti = ["Ascia", "Spada", "Fibula", "Anello"];
    println!("\nReperti trovati:");
    for (indice, reperto) in reperti.iter().enumerate() {
        println!("  {}. {}", indice + 1, reperto);
    }

    // FOR con range esclusivo (non include l'ultimo)
    print!("\nRange 0..5: ");
    for i in 0..5 {     // 0, 1, 2, 3, 4 (il 5 NON e incluso)
        print!("{} ", i);
    }
    println!();

    // LOOP ETICHETTATI - utili con cicli annidati
    println!("\nTabella 3x3 con loop etichettati:");
    'esterno: for riga in 1..=3 {
        for colonna in 1..=3 {
            if riga == 2 && colonna == 2 {
                println!("  ({},{}) -> skip!", riga, colonna);
                continue 'esterno;  // salta al prossimo ciclo esterno
            }
            print!("  ({},{}) ", riga, colonna);
        }
        println!();
    }

    // ========================================================================
    // 1.8 - MACRO println! E FORMATTAZIONE
    // ========================================================================
    println!("\n--- 1.8 Formattazione ---\n");

    let nome = "Ascia";
    let peso = 3.14159;
    let quantita = 42;

    // Formattazione di base
    println!("Nome: {}", nome);
    println!("Peso con 2 decimali: {:.2}", peso);
    println!("Quantita con padding: {:>10}", quantita);   // allineato a destra
    println!("Quantita con padding: {:<10}|", quantita);   // allineato a sinistra
    println!("Quantita con zeri: {:05}", quantita);        // 00042
    println!("Binario: {:b}", quantita);                   // 101010
    println!("Esadecimale: {:x}", quantita);               // 2a
    println!("Debug di un array: {:?}", [1, 2, 3]);        // [1, 2, 3]
    println!("Debug formattato: {:#?}", ("Rust", 2015, true)); // Pretty-print

    // Argomenti nominati
    println!(
        "{linguaggio} e stato creato nel {anno}",
        linguaggio = "Rust",
        anno = 2010
    );

    println!("\n✅ Capitolo 1 completato!");
}

// ============================================================================
// DEFINIZIONI DELLE FUNZIONI
// ============================================================================

/// Funzione che saluta qualcuno.
/// In Rust, i parametri DEVONO avere il tipo annotato.
fn saluta(nome: &str) {
    println!("Ciao, {}! Benvenuto nel mondo di Rust.", nome);
}

/// Funzione che somma due numeri e restituisce il risultato.
/// La freccia -> indica il tipo di ritorno.
fn somma(a: i32, b: i32) -> i32 {
    a + b  // Nessun punto e virgola = valore di ritorno (espressione)
    // Equivalente a: return a + b;
}

/// Calcola l'area di un rettangolo.
fn area_rettangolo(base: f64, altezza: f64) -> f64 {
    base * altezza
}

/// Trova il minimo e il massimo tra due numeri.
/// Restituisce una tupla (min, max).
fn trova_min_max(a: i32, b: i32) -> (i32, i32) {
    if a < b {
        (a, b)
    } else {
        (b, a)
    }
}

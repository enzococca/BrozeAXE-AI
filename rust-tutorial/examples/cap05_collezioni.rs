// ============================================================================
// CAPITOLO 5: COLLEZIONI
// ============================================================================
// Le tre collezioni piu usate in Rust:
// - Vec<T>: vettore dinamico (come ArrayList in Java, list in Python)
// - String: stringa mutabile UTF-8
// - HashMap<K, V>: mappa chiave-valore (come dict in Python)
//
// Bonus: iteratori e programmazione funzionale
//
// Esegui con: cargo run --example cap05_collezioni
// ============================================================================

use std::collections::HashMap;

fn main() {
    println!("╔══════════════════════════════════════════════╗");
    println!("║   CAPITOLO 5: COLLEZIONI                     ║");
    println!("╚══════════════════════════════════════════════╝\n");

    // ========================================================================
    // 5.1 - VEC<T> (VETTORI)
    // ========================================================================
    println!("--- 5.1 Vec<T> ---\n");

    // Creazione
    let mut reperti: Vec<String> = Vec::new(); // vettore vuoto
    let numeri = vec![1, 2, 3, 4, 5];          // macro vec! con valori iniziali
    let zeri = vec![0; 10];                     // 10 elementi, tutti 0

    println!("Numeri: {:?}", numeri);
    println!("Zeri: {:?}", zeri);

    // Aggiungere elementi
    reperti.push(String::from("Ascia"));
    reperti.push(String::from("Spada"));
    reperti.push(String::from("Fibula"));
    reperti.push(String::from("Anello"));
    reperti.push(String::from("Pugnale"));

    println!("Reperti: {:?}", reperti);
    println!("Lunghezza: {}", reperti.len());

    // Accesso sicuro con get() -> Option<&T>
    match reperti.get(2) {
        Some(r) => println!("Indice 2: {}", r),
        None => println!("Indice non valido"),
    }

    // Accesso diretto (panic se fuori range!)
    println!("Primo: {}", reperti[0]);
    // println!("{}", reperti[99]); // PANIC!

    // Rimuovere elementi
    let rimosso = reperti.pop(); // rimuove l'ultimo
    println!("Rimosso: {:?}", rimosso); // Some("Pugnale")

    reperti.remove(1); // rimuove all'indice 1 (Spada)
    println!("Dopo remove(1): {:?}", reperti);

    // Inserire a un indice specifico
    reperti.insert(0, String::from("Elmo"));
    println!("Dopo insert(0): {:?}", reperti);

    // Ordinamento
    reperti.sort();
    println!("Ordinato: {:?}", reperti);

    // Cercare
    println!("Contiene 'Ascia': {}", reperti.contains(&String::from("Ascia")));
    println!("Posizione 'Fibula': {:?}", reperti.iter().position(|r| r == "Fibula"));

    // Deduplicare (prima ordina!)
    let mut con_duplicati = vec![3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5];
    con_duplicati.sort();
    con_duplicati.dedup();
    println!("Senza duplicati: {:?}", con_duplicati);

    // Slicing
    let primi_due = &reperti[..2];
    println!("Primi due: {:?}", primi_due);

    println!();

    // ========================================================================
    // 5.2 - STRING E &str
    // ========================================================================
    println!("--- 5.2 String e &str ---\n");

    // Le stringhe in Rust sono UTF-8. Ci sono due tipi principali:
    // - &str: string slice, immutabile, reference a dati UTF-8
    // - String: stringa posseduta, mutabile, nell'heap

    // Creazione
    let letterale: &str = "Ciao mondo";              // &str (compilato nel binario)
    let posseduta = String::from("Ciao mondo");       // String
    let da_to_string = "Ciao mondo".to_string();      // &str -> String
    let da_format = format!("{} {}", "Ciao", "mondo");// format! -> String

    println!("{}, {}, {}, {}", letterale, posseduta, da_to_string, da_format);

    // Concatenazione
    let mut saluto = String::from("Benvenuto");
    saluto.push(' ');                    // un singolo carattere
    saluto.push_str("nel museo!");       // una stringa
    println!("{}", saluto);

    // Concatenazione con +  (nota: consuma il primo operando!)
    let parte1 = String::from("Eta del ");
    let parte2 = String::from("Bronzo");
    let insieme = parte1 + &parte2;  // parte1 e stata mossa!
    println!("{}", insieme);
    // println!("{}", parte1); // ERRORE! parte1 e stata consumata

    // format! non consuma nulla (preferibile per concatenazioni complesse)
    let sito = "Savignano";
    let anno = 2019;
    let descrizione = format!("Scavo di {} (anno {})", sito, anno);
    println!("{}", descrizione);

    // Iterare sui caratteri
    let parola = "Bronzo";
    print!("Caratteri: ");
    for c in parola.chars() {
        print!("{} ", c);
    }
    println!();

    // Iterare sui byte
    print!("Bytes: ");
    for b in parola.bytes() {
        print!("{} ", b);
    }
    println!();

    // Metodi utili
    let testo = "  Ascia di Bronzo  ";
    println!("\ntrim: '{}'", testo.trim());
    println!("to_uppercase: '{}'", testo.trim().to_uppercase());
    println!("to_lowercase: '{}'", testo.trim().to_lowercase());
    println!("contains 'Bronzo': {}", testo.contains("Bronzo"));
    println!("starts_with 'Ascia': {}", testo.trim().starts_with("Ascia"));
    println!("replace: '{}'", testo.trim().replace("Bronzo", "Ferro"));

    // Split
    let csv = "Ascia,Spada,Fibula,Anello";
    let pezzi: Vec<&str> = csv.split(',').collect();
    println!("Split: {:?}", pezzi);

    // ATTENZIONE con UTF-8: un "carattere" puo occupare piu byte!
    let emoji = "Ciao 🦀!";
    println!("\n'{}' ha {} byte ma {} caratteri",
        emoji, emoji.len(), emoji.chars().count());

    println!();

    // ========================================================================
    // 5.3 - HASHMAP<K, V>
    // ========================================================================
    println!("--- 5.3 HashMap<K, V> ---\n");

    // Creazione
    let mut inventario: HashMap<String, u32> = HashMap::new();

    // Inserimento
    inventario.insert(String::from("Asce"), 15);
    inventario.insert(String::from("Spade"), 8);
    inventario.insert(String::from("Fibule"), 23);
    inventario.insert(String::from("Anelli"), 12);

    println!("Inventario: {:?}", inventario);

    // Accesso
    match inventario.get("Asce") {
        Some(&count) => println!("Asce trovate: {}", count),
        None => println!("Nessuna ascia"),
    }

    // Accesso con default
    let lame = inventario.get("Lame").copied().unwrap_or(0);
    println!("Lame: {} (default 0)", lame);

    // Entry API: inserisci solo se la chiave non esiste
    inventario.entry(String::from("Lame")).or_insert(5);
    inventario.entry(String::from("Asce")).or_insert(999); // non modifica: esiste gia!
    println!("Dopo entry: Lame={}, Asce={}", inventario["Lame"], inventario["Asce"]);

    // Entry API: modifica il valore esistente
    let conteggio = inventario.entry(String::from("Asce")).or_insert(0);
    *conteggio += 10;
    println!("Asce dopo modifica: {}", inventario["Asce"]);

    // Iterazione
    println!("\nInventario completo:");
    for (tipo, quantita) in &inventario {
        println!("  {}: {} pezzi", tipo, quantita);
    }

    // Rimuovere
    inventario.remove("Lame");
    println!("\nDopo rimozione 'Lame': {}", inventario.contains_key("Lame"));

    // Conteggio parole (esempio classico)
    let testo = "bronzo ferro bronzo rame bronzo ferro oro bronzo";
    let mut conteggio_parole: HashMap<&str, u32> = HashMap::new();
    for parola in testo.split_whitespace() {
        let contatore = conteggio_parole.entry(parola).or_insert(0);
        *contatore += 1;
    }
    println!("\nConteggio parole:");
    let mut parole_ordinate: Vec<_> = conteggio_parole.iter().collect();
    parole_ordinate.sort_by(|a, b| b.1.cmp(a.1));
    for (parola, conteggio) in parole_ordinate {
        println!("  {}: {}", parola, conteggio);
    }

    println!();

    // ========================================================================
    // 5.4 - ITERATORI
    // ========================================================================
    println!("--- 5.4 Iteratori ---\n");

    // Gli iteratori sono uno dei punti di forza di Rust.
    // Sono LAZY: non fanno nulla finche non consumi i risultati.
    // Sono ZERO-COST: il compilatore li ottimizza quanto un loop manuale.

    let numeri = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

    // iter() -> iteratore su &T (reference)
    // into_iter() -> iteratore su T (consuma il vettore)
    // iter_mut() -> iteratore su &mut T (reference mutabile)

    // MAP: trasforma ogni elemento
    let doppi: Vec<i32> = numeri.iter().map(|&n| n * 2).collect();
    println!("Doppi: {:?}", doppi);

    // FILTER: seleziona elementi
    let pari: Vec<&i32> = numeri.iter().filter(|&&n| n % 2 == 0).collect();
    println!("Pari: {:?}", pari);

    // Combinazione map + filter (MOLTO comune in Rust)
    let quadrati_dei_pari: Vec<i32> = numeri.iter()
        .filter(|&&n| n % 2 == 0)
        .map(|&n| n * n)
        .collect();
    println!("Quadrati dei pari: {:?}", quadrati_dei_pari);

    // FOLD: riduce a un singolo valore (come reduce in Python/JS)
    let somma: i32 = numeri.iter().fold(0, |acc, &n| acc + n);
    println!("Somma (fold): {}", somma);

    // SUM: scorciatoia per la somma
    let somma: i32 = numeri.iter().sum();
    println!("Somma (sum): {}", somma);

    // ENUMERATE: aggiunge l'indice
    println!("\nCon indice:");
    for (i, n) in numeri.iter().enumerate().take(5) {
        println!("  [{}] = {}", i, n);
    }

    // ZIP: combina due iteratori
    let nomi = vec!["Ascia", "Spada", "Fibula"];
    let pesi = vec![350, 800, 45];
    let catalogo: Vec<_> = nomi.iter().zip(pesi.iter()).collect();
    println!("\nZip: {:?}", catalogo);

    // CHAIN: concatena iteratori
    let primi = vec![1, 2, 3];
    let secondi = vec![4, 5, 6];
    let tutti: Vec<&i32> = primi.iter().chain(secondi.iter()).collect();
    println!("Chain: {:?}", tutti);

    // FIND: trova il primo elemento che soddisfa una condizione
    let primo_maggiore_5 = numeri.iter().find(|&&n| n > 5);
    println!("Primo > 5: {:?}", primo_maggiore_5);

    // ANY e ALL
    println!("Qualcuno > 5: {}", numeri.iter().any(|&n| n > 5));
    println!("Tutti > 0: {}", numeri.iter().all(|&n| n > 0));

    // COUNT e MIN/MAX
    println!("Quanti pari: {}", numeri.iter().filter(|&&n| n % 2 == 0).count());
    println!("Minimo: {:?}", numeri.iter().min());
    println!("Massimo: {:?}", numeri.iter().max());

    // FLAT_MAP: mappa e appiattisce
    let frasi = vec!["ciao mondo", "hello world"];
    let parole: Vec<&str> = frasi.iter().flat_map(|s| s.split(' ')).collect();
    println!("Flat map: {:?}", parole);

    // WINDOWS e CHUNKS
    let dati = vec![1, 2, 3, 4, 5, 6];
    let finestre: Vec<&[i32]> = dati.windows(3).collect();
    println!("\nWindows(3): {:?}", finestre);

    let blocchi: Vec<&[i32]> = dati.chunks(2).collect();
    println!("Chunks(2): {:?}", blocchi);

    println!();

    // ========================================================================
    // 5.5 - ESEMPIO PRATICO: ANALISI DATI ARCHEOLOGICI
    // ========================================================================
    println!("--- 5.5 Esempio: Analisi Dati ---\n");

    let reperti = vec![
        Reperto { nome: "Ascia tipo A".into(), peso: 350.0, periodo: "BF".into() },
        Reperto { nome: "Ascia tipo B".into(), peso: 420.0, periodo: "BF".into() },
        Reperto { nome: "Spada corta".into(), peso: 800.0, periodo: "BR".into() },
        Reperto { nome: "Fibula".into(), peso: 45.0, periodo: "EF".into() },
        Reperto { nome: "Pugnale".into(), peso: 280.0, periodo: "BF".into() },
        Reperto { nome: "Ascia tipo C".into(), peso: 390.0, periodo: "BR".into() },
        Reperto { nome: "Anello".into(), peso: 15.0, periodo: "EF".into() },
        Reperto { nome: "Punta di lancia".into(), peso: 150.0, periodo: "BF".into() },
    ];

    // Peso medio
    let peso_medio = reperti.iter().map(|r| r.peso).sum::<f64>() / reperti.len() as f64;
    println!("Peso medio: {:.1}g", peso_medio);

    // Reperto piu pesante
    let piu_pesante = reperti.iter().max_by(|a, b| a.peso.partial_cmp(&b.peso).unwrap());
    if let Some(r) = piu_pesante {
        println!("Piu pesante: {} ({:.0}g)", r.nome, r.peso);
    }

    // Reperto piu leggero
    let piu_leggero = reperti.iter().min_by(|a, b| a.peso.partial_cmp(&b.peso).unwrap());
    if let Some(r) = piu_leggero {
        println!("Piu leggero: {} ({:.0}g)", r.nome, r.peso);
    }

    // Raggruppamento per periodo
    let mut per_periodo: HashMap<&str, Vec<&Reperto>> = HashMap::new();
    for r in &reperti {
        per_periodo.entry(&r.periodo).or_default().push(r);
    }

    println!("\nReperti per periodo:");
    for (periodo, gruppo) in &per_periodo {
        let periodo_nome = match *periodo {
            "BR" => "Bronzo Recente",
            "BF" => "Bronzo Finale",
            "EF" => "Eta del Ferro",
            _ => periodo,
        };
        let peso_medio_gruppo = gruppo.iter().map(|r| r.peso).sum::<f64>() / gruppo.len() as f64;
        println!("  {} ({} pezzi, peso medio {:.0}g):", periodo_nome, gruppo.len(), peso_medio_gruppo);
        for r in gruppo {
            println!("    - {} ({:.0}g)", r.nome, r.peso);
        }
    }

    // Solo le asce, ordinate per peso
    let mut asce: Vec<&Reperto> = reperti.iter()
        .filter(|r| r.nome.contains("Ascia"))
        .collect();
    asce.sort_by(|a, b| a.peso.partial_cmp(&b.peso).unwrap());

    println!("\nAsce ordinate per peso:");
    for ascia in &asce {
        println!("  {} - {:.0}g", ascia.nome, ascia.peso);
    }

    println!("\n✅ Capitolo 5 completato!");
}

// ============================================================================
// TIPI
// ============================================================================

#[derive(Debug)]
struct Reperto {
    nome: String,
    peso: f64,
    periodo: String,
}

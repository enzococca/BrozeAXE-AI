// ============================================================================
// CAPITOLO 8: CONCORRENZA
// ============================================================================
// Rust garantisce la sicurezza della concorrenza A TEMPO DI COMPILAZIONE.
// "Fearless concurrency": se compila, non hai data race.
//
// Concetti:
// - Thread: unita di esecuzione parallela
// - Message Passing: canali (mpsc) per comunicare tra thread
// - Shared State: Mutex e Arc per condividere dati
//
// Esegui con: cargo run --example cap08_concorrenza
// ============================================================================

use std::sync::{Arc, Mutex};
use std::sync::mpsc;
use std::thread;
use std::time::Duration;
use std::collections::HashMap;

fn main() {
    println!("╔══════════════════════════════════════════════╗");
    println!("║   CAPITOLO 8: CONCORRENZA                    ║");
    println!("╚══════════════════════════════════════════════╝\n");

    // ========================================================================
    // 8.1 - CREARE THREAD
    // ========================================================================
    println!("--- 8.1 Thread di base ---\n");

    // thread::spawn crea un nuovo thread
    let handle = thread::spawn(|| {
        for i in 1..=3 {
            println!("  [Thread figlio] contatore: {}", i);
            thread::sleep(Duration::from_millis(10));
        }
        42 // il thread restituisce un valore
    });

    for i in 1..=3 {
        println!("  [Thread main] contatore: {}", i);
        thread::sleep(Duration::from_millis(10));
    }

    // .join() aspetta che il thread finisca e recupera il valore di ritorno
    let risultato = handle.join().unwrap();
    println!("  Il thread figlio ha restituito: {}\n", risultato);

    // ========================================================================
    // 8.2 - MOVE CLOSURE (SPOSTARE DATI NEI THREAD)
    // ========================================================================
    println!("--- 8.2 Move Closure ---\n");

    // Per usare dati del thread principale in un thread figlio,
    // devi SPOSTARE l'ownership con `move`

    let messaggio = String::from("Ciao dal thread principale!");

    let handle = thread::spawn(move || {
        // `messaggio` e stato MOSSO qui. Il thread principale non puo piu usarlo.
        println!("  Thread figlio riceve: {}", messaggio);
    });

    // println!("{}", messaggio); // ERRORE! `messaggio` e stato mosso
    handle.join().unwrap();

    // Se vuoi CONDIVIDERE dati (non spostare), devi usare Arc (vedi sezione 8.4)

    println!();

    // ========================================================================
    // 8.3 - CANALI (MESSAGE PASSING)
    // ========================================================================
    println!("--- 8.3 Canali (mpsc) ---\n");

    // mpsc = Multi-Producer, Single-Consumer
    // Un canale ha due estremita:
    // - tx (transmitter): invia messaggi
    // - rx (receiver): riceve messaggi

    let (tx, rx) = mpsc::channel();

    // Thread produttore
    thread::spawn(move || {
        let reperti = vec![
            "Ascia a margini rialzati",
            "Spada tipo Allerona",
            "Fibula ad arco",
            "Pugnale a lingua",
        ];

        for reperto in reperti {
            tx.send(reperto.to_string()).unwrap();
            println!("  [Produttore] Inviato: {}", reperto);
            thread::sleep(Duration::from_millis(50));
        }
        // `tx` viene droppato qui -> il canale si chiude
    });

    // Thread consumatore (main)
    println!("  [Consumatore] In attesa...");
    // rx.recv() BLOCCA finche non riceve un messaggio
    // Quando il canale si chiude, recv() restituisce Err
    for messaggio in rx {
        println!("  [Consumatore] Ricevuto: {}", messaggio);
    }
    println!("  Canale chiuso - tutti i messaggi ricevuti\n");

    // ========================================================================
    // 8.3b - PRODUTTORI MULTIPLI
    // ========================================================================
    println!("--- 8.3b Produttori Multipli ---\n");

    let (tx, rx) = mpsc::channel();

    // Clona il trasmettitore per ogni produttore
    for sito_id in 1..=3 {
        let tx_clone = tx.clone();
        thread::spawn(move || {
            let messaggio = format!("Reperto dal sito #{}", sito_id);
            tx_clone.send(messaggio).unwrap();
        });
    }

    // Droppa il trasmettitore originale (altrimenti rx non si chiude mai)
    drop(tx);

    for msg in rx {
        println!("  Ricevuto: {}", msg);
    }

    println!();

    // ========================================================================
    // 8.4 - STATO CONDIVISO: MUTEX E ARC
    // ========================================================================
    println!("--- 8.4 Mutex e Arc ---\n");

    // Mutex<T> = Mutual Exclusion: solo un thread alla volta puo accedere ai dati
    // Arc<T> = Atomic Reference Counting: permette ownership condivisa tra thread
    //          (come Rc<T>, ma thread-safe)

    // Esempio: contatore condiviso tra 10 thread
    let contatore = Arc::new(Mutex::new(0));
    let mut handles = vec![];

    for i in 0..10 {
        let contatore = Arc::clone(&contatore);
        let handle = thread::spawn(move || {
            // .lock() acquisisce il mutex (blocca finche non disponibile)
            let mut num = contatore.lock().unwrap();
            *num += 1;
            println!("  Thread {} ha incrementato a {}", i, *num);
            // Il lock viene rilasciato automaticamente quando `num` esce dallo scope
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    println!("  Risultato finale: {}", *contatore.lock().unwrap());
    println!();

    // ========================================================================
    // 8.5 - ESEMPIO PRATICO: ANALISI PARALLELA
    // ========================================================================
    println!("--- 8.5 Analisi Parallela di Reperti ---\n");

    // Simuliamo l'analisi parallela di reperti archeologici
    // Ogni thread analizza un gruppo di reperti e invia i risultati

    let reperti = vec![
        ("Ascia tipo A", 350.0, "BF"),
        ("Ascia tipo B", 420.0, "BF"),
        ("Spada corta", 800.0, "BR"),
        ("Fibula", 45.0, "EF"),
        ("Pugnale", 280.0, "BF"),
        ("Punta di lancia", 150.0, "BR"),
        ("Anello", 15.0, "EF"),
        ("Ascia tipo C", 390.0, "BF"),
        ("Falce", 200.0, "BR"),
    ];

    let (tx, rx) = mpsc::channel();
    let risultati_globali = Arc::new(Mutex::new(HashMap::new()));

    // Dividi i reperti in gruppi e analizza in parallelo
    let chunk_size = 3;
    let chunks: Vec<Vec<(&str, f64, &str)>> = reperti
        .chunks(chunk_size)
        .map(|c| c.to_vec())
        .collect();

    let n_threads = chunks.len();
    println!("  Avvio {} thread di analisi...\n", n_threads);

    for (thread_id, chunk) in chunks.into_iter().enumerate() {
        let tx = tx.clone();
        let risultati = Arc::clone(&risultati_globali);

        thread::spawn(move || {
            for (nome, peso, periodo) in &chunk {
                // "Analisi" simulata
                let punteggio = peso / 100.0 + nome.len() as f64 * 0.5;

                // Salva nel risultato globale
                let mut map = risultati.lock().unwrap();
                map.insert(nome.to_string(), punteggio);

                // Invia messaggio al thread principale
                tx.send(format!(
                    "[T{}] Analizzato '{}' ({}): punteggio {:.1}",
                    thread_id, nome, periodo, punteggio
                )).unwrap();

                thread::sleep(Duration::from_millis(20));
            }
        });
    }

    drop(tx); // Chiudi il canale

    // Raccogli tutti i messaggi
    for msg in rx {
        println!("  {}", msg);
    }

    // Mostra risultati aggregati
    let risultati = risultati_globali.lock().unwrap();
    println!("\n  Risultati aggregati ({} reperti):", risultati.len());

    let mut sorted: Vec<_> = risultati.iter().collect();
    sorted.sort_by(|a, b| b.1.partial_cmp(a.1).unwrap());

    for (nome, punteggio) in &sorted {
        let barre = "#".repeat((*punteggio * 2.0) as usize);
        println!("    {:<25} {:.1} {}", nome, punteggio, barre);
    }

    let media: f64 = risultati.values().sum::<f64>() / risultati.len() as f64;
    println!("\n  Punteggio medio: {:.1}", media);

    println!();

    // ========================================================================
    // 8.6 - SEND E SYNC TRAITS
    // ========================================================================
    println!("--- 8.6 Send e Sync ---\n");

    // Rust ha due traits marker per la concorrenza:
    //
    // Send: un tipo puo essere TRASFERITO tra thread
    //   - Quasi tutti i tipi sono Send
    //   - Eccezione: Rc<T> (non thread-safe, usa Arc<T> invece)
    //
    // Sync: un tipo puo essere RIFERITO da piu thread contemporaneamente
    //   - T e Sync se &T e Send
    //   - Mutex<T> e Sync (anche se T non lo e)
    //   - Rc<T> non e Sync
    //
    // Il compilatore verifica automaticamente questi traits.
    // Se provi a inviare un tipo non-Send a un thread, ERRORE di compilazione!

    println!("  i32: Send + Sync (puo essere condiviso liberamente)");
    println!("  String: Send + Sync");
    println!("  Vec<T>: Send + Sync (se T e Send + Sync)");
    println!("  Arc<T>: Send + Sync (se T e Send + Sync)");
    println!("  Mutex<T>: Send + Sync (anche se T non e Sync)");
    println!("  Rc<T>: NE Send NE Sync (solo per singolo thread)");
    println!();
    println!("  Se provi a usare Rc<T> in un thread:");
    println!("    let rc = Rc::new(5);");
    println!("    thread::spawn(move || {{ rc }});");
    println!("    // ERRORE: `Rc<i32>` cannot be sent between threads safely");

    println!();

    // ========================================================================
    // 8.7 - PATTERN PRODUTTORE-CONSUMATORE
    // ========================================================================
    println!("--- 8.7 Pattern Produttore-Consumatore ---\n");

    // Un pattern classico: un thread produce dati, un altro li consuma
    // Utile per pipeline di elaborazione

    let (tx_raw, rx_raw) = mpsc::channel::<String>();
    let (tx_processed, rx_processed) = mpsc::channel::<String>();

    // Stage 1: Produttore - genera dati grezzi
    thread::spawn(move || {
        let dati = vec!["ascia_001", "spada_002", "fibula_003", "pugnale_004"];
        for dato in dati {
            tx_raw.send(dato.to_string()).unwrap();
        }
    });

    // Stage 2: Processore - elabora i dati
    thread::spawn(move || {
        for dato_grezzo in rx_raw {
            let processato = format!(
                "[ELABORATO] {} -> {}",
                dato_grezzo,
                dato_grezzo.to_uppercase().replace("_", " #")
            );
            tx_processed.send(processato).unwrap();
        }
    });

    // Stage 3: Consumatore (main) - raccoglie i risultati
    println!("  Pipeline a 3 stadi:");
    for risultato in rx_processed {
        println!("    {}", risultato);
    }

    // ========================================================================
    // 8.8 - RIEPILOGO
    // ========================================================================
    println!("\n--- 8.8 Riepilogo ---\n");

    println!("┌──────────────────────────────────────────────────┐");
    println!("│  STRUMENTI DI CONCORRENZA IN RUST               │");
    println!("├──────────────────────────────────────────────────┤");
    println!("│                                                  │");
    println!("│  thread::spawn  -> crea un nuovo thread          │");
    println!("│  handle.join()  -> aspetta che il thread finisca │");
    println!("│  move ||        -> sposta dati nel thread        │");
    println!("│                                                  │");
    println!("│  mpsc::channel  -> comunicazione tra thread      │");
    println!("│  tx.send()      -> invia un messaggio            │");
    println!("│  rx.recv()      -> ricevi un messaggio           │");
    println!("│                                                  │");
    println!("│  Mutex<T>       -> accesso esclusivo ai dati     │");
    println!("│  Arc<T>         -> ownership condivisa (thread)  │");
    println!("│  Arc<Mutex<T>>  -> dati condivisi e mutabili     │");
    println!("│                                                  │");
    println!("│  Send trait     -> tipo trasferibile tra thread  │");
    println!("│  Sync trait     -> tipo riferibile da piu thread │");
    println!("│                                                  │");
    println!("│  GARANZIA: se compila, niente data race!         │");
    println!("│                                                  │");
    println!("└──────────────────────────────────────────────────┘");

    println!("\n✅ Capitolo 8 completato!");
}

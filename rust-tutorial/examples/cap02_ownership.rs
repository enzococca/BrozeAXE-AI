// ============================================================================
// CAPITOLO 2: OWNERSHIP E BORROWING
// ============================================================================
// Questo e IL concetto fondamentale di Rust. Capire l'ownership e la chiave
// per padroneggiare il linguaggio. E il sistema che permette a Rust di
// garantire la sicurezza della memoria SENZA garbage collector.
//
// Esegui con: cargo run --example cap02_ownership
// ============================================================================

fn main() {
    println!("╔══════════════════════════════════════════════╗");
    println!("║   CAPITOLO 2: OWNERSHIP E BORROWING          ║");
    println!("╚══════════════════════════════════════════════╝\n");

    // ========================================================================
    // 2.1 - LE TRE REGOLE DELL'OWNERSHIP
    // ========================================================================
    println!("--- 2.1 Le Tre Regole dell'Ownership ---\n");

    // REGOLA 1: Ogni valore in Rust ha una variabile che e il suo "owner"
    // REGOLA 2: Ci puo essere UN SOLO owner alla volta
    // REGOLA 3: Quando l'owner esce dallo scope, il valore viene deallocato (drop)

    {
        // `s` e l'owner della String "ciao"
        let s = String::from("ciao");
        println!("Dentro lo scope: {}", s);
    } // <-- Qui `s` esce dallo scope. Rust chiama automaticamente `drop()`.
      //     La memoria della String viene liberata. NESSUN garbage collector necessario.

    // println!("{}", s); // ERRORE! `s` non esiste piu.

    println!("La String e stata deallocata automaticamente\n");

    // ========================================================================
    // 2.2 - MOVE (SPOSTAMENTO)
    // ========================================================================
    println!("--- 2.2 Move ---\n");

    // Con i tipi che vivono nell'HEAP (come String), l'assegnamento
    // SPOSTA l'ownership. Il valore originale non e piu valido.

    let s1 = String::from("Ascia di bronzo");
    let s2 = s1;  // s1 viene MOSSO in s2. s1 non e piu valido!

    // println!("{}", s1); // ERRORE! "value used here after move"
    println!("s2 = {} (s1 e stato mosso qui)", s2);

    // PERCHE? Perche String contiene un puntatore ai dati nell'heap.
    // Se entrambi s1 e s2 puntassero agli stessi dati, quando uno dei due
    // esce dallo scope, i dati verrebbero liberati e l'altro avrebbe un
    // "dangling pointer" (puntatore a memoria liberata). Rust lo impedisce!

    // Lo stesso avviene quando passi un valore a una funzione:
    let reperto = String::from("Fibula");
    prendi_ownership(reperto);
    // println!("{}", reperto); // ERRORE! `reperto` e stato mosso nella funzione

    println!();

    // ========================================================================
    // 2.3 - COPY (PER TIPI SEMPLICI)
    // ========================================================================
    println!("--- 2.3 Copy (tipi semplici) ---\n");

    // I tipi che vivono nello STACK (interi, float, bool, char) implementano
    // il trait Copy. Per loro, l'assegnamento COPIA il valore (non lo muove).

    let a = 42;
    let b = a;  // `a` viene COPIATO (non mosso)
    println!("a = {}, b = {} (entrambi validi!)", a, b);

    let x = 3.14;
    let y = x;  // Anche i float vengono copiati
    println!("x = {}, y = {}", x, y);

    let vero = true;
    let anche_vero = vero;  // Anche i bool vengono copiati
    println!("vero = {}, anche_vero = {}", vero, anche_vero);

    // Perche la differenza? I tipi stack hanno dimensione nota e sono piccoli.
    // Copiarli e veloce quanto spostarli. I tipi heap (String, Vec, etc.)
    // possono essere enormi - copiarli sarebbe costoso e va fatto esplicitamente.

    println!();

    // ========================================================================
    // 2.4 - CLONE (COPIA PROFONDA)
    // ========================================================================
    println!("--- 2.4 Clone ---\n");

    // Se VUOI copiare un valore heap, devi usare `.clone()` esplicitamente.
    // Questo fa una "deep copy" - copia tutti i dati nell'heap.

    let originale = String::from("Reperto archeologico");
    let copia = originale.clone();

    // Entrambi sono validi perche sono dati indipendenti nell'heap
    println!("Originale: {}", originale);
    println!("Copia:     {}", copia);

    // `.clone()` e costoso per dati grandi - Rust ti costringe a essere esplicito
    // quando vuoi pagare questo costo, invece di farlo silenziosamente.

    println!();

    // ========================================================================
    // 2.5 - REFERENCES E BORROWING
    // ========================================================================
    println!("--- 2.5 References e Borrowing ---\n");

    // Spesso vuoi usare un valore SENZA prenderne l'ownership.
    // Questo si chiama "borrowing" (prestito) e si fa con & (reference).

    let messaggio = String::from("Il bronzo e una lega di rame e stagno");

    // &messaggio crea una REFERENCE (riferimento). Non sposta l'ownership.
    let lunghezza = calcola_lunghezza(&messaggio);
    println!("\"{}\" ha {} caratteri", messaggio, lunghezza);
    // `messaggio` e ancora valido! L'abbiamo solo "prestato" alla funzione.

    // Le references sono IMMUTABILI per default - non puoi modificare
    // il dato attraverso una reference.

    // Puoi avere INFINITE references immutabili contemporaneamente:
    let r1 = &messaggio;
    let r2 = &messaggio;
    let r3 = &messaggio;
    println!("r1: {}", r1);
    println!("r2: {}", r2);
    println!("r3: {}", r3);

    println!();

    // ========================================================================
    // 2.6 - MUTABLE REFERENCES
    // ========================================================================
    println!("--- 2.6 Mutable References ---\n");

    // Per modificare un dato in prestito, serve una reference MUTABILE: &mut

    let mut testo = String::from("Ciao");
    println!("Prima: {}", testo);

    aggiungi_esclamativo(&mut testo);
    println!("Dopo:  {}", testo);

    // REGOLA FONDAMENTALE:
    // Puoi avere O:
    //   - UNA sola reference mutabile (&mut T)
    //   - OPPURE quante reference immutabili vuoi (&T)
    // Ma MAI entrambe contemporaneamente!

    // Questo impedisce i DATA RACE (due thread che modificano lo stesso dato).

    let mut dati = String::from("dati");

    let r1 = &dati;      // OK - reference immutabile
    let r2 = &dati;      // OK - un'altra reference immutabile
    println!("r1: {}, r2: {}", r1, r2);
    // r1 e r2 non vengono piu usati dopo questa riga (NLL - Non-Lexical Lifetimes)

    let r3 = &mut dati;  // OK - nessuna reference immutabile e ancora attiva
    r3.push_str(" modificati");
    println!("r3: {}", r3);

    // Nota: in versioni vecchie di Rust questo sarebbe stato un errore.
    // NLL (Non-Lexical Lifetimes) permette al compilatore di capire che
    // r1 e r2 non sono piu usati dopo il println!, quindi r3 e sicuro.

    println!();

    // ========================================================================
    // 2.7 - DANGLING REFERENCES (IMPOSSIBILI IN RUST)
    // ========================================================================
    println!("--- 2.7 Dangling References (impossibili!) ---\n");

    // In C/C++ puoi creare un puntatore a memoria gia liberata.
    // In Rust questo e IMPOSSIBILE - il compilatore lo impedisce.

    // Questa funzione NON compilerebbe:
    // fn dangling() -> &String {
    //     let s = String::from("ciao");
    //     &s  // ERRORE! `s` viene deallocato alla fine della funzione
    //         // ma stiamo provando a restituire una reference ad esso
    // }

    // La soluzione e restituire il valore direttamente (spostando l'ownership):
    let s = non_dangling();
    println!("Valore restituito (non dangling): {}", s);

    println!();

    // ========================================================================
    // 2.8 - SLICES
    // ========================================================================
    println!("--- 2.8 Slices ---\n");

    // Le slices sono references a una PORZIONE di una collezione.
    // Non hanno ownership dei dati.

    let frase = String::from("Eta del Bronzo Finale");

    // String slices (&str)
    let prima_parola = &frase[0..3];      // "Eta"
    let seconda_parola = &frase[8..14];   // "Bronzo"
    println!("Prima parola: {}", prima_parola);
    println!("Seconda parola: {}", seconda_parola);

    // Sintassi abbreviata
    let inizio = &frase[..3];     // dall'inizio fino a 3 (escluso)
    let fine = &frase[14..];      // da 14 fino alla fine
    let tutto = &frase[..];       // tutta la stringa
    println!("Inizio: {}", inizio);
    println!("Fine: {}", fine);
    println!("Tutto: {}", tutto);

    // Funzione che trova la prima parola
    let parola = prima_parola_fn(&frase);
    println!("\nPrima parola (trovata): {}", parola);

    // Le slices funzionano anche con gli array!
    let numeri = [10, 20, 30, 40, 50];
    let fetta = &numeri[1..4];  // [20, 30, 40]
    println!("Slice di array: {:?}", fetta);

    println!();

    // ========================================================================
    // 2.9 - OWNERSHIP CON STRUCT (ANTEPRIMA)
    // ========================================================================
    println!("--- 2.9 Ownership con le Struct ---\n");

    // L'ownership si applica anche ai campi delle struct.

    let reperto1 = crea_reperto(String::from("Ascia"), 1250);
    println!("Reperto: {} ({}a.C.)", reperto1.0, reperto1.1);

    // Se passi la struct a una funzione, viene MOSSA (a meno che non usi &)
    stampa_reperto(&reperto1);
    println!("Reperto ancora valido: {}", reperto1.0); // OK perche abbiamo usato &

    println!();

    // ========================================================================
    // 2.10 - RIEPILOGO VISUALE
    // ========================================================================
    println!("--- 2.10 Riepilogo ---\n");

    println!("┌──────────────────────────────────────────────┐");
    println!("│  RIEPILOGO OWNERSHIP E BORROWING             │");
    println!("├──────────────────────────────────────────────┤");
    println!("│                                              │");
    println!("│  let s1 = String::from(\"ciao\");              │");
    println!("│  let s2 = s1;    // MOVE: s1 non valido     │");
    println!("│  let s3 = s2.clone(); // CLONE: copia deep  │");
    println!("│                                              │");
    println!("│  let r = &s2;    // BORROW: prestito immut. │");
    println!("│  let m = &mut s; // BORROW: prestito mut.   │");
    println!("│                                              │");
    println!("│  REGOLE:                                     │");
    println!("│  - 1 owner alla volta                        │");
    println!("│  - N riferimenti immutabili (&T) OPPURE      │");
    println!("│    1 riferimento mutabile (&mut T)           │");
    println!("│  - I riferimenti devono sempre essere validi │");
    println!("│                                              │");
    println!("└──────────────────────────────────────────────┘");

    println!("\n✅ Capitolo 2 completato!");
}

// ============================================================================
// FUNZIONI DI SUPPORTO
// ============================================================================

/// Questa funzione prende ownership della String.
/// Dopo la chiamata, il chiamante non puo piu usare il valore.
fn prendi_ownership(s: String) {
    println!("Ho preso ownership di: \"{}\"", s);
} // `s` viene deallocato qui

/// Questa funzione PRENDE IN PRESTITO la String (reference immutabile).
/// Il chiamante mantiene l'ownership.
fn calcola_lunghezza(s: &String) -> usize {
    s.len()
    // `s` e solo una reference - non viene deallocato nulla qui
}

/// Questa funzione prende una reference MUTABILE e modifica la String.
fn aggiungi_esclamativo(s: &mut String) {
    s.push('!');
}

/// NON dangling - restituisce il valore (sposta l'ownership al chiamante)
fn non_dangling() -> String {
    let s = String::from("Sono al sicuro!");
    s  // l'ownership di `s` viene spostata al chiamante
}

/// Trova la prima parola in una stringa (restituisce una slice)
fn prima_parola_fn(s: &str) -> &str {
    let bytes = s.as_bytes();

    for (i, &byte) in bytes.iter().enumerate() {
        if byte == b' ' {
            return &s[..i];
        }
    }

    s // se non ci sono spazi, tutta la stringa e una parola
}

/// Crea un reperto come tupla
fn crea_reperto(nome: String, anno: i32) -> (String, i32) {
    (nome, anno)
}

/// Stampa un reperto prendendo in prestito la tupla
fn stampa_reperto(reperto: &(String, i32)) {
    println!("  -> Reperto: {} dall'anno {}a.C.", reperto.0, reperto.1);
}

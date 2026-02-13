# Tutorial Rust: Da Zero a Hero

## Guida completa al linguaggio Rust con esempi reali e funzionanti

---

## Indice

1. [Perche Rust?](#perche-rust)
2. [Dove si usa Rust?](#dove-si-usa-rust)
3. [Capitolo 1: Le Basi](#capitolo-1-le-basi)
4. [Capitolo 2: Ownership e Borrowing](#capitolo-2-ownership-e-borrowing)
5. [Capitolo 3: Struct, Enum e Pattern Matching](#capitolo-3-struct-enum-e-pattern-matching)
6. [Capitolo 4: Gestione degli Errori](#capitolo-4-gestione-degli-errori)
7. [Capitolo 5: Collezioni](#capitolo-5-collezioni)
8. [Capitolo 6: Traits e Generics](#capitolo-6-traits-e-generics)
9. [Capitolo 7: Moduli e Organizzazione](#capitolo-7-moduli-e-organizzazione)
10. [Capitolo 8: Concorrenza](#capitolo-8-concorrenza)
11. [Capitolo 9: Progetto Finale](#capitolo-9-progetto-finale)

---

## Perche Rust?

### Il problema che Rust risolve

Nei linguaggi tradizionali hai due scelte:

- **C/C++**: Velocissimi, ma pieni di bug di memoria (buffer overflow, use-after-free, data race).
  Questi bug causano circa il **70% delle vulnerabilita di sicurezza** nei software di grandi aziende
  (fonte: Microsoft, Google, Mozilla).

- **Python/Java/Go**: Sicuri grazie al Garbage Collector, ma piu lenti e con meno controllo
  sulla memoria.

**Rust rompe questo compromesso**: ti da le prestazioni di C/C++ con la sicurezza di un linguaggio
gestito, **senza Garbage Collector**. Come? Con il sistema di **Ownership** - un insieme di regole
che il compilatore verifica a tempo di compilazione. Se il codice compila, non hai bug di memoria.
Punto.

### I 5 motivi principali per scegliere Rust

| Motivo | Dettaglio |
|--------|-----------|
| **Sicurezza della memoria** | Nessun null pointer, nessun buffer overflow, nessun data race - garantito dal compilatore |
| **Prestazioni** | Veloce quanto C/C++. Zero-cost abstractions: le astrazioni di alto livello non costano nulla a runtime |
| **Concorrenza senza paura** | Il compilatore impedisce i data race. Puoi scrivere codice parallelo senza i bug tipici del multithreading |
| **Ecosistema moderno** | Cargo (package manager), crates.io (repository), rustfmt (formattazione), clippy (linting) |
| **Messaggi di errore eccellenti** | Il compilatore Rust ti dice esattamente cosa hai sbagliato e come correggerlo |

### Confronto prestazioni reale

```
Benchmark: Parsing di 1 milione di righe JSON

Python:     12.4 secondi
Java:        1.8 secondi
Go:          0.9 secondi
Rust:        0.3 secondi
C:           0.3 secondi
```

Rust raggiunge le prestazioni di C con la sicurezza di Java/Go.

---

## Dove si usa Rust?

### Aziende che usano Rust in produzione

| Azienda | Uso |
|---------|-----|
| **Mozilla** | Firefox (motore Servo/Stylo), il linguaggio e nato qui |
| **Google** | Android (parti del kernel), ChromeOS, Fuchsia OS |
| **Microsoft** | Windows kernel, Azure, tool di sviluppo |
| **Amazon AWS** | Firecracker (microVM per Lambda/Fargate), Bottlerocket OS |
| **Meta** | Infrastruttura backend, Mononoke (source control) |
| **Cloudflare** | Proxy, Workers runtime, Pingora |
| **Discord** | Migrato da Go a Rust per ridurre le latenze |
| **Dropbox** | Motore di sincronizzazione file |
| **Linux Kernel** | Secondo linguaggio ufficiale dal 2022 (dopo C) |

### Ambiti di applicazione

1. **Sistemi operativi e kernel** - Linux, Redox OS, Theseus OS
2. **WebAssembly (WASM)** - Applicazioni web ad alte prestazioni
3. **Backend web** - Actix-web, Axum, Rocket (piu veloce di Node.js/Express)
4. **CLI tools** - ripgrep, bat, exa, fd (sostituti moderni di grep, cat, ls, find)
5. **Database e storage** - TiKV, SurrealDB, Neon
6. **Crittografia e blockchain** - Solana, Polkadot, Near Protocol
7. **Embedded e IoT** - Microcontrollori senza sistema operativo
8. **Game development** - Bevy engine, game logic ad alte prestazioni
9. **Networking** - Proxy, load balancer, firewall
10. **Intelligenza artificiale** - Candle (framework ML), tokenizer di HuggingFace

---

## Come usare questo tutorial

Ogni capitolo ha un file di esempio in `examples/`. Per eseguirli:

```bash
# Entra nella cartella del tutorial
cd rust-tutorial

# Esegui un capitolo specifico
cargo run --example cap01_basi
cargo run --example cap02_ownership
cargo run --example cap03_strutture
cargo run --example cap04_errori
cargo run --example cap05_collezioni
cargo run --example cap06_traits
cargo run --example cap07_moduli
cargo run --example cap08_concorrenza
cargo run --example cap09_progetto_finale

# Esegui il progetto principale (main.rs)
cargo run
```

Leggi il codice sorgente in `examples/` - ogni riga e commentata in italiano.

---

## Capitolo 1: Le Basi

**File:** `examples/cap01_basi.rs`

### Concetti trattati
- Funzione `main()` e stampa con `println!`
- Variabili immutabili (`let`) e mutabili (`let mut`)
- Tipi di dato: interi, float, bool, char, stringhe
- Costanti
- Tuple e array
- Funzioni con parametri e valori di ritorno
- Istruzioni condizionali `if/else`
- Cicli `loop`, `while`, `for`
- Shadowing delle variabili

### Punti chiave

In Rust le variabili sono **immutabili per default**. Devi scrivere `let mut` se vuoi modificarle.
Questo ti costringe a pensare: "Ho davvero bisogno di modificare questo valore?" - portando a
codice piu sicuro e leggibile.

```rust
let x = 5;       // immutabile - non puoi cambiarlo
let mut y = 10;  // mutabile - puoi cambiarlo
y = 20;          // OK
// x = 6;        // ERRORE di compilazione!
```

---

## Capitolo 2: Ownership e Borrowing

**File:** `examples/cap02_ownership.rs`

### Concetti trattati
- Le 3 regole dell'ownership
- Move semantics
- Clone vs Copy
- References (`&`) e borrowing
- Mutable references (`&mut`)
- Lifetimes di base
- Slices

### Punti chiave

Questo e **IL concetto fondamentale di Rust**. Le 3 regole:

1. Ogni valore ha un **owner** (proprietario)
2. Ci puo essere **un solo owner** alla volta
3. Quando l'owner esce dallo scope, il valore viene **rilasciato** (drop)

```rust
let s1 = String::from("ciao");
let s2 = s1;          // s1 viene MOSSO in s2
// println!("{}", s1); // ERRORE! s1 non e piu valido

let s3 = s2.clone();  // Copia profonda - entrambi validi
println!("{} {}", s2, s3); // OK
```

---

## Capitolo 3: Struct, Enum e Pattern Matching

**File:** `examples/cap03_strutture.rs`

### Concetti trattati
- Struct classiche, tuple struct, unit struct
- Metodi e funzioni associate (`impl`)
- Enum con dati
- Pattern matching con `match`
- `if let` e `while let`
- `Option<T>` come sostituto di null

### Punti chiave

Rust non ha `null`. Al suo posto usa `Option<T>`:

```rust
enum Option<T> {
    Some(T),  // contiene un valore
    None,     // nessun valore
}

let numero: Option<i32> = Some(42);
match numero {
    Some(n) => println!("Ho il numero: {}", n),
    None => println!("Nessun numero"),
}
```

---

## Capitolo 4: Gestione degli Errori

**File:** `examples/cap04_errori.rs`

### Concetti trattati
- `panic!` per errori irrecuperabili
- `Result<T, E>` per errori recuperabili
- Operatore `?` per propagare errori
- Errori personalizzati
- `unwrap()` e `expect()` (e quando NON usarli)
- Pattern `map`, `and_then`, `unwrap_or`

### Punti chiave

Rust ti obbliga a gestire gli errori. Non puoi ignorarli:

```rust
// Questo POTREBBE fallire - il tipo lo dice chiaramente
fn leggi_file(path: &str) -> Result<String, io::Error> {
    std::fs::read_to_string(path) // restituisce Result
}

// Devi gestire il Result - il compilatore ti obbliga
match leggi_file("dati.txt") {
    Ok(contenuto) => println!("{}", contenuto),
    Err(errore) => eprintln!("Errore: {}", errore),
}
```

---

## Capitolo 5: Collezioni

**File:** `examples/cap05_collezioni.rs`

### Concetti trattati
- `Vec<T>` - vettori dinamici
- `String` e `&str` - stringhe
- `HashMap<K, V>` - mappe chiave-valore
- Iteratori e metodi funzionali (`map`, `filter`, `fold`, `collect`)
- Iteratori lazy e chain di operazioni

### Punti chiave

Gli iteratori di Rust sono **zero-cost abstractions**:

```rust
let numeri = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

let somma_pari: i32 = numeri.iter()
    .filter(|&&n| n % 2 == 0)  // prendi solo i pari
    .map(|&n| n * n)            // eleva al quadrato
    .sum();                     // somma tutto

// Risultato: 4 + 16 + 36 + 64 + 100 = 220
```

Questo codice e veloce quanto un ciclo for scritto a mano in C.

---

## Capitolo 6: Traits e Generics

**File:** `examples/cap06_traits.rs`

### Concetti trattati
- Definire e implementare traits
- Traits come interfacce
- Generics con trait bounds
- Impl Trait (sintassi abbreviata)
- Trait objects (`dyn Trait`) e dispatch dinamico
- Traits della libreria standard: `Display`, `Debug`, `Clone`, `Iterator`
- Derivazione automatica dei traits

### Punti chiave

I traits sono come le interfacce in Java/Go, ma piu potenti:

```rust
trait Forma {
    fn area(&self) -> f64;
    fn nome(&self) -> &str;

    // Metodo con implementazione di default
    fn descrizione(&self) -> String {
        format!("{}: area = {:.2}", self.nome(), self.area())
    }
}
```

---

## Capitolo 7: Moduli e Organizzazione

**File:** `examples/cap07_moduli.rs`

### Concetti trattati
- Moduli con `mod`
- Visibilita con `pub`
- `use` per importare
- Organizzazione in file multipli
- Crates e dipendenze esterne
- Workspace di Cargo
- Documentazione con `///` e `//!`

### Punti chiave

La struttura tipica di un progetto Rust:

```
mio_progetto/
  Cargo.toml         # Configurazione e dipendenze
  src/
    main.rs          # Entry point (binary)
    lib.rs           # Entry point (library)
    modulo_a.rs      # Modulo A
    modulo_b/
      mod.rs         # Modulo B (con sotto-moduli)
      sotto_modulo.rs
  tests/
    integration.rs   # Test di integrazione
  examples/
    esempio.rs       # Codice di esempio
```

---

## Capitolo 8: Concorrenza

**File:** `examples/cap08_concorrenza.rs`

### Concetti trattati
- Thread con `std::thread`
- Canali (`mpsc`) per comunicazione tra thread
- `Mutex<T>` e `Arc<T>` per stato condiviso
- `Send` e `Sync` traits
- Parallelismo con iteratori

### Punti chiave

Il compilatore Rust **impedisce i data race a tempo di compilazione**:

```rust
use std::thread;
use std::sync::{Arc, Mutex};

let contatore = Arc::new(Mutex::new(0));
let mut handles = vec![];

for _ in 0..10 {
    let contatore = Arc::clone(&contatore);
    let handle = thread::spawn(move || {
        let mut num = contatore.lock().unwrap();
        *num += 1;
    });
    handles.push(handle);
}
```

Se provi a condividere dati tra thread senza `Arc`/`Mutex`, il compilatore ti blocca.

---

## Capitolo 9: Progetto Finale

**File:** `examples/cap09_progetto_finale.rs`

### Un'applicazione completa: Gestore di Inventario Archeologico

Questo progetto finale combina tutti i concetti appresi per creare un'applicazione
reale e funzionante: un sistema di gestione inventario per reperti archeologici
(in tema con il progetto BrozeAXE-AI!).

### Funzionalita
- Aggiunta, ricerca e rimozione di reperti
- Serializzazione/deserializzazione JSON
- Statistiche aggregate
- Gestione errori robusta
- Organizzazione modulare del codice

---

## Prossimi passi

Dopo aver completato questo tutorial, ecco cosa esplorare:

1. **Async/Await** - Programmazione asincrona con `tokio`
2. **Web development** - Framework `Axum` o `Actix-web`
3. **WebAssembly** - Compilare Rust per il browser con `wasm-pack`
4. **Embedded** - Programmare microcontrollori con `embedded-hal`
5. **Game dev** - Engine `Bevy`
6. **The Rust Book** - https://doc.rust-lang.org/book/ (la bibbia ufficiale)
7. **Rust by Example** - https://doc.rust-lang.org/rust-by-example/
8. **Rustlings** - Esercizi interattivi: https://github.com/rust-lang/rustlings

---

*Tutorial creato per il progetto BrozeAXE-AI - Sistema di classificazione archeologica*

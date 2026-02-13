// ============================================================================
// TUTORIAL RUST: DA ZERO A HERO
// ============================================================================
// Benvenuto! Questo e il punto di ingresso del progetto tutorial.
//
// Per eseguire i singoli capitoli:
//   cargo run --example cap01_basi
//   cargo run --example cap02_ownership
//   ... e cosi via fino a cap09_progetto_finale
//
// Per eseguire questo file:
//   cargo run
// ============================================================================

fn main() {
    println!("╔══════════════════════════════════════════════════════════╗");
    println!("║                                                          ║");
    println!("║          TUTORIAL RUST: DA ZERO A HERO                   ║");
    println!("║                                                          ║");
    println!("║   Una guida completa al linguaggio Rust                  ║");
    println!("║   con esempi reali e funzionanti                         ║");
    println!("║                                                          ║");
    println!("╠══════════════════════════════════════════════════════════╣");
    println!("║                                                          ║");
    println!("║   CAPITOLI DISPONIBILI:                                  ║");
    println!("║                                                          ║");
    println!("║   1. Le Basi            cargo run --example cap01_basi   ║");
    println!("║   2. Ownership          cargo run --example cap02_owner~ ║");
    println!("║   3. Struct/Enum        cargo run --example cap03_strut~ ║");
    println!("║   4. Gestione Errori    cargo run --example cap04_errori ║");
    println!("║   5. Collezioni         cargo run --example cap05_colle~ ║");
    println!("║   6. Traits/Generics    cargo run --example cap06_traits ║");
    println!("║   7. Moduli             cargo run --example cap07_moduli ║");
    println!("║   8. Concorrenza        cargo run --example cap08_conco~ ║");
    println!("║   9. Progetto Finale    cargo run --example cap09_proge~ ║");
    println!("║                                                          ║");
    println!("╠══════════════════════════════════════════════════════════╣");
    println!("║                                                          ║");
    println!("║   PERCHE RUST?                                           ║");
    println!("║                                                          ║");
    println!("║   - Sicurezza della memoria senza garbage collector      ║");
    println!("║   - Prestazioni pari a C/C++                             ║");
    println!("║   - Concorrenza senza data race                          ║");
    println!("║   - Compilatore che ti guida e ti protegge               ║");
    println!("║   - Ecosistema moderno (Cargo, crates.io)                ║");
    println!("║                                                          ║");
    println!("╠══════════════════════════════════════════════════════════╣");
    println!("║                                                          ║");
    println!("║   CHI USA RUST?                                          ║");
    println!("║                                                          ║");
    println!("║   Mozilla (Firefox), Google (Android), Microsoft,        ║");
    println!("║   Amazon AWS, Meta, Cloudflare, Discord, Dropbox,        ║");
    println!("║   Linux Kernel (secondo linguaggio ufficiale)            ║");
    println!("║                                                          ║");
    println!("╠══════════════════════════════════════════════════════════╣");
    println!("║                                                          ║");
    println!("║   Leggi TUTORIAL_RUST.md per la guida completa!          ║");
    println!("║                                                          ║");
    println!("╚══════════════════════════════════════════════════════════╝");

    println!("\n  Versione Rust: {}", env!("CARGO_PKG_VERSION"));
    println!("  Edizione: 2021");

    // Piccola demo: dimostriamo i concetti chiave di Rust in poche righe

    println!("\n--- Demo rapida dei concetti chiave ---\n");

    // 1. Ownership
    let nome = String::from("Rust");
    let saluto = crea_saluto(&nome);  // borrowing: &nome
    println!("  Ownership: {} -> {}", nome, saluto);

    // 2. Pattern matching
    let voto = 85;
    let giudizio = match voto {
        90..=100 => "Eccellente",
        80..=89 => "Ottimo",
        70..=79 => "Buono",
        _ => "Da migliorare",
    };
    println!("  Pattern matching: voto {} = {}", voto, giudizio);

    // 3. Option (niente null!)
    let numeri = vec![10, 20, 30];
    let trovato = numeri.get(1);      // Some(&20)
    let non_trovato = numeri.get(99); // None
    println!("  Option: get(1)={:?}, get(99)={:?}", trovato, non_trovato);

    // 4. Iteratori
    let somma_quadrati: i32 = (1..=5).map(|n| n * n).sum();
    println!("  Iteratori: somma quadrati 1..5 = {}", somma_quadrati);

    // 5. Result (gestione errori)
    let ok: Result<i32, &str> = Ok(42);
    let err: Result<i32, &str> = Err("errore!");
    println!("  Result: ok={:?}, err={:?}", ok, err);

    println!("\n  Esegui i capitoli per approfondire ogni concetto!");
}

fn crea_saluto(nome: &str) -> String {
    format!("Ciao, {}!", nome)
}

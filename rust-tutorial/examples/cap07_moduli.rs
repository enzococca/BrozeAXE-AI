// ============================================================================
// CAPITOLO 7: MODULI E ORGANIZZAZIONE DEL CODICE
// ============================================================================
// Rust ha un sistema di moduli potente per organizzare il codice.
// In un singolo file, usiamo `mod` per definire moduli inline.
// In progetti reali, ogni modulo puo essere in un file separato.
//
// Esegui con: cargo run --example cap07_moduli
// ============================================================================

// ============================================================================
// DEFINIZIONE DEI MODULI
// ============================================================================

/// Modulo per la gestione del database dei reperti
mod database {
    // Tutto in un modulo e PRIVATO per default.
    // Devi usare `pub` per renderlo visibile all'esterno.

    /// Struttura pubblica per un record nel database
    #[derive(Debug, Clone)]
    pub struct Record {
        pub id: u32,
        pub nome: String,
        pub categoria: String,
        dati_interni: String, // campo privato: non accessibile fuori dal modulo
    }

    impl Record {
        /// Costruttore pubblico
        pub fn nuovo(id: u32, nome: &str, categoria: &str) -> Self {
            Record {
                id,
                nome: nome.to_string(),
                categoria: categoria.to_string(),
                dati_interni: format!("internal_{}", id), // gestito internamente
            }
        }

        /// Metodo pubblico
        pub fn sommario(&self) -> String {
            format!("#{}: {} [{}]", self.id, self.nome, self.categoria)
        }

        /// Metodo privato - usato solo internamente al modulo
        fn _codice_interno(&self) -> &str {
            &self.dati_interni
        }
    }

    /// Database pubblico
    pub struct Database {
        records: Vec<Record>, // il campo e privato, ma i metodi pub lo espongono
        nome: String,
    }

    impl Database {
        pub fn nuovo(nome: &str) -> Self {
            Database {
                records: Vec::new(),
                nome: nome.to_string(),
            }
        }

        pub fn inserisci(&mut self, record: Record) {
            println!("  [DB:{}] Inserito: {}", self.nome, record.sommario());
            self.records.push(record);
        }

        pub fn cerca(&self, nome: &str) -> Vec<&Record> {
            self.records.iter()
                .filter(|r| r.nome.to_lowercase().contains(&nome.to_lowercase()))
                .collect()
        }

        pub fn tutti(&self) -> &[Record] {
            &self.records
        }

        pub fn conteggio(&self) -> usize {
            self.records.len()
        }
    }

    /// Sotto-modulo per le migrazioni del database
    pub mod migrazione {
        /// Versione dello schema
        pub const VERSIONE_SCHEMA: &str = "1.0.0";

        pub fn esegui_migrazione() -> Result<(), String> {
            println!("  [Migrazione] Schema v{} applicato", VERSIONE_SCHEMA);
            Ok(())
        }
    }
}

/// Modulo per l'analisi dei reperti
mod analisi {
    // Importiamo dal modulo fratello
    use super::database::Record;

    /// Risultato di un'analisi
    #[derive(Debug)]
    pub struct RisultatoAnalisi {
        pub reperto: String,
        pub punteggio: f64,
        pub classificazione: Classificazione,
    }

    /// Classificazione possibile
    #[derive(Debug)]
    pub enum Classificazione {
        Arma,
        Utensile,
        Ornamento,
        Ceramica,
        Altro(String),
    }

    impl std::fmt::Display for Classificazione {
        fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
            match self {
                Classificazione::Arma => write!(f, "Arma"),
                Classificazione::Utensile => write!(f, "Utensile"),
                Classificazione::Ornamento => write!(f, "Ornamento"),
                Classificazione::Ceramica => write!(f, "Ceramica"),
                Classificazione::Altro(s) => write!(f, "Altro: {}", s),
            }
        }
    }

    /// Analizzatore principale
    pub struct Analizzatore {
        pub nome: String,
        soglia: f64, // campo privato
    }

    impl Analizzatore {
        pub fn nuovo(nome: &str, soglia: f64) -> Self {
            Analizzatore {
                nome: nome.to_string(),
                soglia,
            }
        }

        /// Analizza un record e restituisce un risultato
        pub fn analizza(&self, record: &Record) -> RisultatoAnalisi {
            let classificazione = classifica_per_categoria(&record.categoria);
            let punteggio = calcola_punteggio(record);

            RisultatoAnalisi {
                reperto: record.nome.clone(),
                punteggio,
                classificazione,
            }
        }

        /// Filtra i risultati sopra la soglia
        pub fn filtra_significativi<'a>(&self, risultati: &'a [RisultatoAnalisi]) -> Vec<&'a RisultatoAnalisi> {
            risultati.iter()
                .filter(|r| r.punteggio >= self.soglia)
                .collect()
        }
    }

    // Funzioni private del modulo - non visibili all'esterno

    fn classifica_per_categoria(categoria: &str) -> Classificazione {
        match categoria.to_lowercase().as_str() {
            "arma" | "spada" | "pugnale" | "lancia" => Classificazione::Arma,
            "utensile" | "ascia" | "falce" => Classificazione::Utensile,
            "ornamento" | "fibula" | "anello" => Classificazione::Ornamento,
            "ceramica" | "vaso" | "anfora" => Classificazione::Ceramica,
            altro => Classificazione::Altro(altro.to_string()),
        }
    }

    fn calcola_punteggio(record: &Record) -> f64 {
        // Simulazione di un punteggio basato sulla lunghezza del nome
        // (in un caso reale, si baserebbero su misurazioni)
        let base = record.nome.len() as f64 * 3.7;
        (base % 10.0).round() / 10.0 * 10.0
    }

    /// Sotto-modulo per statistiche
    pub mod statistiche {
        use super::RisultatoAnalisi;

        pub fn media_punteggi(risultati: &[RisultatoAnalisi]) -> f64 {
            if risultati.is_empty() {
                return 0.0;
            }
            let somma: f64 = risultati.iter().map(|r| r.punteggio).sum();
            somma / risultati.len() as f64
        }

        pub fn conteggio_per_tipo(risultati: &[RisultatoAnalisi]) -> Vec<(String, usize)> {
            let mut conteggi = std::collections::HashMap::new();
            for r in risultati {
                let tipo = format!("{}", r.classificazione);
                *conteggi.entry(tipo).or_insert(0) += 1;
            }
            let mut vec: Vec<_> = conteggi.into_iter().collect();
            vec.sort_by(|a, b| b.1.cmp(&a.1));
            vec
        }
    }
}

/// Modulo per l'esportazione dei report
mod report {
    use super::analisi::RisultatoAnalisi;

    /// Formato di esportazione
    pub enum Formato {
        Testo,
        Csv,
        Json,
    }

    /// Genera un report
    pub fn genera(risultati: &[RisultatoAnalisi], formato: &Formato) -> String {
        match formato {
            Formato::Testo => genera_testo(risultati),
            Formato::Csv => genera_csv(risultati),
            Formato::Json => genera_json(risultati),
        }
    }

    fn genera_testo(risultati: &[RisultatoAnalisi]) -> String {
        let mut output = String::from("=== REPORT ANALISI ===\n");
        for r in risultati {
            output.push_str(&format!(
                "  {} - Tipo: {} - Punteggio: {:.1}\n",
                r.reperto, r.classificazione, r.punteggio
            ));
        }
        output.push_str(&format!("Totale: {} reperti\n", risultati.len()));
        output
    }

    fn genera_csv(risultati: &[RisultatoAnalisi]) -> String {
        let mut output = String::from("reperto,tipo,punteggio\n");
        for r in risultati {
            output.push_str(&format!(
                "{},{},{:.1}\n",
                r.reperto, r.classificazione, r.punteggio
            ));
        }
        output
    }

    fn genera_json(risultati: &[RisultatoAnalisi]) -> String {
        let mut output = String::from("[\n");
        for (i, r) in risultati.iter().enumerate() {
            output.push_str(&format!(
                "  {{\"reperto\": \"{}\", \"tipo\": \"{}\", \"punteggio\": {:.1}}}",
                r.reperto, r.classificazione, r.punteggio
            ));
            if i < risultati.len() - 1 {
                output.push(',');
            }
            output.push('\n');
        }
        output.push(']');
        output
    }
}

/// Modulo utilita con funzioni helper
mod utils {
    /// Formatta un numero con separatore delle migliaia
    pub fn formatta_numero(n: u64) -> String {
        let s = n.to_string();
        let mut result = String::new();
        for (i, c) in s.chars().rev().enumerate() {
            if i > 0 && i % 3 == 0 {
                result.push('.');
            }
            result.push(c);
        }
        result.chars().rev().collect()
    }

    /// Capitalizza la prima lettera
    pub fn capitalizza(s: &str) -> String {
        let mut chars = s.chars();
        match chars.next() {
            None => String::new(),
            Some(c) => c.to_uppercase().collect::<String>() + chars.as_str(),
        }
    }
}

// ============================================================================
// FUNZIONE MAIN - USA TUTTI I MODULI
// ============================================================================

// Importazioni con `use`
use database::{Database, Record};
use analisi::{Analizzatore, statistiche};
use report::Formato;

fn main() {
    println!("╔══════════════════════════════════════════════╗");
    println!("║   CAPITOLO 7: MODULI E ORGANIZZAZIONE        ║");
    println!("╚══════════════════════════════════════════════╝\n");

    // ========================================================================
    // 7.1 - USARE I MODULI
    // ========================================================================
    println!("--- 7.1 Usare i Moduli ---\n");

    // Esegui migrazione
    database::migrazione::esegui_migrazione().unwrap();

    // Crea il database
    let mut db = Database::nuovo("ArcheoDB");

    // Inserisci record
    let reperti_data = vec![
        ("Ascia a margini rialzati", "Utensile"),
        ("Spada tipo Allerona", "Arma"),
        ("Fibula ad arco", "Ornamento"),
        ("Pugnale a lingua da presa", "Arma"),
        ("Vaso a collo", "Ceramica"),
        ("Anello con castone", "Ornamento"),
        ("Punta di lancia", "Arma"),
        ("Falce in bronzo", "Utensile"),
    ];

    println!();
    for (i, (nome, cat)) in reperti_data.iter().enumerate() {
        let record = Record::nuovo(i as u32 + 1, nome, cat);
        db.inserisci(record);
    }

    println!("\nTotale record: {}", db.conteggio());

    // ========================================================================
    // 7.2 - RICERCA
    // ========================================================================
    println!("\n--- 7.2 Ricerca ---\n");

    let risultati_ricerca = db.cerca("arco");
    println!("Ricerca 'arco': {} risultati", risultati_ricerca.len());
    for r in &risultati_ricerca {
        println!("  {}", r.sommario());
    }

    let risultati_ricerca = db.cerca("a");
    println!("\nRicerca 'a': {} risultati", risultati_ricerca.len());
    for r in &risultati_ricerca {
        println!("  {}", r.sommario());
    }

    // ========================================================================
    // 7.3 - ANALISI
    // ========================================================================
    println!("\n--- 7.3 Analisi ---\n");

    let analizzatore = Analizzatore::nuovo("Classificatore v1", 3.0);

    let risultati: Vec<_> = db.tutti().iter()
        .map(|r| analizzatore.analizza(r))
        .collect();

    println!("Risultati analisi:");
    for r in &risultati {
        println!("  {} -> {} (punteggio: {:.1})",
            r.reperto, r.classificazione, r.punteggio);
    }

    // Statistiche
    let media = statistiche::media_punteggi(&risultati);
    println!("\nMedia punteggi: {:.1}", media);

    let conteggi = statistiche::conteggio_per_tipo(&risultati);
    println!("Distribuzione per tipo:");
    for (tipo, count) in &conteggi {
        println!("  {}: {}", tipo, count);
    }

    // ========================================================================
    // 7.4 - REPORT IN DIVERSI FORMATI
    // ========================================================================
    println!("\n--- 7.4 Report ---\n");

    // Report testuale
    println!("FORMATO TESTO:");
    println!("{}", report::genera(&risultati, &Formato::Testo));

    // Report CSV
    println!("FORMATO CSV:");
    println!("{}", report::genera(&risultati, &Formato::Csv));

    // Report JSON
    println!("FORMATO JSON:");
    println!("{}", report::genera(&risultati, &Formato::Json));

    // ========================================================================
    // 7.5 - MODULO UTILS
    // ========================================================================
    println!("--- 7.5 Utilita ---\n");

    println!("Numero formattato: {}", utils::formatta_numero(1_234_567));
    println!("Capitalizzato: {}", utils::capitalizza("ciao mondo"));

    // ========================================================================
    // 7.6 - STRUTTURA DI UN PROGETTO REALE
    // ========================================================================
    println!("\n--- 7.6 Struttura Progetto Reale ---\n");

    println!("In un progetto reale, ogni modulo sarebbe in un file separato:");
    println!();
    println!("  mio_progetto/");
    println!("  ├── Cargo.toml");
    println!("  ├── src/");
    println!("  │   ├── main.rs          // entry point");
    println!("  │   ├── lib.rs           // libreria (opzionale)");
    println!("  │   ├── database.rs      // mod database");
    println!("  │   ├── analisi/");
    println!("  │   │   ├── mod.rs       // mod analisi");
    println!("  │   │   └── statistiche.rs  // sotto-modulo");
    println!("  │   ├── report.rs        // mod report");
    println!("  │   └── utils.rs         // mod utils");
    println!("  ├── tests/");
    println!("  │   └── integration.rs   // test di integrazione");
    println!("  └── examples/");
    println!("      └── esempio.rs       // esempio d'uso");
    println!();
    println!("In main.rs:");
    println!("  mod database;    // carica da src/database.rs");
    println!("  mod analisi;     // carica da src/analisi/mod.rs");
    println!("  mod report;      // carica da src/report.rs");
    println!("  mod utils;       // carica da src/utils.rs");
    println!();
    println!("VISIBILITA:");
    println!("  (niente) -> privato al modulo corrente");
    println!("  pub      -> visibile a tutti");
    println!("  pub(crate) -> visibile solo nel crate corrente");
    println!("  pub(super) -> visibile al modulo padre");

    println!("\n✅ Capitolo 7 completato!");
}

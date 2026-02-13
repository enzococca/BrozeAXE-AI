// ============================================================================
// CAPITOLO 3: STRUCT, ENUM E PATTERN MATCHING
// ============================================================================
// Le struct e gli enum sono i mattoni fondamentali per creare tipi di dato
// personalizzati in Rust. Il pattern matching con `match` e uno degli
// strumenti piu potenti del linguaggio.
//
// Esegui con: cargo run --example cap03_strutture
// ============================================================================

fn main() {
    println!("╔══════════════════════════════════════════════╗");
    println!("║   CAPITOLO 3: STRUCT, ENUM, PATTERN MATCHING ║");
    println!("╚══════════════════════════════════════════════╝\n");

    // ========================================================================
    // 3.1 - STRUCT CLASSICHE
    // ========================================================================
    println!("--- 3.1 Struct Classiche ---\n");

    // Una struct raggruppa dati correlati sotto un nome significativo.
    // E simile a una class in altri linguaggi, ma senza ereditarieta.

    // Creazione di un'istanza
    let mut reperto = RepertoArcheologico {
        id: 1,
        nome: String::from("Ascia a margini rialzati"),
        materiale: String::from("Bronzo"),
        peso_grammi: 350.0,
        anno_ritrovamento: 2019,
        integro: true,
    };

    println!("Reperto: {} ({})", reperto.nome, reperto.materiale);
    println!("Peso: {}g, Anno: {}", reperto.peso_grammi, reperto.anno_ritrovamento);

    // Modifica di un campo (la struct deve essere `mut`)
    reperto.peso_grammi = 348.5;
    println!("Peso corretto: {}g", reperto.peso_grammi);

    // Creazione con shorthand (se il nome della variabile coincide col campo)
    let nome = String::from("Pugnale");
    let materiale = String::from("Bronzo");
    let pugnale = RepertoArcheologico {
        id: 2,
        nome,       // shorthand: equivale a `nome: nome`
        materiale,  // shorthand: equivale a `materiale: materiale`
        peso_grammi: 180.0,
        anno_ritrovamento: 2020,
        integro: false,
    };
    println!("\nPugnale: {} (integro: {})", pugnale.nome, pugnale.integro);

    // Struct update syntax: crea una nuova struct copiando i campi da un'altra
    let reperto_simile = RepertoArcheologico {
        id: 3,
        nome: String::from("Ascia a tallone"),
        ..pugnale  // copia tutti gli altri campi da `pugnale`
        // ATTENZIONE: `pugnale.materiale` e stato MOSSO (String non e Copy)
    };
    println!("Reperto simile: {} ({})", reperto_simile.nome, reperto_simile.materiale);

    println!();

    // ========================================================================
    // 3.2 - METODI E FUNZIONI ASSOCIATE (impl)
    // ========================================================================
    println!("--- 3.2 Metodi (impl) ---\n");

    // I metodi si definiscono in un blocco `impl`.
    // Il primo parametro e `self` (l'istanza).

    let sito = SitoArcheologico::nuovo(
        "Savignano Irpino",
        40.88,
        15.18,
    );

    println!("{}", sito.descrizione());
    println!("A quanti km da Roma? {:.0} km", sito.distanza_da(41.90, 12.49));

    // Aggiungi reperti al sito
    let mut sito = sito; // rendiamo mutabile
    sito.aggiungi_reperto("Ascia tipo Savignano");
    sito.aggiungi_reperto("Fibula ad arco");
    sito.aggiungi_reperto("Pugnale a lingua da presa");

    println!("\nReperti nel sito:");
    for (i, r) in sito.reperti.iter().enumerate() {
        println!("  {}. {}", i + 1, r);
    }
    println!("Totale reperti: {}", sito.numero_reperti());

    println!();

    // ========================================================================
    // 3.3 - TUPLE STRUCT E UNIT STRUCT
    // ========================================================================
    println!("--- 3.3 Tuple Struct e Unit Struct ---\n");

    // Tuple struct: come una tupla ma con un nome.
    // Utili per creare tipi distinti da tipi primitivi (newtypes).

    let coord = Coordinate(40.88, 15.18);
    println!("Coordinate: lat={}, lon={}", coord.0, coord.1);

    let peso = Peso(350.0);
    let lunghezza = Lunghezza(25.5);
    println!("Peso: {}g", peso.0);
    println!("Lunghezza: {}cm", lunghezza.0);

    // Non puoi confondere Peso e Lunghezza anche se entrambi contengono f64!
    // calcola(peso, lunghezza); // Questo NON compilerebbe se i tipi non corrispondono

    // Unit struct: struct senza campi. Usate come marker/sentinel.
    let _marker = Vuoto;

    println!();

    // ========================================================================
    // 3.4 - ENUM
    // ========================================================================
    println!("--- 3.4 Enum ---\n");

    // Gli enum in Rust sono MOLTO piu potenti che in C/Java.
    // Ogni variante puo contenere dati di tipo diverso!

    let periodo1 = PeriodoStorico::BronzoAntico;
    let periodo2 = PeriodoStorico::BronzoMedio;
    let periodo3 = PeriodoStorico::BronzoRecente;
    let periodo4 = PeriodoStorico::BronzoFinale;
    let periodo5 = PeriodoStorico::EtaDelFerro;
    let periodo6 = PeriodoStorico::Sconosciuto(String::from("Forse transizione"));

    println!("Periodi storici:");
    println!("  {} ({})", periodo1.nome(), periodo1.range_anni());
    println!("  {} ({})", periodo2.nome(), periodo2.range_anni());
    println!("  {} ({})", periodo3.nome(), periodo3.range_anni());
    println!("  {} ({})", periodo4.nome(), periodo4.range_anni());
    println!("  {} ({})", periodo5.nome(), periodo5.range_anni());
    println!("  {} ({})", periodo6.nome(), periodo6.range_anni());

    // Enum con dati diversi per ogni variante
    let misura1 = Misurazione::Peso(350.0);
    let misura2 = Misurazione::Dimensioni { lunghezza: 25.0, larghezza: 8.0, altezza: 3.0 };
    let misura3 = Misurazione::Descrizione(String::from("Patina verde uniforme"));
    let misura4 = Misurazione::NonDisponibile;

    println!("\nMisurazioni:");
    stampa_misurazione(&misura1);
    stampa_misurazione(&misura2);
    stampa_misurazione(&misura3);
    stampa_misurazione(&misura4);

    println!();

    // ========================================================================
    // 3.5 - PATTERN MATCHING CON match
    // ========================================================================
    println!("--- 3.5 Pattern Matching ---\n");

    // `match` e ESAUSTIVO: DEVE coprire tutti i casi possibili.
    // Il compilatore ti avvisa se dimentichi un caso!

    let reperto = TipoReperto::Arma(String::from("Spada"), 75.0);

    match &reperto {
        TipoReperto::Arma(nome, lunghezza) => {
            println!("Arma: {} ({:.1}cm)", nome, lunghezza);
        }
        TipoReperto::Utensile(nome) => {
            println!("Utensile: {}", nome);
        }
        TipoReperto::Ornamento { tipo, materiale } => {
            println!("Ornamento: {} in {}", tipo, materiale);
        }
        TipoReperto::Frammento => {
            println!("Frammento non identificato");
        }
    }

    // Match con guardie (condizioni aggiuntive)
    let temperatura = 42;
    let messaggio = match temperatura {
        t if t < 0 => "Sotto zero",
        0..=15 => "Freddo",
        16..=25 => "Piacevole",
        26..=35 => "Caldo",
        t if t > 35 => "Molto caldo!",
        _ => "Fuori scala",
    };
    println!("\nTemperatura {}: {}", temperatura, messaggio);

    // Match con binding (@)
    let eta = 3200;
    let classificazione = match eta {
        anni @ 0..=1000 => format!("Recente ({} anni)", anni),
        anni @ 1001..=3000 => format!("Antico ({} anni)", anni),
        anni @ 3001..=5000 => format!("Molto antico ({} anni!)", anni),
        anni => format!("Preistorico ({} anni!!)", anni),
    };
    println!("Classificazione: {}", classificazione);

    println!();

    // ========================================================================
    // 3.6 - if let E while let
    // ========================================================================
    println!("--- 3.6 if let e while let ---\n");

    // `if let` e zucchero sintattico per un match con un solo caso interessante

    let valore: Option<i32> = Some(42);

    // Invece di scrivere:
    match valore {
        Some(n) => println!("Match: trovato {}", n),
        None => {}
    }

    // Puoi scrivere:
    if let Some(n) = valore {
        println!("if let: trovato {}", n);
    }

    // Con else
    let vuoto: Option<i32> = None;
    if let Some(n) = vuoto {
        println!("Trovato: {}", n);
    } else {
        println!("Nessun valore trovato (None)");
    }

    // `while let` - cicla finche il pattern corrisponde
    let mut stack = vec![1, 2, 3, 4, 5];
    print!("Stack pop: ");
    while let Some(top) = stack.pop() {
        print!("{} ", top);
    }
    println!("(stack vuoto)\n");

    // ========================================================================
    // 3.7 - OPTION<T>: L'ALTERNATIVA A NULL
    // ========================================================================
    println!("--- 3.7 Option<T> ---\n");

    // Rust NON ha null. Al suo posto usa Option<T>:
    // enum Option<T> {
    //     Some(T),  // contiene un valore
    //     None,     // nessun valore
    // }

    let reperti = vec!["Ascia", "Spada", "Fibula"];

    // .get() restituisce Option<&T>
    let primo = reperti.get(0);    // Some(&"Ascia")
    let quarto = reperti.get(3);   // None (indice fuori range)

    println!("Primo: {:?}", primo);
    println!("Quarto: {:?}", quarto);

    // Metodi utili di Option
    println!("unwrap_or: {}", quarto.unwrap_or(&"Non trovato"));
    println!("is_some: {}", primo.is_some());
    println!("is_none: {}", quarto.is_none());

    // map - trasforma il valore interno (se presente)
    let lunghezza = primo.map(|s| s.len());
    println!("Lunghezza primo: {:?}", lunghezza); // Some(5)

    // and_then (flatmap) - per operazioni che restituiscono Option
    let maiuscolo = primo.map(|s| s.to_uppercase());
    let risultato = maiuscolo.as_deref().unwrap_or("N/A");
    println!("Maiuscolo: {}", risultato);

    // ========================================================================
    // 3.8 - ESEMPIO COMPLETO: CATALOGO REPERTI
    // ========================================================================
    println!("\n--- 3.8 Esempio Completo: Catalogo ---\n");

    let mut catalogo = Catalogo::nuovo();

    catalogo.aggiungi(Pezzo {
        id: 1,
        nome: String::from("Ascia a margini rialzati"),
        tipo: TipoReperto::Utensile(String::from("Ascia")),
        periodo: PeriodoStorico::BronzoRecente,
        stato: StatoConservazione::Buono,
    });

    catalogo.aggiungi(Pezzo {
        id: 2,
        nome: String::from("Spada tipo Allerona"),
        tipo: TipoReperto::Arma(String::from("Spada"), 65.0),
        periodo: PeriodoStorico::BronzoFinale,
        stato: StatoConservazione::Discreto,
    });

    catalogo.aggiungi(Pezzo {
        id: 3,
        nome: String::from("Fibula ad arco serpeggiante"),
        tipo: TipoReperto::Ornamento {
            tipo: String::from("Fibula"),
            materiale: String::from("Bronzo"),
        },
        periodo: PeriodoStorico::EtaDelFerro,
        stato: StatoConservazione::Ottimo,
    });

    catalogo.aggiungi(Pezzo {
        id: 4,
        nome: String::from("Frammento non identificato"),
        tipo: TipoReperto::Frammento,
        periodo: PeriodoStorico::Sconosciuto(String::from("Decontestualizzato")),
        stato: StatoConservazione::Frammento,
    });

    // Stampa tutto il catalogo
    catalogo.stampa();

    // Cerca per periodo
    println!("Reperti del Bronzo Finale:");
    for pezzo in catalogo.cerca_per_periodo(&PeriodoStorico::BronzoFinale) {
        println!("  - {} ({})", pezzo.nome, pezzo.stato.descrizione());
    }

    // Cerca per ID
    match catalogo.trova_per_id(2) {
        Some(pezzo) => println!("\nTrovato ID 2: {}", pezzo.nome),
        None => println!("\nID 2 non trovato"),
    }

    // Statistiche
    println!("\nStatistiche:");
    println!("  Totale pezzi: {}", catalogo.totale());
    println!("  Pezzi in buono stato: {}", catalogo.conta_per_stato(&StatoConservazione::Buono));
    println!("  Pezzi in ottimo stato: {}", catalogo.conta_per_stato(&StatoConservazione::Ottimo));

    println!("\n✅ Capitolo 3 completato!");
}

// ============================================================================
// DEFINIZIONI DEI TIPI
// ============================================================================

/// Struct classica per un reperto archeologico
struct RepertoArcheologico {
    id: u32,
    nome: String,
    materiale: String,
    peso_grammi: f64,
    anno_ritrovamento: u16,
    integro: bool,
}

/// Sito archeologico con metodi
struct SitoArcheologico {
    nome: String,
    latitudine: f64,
    longitudine: f64,
    reperti: Vec<String>,
}

impl SitoArcheologico {
    /// Funzione associata (come un costruttore statico) - non ha `self`
    fn nuovo(nome: &str, lat: f64, lon: f64) -> Self {
        SitoArcheologico {
            nome: String::from(nome),
            latitudine: lat,
            longitudine: lon,
            reperti: Vec::new(),
        }
    }

    /// Metodo - prende &self (reference immutabile all'istanza)
    fn descrizione(&self) -> String {
        format!(
            "Sito: {} (lat: {:.2}, lon: {:.2})",
            self.nome, self.latitudine, self.longitudine
        )
    }

    /// Calcola distanza approssimativa da un punto (formula di Haversine semplificata)
    fn distanza_da(&self, lat: f64, lon: f64) -> f64 {
        let dlat = (self.latitudine - lat).to_radians();
        let dlon = (self.longitudine - lon).to_radians();
        let a = (dlat / 2.0).sin().powi(2)
            + self.latitudine.to_radians().cos()
                * lat.to_radians().cos()
                * (dlon / 2.0).sin().powi(2);
        let c = 2.0 * a.sqrt().asin();
        6371.0 * c // raggio terrestre in km
    }

    /// Metodo mutabile - prende &mut self
    fn aggiungi_reperto(&mut self, nome: &str) {
        self.reperti.push(String::from(nome));
    }

    fn numero_reperti(&self) -> usize {
        self.reperti.len()
    }
}

/// Tuple struct per coordinate
struct Coordinate(f64, f64);

/// Newtype pattern: tipi distinti per evitare confusione
struct Peso(f64);
struct Lunghezza(f64);

/// Unit struct
struct Vuoto;

/// Enum per i periodi storici
#[derive(PartialEq)]
enum PeriodoStorico {
    BronzoAntico,
    BronzoMedio,
    BronzoRecente,
    BronzoFinale,
    EtaDelFerro,
    Sconosciuto(String),
}

impl PeriodoStorico {
    fn nome(&self) -> &str {
        match self {
            PeriodoStorico::BronzoAntico => "Bronzo Antico",
            PeriodoStorico::BronzoMedio => "Bronzo Medio",
            PeriodoStorico::BronzoRecente => "Bronzo Recente",
            PeriodoStorico::BronzoFinale => "Bronzo Finale",
            PeriodoStorico::EtaDelFerro => "Eta del Ferro",
            PeriodoStorico::Sconosciuto(_) => "Periodo sconosciuto",
        }
    }

    fn range_anni(&self) -> &str {
        match self {
            PeriodoStorico::BronzoAntico => "2300-1700 a.C.",
            PeriodoStorico::BronzoMedio => "1700-1350 a.C.",
            PeriodoStorico::BronzoRecente => "1350-1200 a.C.",
            PeriodoStorico::BronzoFinale => "1200-950 a.C.",
            PeriodoStorico::EtaDelFerro => "950-500 a.C.",
            PeriodoStorico::Sconosciuto(_) => "datazione incerta",
        }
    }
}

/// Enum con dati diversi per variante
enum Misurazione {
    Peso(f64),
    Dimensioni { lunghezza: f64, larghezza: f64, altezza: f64 },
    Descrizione(String),
    NonDisponibile,
}

fn stampa_misurazione(m: &Misurazione) {
    match m {
        Misurazione::Peso(p) => println!("  Peso: {:.1}g", p),
        Misurazione::Dimensioni { lunghezza, larghezza, altezza } => {
            println!("  Dimensioni: {:.1} x {:.1} x {:.1} cm", lunghezza, larghezza, altezza);
        }
        Misurazione::Descrizione(d) => println!("  Nota: {}", d),
        Misurazione::NonDisponibile => println!("  Misurazione non disponibile"),
    }
}

/// Enum per tipi di reperto
enum TipoReperto {
    Arma(String, f64),      // nome, lunghezza in cm
    Utensile(String),       // nome
    Ornamento { tipo: String, materiale: String },
    Frammento,
}

/// Stato di conservazione
#[derive(PartialEq)]
enum StatoConservazione {
    Ottimo,
    Buono,
    Discreto,
    Frammento,
}

impl StatoConservazione {
    fn descrizione(&self) -> &str {
        match self {
            StatoConservazione::Ottimo => "Ottimo stato",
            StatoConservazione::Buono => "Buono stato",
            StatoConservazione::Discreto => "Discreto stato",
            StatoConservazione::Frammento => "Frammentario",
        }
    }
}

/// Un pezzo nel catalogo
struct Pezzo {
    id: u32,
    nome: String,
    tipo: TipoReperto,
    periodo: PeriodoStorico,
    stato: StatoConservazione,
}

/// Catalogo di pezzi
struct Catalogo {
    pezzi: Vec<Pezzo>,
}

impl Catalogo {
    fn nuovo() -> Self {
        Catalogo { pezzi: Vec::new() }
    }

    fn aggiungi(&mut self, pezzo: Pezzo) {
        self.pezzi.push(pezzo);
    }

    fn stampa(&self) {
        println!("╔═══════════════════════════════════════════╗");
        println!("║          CATALOGO REPERTI                 ║");
        println!("╠═══════════════════════════════════════════╣");
        for pezzo in &self.pezzi {
            let tipo_str = match &pezzo.tipo {
                TipoReperto::Arma(n, l) => format!("Arma: {} ({:.0}cm)", n, l),
                TipoReperto::Utensile(n) => format!("Utensile: {}", n),
                TipoReperto::Ornamento { tipo, materiale } => {
                    format!("Ornamento: {} ({})", tipo, materiale)
                }
                TipoReperto::Frammento => "Frammento".to_string(),
            };
            println!("║ #{} - {}", pezzo.id, pezzo.nome);
            println!("║    Tipo: {}", tipo_str);
            println!("║    Periodo: {} ({})", pezzo.periodo.nome(), pezzo.periodo.range_anni());
            println!("║    Stato: {}", pezzo.stato.descrizione());
            println!("╠═══════════════════════════════════════════╣");
        }
        println!("╚═══════════════════════════════════════════╝\n");
    }

    fn trova_per_id(&self, id: u32) -> Option<&Pezzo> {
        self.pezzi.iter().find(|p| p.id == id)
    }

    fn cerca_per_periodo(&self, periodo: &PeriodoStorico) -> Vec<&Pezzo> {
        self.pezzi.iter().filter(|p| &p.periodo == periodo).collect()
    }

    fn totale(&self) -> usize {
        self.pezzi.len()
    }

    fn conta_per_stato(&self, stato: &StatoConservazione) -> usize {
        self.pezzi.iter().filter(|p| &p.stato == stato).count()
    }
}

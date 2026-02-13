// ============================================================================
// CAPITOLO 6: TRAITS E GENERICS
// ============================================================================
// I traits definiscono comportamenti condivisi (come le interfacce).
// I generics permettono di scrivere codice che funziona con qualsiasi tipo.
// Insieme, sono la base del polimorfismo in Rust.
//
// Esegui con: cargo run --example cap06_traits
// ============================================================================

use std::fmt;

fn main() {
    println!("╔══════════════════════════════════════════════╗");
    println!("║   CAPITOLO 6: TRAITS E GENERICS              ║");
    println!("╚══════════════════════════════════════════════╝\n");

    // ========================================================================
    // 6.1 - DEFINIRE E IMPLEMENTARE TRAITS
    // ========================================================================
    println!("--- 6.1 Traits di base ---\n");

    let ascia = Ascia {
        nome: String::from("Ascia a margini rialzati"),
        lunghezza_cm: 18.5,
        peso_grammi: 350.0,
        materiale: Materiale::Bronzo,
    };

    let spada = Spada {
        nome: String::from("Spada tipo Allerona"),
        lunghezza_lama_cm: 55.0,
        lunghezza_totale_cm: 70.0,
        peso_grammi: 850.0,
    };

    let fibula = Fibula {
        nome: String::from("Fibula ad arco"),
        diametro_cm: 4.5,
        peso_grammi: 25.0,
    };

    // Tutti implementano il trait Reperto
    println!("{}", ascia.scheda());
    println!("{}", spada.scheda());
    println!("{}", fibula.scheda());

    // Chiamiamo i metodi del trait
    println!("Ascia - categoria: {}", ascia.categoria());
    println!("Spada - categoria: {}", spada.categoria());
    println!("Fibula - categoria: {}", fibula.categoria());

    // Metodo con implementazione di default
    println!("\nAscia pericolosa? {}", ascia.e_pericolosa());
    println!("Fibula pericolosa? {}", fibula.e_pericolosa());

    println!();

    // ========================================================================
    // 6.2 - TRAITS COME PARAMETRI (TRAIT BOUNDS)
    // ========================================================================
    println!("--- 6.2 Trait Bounds ---\n");

    // Funzione che accetta QUALSIASI tipo che implementa Reperto
    stampa_info(&ascia);
    stampa_info(&spada);
    stampa_info(&fibula);

    // Funzione con trait bounds multipli
    println!("\nConfronto pesi:");
    confronta_peso(&ascia, &spada);
    confronta_peso(&fibula, &ascia);

    println!();

    // ========================================================================
    // 6.3 - GENERICS
    // ========================================================================
    println!("--- 6.3 Generics ---\n");

    // Struct generica
    let punto_intero = Punto { x: 5, y: 10 };
    let punto_float = Punto { x: 3.14, y: 2.71 };
    let punto_misto = PuntoMisto { x: 5, y: 3.14 };

    println!("Punto intero: ({}, {})", punto_intero.x, punto_intero.y);
    println!("Punto float: ({}, {})", punto_float.x, punto_float.y);
    println!("Punto misto: ({}, {})", punto_misto.x, punto_misto.y);

    // Metodo generico
    println!("Distanza dall'origine: {:.2}", punto_float.distanza_origine());

    // Funzione generica
    let max = trova_massimo(&[3, 7, 2, 9, 1, 5]);
    println!("\nMassimo di [3,7,2,9,1,5]: {}", max);

    let max = trova_massimo(&[3.14, 2.71, 1.41, 1.73]);
    println!("Massimo di [3.14,2.71,1.41,1.73]: {}", max);

    // Contenitore generico
    let mut contenitore: Contenitore<String> = Contenitore::nuovo(5);
    contenitore.aggiungi(String::from("Ascia"));
    contenitore.aggiungi(String::from("Spada"));
    contenitore.aggiungi(String::from("Fibula"));
    println!("\nContenitore: {:?}", contenitore);
    println!("Pieno? {}", contenitore.e_pieno());

    println!();

    // ========================================================================
    // 6.4 - TRAIT OBJECTS (DISPATCH DINAMICO)
    // ========================================================================
    println!("--- 6.4 Trait Objects (dyn) ---\n");

    // Con `dyn Trait` puoi avere una collezione di tipi diversi
    // che implementano lo stesso trait.
    // Questo e il DISPATCH DINAMICO (come virtual in C++).

    let collezione: Vec<Box<dyn Reperto>> = vec![
        Box::new(Ascia {
            nome: String::from("Ascia tipo A"),
            lunghezza_cm: 15.0,
            peso_grammi: 300.0,
            materiale: Materiale::Bronzo,
        }),
        Box::new(Spada {
            nome: String::from("Spada tipo B"),
            lunghezza_lama_cm: 50.0,
            lunghezza_totale_cm: 65.0,
            peso_grammi: 750.0,
        }),
        Box::new(Fibula {
            nome: String::from("Fibula tipo C"),
            diametro_cm: 3.0,
            peso_grammi: 20.0,
        }),
    ];

    println!("Collezione mista (dispatch dinamico):");
    for reperto in &collezione {
        println!("  {} ({}) - {:.0}g",
            reperto.nome(), reperto.categoria(), reperto.peso());
    }

    // Calcola peso totale usando trait objects
    let peso_totale: f64 = collezione.iter().map(|r| r.peso()).sum();
    println!("Peso totale: {:.0}g", peso_totale);

    println!();

    // ========================================================================
    // 6.5 - TRAITS DELLA LIBRERIA STANDARD
    // ========================================================================
    println!("--- 6.5 Traits Standard ---\n");

    // Display: per formattazione leggibile ({})
    let moneta = Moneta {
        nome: String::from("Didramma"),
        valore: 2.0,
        metallo: String::from("Argento"),
    };
    println!("Display: {}", moneta);

    // Debug: per formattazione di debug ({:?})
    println!("Debug: {:?}", moneta);
    println!("Pretty Debug: {:#?}", moneta);

    // Clone
    let copia = moneta.clone();
    println!("Clone: {}", copia);

    // PartialEq: confronto ==
    let moneta2 = Moneta {
        nome: String::from("Didramma"),
        valore: 2.0,
        metallo: String::from("Argento"),
    };
    println!("Uguali? {}", moneta == moneta2);

    // PartialOrd: confronto <, >, <=, >=
    let moneta3 = Moneta {
        nome: String::from("Tetradramma"),
        valore: 4.0,
        metallo: String::from("Argento"),
    };
    println!("moneta < moneta3? {}", moneta < moneta3);

    println!();

    // ========================================================================
    // 6.6 - DERIVE (DERIVAZIONE AUTOMATICA)
    // ========================================================================
    println!("--- 6.6 Derive ---\n");

    // #[derive(...)] implementa automaticamente alcuni traits.
    // Funziona solo se tutti i campi implementano quel trait.

    let coord1 = Coordinata { lat: 40.88, lon: 15.18 };
    let coord2 = Coordinata { lat: 40.88, lon: 15.18 };
    let coord3 = coord1.clone();

    println!("Debug: {:?}", coord1);
    println!("Uguali? {}", coord1 == coord2);
    println!("Clone: {:?}", coord3);

    println!();

    // ========================================================================
    // 6.7 - WHERE CLAUSE E TRAIT BOUNDS COMPLESSI
    // ========================================================================
    println!("--- 6.7 Where Clause ---\n");

    // Quando i trait bounds diventano complessi, usa `where`
    let registro = Registro {
        elementi: vec![
            Elemento { nome: String::from("Ascia"), valore: 350 },
            Elemento { nome: String::from("Spada"), valore: 800 },
            Elemento { nome: String::from("Fibula"), valore: 45 },
        ],
    };

    println!("Registro: {}", registro);
    println!("Sommario: {}", registro.sommario());

    println!();

    // ========================================================================
    // 6.8 - IMPL TRAIT (SINTASSI ABBREVIATA)
    // ========================================================================
    println!("--- 6.8 impl Trait ---\n");

    // `impl Trait` come tipo di ritorno: il tipo esatto e nascosto
    let iteratore = crea_contatore(1, 5);
    let numeri: Vec<i32> = iteratore.collect();
    println!("Contatore 1..=5: {:?}", numeri);

    // `impl Trait` come parametro (equivalente a un generic con trait bound)
    mostra_reperto(&ascia);
    mostra_reperto(&spada);

    // ========================================================================
    // 6.9 - ESEMPIO COMPLETO: SISTEMA DI CLASSIFICAZIONE
    // ========================================================================
    println!("\n--- 6.9 Sistema di Classificazione ---\n");

    let reperti_classificabili: Vec<Box<dyn Classificabile>> = vec![
        Box::new(ascia),
        Box::new(spada),
        Box::new(fibula),
    ];

    let mut report = ClassificazioneReport::nuovo();
    for reperto in &reperti_classificabili {
        report.aggiungi(reperto.as_ref());
    }

    report.stampa();

    println!("\n✅ Capitolo 6 completato!");
}

// ============================================================================
// DEFINIZIONI
// ============================================================================

/// Materiali possibili
#[derive(Debug, Clone)]
enum Materiale {
    Bronzo,
    Ferro,
    Oro,
    Argento,
}

impl fmt::Display for Materiale {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Materiale::Bronzo => write!(f, "Bronzo"),
            Materiale::Ferro => write!(f, "Ferro"),
            Materiale::Oro => write!(f, "Oro"),
            Materiale::Argento => write!(f, "Argento"),
        }
    }
}

// ============================================================================
// TRAIT PRINCIPALE: Reperto
// ============================================================================

/// Trait che definisce il comportamento di un reperto archeologico
trait Reperto {
    /// Nome del reperto (obbligatorio implementare)
    fn nome(&self) -> &str;

    /// Categoria (obbligatorio)
    fn categoria(&self) -> &str;

    /// Peso in grammi (obbligatorio)
    fn peso(&self) -> f64;

    /// Scheda descrittiva (implementazione di default)
    fn scheda(&self) -> String {
        format!("[{}] {} - {:.0}g", self.categoria(), self.nome(), self.peso())
    }

    /// Determina se e pericolosa (implementazione di default)
    fn e_pericolosa(&self) -> bool {
        self.categoria() == "Arma"
    }
}

/// Trait aggiuntivo per la classificazione
trait Classificabile: Reperto {
    fn periodo_stimato(&self) -> &str;
    fn punteggio_importanza(&self) -> u32;
}

// ============================================================================
// STRUCT CHE IMPLEMENTANO I TRAITS
// ============================================================================

struct Ascia {
    nome: String,
    lunghezza_cm: f64,
    peso_grammi: f64,
    materiale: Materiale,
}

impl Reperto for Ascia {
    fn nome(&self) -> &str { &self.nome }
    fn categoria(&self) -> &str { "Utensile/Arma" }
    fn peso(&self) -> f64 { self.peso_grammi }

    fn scheda(&self) -> String {
        format!("[{}] {} - {:.0}g, {:.1}cm, {}",
            self.categoria(), self.nome, self.peso_grammi,
            self.lunghezza_cm, self.materiale)
    }

    fn e_pericolosa(&self) -> bool { true }
}

impl Classificabile for Ascia {
    fn periodo_stimato(&self) -> &str { "Bronzo Finale (1200-950 a.C.)" }
    fn punteggio_importanza(&self) -> u32 { 8 }
}

struct Spada {
    nome: String,
    lunghezza_lama_cm: f64,
    lunghezza_totale_cm: f64,
    peso_grammi: f64,
}

impl Reperto for Spada {
    fn nome(&self) -> &str { &self.nome }
    fn categoria(&self) -> &str { "Arma" }
    fn peso(&self) -> f64 { self.peso_grammi }

    fn scheda(&self) -> String {
        format!("[{}] {} - {:.0}g, lama {:.1}cm, totale {:.1}cm",
            self.categoria(), self.nome, self.peso_grammi,
            self.lunghezza_lama_cm, self.lunghezza_totale_cm)
    }
}

impl Classificabile for Spada {
    fn periodo_stimato(&self) -> &str { "Bronzo Finale (1200-950 a.C.)" }
    fn punteggio_importanza(&self) -> u32 { 9 }
}

struct Fibula {
    nome: String,
    diametro_cm: f64,
    peso_grammi: f64,
}

impl Reperto for Fibula {
    fn nome(&self) -> &str { &self.nome }
    fn categoria(&self) -> &str { "Ornamento" }
    fn peso(&self) -> f64 { self.peso_grammi }

    fn scheda(&self) -> String {
        format!("[{}] {} - {:.0}g, diametro {:.1}cm",
            self.categoria(), self.nome, self.peso_grammi, self.diametro_cm)
    }
}

impl Classificabile for Fibula {
    fn periodo_stimato(&self) -> &str { "Eta del Ferro (950-500 a.C.)" }
    fn punteggio_importanza(&self) -> u32 { 6 }
}

// ============================================================================
// GENERICS
// ============================================================================

/// Struct generica con un tipo
struct Punto<T> {
    x: T,
    y: T,
}

/// Implementazione specifica per f64
impl Punto<f64> {
    fn distanza_origine(&self) -> f64 {
        (self.x * self.x + self.y * self.y).sqrt()
    }
}

/// Struct generica con due tipi
struct PuntoMisto<T, U> {
    x: T,
    y: U,
}

/// Contenitore generico con capacita massima
#[derive(Debug)]
struct Contenitore<T> {
    elementi: Vec<T>,
    capacita: usize,
}

impl<T> Contenitore<T> {
    fn nuovo(capacita: usize) -> Self {
        Contenitore {
            elementi: Vec::new(),
            capacita,
        }
    }

    fn aggiungi(&mut self, elemento: T) -> bool {
        if self.elementi.len() < self.capacita {
            self.elementi.push(elemento);
            true
        } else {
            false
        }
    }

    fn e_pieno(&self) -> bool {
        self.elementi.len() >= self.capacita
    }
}

/// Funzione generica con trait bound
fn trova_massimo<T: PartialOrd>(lista: &[T]) -> &T {
    let mut max = &lista[0];
    for item in &lista[1..] {
        if item > max {
            max = item;
        }
    }
    max
}

// ============================================================================
// FUNZIONI CON TRAIT BOUNDS
// ============================================================================

/// Accetta qualsiasi tipo che implementa Reperto (generics - dispatch statico)
fn stampa_info<T: Reperto>(reperto: &T) {
    println!("  {} [{}] - {:.0}g", reperto.nome(), reperto.categoria(), reperto.peso());
}

/// Trait bounds multipli
fn confronta_peso<T: Reperto, U: Reperto>(a: &T, b: &U) {
    let diff = (a.peso() - b.peso()).abs();
    if a.peso() > b.peso() {
        println!("  {} e piu pesante di {} di {:.0}g", a.nome(), b.nome(), diff);
    } else {
        println!("  {} e piu leggero di {} di {:.0}g", a.nome(), b.nome(), diff);
    }
}

/// impl Trait come parametro
fn mostra_reperto(r: &impl Reperto) {
    println!("  -> {}", r.scheda());
}

/// impl Trait come tipo di ritorno
fn crea_contatore(inizio: i32, fine: i32) -> impl Iterator<Item = i32> {
    inizio..=fine
}

// ============================================================================
// TRAITS STANDARD
// ============================================================================

#[derive(Debug, Clone, PartialEq, PartialOrd)]
struct Moneta {
    nome: String,
    valore: f64,
    metallo: String,
}

/// Implementazione manuale di Display
impl fmt::Display for Moneta {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{} ({} - valore: {})", self.nome, self.metallo, self.valore)
    }
}

/// Derive automatica per Coordinata
#[derive(Debug, Clone, PartialEq)]
struct Coordinata {
    lat: f64,
    lon: f64,
}

// ============================================================================
// WHERE CLAUSE
// ============================================================================

#[derive(Debug)]
struct Elemento {
    nome: String,
    valore: i32,
}

impl fmt::Display for Elemento {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}({})", self.nome, self.valore)
    }
}

struct Registro<T> {
    elementi: Vec<T>,
}

/// Where clause per trait bounds complessi
impl<T> Registro<T>
where
    T: fmt::Display + fmt::Debug,
{
    fn sommario(&self) -> String {
        self.elementi
            .iter()
            .map(|e| format!("{}", e))
            .collect::<Vec<_>>()
            .join(", ")
    }
}

impl<T: fmt::Display> fmt::Display for Registro<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Registro con {} elementi", self.elementi.len())
    }
}

// ============================================================================
// SISTEMA DI CLASSIFICAZIONE (ESEMPIO COMPLETO)
// ============================================================================

struct ClassificazioneReport {
    entries: Vec<(String, String, u32, f64)>, // nome, periodo, importanza, peso
}

impl ClassificazioneReport {
    fn nuovo() -> Self {
        ClassificazioneReport { entries: Vec::new() }
    }

    fn aggiungi(&mut self, reperto: &dyn Classificabile) {
        self.entries.push((
            reperto.nome().to_string(),
            reperto.periodo_stimato().to_string(),
            reperto.punteggio_importanza(),
            reperto.peso(),
        ));
    }

    fn stampa(&self) {
        println!("╔═══════════════════════════════════════════════════╗");
        println!("║         REPORT DI CLASSIFICAZIONE                ║");
        println!("╠═══════════════════════════════════════════════════╣");
        for (nome, periodo, importanza, peso) in &self.entries {
            println!("║ {} ", nome);
            println!("║   Periodo: {}", periodo);
            println!("║   Importanza: {}/10 | Peso: {:.0}g", importanza, peso);
            println!("╠═══════════════════════════════════════════════════╣");
        }
        let media_importanza: f64 = self.entries.iter()
            .map(|(_, _, imp, _)| *imp as f64)
            .sum::<f64>() / self.entries.len() as f64;
        println!("║ Media importanza: {:.1}/10", media_importanza);
        println!("╚═══════════════════════════════════════════════════╝");
    }
}

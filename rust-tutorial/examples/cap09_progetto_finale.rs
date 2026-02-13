// ============================================================================
// CAPITOLO 9: PROGETTO FINALE
// ============================================================================
// Un'applicazione completa che combina TUTTI i concetti appresi:
//
// GESTORE DI INVENTARIO ARCHEOLOGICO
// - Struct, enum, traits (Cap 3, 6)
// - Ownership e borrowing (Cap 2)
// - Gestione errori con Result (Cap 4)
// - Collezioni e iteratori (Cap 5)
// - Moduli (Cap 7)
// - Serializzazione JSON con serde
//
// Esegui con: cargo run --example cap09_progetto_finale
// ============================================================================

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fmt;

// ============================================================================
// MODULO: MODELLI
// ============================================================================
mod modelli {
    use super::*;

    /// Materiale del reperto
    #[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
    pub enum Materiale {
        Bronzo,
        Ferro,
        Oro,
        Argento,
        Ceramica,
        Pietra,
        Osso,
        Altro(String),
    }

    impl fmt::Display for Materiale {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
            match self {
                Materiale::Bronzo => write!(f, "Bronzo"),
                Materiale::Ferro => write!(f, "Ferro"),
                Materiale::Oro => write!(f, "Oro"),
                Materiale::Argento => write!(f, "Argento"),
                Materiale::Ceramica => write!(f, "Ceramica"),
                Materiale::Pietra => write!(f, "Pietra"),
                Materiale::Osso => write!(f, "Osso"),
                Materiale::Altro(s) => write!(f, "Altro: {}", s),
            }
        }
    }

    /// Periodo storico
    #[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
    pub enum Periodo {
        BronzoAntico,     // 2300-1700 a.C.
        BronzoMedio,      // 1700-1350 a.C.
        BronzoRecente,    // 1350-1200 a.C.
        BronzoFinale,     // 1200-950 a.C.
        PrimaEtaFerro,   // 950-750 a.C.
        Sconosciuto,
    }

    impl fmt::Display for Periodo {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
            match self {
                Periodo::BronzoAntico => write!(f, "Bronzo Antico (2300-1700 a.C.)"),
                Periodo::BronzoMedio => write!(f, "Bronzo Medio (1700-1350 a.C.)"),
                Periodo::BronzoRecente => write!(f, "Bronzo Recente (1350-1200 a.C.)"),
                Periodo::BronzoFinale => write!(f, "Bronzo Finale (1200-950 a.C.)"),
                Periodo::PrimaEtaFerro => write!(f, "Prima Eta del Ferro (950-750 a.C.)"),
                Periodo::Sconosciuto => write!(f, "Periodo sconosciuto"),
            }
        }
    }

    /// Stato di conservazione
    #[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
    pub enum Conservazione {
        Integro,
        Buono,
        Discreto,
        Frammentario,
        Pessimo,
    }

    impl Conservazione {
        pub fn punteggio(&self) -> u8 {
            match self {
                Conservazione::Integro => 5,
                Conservazione::Buono => 4,
                Conservazione::Discreto => 3,
                Conservazione::Frammentario => 2,
                Conservazione::Pessimo => 1,
            }
        }
    }

    impl fmt::Display for Conservazione {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
            match self {
                Conservazione::Integro => write!(f, "Integro"),
                Conservazione::Buono => write!(f, "Buono"),
                Conservazione::Discreto => write!(f, "Discreto"),
                Conservazione::Frammentario => write!(f, "Frammentario"),
                Conservazione::Pessimo => write!(f, "Pessimo"),
            }
        }
    }

    /// Coordinate geografiche
    #[derive(Debug, Clone, Serialize, Deserialize)]
    pub struct Coordinate {
        pub latitudine: f64,
        pub longitudine: f64,
    }

    impl fmt::Display for Coordinate {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
            write!(f, "({:.4}, {:.4})", self.latitudine, self.longitudine)
        }
    }

    /// Misurazioni del reperto
    #[derive(Debug, Clone, Serialize, Deserialize)]
    pub struct Misurazioni {
        pub lunghezza_cm: Option<f64>,
        pub larghezza_cm: Option<f64>,
        pub altezza_cm: Option<f64>,
        pub peso_grammi: Option<f64>,
    }

    impl Misurazioni {
        pub fn nuove() -> Self {
            Misurazioni {
                lunghezza_cm: None,
                larghezza_cm: None,
                altezza_cm: None,
                peso_grammi: None,
            }
        }

        pub fn con_dimensioni(mut self, l: f64, w: f64, h: f64) -> Self {
            self.lunghezza_cm = Some(l);
            self.larghezza_cm = Some(w);
            self.altezza_cm = Some(h);
            self
        }

        pub fn con_peso(mut self, p: f64) -> Self {
            self.peso_grammi = Some(p);
            self
        }

        pub fn volume_approssimativo(&self) -> Option<f64> {
            match (self.lunghezza_cm, self.larghezza_cm, self.altezza_cm) {
                (Some(l), Some(w), Some(h)) => Some(l * w * h),
                _ => None,
            }
        }
    }

    impl fmt::Display for Misurazioni {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
            let mut parti = Vec::new();
            if let Some(l) = self.lunghezza_cm {
                parti.push(format!("L:{:.1}cm", l));
            }
            if let Some(w) = self.larghezza_cm {
                parti.push(format!("W:{:.1}cm", w));
            }
            if let Some(h) = self.altezza_cm {
                parti.push(format!("H:{:.1}cm", h));
            }
            if let Some(p) = self.peso_grammi {
                parti.push(format!("{:.0}g", p));
            }
            if parti.is_empty() {
                write!(f, "N/D")
            } else {
                write!(f, "{}", parti.join(", "))
            }
        }
    }

    /// Reperto archeologico - la struct principale
    #[derive(Debug, Clone, Serialize, Deserialize)]
    pub struct Reperto {
        pub id: u32,
        pub nome: String,
        pub descrizione: String,
        pub materiale: Materiale,
        pub periodo: Periodo,
        pub conservazione: Conservazione,
        pub sito: String,
        pub coordinate: Option<Coordinate>,
        pub misurazioni: Misurazioni,
        pub note: Vec<String>,
    }

    impl fmt::Display for Reperto {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
            write!(
                f,
                "#{} {} ({}, {}, {})",
                self.id, self.nome, self.materiale, self.periodo, self.conservazione
            )
        }
    }
}

// ============================================================================
// MODULO: ERRORI
// ============================================================================
mod errori {
    use super::*;

    #[derive(Debug)]
    pub enum ErroreInventario {
        RepertoNonTrovato(u32),
        NomeVuoto,
        IdDuplicato(u32),
        DatiNonValidi(String),
        SerializzazioneErrore(String),
    }

    impl fmt::Display for ErroreInventario {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
            match self {
                ErroreInventario::RepertoNonTrovato(id) => {
                    write!(f, "Reperto con ID {} non trovato", id)
                }
                ErroreInventario::NomeVuoto => write!(f, "Il nome del reperto non puo essere vuoto"),
                ErroreInventario::IdDuplicato(id) => {
                    write!(f, "Esiste gia un reperto con ID {}", id)
                }
                ErroreInventario::DatiNonValidi(msg) => write!(f, "Dati non validi: {}", msg),
                ErroreInventario::SerializzazioneErrore(msg) => {
                    write!(f, "Errore serializzazione: {}", msg)
                }
            }
        }
    }

    impl From<serde_json::Error> for ErroreInventario {
        fn from(e: serde_json::Error) -> Self {
            ErroreInventario::SerializzazioneErrore(e.to_string())
        }
    }
}

// ============================================================================
// MODULO: INVENTARIO
// ============================================================================
mod inventario {
    use super::errori::ErroreInventario;
    use super::modelli::*;
    use std::collections::HashMap;

    /// Inventario principale
    pub struct Inventario {
        reperti: HashMap<u32, Reperto>,
        prossimo_id: u32,
    }

    impl Inventario {
        pub fn nuovo() -> Self {
            Inventario {
                reperti: HashMap::new(),
                prossimo_id: 1,
            }
        }

        /// Aggiungi un reperto con ID automatico
        pub fn aggiungi(&mut self, mut reperto: Reperto) -> Result<u32, ErroreInventario> {
            if reperto.nome.trim().is_empty() {
                return Err(ErroreInventario::NomeVuoto);
            }

            let id = self.prossimo_id;
            reperto.id = id;
            self.reperti.insert(id, reperto);
            self.prossimo_id += 1;
            Ok(id)
        }

        /// Cerca un reperto per ID
        pub fn cerca_per_id(&self, id: u32) -> Result<&Reperto, ErroreInventario> {
            self.reperti
                .get(&id)
                .ok_or(ErroreInventario::RepertoNonTrovato(id))
        }

        /// Cerca reperti per nome (ricerca parziale, case-insensitive)
        pub fn cerca_per_nome(&self, query: &str) -> Vec<&Reperto> {
            let query_lower = query.to_lowercase();
            self.reperti
                .values()
                .filter(|r| r.nome.to_lowercase().contains(&query_lower))
                .collect()
        }

        /// Cerca reperti per materiale
        pub fn cerca_per_materiale(&self, materiale: &Materiale) -> Vec<&Reperto> {
            self.reperti
                .values()
                .filter(|r| &r.materiale == materiale)
                .collect()
        }

        /// Cerca reperti per periodo
        pub fn cerca_per_periodo(&self, periodo: &Periodo) -> Vec<&Reperto> {
            self.reperti
                .values()
                .filter(|r| &r.periodo == periodo)
                .collect()
        }

        /// Cerca reperti per sito
        pub fn cerca_per_sito(&self, sito: &str) -> Vec<&Reperto> {
            let sito_lower = sito.to_lowercase();
            self.reperti
                .values()
                .filter(|r| r.sito.to_lowercase().contains(&sito_lower))
                .collect()
        }

        /// Rimuovi un reperto
        pub fn rimuovi(&mut self, id: u32) -> Result<Reperto, ErroreInventario> {
            self.reperti
                .remove(&id)
                .ok_or(ErroreInventario::RepertoNonTrovato(id))
        }

        /// Aggiungi una nota a un reperto
        pub fn aggiungi_nota(&mut self, id: u32, nota: &str) -> Result<(), ErroreInventario> {
            let reperto = self.reperti
                .get_mut(&id)
                .ok_or(ErroreInventario::RepertoNonTrovato(id))?;
            reperto.note.push(nota.to_string());
            Ok(())
        }

        /// Tutti i reperti
        pub fn tutti(&self) -> Vec<&Reperto> {
            let mut reperti: Vec<_> = self.reperti.values().collect();
            reperti.sort_by_key(|r| r.id);
            reperti
        }

        /// Numero totale di reperti
        pub fn totale(&self) -> usize {
            self.reperti.len()
        }

        /// Serializza l'inventario in JSON
        pub fn to_json(&self) -> Result<String, serde_json::Error> {
            let reperti: Vec<&Reperto> = self.tutti();
            serde_json::to_string_pretty(&reperti)
        }
    }
}

// ============================================================================
// MODULO: STATISTICHE
// ============================================================================
mod statistiche {
    use super::modelli::*;
    use std::collections::HashMap;

    pub struct ReportStatistiche {
        pub totale_reperti: usize,
        pub per_materiale: HashMap<String, usize>,
        pub per_periodo: HashMap<String, usize>,
        pub per_sito: HashMap<String, usize>,
        pub per_conservazione: HashMap<String, usize>,
        pub peso_medio: Option<f64>,
        pub peso_totale: f64,
        pub punteggio_conservazione_medio: f64,
    }

    pub fn genera_report(reperti: &[&Reperto]) -> ReportStatistiche {
        let mut per_materiale: HashMap<String, usize> = HashMap::new();
        let mut per_periodo: HashMap<String, usize> = HashMap::new();
        let mut per_sito: HashMap<String, usize> = HashMap::new();
        let mut per_conservazione: HashMap<String, usize> = HashMap::new();

        let mut peso_totale = 0.0;
        let mut count_peso = 0;
        let mut somma_conservazione = 0u32;

        for reperto in reperti {
            *per_materiale
                .entry(format!("{}", reperto.materiale))
                .or_insert(0) += 1;
            *per_periodo
                .entry(format!("{}", reperto.periodo))
                .or_insert(0) += 1;
            *per_sito
                .entry(reperto.sito.clone())
                .or_insert(0) += 1;
            *per_conservazione
                .entry(format!("{}", reperto.conservazione))
                .or_insert(0) += 1;

            if let Some(peso) = reperto.misurazioni.peso_grammi {
                peso_totale += peso;
                count_peso += 1;
            }

            somma_conservazione += reperto.conservazione.punteggio() as u32;
        }

        let peso_medio = if count_peso > 0 {
            Some(peso_totale / count_peso as f64)
        } else {
            None
        };

        let punteggio_conservazione_medio = if !reperti.is_empty() {
            somma_conservazione as f64 / reperti.len() as f64
        } else {
            0.0
        };

        ReportStatistiche {
            totale_reperti: reperti.len(),
            per_materiale,
            per_periodo,
            per_sito,
            per_conservazione,
            peso_medio,
            peso_totale,
            punteggio_conservazione_medio,
        }
    }

    pub fn stampa_report(report: &ReportStatistiche) {
        println!("╔═══════════════════════════════════════════════════════╗");
        println!("║            STATISTICHE INVENTARIO                    ║");
        println!("╠═══════════════════════════════════════════════════════╣");
        println!("║  Totale reperti: {:>4}                                ║", report.totale_reperti);
        println!("║  Peso totale: {:>8.0}g                              ║", report.peso_totale);
        if let Some(medio) = report.peso_medio {
            println!("║  Peso medio:  {:>8.1}g                              ║", medio);
        }
        println!("║  Conservazione media: {:.1}/5                          ║",
            report.punteggio_conservazione_medio);
        println!("╠═══════════════════════════════════════════════════════╣");

        println!("║  PER MATERIALE:                                      ║");
        let mut materiali: Vec<_> = report.per_materiale.iter().collect();
        materiali.sort_by(|a, b| b.1.cmp(a.1));
        for (mat, count) in &materiali {
            let barre = "#".repeat(*count * 2);
            println!("║    {:<15} {:>3} {:<20}       ║", mat, count, barre);
        }

        println!("╠═══════════════════════════════════════════════════════╣");
        println!("║  PER PERIODO:                                        ║");
        let mut periodi: Vec<_> = report.per_periodo.iter().collect();
        periodi.sort_by(|a, b| b.1.cmp(a.1));
        for (per, count) in &periodi {
            println!("║    {:<40} {:>3}  ║", per, count);
        }

        println!("╠═══════════════════════════════════════════════════════╣");
        println!("║  PER SITO:                                           ║");
        let mut siti: Vec<_> = report.per_sito.iter().collect();
        siti.sort_by(|a, b| b.1.cmp(a.1));
        for (sito, count) in &siti {
            println!("║    {:<40} {:>3}  ║", sito, count);
        }

        println!("╠═══════════════════════════════════════════════════════╣");
        println!("║  PER CONSERVAZIONE:                                  ║");
        let mut conservazione: Vec<_> = report.per_conservazione.iter().collect();
        conservazione.sort_by(|a, b| b.1.cmp(a.1));
        for (stato, count) in &conservazione {
            println!("║    {:<15} {:>3}                                  ║", stato, count);
        }

        println!("╚═══════════════════════════════════════════════════════╝");
    }
}

// ============================================================================
// MAIN - DIMOSTRAZIONE COMPLETA
// ============================================================================

use modelli::*;
use errori::ErroreInventario;
use inventario::Inventario;

fn main() {
    println!("╔══════════════════════════════════════════════════════════╗");
    println!("║   CAPITOLO 9: PROGETTO FINALE                           ║");
    println!("║   Gestore di Inventario Archeologico                     ║");
    println!("╚══════════════════════════════════════════════════════════╝\n");

    // ========================================================================
    // FASE 1: Creazione dell'inventario
    // ========================================================================
    println!("--- Fase 1: Popolamento Inventario ---\n");

    let mut inv = Inventario::nuovo();

    // Reperti del ripostiglio di Savignano
    let reperti_da_inserire = vec![
        Reperto {
            id: 0,
            nome: "Ascia a margini rialzati tipo Savignano".to_string(),
            descrizione: "Ascia in bronzo con margini rialzati e tallone distinto".to_string(),
            materiale: Materiale::Bronzo,
            periodo: Periodo::BronzoFinale,
            conservazione: Conservazione::Buono,
            sito: "Savignano Irpino".to_string(),
            coordinate: Some(Coordinate { latitudine: 41.2247, longitudine: 15.1788 }),
            misurazioni: Misurazioni::nuove().con_dimensioni(18.5, 4.2, 2.1).con_peso(350.0),
            note: vec!["Patina verde uniforme".to_string()],
        },
        Reperto {
            id: 0,
            nome: "Ascia a tallone tipo appenninico".to_string(),
            descrizione: "Ascia con tallone sviluppato e lama espansa".to_string(),
            materiale: Materiale::Bronzo,
            periodo: Periodo::BronzoFinale,
            conservazione: Conservazione::Integro,
            sito: "Savignano Irpino".to_string(),
            coordinate: Some(Coordinate { latitudine: 41.2247, longitudine: 15.1788 }),
            misurazioni: Misurazioni::nuove().con_dimensioni(21.0, 5.5, 2.8).con_peso(480.0),
            note: vec![],
        },
        Reperto {
            id: 0,
            nome: "Spada tipo Allerona".to_string(),
            descrizione: "Spada con lingua da presa e lama a foglia".to_string(),
            materiale: Materiale::Bronzo,
            periodo: Periodo::BronzoFinale,
            conservazione: Conservazione::Discreto,
            sito: "Savignano Irpino".to_string(),
            coordinate: Some(Coordinate { latitudine: 41.2247, longitudine: 15.1788 }),
            misurazioni: Misurazioni::nuove().con_dimensioni(65.0, 5.0, 1.5).con_peso(850.0),
            note: vec!["Lama con segni di utilizzo".to_string(), "Punta spezzata".to_string()],
        },
        Reperto {
            id: 0,
            nome: "Pugnale a lingua da presa".to_string(),
            descrizione: "Pugnale con manico a lingua e rivetti".to_string(),
            materiale: Materiale::Bronzo,
            periodo: Periodo::BronzoRecente,
            conservazione: Conservazione::Buono,
            sito: "Savignano Irpino".to_string(),
            coordinate: None,
            misurazioni: Misurazioni::nuove().con_dimensioni(28.0, 4.0, 1.0).con_peso(280.0),
            note: vec![],
        },
        Reperto {
            id: 0,
            nome: "Fibula ad arco serpeggiante".to_string(),
            descrizione: "Fibula in bronzo con arco a serpentina".to_string(),
            materiale: Materiale::Bronzo,
            periodo: Periodo::PrimaEtaFerro,
            conservazione: Conservazione::Integro,
            sito: "Pontecagnano".to_string(),
            coordinate: Some(Coordinate { latitudine: 40.6435, longitudine: 14.8715 }),
            misurazioni: Misurazioni::nuove().con_dimensioni(8.5, 3.0, 2.0).con_peso(45.0),
            note: vec!["Ardiglione integro".to_string()],
        },
        Reperto {
            id: 0,
            nome: "Punta di lancia a fiamma".to_string(),
            descrizione: "Punta di lancia con lama a fiamma e cannone".to_string(),
            materiale: Materiale::Bronzo,
            periodo: Periodo::BronzoRecente,
            conservazione: Conservazione::Frammentario,
            sito: "Toppo Daguzzo".to_string(),
            coordinate: None,
            misurazioni: Misurazioni::nuove().con_dimensioni(22.0, 4.5, 3.0).con_peso(150.0),
            note: vec!["Cannone fratturato".to_string()],
        },
        Reperto {
            id: 0,
            nome: "Anello a cerchio".to_string(),
            descrizione: "Anello in bronzo con sezione circolare".to_string(),
            materiale: Materiale::Bronzo,
            periodo: Periodo::BronzoFinale,
            conservazione: Conservazione::Integro,
            sito: "Savignano Irpino".to_string(),
            coordinate: Some(Coordinate { latitudine: 41.2247, longitudine: 15.1788 }),
            misurazioni: Misurazioni::nuove().con_dimensioni(3.0, 3.0, 0.5).con_peso(25.0),
            note: vec![],
        },
        Reperto {
            id: 0,
            nome: "Frammento di vaso a impasto".to_string(),
            descrizione: "Frammento di parete con decorazione a cordoni".to_string(),
            materiale: Materiale::Ceramica,
            periodo: Periodo::BronzoMedio,
            conservazione: Conservazione::Frammentario,
            sito: "Toppo Daguzzo".to_string(),
            coordinate: None,
            misurazioni: Misurazioni::nuove().con_dimensioni(8.0, 6.0, 0.8).con_peso(95.0),
            note: vec!["Decorazione a cordoni plastici".to_string()],
        },
        Reperto {
            id: 0,
            nome: "Rasoio lunato".to_string(),
            descrizione: "Rasoio in bronzo a forma di mezzaluna".to_string(),
            materiale: Materiale::Bronzo,
            periodo: Periodo::PrimaEtaFerro,
            conservazione: Conservazione::Discreto,
            sito: "Pontecagnano".to_string(),
            coordinate: Some(Coordinate { latitudine: 40.6435, longitudine: 14.8715 }),
            misurazioni: Misurazioni::nuove().con_dimensioni(12.0, 8.0, 0.3).con_peso(65.0),
            note: vec![],
        },
        Reperto {
            id: 0,
            nome: "Falce in bronzo".to_string(),
            descrizione: "Falce con innesto a codolo".to_string(),
            materiale: Materiale::Bronzo,
            periodo: Periodo::BronzoRecente,
            conservazione: Conservazione::Pessimo,
            sito: "Savignano Irpino".to_string(),
            coordinate: None,
            misurazioni: Misurazioni::nuove().con_dimensioni(25.0, 3.5, 0.5).con_peso(180.0),
            note: vec!["Fortemente ossidata".to_string(), "Codolo frammentato".to_string()],
        },
    ];

    for reperto in reperti_da_inserire {
        match inv.aggiungi(reperto) {
            Ok(id) => println!("  Aggiunto reperto ID #{}", id),
            Err(e) => println!("  ERRORE: {}", e),
        }
    }

    println!("\n  Totale reperti inseriti: {}", inv.totale());

    // ========================================================================
    // FASE 2: Ricerche
    // ========================================================================
    println!("\n--- Fase 2: Ricerche ---\n");

    // Per ID
    print_search_result("Ricerca ID #3", || {
        inv.cerca_per_id(3).map(|r| format!("  {}", r))
    });

    // ID non esistente
    print_search_result("Ricerca ID #99", || {
        inv.cerca_per_id(99).map(|r| format!("  {}", r))
    });

    // Per nome
    println!("Ricerca nome 'ascia':");
    for r in inv.cerca_per_nome("ascia") {
        println!("  {}", r);
    }

    // Per materiale
    println!("\nReperti in Ceramica:");
    for r in inv.cerca_per_materiale(&Materiale::Ceramica) {
        println!("  {}", r);
    }

    // Per periodo
    println!("\nReperti Bronzo Finale:");
    for r in inv.cerca_per_periodo(&Periodo::BronzoFinale) {
        println!("  {}", r);
    }

    // Per sito
    println!("\nReperti da Pontecagnano:");
    for r in inv.cerca_per_sito("pontecagnano") {
        println!("  {}", r);
    }

    // ========================================================================
    // FASE 3: Operazioni sull'inventario
    // ========================================================================
    println!("\n--- Fase 3: Operazioni ---\n");

    // Aggiungi note
    match inv.aggiungi_nota(1, "Analisi XRF completata: Cu 88%, Sn 12%") {
        Ok(()) => println!("  Nota aggiunta al reperto #1"),
        Err(e) => println!("  Errore: {}", e),
    }

    // Mostra reperto con note
    if let Ok(reperto) = inv.cerca_per_id(1) {
        println!("  Reperto #1 - Note:");
        for nota in &reperto.note {
            println!("    - {}", nota);
        }
    }

    // Rimuovi un reperto
    match inv.rimuovi(10) {
        Ok(rimosso) => println!("\n  Rimosso: {}", rimosso.nome),
        Err(e) => println!("\n  Errore rimozione: {}", e),
    }
    println!("  Totale dopo rimozione: {}", inv.totale());

    // ========================================================================
    // FASE 4: Statistiche
    // ========================================================================
    println!("\n--- Fase 4: Statistiche ---\n");

    let tutti = inv.tutti();
    let report = statistiche::genera_report(&tutti);
    statistiche::stampa_report(&report);

    // ========================================================================
    // FASE 5: Analisi avanzate con iteratori
    // ========================================================================
    println!("\n--- Fase 5: Analisi Avanzate ---\n");

    // Reperto piu pesante
    let piu_pesante = inv.tutti().into_iter()
        .filter(|r| r.misurazioni.peso_grammi.is_some())
        .max_by(|a, b| {
            a.misurazioni.peso_grammi.unwrap()
                .partial_cmp(&b.misurazioni.peso_grammi.unwrap())
                .unwrap()
        });

    if let Some(r) = piu_pesante {
        println!("  Reperto piu pesante: {} ({:.0}g)",
            r.nome, r.misurazioni.peso_grammi.unwrap());
    }

    // Reperto piu leggero
    let piu_leggero = inv.tutti().into_iter()
        .filter(|r| r.misurazioni.peso_grammi.is_some())
        .min_by(|a, b| {
            a.misurazioni.peso_grammi.unwrap()
                .partial_cmp(&b.misurazioni.peso_grammi.unwrap())
                .unwrap()
        });

    if let Some(r) = piu_leggero {
        println!("  Reperto piu leggero: {} ({:.0}g)",
            r.nome, r.misurazioni.peso_grammi.unwrap());
    }

    // Distribuzione pesi per periodo
    println!("\n  Peso medio per periodo:");
    let mut pesi_per_periodo: HashMap<String, (f64, usize)> = HashMap::new();
    for r in inv.tutti() {
        if let Some(peso) = r.misurazioni.peso_grammi {
            let entry = pesi_per_periodo
                .entry(format!("{}", r.periodo))
                .or_insert((0.0, 0));
            entry.0 += peso;
            entry.1 += 1;
        }
    }
    let mut periodi_ordinati: Vec<_> = pesi_per_periodo.iter().collect();
    periodi_ordinati.sort_by(|a, b| {
        let media_a = a.1.0 / a.1.1 as f64;
        let media_b = b.1.0 / b.1.1 as f64;
        media_b.partial_cmp(&media_a).unwrap()
    });
    for (periodo, (totale, count)) in &periodi_ordinati {
        let media = totale / *count as f64;
        println!("    {}: {:.0}g (media su {} reperti)", periodo, media, count);
    }

    // Reperti con coordinate
    let con_coordinate: Vec<_> = inv.tutti().into_iter()
        .filter(|r| r.coordinate.is_some())
        .collect();
    println!("\n  Reperti con coordinate GPS: {}/{}", con_coordinate.len(), inv.totale());

    // Volume approssimativo
    println!("\n  Volumi approssimativi:");
    for r in inv.tutti() {
        if let Some(vol) = r.misurazioni.volume_approssimativo() {
            println!("    {}: {:.1} cm3", r.nome, vol);
        }
    }

    // ========================================================================
    // FASE 6: Esportazione JSON
    // ========================================================================
    println!("\n--- Fase 6: Esportazione JSON ---\n");

    match inv.to_json() {
        Ok(json) => {
            // Mostra solo le prime righe per non inondare l'output
            let righe: Vec<&str> = json.lines().collect();
            let max_righe = 20;
            for riga in righe.iter().take(max_righe) {
                println!("  {}", riga);
            }
            if righe.len() > max_righe {
                println!("  ... ({} righe totali)", righe.len());
            }
            println!("\n  JSON generato con successo ({} bytes)", json.len());
        }
        Err(e) => println!("  Errore esportazione: {}", e),
    }

    // ========================================================================
    // RIEPILOGO
    // ========================================================================
    println!("\n--- Riepilogo del Progetto ---\n");

    println!("Questo progetto ha utilizzato:");
    println!("  Cap 1 - Variabili, funzioni, cicli, formattazione");
    println!("  Cap 2 - Ownership (&, &mut, clone) in tutte le funzioni");
    println!("  Cap 3 - Struct (Reperto, Misurazioni), Enum (Materiale, Periodo)");
    println!("  Cap 4 - Result<T,E>, ErroreInventario, operatore ?");
    println!("  Cap 5 - Vec, HashMap, String, iteratori (filter, map, fold)");
    println!("  Cap 6 - Display trait, Serialize/Deserialize, From trait");
    println!("  Cap 7 - Moduli (modelli, errori, inventario, statistiche)");
    println!("  Cap 8 - (La concorrenza si applica in server/analisi parallela)");

    println!("\n✅ Capitolo 9 completato! Congratulazioni, hai completato il tutorial!");
    println!("   Ora sei pronto per costruire applicazioni reali in Rust.");
}

// ============================================================================
// FUNZIONI HELPER
// ============================================================================

fn print_search_result<F>(label: &str, f: F)
where
    F: FnOnce() -> Result<String, ErroreInventario>,
{
    print!("{}:", label);
    match f() {
        Ok(msg) => println!("\n{}", msg),
        Err(e) => println!(" {}", e),
    }
}

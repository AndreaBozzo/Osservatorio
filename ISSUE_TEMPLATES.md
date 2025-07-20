# Issue Templates - Osservatorio ISTAT

Questo progetto utilizza template strutturati per GitHub Issues per migliorare la qualit� delle segnalazioni e facilitare la gestione del progetto.

## =� Template Disponibili

### = Bug Report (`.github/ISSUE_TEMPLATE/bug_report.yml`)
Per segnalare malfunzionamenti, errori o comportamenti non attesi del sistema.

**Campi principali:**
- Descrizione dettagliata del problema
- Passi per riprodurre l'errore
- Comportamento atteso vs attuale
- Informazioni sull'ambiente di sviluppo
- Log e output di errore
- Priorit� e componente interessato

**Labels automatici:** `type: bug`, `status: ready`

### ( Feature Request (`.github/ISSUE_TEMPLATE/feature_request.yml`)
Per proporre nuove funzionalit� o miglioramenti al sistema.

**Campi principali:**
- Riassunto della funzionalit� proposta
- Problema che la funzionalit� risolverebbe
- Soluzione dettagliata proposta
- Casi d'uso specifici
- Priorit� e sforzo stimato
- Dettagli tecnici e mockup

**Labels automatici:** `type: feature`, `status: ready`

### =� Documentation (`.github/ISSUE_TEMPLATE/documentation.yml`)
Per segnalare problemi con la documentazione o proporre miglioramenti.

**Campi principali:**
- Tipo di problema documentazione
- Posizione specifica del problema
- Contenuto attuale problematico
- Suggerimenti per il miglioramento
- Pubblico target della documentazione
- Priorit� della modifica

**Labels automatici:** `type: documentation`, `status: ready`

## <� Sistema di Labels

I template utilizzano il sistema di labels standardizzato del progetto:

### Type Labels
- `type: bug` - Segnalazioni di malfunzionamenti
- `type: feature` - Richieste di nuove funzionalit�
- `type: documentation` - Problemi/miglioramenti documentazione
- `type: refactor` - Ristrutturazione codice
- `type: test` - Miglioramenti ai test
- `type: performance` - Ottimizzazioni prestazioni
- `type: security` - Questioni di sicurezza

### Priority Labels
- `priority: critical` - Problemi bloccanti
- `priority: high` - Alta priorit�
- `priority: medium` - Media priorit�
- `priority: low` - Bassa priorit�

### Status Labels
- `status: ready` - Pronto per essere lavorato
- `status: in progress` - In lavorazione
- `status: blocked` - Bloccato da dipendenze
- `status: review needed` - Richiede revisione
- `status: waiting for info` - In attesa di informazioni

### Component Labels
- `component: api` - API layer (ISTAT, PowerBI, Tableau)
- `component: dashboard` - Streamlit dashboard
- `component: database` - Layer database (DuckDB)
- `component: etl` - Elaborazione dati
- `component: infrastructure` - Docker, CI/CD, deployment
- `component: testing` - Suite di test

## =� Best Practices per i Contributori

### Prima di Creare un Issue
1. **Cerca issue esistenti** simili per evitare duplicati
2. **Usa il template appropriato** per il tipo di segnalazione
3. **Fornisci informazioni complete** compilando tutti i campi richiesti
4. **Aggiungi contesto specifico** al progetto Osservatorio ISTAT

### Compilazione dei Template
1. **Sii specifico e dettagliato** nelle descrizioni
2. **Includi esempi concreti** quando possibile
3. **Aggiungi screenshot o log** se rilevanti
4. **Indica chiaramente i passi di riproduzione** per i bug
5. **Specifica l'ambiente di sviluppo** (Python, OS, browser)

### Esempi di Buone Pratiche

#### Bug Report 
```
Titolo: [BUG] Dashboard Streamlit non carica dati ISTAT su Python 3.13
- Descrizione dettagliata del problema
- Passi precisi per riprodurre
- Log di errore completi
- Informazioni ambiente (OS, Python, dipendenze)
```

#### Feature Request 
```
Titolo: [FEATURE] Integrazione API Eurostat per dati comparativi
- Problema business chiaro
- Soluzione tecnica dettagliata
- Casi d'uso specifici per analisti
- Mockup o diagrammi (se applicabile)
```

#### Documentation 
```
Titolo: [DOCS] Istruzioni installazione DuckDB mancanti in README
- Posizione esatta del problema
- Contenuto attuale problematico
- Testo corretto suggerito
- Contesto dell'utente target
```

## =' Configurazione per Manutentori

### Modifica dei Template
I template sono in formato YAML e si trovano in `.github/ISSUE_TEMPLATE/`. Per modificarli:

1. Edita i file `.yml` nella directory
2. Testa le modifiche creando issue di prova
3. Aggiorna questa documentazione se necessario

### Gestione Labels
I labels sono configurati automaticamente. Per aggiungere nuovi labels:

1. Usa l'interfaccia GitHub Settings � Labels
2. Segui la convenzione `category: name`
3. Aggiorna i template per utilizzare i nuovi labels
4. Documenta i cambiamenti in questo file

## =� Risorse Aggiuntive

- [GitHub Issue Template Documentation](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests)
- [CONTRIBUTING.md](docs/guides/CONTRIBUTING.md) - Guida per contributori
- [PROJECT_STATE.md](PROJECT_STATE.md) - Stato corrente del progetto
- [Architecture Documentation](docs/ARCHITECTURE.md) - Architettura del sistema

---

**Nota:** Questo sistema di template � progettato per migliorare la collaborazione e la qualit� delle segnalazioni. Se hai suggerimenti per migliorare i template, apri un issue usando il template "Documentation"!

# 🛠️ Osservatorio Scripts

Collezione di script per automatizzare tasks comuni del progetto.

## 🚀 create-issue.sh

Script rapido e intuitivo per creare GitHub issues, creato specificamente per @Gasta88.

### ✨ Features
- **3 modalità operative**: Interactive, Express, Template
- **Auto-completamento labels**: Sistema di labels comprensivo
- **Templates predefiniti**: Bug, Feature, Performance, Security, etc.
- **UI colorata e intuitiva**: Facilita l'uso con colori e emoji
- **Validazione input**: Controlli di sicurezza e coerenza
- **Browser integration**: Apre direttamente l'issue nel browser

### 🔧 Setup
```bash
# Rendi eseguibile (una sola volta)
chmod +x scripts/create-issue.sh

# Assicurati che GitHub CLI sia installato e configurato
sudo apt install gh  # Ubuntu/Debian
gh auth login
```

### 📖 Usage

#### Modalità Interactive (Raccomandata)
```bash
./scripts/create-issue.sh
# Segui il wizard step-by-step
```

#### Express Mode (Veloce)
```bash
./scripts/create-issue.sh
# Scegli modalità 2, inserisci solo title/description/labels
```

#### Template Mode (Pre-configurata)
```bash
./scripts/create-issue.sh
# Scegli modalità 3, seleziona template (bug/feature/etc.)
```

#### Show Available Labels
```bash
./scripts/create-issue.sh
# Scegli modalità 4 per vedere tutte le labels disponibili
```

### 🏷️ Sistema Labels Comprensivo

#### Type Labels
- `type: bug` - Problemi e malfunzionamenti
- `type: feature` - Nuove funzionalità
- `type: enhancement` - Miglioramenti esistenti
- `type: documentation` - Documentazione
- `type: performance` - Ottimizzazioni performance
- `type: security` - Sicurezza e vulnerabilità
- `type: test` - Testing e QA
- `type: refactor` - Refactoring codice

#### Priority Labels
- `priority: critical` - Bloccante, immediata
- `priority: high` - Alta priorità
- `priority: medium` - Priorità normale
- `priority: low` - Nice to have

#### Component Labels
- `component: api` - API endpoints
- `component: auth` - Autenticazione
- `component: cache` - Sistema caching
- `component: cli` - Command-line interface
- `component: config` - Configurazione
- `component: database` - Database (SQLite/DuckDB)
- `component: dashboard` - Streamlit dashboard
- `component: etl` - Extract Transform Load
- `component: integration` - Integrazioni esterne
- `component: monitoring` - Monitoring e logging
- `component: security` - Security audit
- `component: testing` - Test suite

#### Status Labels
- `status: ready` - Pronto per essere lavorato
- `status: in progress` - Work in progress
- `status: blocked` - Bloccato da dipendenze
- `status: review needed` - Needs review
- `status: waiting for info` - Info mancanti

#### Effort Labels
- `effort: minutes` - <1 ora
- `effort: hours` - Qualche ora
- `effort: days` - 1+ giorni
- `effort: weeks` - 1+ settimane

#### Scope Labels
- `scope: sprint` - Sprint corrente
- `scope: backlog` - Backlog futuro
- `scope: maintenance` - Tech debt
- `scope: research` - Spike/research

#### Impact Labels
- `impact: breaking` - Breaking changes
- `impact: major` - Cambiamenti significativi
- `impact: minor` - Modifiche minori

#### Platform Labels
- `platform: linux` - Linux-specific
- `platform: windows` - Windows-specific
- `platform: macos` - macOS-specific
- `platform: docker` - Container-related

#### Experience Labels
- `experience: beginner` - Good first issue
- `experience: intermediate` - Richiede esperienza
- `experience: advanced` - Expertise necessaria

### 💡 Tips per @Gasta88

#### Workflow Veloce
1. **Express Mode** per issue semplici
2. **Template Mode** per issue standard (bug/feature)
3. **Interactive Mode** per issue complesse

#### Labels Raccomandate
- **Bug**: `type: bug,priority: high,status: ready,component: <relevant>`
- **Feature**: `type: feature,priority: medium,scope: sprint,effort: hours`
- **Performance**: `type: performance,priority: high,component: database`
- **Security**: `type: security,priority: critical,component: security`

#### Shortcuts
```bash
# Alias per facilità
alias issue='./scripts/create-issue.sh'
issue  # Lancia lo script velocemente
```

### 🔧 Customizzazione

Per aggiungere nuovi template o modificare le labels, edita:
- `TEMPLATES` array per nuovi template
- `LABEL_CATEGORIES` per nuove categorie di labels

### 📞 Support

Per problemi o suggerimenti:
- **GitHub Issues**: Usa il proprio script! 😄
- **Discussions**: GitHub Discussions del repo
- **Menzione**: @Gasta88 nelle issue

---

**Creato con ❤️ per automatizzare il workflow di @Gasta88**

# CONTRIBUTING.md

> **Benvenuti in Osservatorio!** 🎯
> Questa guida vi aiuterà a contribuire efficacemente al progetto. Ogni contributo, grande o piccolo, è prezioso.

## 📋 Table of Contents

1. [Codice di Condotta](#codice-di-condotta)
2. [Come Iniziare](#come-iniziare)
3. [Processo di Sviluppo](#processo-di-sviluppo)
4. [Standard di Codice](#standard-di-codice)
5. [Testing](#testing)
6. [Documentazione](#documentazione)
7. [Submission Guidelines](#submission-guidelines)
8. [Riconoscimenti](#riconoscimenti)

## 🤝 Codice di Condotta

### I Nostri Valori
- **Rispetto**: Ogni opinione conta, ogni approccio merita considerazione
- **Collaborazione**: Il successo del progetto dipende dal lavoro di squadra
- **Qualità**: Preferiamo soluzioni robuste a fix veloci
- **Trasparenza**: Documentiamo decisioni e processi apertamente

### Comportamenti Attesi
- Usare un linguaggio accogliente e inclusivo
- Rispettare punti di vista ed esperienze diverse
- Accettare critiche costruttive con professionalità
- Focalizzarsi su ciò che è meglio per il progetto e la community

## 🚀 Come Iniziare

### 1. Setup Ambiente di Sviluppo

```bash
# Fork e clone del repository
git clone https://github.com/YOUR_USERNAME/Osservatorio.git
cd Osservatorio

# Crea virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure
venv\Scripts\activate  # Windows

# Installa dipendenze
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Verifica che tutto funzioni
pytest
```

### 2. Esplora la Codebase

Prima di contribuire, familiarizzati con:

- `docs/architecture.md` - Overview architetturale
- `docs/api-mapping.md` - Documentazione API esterne
- `PROJECT_STATE.md` - Stato attuale e roadmap
- Issue board - Task disponibili e priorità

### 3. Scegli un Task

#### Per Nuovi Contributors
Cerca issue con label:

- `good first issue` - Perfetti per iniziare
- `help wanted` - Dove abbiamo bisogno di aiuto
- `documentation` - Sempre un ottimo punto di partenza

oppure contatta il maintainer tramite i canali segnalati

#### Per Contributors Esperti

- `enhancement` - Nuove funzionalità
- `performance` - Ottimizzazioni
- `architecture` - Decisioni di design

## 🔄 Processo di Sviluppo

### Git Workflow

```bash
# Crea un branch dal main
git checkout main
git pull origin main
git checkout -b feature/nome-descrittivo
# oppure
git checkout -b fix/bug-description
```

#### Convenzioni per i branch

- `feature/` - Nuove funzionalità
- `fix/` - Bug fixes
- `docs/` - Documentazione
- `test/` - Aggiunta o fix di test
- `refactor/` - Refactoring senza cambi funzionali

#### Commit spesso con messaggi chiari

```bash
# ✅ Buono
git commit -m "feat: aggiunge validazione schema SDMX per dataset popolazione"

# ❌ Evitare
git commit -m "fix stuff"
```

### Commit Message Format

Seguiamo una versione semplificata di Conventional Commits:

```
<type>: <description>

[optional body]

[optional footer]
```

#### Types:

- `feat:` Nuova funzionalità
- `fix:` Bug fix
- `docs:` Solo documentazione
- `test:` Aggiunta o modifica test
- `refactor:` Refactoring codice
- `perf:` Miglioramento performance
- `chore:` Maintenance (dipendenze, config, etc.)

#### Esempi:

```
feat: implementa cache per richieste API ISTAT

Aggiunge un layer di caching con TTL configurabile per ridurre
il carico sulle API esterne. Default TTL: 1 ora.

Closes #123
```
## 📏 Standard di Codice

### Python Style Guide

Seguiamo PEP 8 con alcune estensioni:
```python
# ✅ Imports ordinati e raggruppati
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy import create_engine

from src.utils.logger import get_logger
from src.api.base import BaseAPI

# ✅ Docstring dettagliate per funzioni pubbliche
def process_dataset(
    dataset_id: str,
    transform_options: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Processa un dataset ISTAT applicando le trasformazioni richieste.

    Args:
        dataset_id: Identificativo univoco del dataset
        transform_options: Dizionario con opzioni di trasformazione
            - normalize: bool, normalizza i valori
            - aggregate: str, livello di aggregazione

    Returns:
        DataFrame processato pronto per visualizzazione

    Raises:
        DatasetNotFoundError: Se il dataset non esiste
        TransformationError: Se la trasformazione fallisce
    """
    # Implementazione...

# ✅ Type hints sempre
def calculate_growth_rate(
    current: float,
    previous: float,
    decimals: int = 2
) -> float:
    """Calcola il tasso di crescita percentuale."""
    if previous == 0:
        return 0.0
    return round((current - previous) / previous * 100, decimals)

# ✅ Constants in maiuscolo
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
CACHE_TTL_HOURS = 1
```

### Struttura File

```python
"""
Modulo per gestione cache delle richieste API.

Questo modulo fornisce funzionalità di caching per ridurre
il carico sulle API esterne e migliorare le performance.
"""

# 1. Imports
import ...

# 2. Constants
CACHE_VERSION = "1.0"

# 3. Exceptions
class CacheError(Exception):
    """Errore generico per operazioni di cache."""
    pass

# 4. Classes
class CacheManager:
    """Gestisce il caching delle risposte API."""

    def __init__(self, ttl_hours: int = 1):
        self.ttl_hours = ttl_hours
        # ...

# 5. Functions
def clear_expired_cache() -> int:
    """Rimuove entries scadute dalla cache."""
    # ...

# 6. Main (se applicabile)
if __name__ == "__main__":
    # Test o esempio d'uso
    pass
```

### Best Practices

#### SOLID Principles

- **Single Responsibility**: Ogni classe/funzione fa una cosa sola
- **Open/Closed**: Estendibile senza modificare codice esistente
- **Interface Segregation**: Interfacce piccole e specifiche

#### Error Handling

```python
# ✅ Specifico e informativo
try:
    response = fetch_istat_data(dataset_id)
except requests.RequestException as e:
    logger.error(f"Errore nel fetch del dataset {dataset_id}: {e}")
    raise DataFetchError(f"Impossibile recuperare dataset {dataset_id}") from e

# ❌ Generico
try:
    response = fetch_istat_data(dataset_id)
except Exception:
    print("Errore!")
```

#### Logging

```python
logger = get_logger(__name__)

# Usa livelli appropriati
logger.debug(f"Inizio processing dataset {dataset_id}")
logger.info(f"Dataset {dataset_id} processato con successo")
logger.warning(f"Dataset {dataset_id} contiene valori mancanti")
logger.error(f"Fallito processing dataset {dataset_id}: {error}")
```
## 🧪 Testing

### Filosofia di Testing

- **Test First**: Scrivi test prima del codice quando possibile
- **Coverage Target**: Minimo 70% per nuovo codice
- **Test Pyramid**: Molti unit test, medi integration, pochi E2E

### Struttura Test

```python
# tests/unit/test_cache_manager.py
import pytest
from datetime import datetime, timedelta

from src.cache.manager import CacheManager, CacheError

class TestCacheManager:
    """Test suite per CacheManager."""

    @pytest.fixture
    def cache_manager(self):
        """Fixture che fornisce un'istanza pulita di CacheManager."""
        return CacheManager(ttl_hours=1)

    def test_set_and_get_item(self, cache_manager):
        """Test che verifica set e get di un item."""
        # Arrange
        key = "test_key"
        value = {"data": "test"}

        # Act
        cache_manager.set(key, value)
        result = cache_manager.get(key)

        # Assert
        assert result == value

    def test_get_expired_item_returns_none(self, cache_manager):
        """Test che verifica che item scaduti ritornino None."""
        # Arrange
        key = "test_key"
        value = {"data": "test"}
        cache_manager.set(key, value)

        # Simula scadenza
        cache_manager._cache[key]["expires_at"] = datetime.now() - timedelta(hours=2)

        # Act & Assert
        assert cache_manager.get(key) is None

    @pytest.mark.parametrize("invalid_key", [None, "", 123, []])
    def test_set_with_invalid_key_raises_error(self, cache_manager, invalid_key):
        """Test che verifica validazione delle chiavi."""
        with pytest.raises(ValueError, match="Key deve essere una stringa"):
            cache_manager.set(invalid_key, "value")
```

### Running Tests

```bash
# Run tutti i test
pytest

# Run con coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run solo unit test
pytest tests/unit/

# Run test specifico
pytest tests/unit/test_cache_manager.py::TestCacheManager::test_set_and_get_item

# Run con output verboso
pytest -v

# Run test marcati come slow
pytest -m slow
```

## 📚 Documentazione

### Docstring Standards

```python
def analyze_population_data(
    dataset: pd.DataFrame,
    group_by: List[str],
    metrics: List[str] = ["popolazione_totale"],
    filters: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Analizza dati di popolazione aggregando per dimensioni specificate.

    Questa funzione prende un dataset di popolazione e calcola metriche
    aggregate basate sui raggruppamenti specificati. Supporta filtering
    opzionale dei dati prima dell'aggregazione.

    Args:
        dataset: DataFrame contenente dati popolazione con colonne standard ISTAT
        group_by: Lista di colonne per raggruppamento (es. ['territorio', 'anno'])
        metrics: Lista di metriche da calcolare. Default: ['popolazione_totale']
            Opzioni disponibili:
            - popolazione_totale: Somma della popolazione
            - densita_media: Media della densità abitativa
            - crescita_percentuale: Tasso di crescita YoY
        filters: Dizionario di filtri da applicare prima dell'analisi
            Esempio: {'anno': 2023, 'territorio': 'Roma'}

    Returns:
        DataFrame con dati aggregati contenente:
        - Colonne di raggruppamento
        - Una colonna per ogni metrica richiesta
        - Indice reset per facilitare ulteriori elaborazioni

    Raises:
        ValueError: Se group_by contiene colonne non esistenti
        ValueError: Se metrics contiene metriche non supportate
        DataError: Se il dataset è vuoto dopo i filtri

    Examples:
        >>> df = load_population_data()
        >>> result = analyze_population_data(
        ...     dataset=df,
        ...     group_by=['regione', 'anno'],
        ...     metrics=['popolazione_totale', 'densita_media']
        ... )
        >>> print(result.head())
        regione      anno  popolazione_totale  densita_media
        Abruzzo      2020       1305770            124.5
        Abruzzo      2021       1293941            123.2
        ...

    Note:
        - I dati devono seguire lo schema standard ISTAT
        - Le metriche di crescita richiedono almeno 2 anni di dati
        - I filtri sono applicati con AND logico

    See Also:
        - prepare_population_data: Per preparare i dati per l'analisi
        - export_analysis_results: Per esportare i risultati
    """
    # Implementazione...
```

### Documentazione Moduli

Ogni modulo significativo deve avere:

- `README.md` nella sua directory
- Docstring dettagliata all'inizio del file
- Esempi d'uso nella sezione Examples
- Diagrammi per flussi complessi (Mermaid)

## 📤 Submission Guidelines

### Prima di Creare una Pull Request

#### Aggiorna il tuo branch

```bash
git checkout main
git pull origin main
git checkout feature/tua-feature
git rebase main
```

#### Run test suite completa

```bash
pytest
flake8 src/
black --check src/
```

#### Aggiorna documentazione

- Docstring per nuovo codice
- README se cambi funzionalità
- CHANGELOG.md per cambiamenti utente-facing

### Pull Request Template

```markdown
## Descrizione
Breve descrizione di cosa fa questa PR.

## Tipo di Cambiamento
- [ ] Bug fix (non-breaking change che risolve un problema)
- [ ] Nuova feature (non-breaking change che aggiunge funzionalità)
- [ ] Breaking change (fix o feature che rompe funzionalità esistente)
- [ ] Documentazione

## Testing
- [ ] I test esistenti passano
- [ ] Ho aggiunto test per coprire i miei cambiamenti
- [ ] Coverage resta sopra il 70%

## Checklist
- [ ] Il mio codice segue lo style guide del progetto
- [ ] Ho fatto self-review del mio codice
- [ ] Ho commentato parti particolarmente complesse
- [ ] Ho aggiornato la documentazione
- [ ] I miei cambiamenti non generano nuovi warning

## Screenshots (se applicabile)
Se la PR include cambiamenti UI, includere screenshots.

## Note Aggiuntive
Informazioni extra per i reviewer.

Closes #(issue number)
```

### Review Process

- **Automated Checks**: CI/CD deve passare
- **Code Review**: Almeno 1 approval richiesta
- **Testing**: Reviewer può richiedere test aggiuntivi
- **Merge**: Maintainer effettua squash merge

### Dopo il Merge

La tua PR è stata accettata! 🎉

- Il tuo contributo sarà menzionato nel CHANGELOG
- Sarai aggiunto alla lista contributors
- Per contributi significativi, sarai menzionato nei CREDITS del componente

## 🏆 Riconoscimenti

### Come Riconosciamo i Contributi

- **Contributors File**: CONTRIBUTORS.md aggiornato mensilmente
- **Component Credits**: File CREDITS.md per componente
- **Release Notes**: Menzione nei changelog
- **Hall of Fame**: Top contributors annuali

### Livelli di Contribuzione

- 🌱 **First Timer**: Prima PR accettata
- 🌿 **Active Contributor**: 5+ PRs accettate
- 🌳 **Core Contributor**: Contributi regolari e significativi
- 🏔️ **Maintainer**: Responsabilità su componenti specifici

## 💬 Bisogno di Aiuto?

- **Discord**: [Link al server] (coming soon)
- **Discussions**: Usa GitHub Discussions per domande
- **Issue Templates**: Usa i template per bug/features
- **Email**: osservatorio-dev@example.com

---

**Grazie per contribuire a Osservatorio!** 🚀

Il tuo tempo e le tue competenze rendono questo progetto migliore per tutti. Se hai suggerimenti per migliorare questo processo, apri una issue - anche il processo di contribuzione è open source!

*Ultimo aggiornamento: 20 LUGLIO 2025*

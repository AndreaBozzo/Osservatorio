# 🗂️ Scripts Legacy

Questa cartella contiene script che sono stati utilizzati durante lo sviluppo iniziale del progetto ma che ora sono obsoleti o sostituiti da implementazioni migliori.

## 📋 Script Presenti

### `migrate_repository.py`
- **Scopo**: Migrazione dei file dalla vecchia struttura alla nuova architettura del progetto
- **Stato**: ❌ **OBSOLETO** - Migrazione completata
- **Motivo**: La migrazione della struttura del repository è stata completata con successo. Lo script non è più necessario per il funzionamento del sistema.
- **Ultima esecuzione**: Durante la fase di setup iniziale del progetto

### `validate_step1_2.py`
- **Scopo**: Validazione specifica per lo Step 1.2 del setup PowerBI
- **Stato**: ❌ **OBSOLETO** - Sostituito dai test automatici
- **Motivo**: Le funzionalità di validazione sono ora integrate nei test automatici e nel sistema di CI/CD. Il workflow di validazione manuale è stato sostituito da controlli automatici.
- **Sostituto**: Test suite automatici (`pytest tests/`) e script CI/CD unificato (`test_ci.py`)

### `test_ci_quick.py`
- **Scopo**: Test rapidi per CI/CD con lista specifica di test essenziali
- **Stato**: ❌ **OBSOLETO** - Consolidato nello script unificato
- **Motivo**: Funzionalità integrata nel nuovo script `test_ci.py` con strategia "quick"
- **Sostituto**: `python scripts/test_ci.py --strategy quick`

### `test_ci_minimal.py`
- **Scopo**: Test minimali ultra-robusti per CI/CD senza dipendenze pytest
- **Stato**: ❌ **OBSOLETO** - Consolidato nello script unificato
- **Motivo**: Funzionalità integrata nel nuovo script `test_ci.py` con strategia "minimal"
- **Sostituto**: `python scripts/test_ci.py --strategy minimal`

## 🔄 Criteri per lo Spostamento

Uno script viene spostato in `legacy/` quando:

1. **Obiettivo Raggiunto**: Lo script ha completato il suo scopo (es. migrazione)
2. **Funzionalità Sostituita**: Esistono implementazioni migliori o più moderne
3. **Non Utilizzato**: Non viene più referenziato in workflow, documentazione o codice
4. **Obsoleto**: La funzionalità non è più necessaria nell'architettura corrente

## 📚 Mantenimento

Questi script vengono mantenuti per:
- **Riferimento Storico**: Documentazione del processo di sviluppo
- **Debugging**: Potenziale utilizzo per debugging di problemi legacy
- **Apprendimento**: Esempi di implementazioni precedenti

## ⚠️ Attenzione

- **Non utilizzare** questi script in produzione
- **Non referenziare** questi script nella documentazione attiva
- **Non includere** questi script nei workflow CI/CD

---

*Ultima revisione: Gennaio 2025*

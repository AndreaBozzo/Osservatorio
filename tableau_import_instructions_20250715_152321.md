
# ISTRUZIONI TABLEAU - IMPORT DATI ISTAT
Generato il: 2025-07-15 15:23:21

## 📊 DATASET CONVERTITI (0 pronti)



## 🚀 PASSAGGI TABLEAU

### 1. CONNESSIONE DATI
```
1. Apri Tableau Desktop
2. Connetti a → File di testo (CSV) o Excel
3. Seleziona i file convertiti dalla directory corrente
4. Verifica anteprima dati e tipi colonne
```

### 2. PREPARAZIONE DATI
```
1. Unisci dataset correlati usando Dataset_ID
2. Crea gerarchie temporali da colonne Time
3. Imposta tipi dati corretti (Date/Time, Number, String)
4. Crea calcoli per KPI derivati
```

### 3. VISUALIZZAZIONI CONSIGLIATE

**POPOLAZIONE & DEMOGRAFIA:**
- Serie temporale indicatori demografici
- Mappa coropleta popolazione per regione
- Piramide età popolazione

**ECONOMIA:**
- Dashboard PIL e crescita economica
- Trend inflazione e prezzi
- Confronto regionale indicatori economici

**LAVORO:**
- Tasso disoccupazione nel tempo
- Heatmap disoccupazione per regione/età
- Correlazione PIL-Occupazione

### 4. REFRESH AUTOMATICO
```
1. Pubblica su Tableau Server/Online
2. Configura schedule refresh:
   - Popolazione: Mensile
   - Economia: Trimestrale
   - Lavoro: Mensile
3. Imposta avvisi per qualità dati
```

## 📋 CHECKLIST POST-IMPORT
- [ ] Verificare import corretto di tutti i dataset
- [ ] Controllare tipi dati e formati date
- [ ] Testare join tra dataset correlati
- [ ] Creare data source estratti per performance
- [ ] Impostare refresh schedules
- [ ] Configurare permessi e governance

## 🔧 RISOLUZIONE PROBLEMI
- Se errori import CSV: verificare encoding UTF-8
- Se date non riconosciute: usare colonne Time standardizzate
- Se valori numerici errati: controllare separatori decimali
- Per dataset grandi: preferire extracts a live connections

## 📞 SUPPORTO
Per problemi tecnici consultare la documentazione ISTAT SDMX:
https://www.istat.it/it/metodi-e-strumenti/web-service-sdmx

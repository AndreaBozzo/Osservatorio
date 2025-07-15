# ISTRUZIONI TABLEAU - IMPORT DATI ISTAT
Generato il: 2025-07-15 15:53:28
Directory output: tableau_output

## 📊 DATASET CONVERTITI (13 pronti)


### ECONOMIA

**Conto economico delle risorse e degli impieghi  e contributi alla crescita del Pil - edizioni ottobre 2014 - agosto 2019**
- File CSV: `economia_732_1051_20250715.csv`
- File Excel: `economia_732_1051_20250715.xlsx`
- Righe: 693,196
- Colonne: 7
- Colonne disponibili: Dataset_ID, Category, Obsdimension_Id, Obsdimension_Value, Obsvalue_Value...

**Conto economico delle risorse e degli impieghi  e contributi alla crescita del Pil**
- File CSV: `economia_163_156_20250715.csv`
- File Excel: `economia_163_156_20250715.xlsx`
- Righe: 76,692
- Colonne: 7
- Colonne disponibili: Dataset_ID, Category, Obsdimension_Id, Obsdimension_Value, Obsvalue_Value...

**Prezzi dei prodotti agricoli**
- File CSV: `economia_101_12_20250715.csv`
- File Excel: `economia_101_12_20250715.xlsx`
- Righe: 48,510
- Colonne: 7
- Colonne disponibili: Dataset_ID, Category, Obsdimension_Id, Obsdimension_Value, Obsvalue_Value...

### ISTRUZIONE

**Stato patrimoniale delle università, politecnici ed istituti di istruzione universitaria (euro)**
- File CSV: `istruzione_124_1156_20250715.csv`
- File Excel: `istruzione_124_1156_20250715.xlsx`
- Righe: 308
- Colonne: 7
- Colonne disponibili: Dataset_ID, Category, Obsdimension_Id, Obsdimension_Value, Obsvalue_Value...

**Conto economico delle università, politecnici ed istituti di istruzione universitaria (euro)**
- File CSV: `istruzione_124_1157_20250715.csv`
- File Excel: `istruzione_124_1157_20250715.xlsx`
- Righe: 280
- Colonne: 7
- Colonne disponibili: Dataset_ID, Category, Obsdimension_Id, Obsdimension_Value, Obsvalue_Value...

**Scuola dell'infanzia**
- File CSV: `istruzione_158_149_20250715.csv`
- File Excel: `istruzione_158_149_20250715.xlsx`
- Righe: 39,716
- Colonne: 7
- Colonne disponibili: Dataset_ID, Category, Obsdimension_Id, Obsdimension_Value, Obsvalue_Value...

### LAVORO

**Unemployment  rate - previous regulation (until 2020)**
- File CSV: `lavoro_151_1193_20250715.csv`
- File Excel: `lavoro_151_1193_20250715.xlsx`
- Righe: 426,542
- Colonne: 7
- Colonne disponibili: Dataset_ID, Category, Obsdimension_Id, Obsdimension_Value, Obsvalue_Value...

**Tasso di disoccupazione  - dati mensili - regolamento precedente (fino al 2020)**
- File CSV: `lavoro_151_1176_20250715.csv`
- File Excel: `lavoro_151_1176_20250715.xlsx`
- Righe: 327,088
- Colonne: 7
- Colonne disponibili: Dataset_ID, Category, Obsdimension_Id, Obsdimension_Value, Obsvalue_Value...

**Tasso di disoccupazione - dati trimestrali destagionalizzati  - regolamento precedente (fino al 2020)**
- File CSV: `lavoro_151_1178_20250715.csv`
- File Excel: `lavoro_151_1178_20250715.xlsx`
- Righe: 90,936
- Colonne: 7
- Colonne disponibili: Dataset_ID, Category, Obsdimension_Id, Obsdimension_Value, Obsvalue_Value...

### POPOLAZIONE

**Indicatori  demografici**
- File CSV: `popolazione_22_293_20250715.csv`
- File Excel: `popolazione_22_293_20250715.xlsx`
- Righe: 147,686
- Colonne: 7
- Colonne disponibili: Dataset_ID, Category, Obsdimension_Id, Obsdimension_Value, Obsvalue_Value...

### TERRITORIO

**Caratteristiche professionali e territoriali degli sposi**
- File CSV: `territorio_24_386_20250715.csv`
- File Excel: `territorio_24_386_20250715.xlsx`
- Righe: 451,782
- Colonne: 7
- Colonne disponibili: Dataset_ID, Category, Obsdimension_Id, Obsdimension_Value, Obsvalue_Value...

**Iscritti all'università - comune dell'ateneo**
- File CSV: `territorio_56_1045_20250715.csv`
- File Excel: `territorio_56_1045_20250715.xlsx`
- Righe: 14,346
- Colonne: 7
- Colonne disponibili: Dataset_ID, Category, Obsdimension_Id, Obsdimension_Value, Obsvalue_Value...

**Dottorati - mobilità territoriale**
- File CSV: `territorio_392_586_20250715.csv`
- File Excel: `territorio_392_586_20250715.xlsx`
- Righe: 976
- Colonne: 7
- Colonne disponibili: Dataset_ID, Category, Obsdimension_Id, Obsdimension_Value, Obsvalue_Value...


## 🚀 PASSAGGI TABLEAU DESKTOP

### 1. APERTURA FILE
1. Apri Tableau Desktop
2. Nella schermata iniziale, clicca su "Altro..." sotto "Connetti"
3. Seleziona "File di testo" per CSV o "Microsoft Excel" per XLSX
4. Naviga alla cartella `tableau_output`
5. Seleziona il file desiderato

### 2. CONFIGURAZIONE INIZIALE
1. **Verifica anteprima dati**: Tableau mostra i primi 1000 record
2. **Controlla tipi di dati**:
   - Time → Data
   - Value → Numero (decimale)
   - Territory, Category → Stringa
3. **Rinomina campi** se necessario (click destro → Rinomina)

### 3. CREAZIONE DATA SOURCE
1. Clicca su "Foglio 1" per iniziare l'analisi
2. Per unire più dataset:
   - Torna a "Origine dati"
   - Trascina secondo file nell'area di join
   - Configura join su Dataset_ID o Territory

### 4. VISUALIZZAZIONI CONSIGLIATE

#### SERIE TEMPORALE
1. Trascina `Time` su Colonne
2. Trascina `Value` su Righe
3. Click destro su Time → scegli livello (Anno, Trimestre, Mese)
4. Aggiungi `Territory` o `Category` su Colore

#### MAPPA GEOGRAFICA
1. Trascina `Territory` su Dettaglio
2. Tableau riconosce automaticamente "Italia" e regioni
3. Trascina `Value` su Colore
4. Cambia tipo marca in "Mappa"

#### DASHBOARD INTERATTIVA
1. Crea 3-4 fogli con visualizzazioni diverse
2. Nuovo Dashboard → trascina fogli
3. Aggiungi filtri:
   - Click destro su dimensione → Mostra filtro
   - Dashboard → Azioni → Aggiungi azione filtro

## 📈 BEST PRACTICES TABLEAU

### PERFORMANCE
- Per dataset grandi (>1M righe): Crea estratto
  - Dati → Nuovo estratto
  - Pianifica aggiornamenti automatici
- Usa filtri contestuali per limitare dati caricati
- Aggrega dati quando possibile

### FORMATTAZIONE
- Numeri grandi: Click destro → Formato → Numero → Personalizzato
  - Esempio: #,##0,.0K per mostrare migliaia
- Date: Formato → Data → Personalizzato
  - Esempio: MMM yyyy per "Gen 2024"

### CALCOLI UTILI
```
// Variazione percentuale anno su anno
(SUM([Value]) - LOOKUP(SUM([Value]), -4)) / ABS(LOOKUP(SUM([Value]), -4))

// Media mobile 4 periodi
WINDOW_AVG(SUM([Value]), -3, 0)

// Ranking per territorio
RANK(SUM([Value]))
```

## 🔄 AGGIORNAMENTO DATI

### MANUALE
1. Sostituisci file CSV/Excel nella cartella
2. In Tableau: Dati → Aggiorna origine dati

### AUTOMATICO (Tableau Server/Online)
1. Pubblica workbook su Server
2. Configura pianificazione:
   - Impostazioni → Pianifica aggiornamento
   - Scegli frequenza (giornaliera, settimanale, mensile)

## 🛠️ RISOLUZIONE PROBLEMI

**"Tipo di dati non riconosciuto"**
- Verifica formato date (YYYY-MM-DD)
- Controlla separatore decimale (punto vs virgola)

**"Territorio non riconosciuto sulla mappa"**
- Assegna ruolo geografico: Click destro → Ruolo geografico → Paese/Regione

**"Performance lenta"**
- Crea estratto invece di connessione live
- Limita dati con filtri su origine dati

## 📚 RISORSE UTILI
- [Tableau Public Gallery](https://public.tableau.com/gallery) - Esempi dashboard
- [Tableau Help](https://help.tableau.com) - Documentazione ufficiale
- [ISTAT.it](https://www.istat.it) - Fonte dati originale

---
File generato da IstatXMLtoTableauConverter v2.0

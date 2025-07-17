# 🌐 Landing Page - Osservatorio ISTAT

Landing page statica per il progetto Osservatorio ISTAT, deployata automaticamente su GitHub Pages.

## 🚀 Deployment

La landing page viene deployata automaticamente su GitHub Pages attraverso GitHub Actions quando viene pushato su `main`:

- **URL**: https://AndreaBozzo.github.io/Osservatorio/
- **Trigger**: Push su `main` con modifiche in `dashboard/web/`
- **Workflow**: `.github/workflows/deploy-landing-page.yml`

## 📁 Struttura File

```
dashboard/web/
├── index.html          # Landing page principale
└── README.md          # Questa documentazione
```

## 🎨 Caratteristiche

### Design
- **Framework CSS**: Tailwind CSS (via CDN)
- **Icone**: Font Awesome 6.0
- **Grafici**: Chart.js per visualizzazioni demo
- **Responsive**: Mobile-first design

### Sezioni
1. **Header**: Titolo principale con CTA
2. **Stats**: Metriche live del sistema
3. **Features**: Caratteristiche principali
4. **Categories**: Categorie dati disponibili
5. **Dashboard Preview**: Anteprima con grafico demo
6. **Technical Info**: Stack tecnologico e qualità
7. **Footer**: Link utili e contatti

### Funzionalità Interattive
- **Animazioni**: Contatori animati on-scroll
- **Grafico Demo**: Andamento popolazione Italia
- **Hover Effects**: Effetti card hover
- **Responsive**: Adattamento mobile/desktop

## 🔧 Sviluppo Locale

Per testare la landing page localmente:

```bash
# Apri il file direttamente nel browser
open dashboard/web/index.html

# Oppure usa un server locale
cd dashboard/web
python -m http.server 8000
# Visita: http://localhost:8000
```

## 🌐 SEO e Ottimizzazione

### File generati automaticamente:
- `sitemap.xml` - Sitemap per motori di ricerca
- `robots.txt` - Istruzioni per crawler
- `404.html` - Pagina di errore (copia dell'index)

### Meta Tags implementati:
- Title e description ottimizzati
- Viewport per mobile
- Charset UTF-8
- Favicon (emoji 🇮🇹)

## 📊 Metriche Live

La landing page mostra metriche aggiornate del sistema:

- **Dataset**: 509+ dataset ISTAT disponibili
- **Test Success**: 100% (173 test passati)
- **Categorie**: 6 categorie principali
- **Status**: Indicatore sistema online

## 🔗 Collegamenti

### CTA Principali:
- **Dashboard**: Link al dashboard Streamlit
- **GitHub**: Repository principale
- **Documentazione**: README e docs

### Link Footer:
- GitHub Repository
- Documentazione
- ISTAT Ufficiale
- API ISTAT SDMX

## 📱 Responsive Design

### Breakpoints:
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

### Adattamenti:
- Grid responsive (1-2-3 colonne)
- Menu hamburger mobile (futuro)
- Testi scalabili
- Immagini responsive

## 🎯 Obiettivi

1. **Visibilità**: Showcase del progetto
2. **Accesso**: Gateway al dashboard
3. **Credibilità**: Metriche e qualità
4. **Engagement**: CTA chiari e attraenti
5. **SEO**: Ottimizzazione motori ricerca

## 🔄 Aggiornamenti

### Automatici:
- Deploy su push main
- Validazione HTML
- Generazione sitemap
- Ottimizzazione asset

### Manuali:
- Aggiornamento metriche
- Nuove sezioni
- Miglioramenti UX
- Ottimizzazioni performance

## 📈 Prossimi Miglioramenti

1. **Analytics**: Google Analytics/Plausible
2. **Performance**: Ottimizzazione caricamento
3. **Interazioni**: Più animazioni e effetti
4. **Localizzazione**: Supporto multilingua
5. **PWA**: Progressive Web App features

## 🚀 Deployment Status

La landing page è deployata automaticamente e disponibile a:
**https://AndreaBozzo.github.io/Osservatorio/**

Status: 🟢 Online

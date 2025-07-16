# Script PowerShell per download dataset ISTAT
# Generato automaticamente - Versione corretta

$baseUrl = "http://sdmx.istat.it/SDMXWS/rest/data/"
$outputDir = "istat_data"

# Crea directory output
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir
    Write-Host "Directory creata: $outputDir" -ForegroundColor Green
}

Write-Host "ISTAT Data Download in corso..." -ForegroundColor Green
Write-Host "Downloading 13 priority datasets..." -ForegroundColor Yellow

# Dataset 1: Unemployment rate - previous regulation
Write-Host "Downloading: Unemployment rate - previous regulation" -ForegroundColor Yellow
$url1 = "$baseUrl" + "151_1193"
$output1 = "$outputDir\151_1193.xml"
try {
    Invoke-WebRequest -Uri $url1 -OutFile $output1 -TimeoutSec 120
    $fileSize = (Get-Item $output1).Length / 1MB
    Write-Host "Salvato: $output1 ($($fileSize.ToString('F2')) MB)" -ForegroundColor Green
} catch {
    Write-Host "Errore download 151_1193: $_" -ForegroundColor Red
}
Start-Sleep -Seconds 3

# Dataset 2: Conto economico PIL - edizioni 2014-2019
Write-Host "Downloading: Conto economico PIL - edizioni 2014-2019" -ForegroundColor Yellow
$url2 = "$baseUrl" + "732_1051"
$output2 = "$outputDir\732_1051.xml"
try {
    Invoke-WebRequest -Uri $url2 -OutFile $output2 -TimeoutSec 120
    $fileSize = (Get-Item $output2).Length / 1MB
    Write-Host "Salvato: $output2 ($($fileSize.ToString('F2')) MB)" -ForegroundColor Green
} catch {
    Write-Host "Errore download 732_1051: $_" -ForegroundColor Red
}
Start-Sleep -Seconds 3

# Dataset 3: Indicatori demografici
Write-Host "Downloading: Indicatori demografici" -ForegroundColor Yellow
$url3 = "$baseUrl" + "22_293"
$output3 = "$outputDir\22_293.xml"
try {
    Invoke-WebRequest -Uri $url3 -OutFile $output3 -TimeoutSec 120
    $fileSize = (Get-Item $output3).Length / 1MB
    Write-Host "Salvato: $output3 ($($fileSize.ToString('F2')) MB)" -ForegroundColor Green
} catch {
    Write-Host "Errore download 22_293: $_" -ForegroundColor Red
}
Start-Sleep -Seconds 3

# Dataset 4: Conto economico PIL corrente
Write-Host "Downloading: Conto economico PIL corrente" -ForegroundColor Yellow
$url4 = "$baseUrl" + "163_156"
$output4 = "$outputDir\163_156.xml"
try {
    Invoke-WebRequest -Uri $url4 -OutFile $output4 -TimeoutSec 120
    $fileSize = (Get-Item $output4).Length / 1MB
    Write-Host "Salvato: $output4 ($($fileSize.ToString('F2')) MB)" -ForegroundColor Green
} catch {
    Write-Host "Errore download 163_156: $_" -ForegroundColor Red
}
Start-Sleep -Seconds 3

# Dataset 5: Tasso disoccupazione mensile
Write-Host "Downloading: Tasso disoccupazione mensile" -ForegroundColor Yellow
$url5 = "$baseUrl" + "151_1176"
$output5 = "$outputDir\151_1176.xml"
try {
    Invoke-WebRequest -Uri $url5 -OutFile $output5 -TimeoutSec 120
    $fileSize = (Get-Item $output5).Length / 1MB
    Write-Host "Salvato: $output5 ($($fileSize.ToString('F2')) MB)" -ForegroundColor Green
} catch {
    Write-Host "Errore download 151_1176: $_" -ForegroundColor Red
}
Start-Sleep -Seconds 3

# Dataset 6: Tasso disoccupazione trimestrale
Write-Host "Downloading: Tasso disoccupazione trimestrale" -ForegroundColor Yellow
$url6 = "$baseUrl" + "151_1178"
$output6 = "$outputDir\151_1178.xml"
try {
    Invoke-WebRequest -Uri $url6 -OutFile $output6 -TimeoutSec 120
    $fileSize = (Get-Item $output6).Length / 1MB
    Write-Host "Salvato: $output6 ($($fileSize.ToString('F2')) MB)" -ForegroundColor Green
} catch {
    Write-Host "Errore download 151_1178: $_" -ForegroundColor Red
}
Start-Sleep -Seconds 3

# Dataset 7: Stato patrimoniale universita
Write-Host "Downloading: Stato patrimoniale universita" -ForegroundColor Yellow
$url7 = "$baseUrl" + "124_1156"
$output7 = "$outputDir\124_1156.xml"
try {
    Invoke-WebRequest -Uri $url7 -OutFile $output7 -TimeoutSec 120
    $fileSize = (Get-Item $output7).Length / 1MB
    Write-Host "Salvato: $output7 ($($fileSize.ToString('F2')) MB)" -ForegroundColor Green
} catch {
    Write-Host "Errore download 124_1156: $_" -ForegroundColor Red
}
Start-Sleep -Seconds 3

# Dataset 8: Conto economico universita
Write-Host "Downloading: Conto economico universita" -ForegroundColor Yellow
$url8 = "$baseUrl" + "124_1157"
$output8 = "$outputDir\124_1157.xml"
try {
    Invoke-WebRequest -Uri $url8 -OutFile $output8 -TimeoutSec 120
    $fileSize = (Get-Item $output8).Length / 1MB
    Write-Host "Salvato: $output8 ($($fileSize.ToString('F2')) MB)" -ForegroundColor Green
} catch {
    Write-Host "Errore download 124_1157: $_" -ForegroundColor Red
}
Start-Sleep -Seconds 3

# Dataset 9: Caratteristiche sposi
Write-Host "Downloading: Caratteristiche professionali sposi" -ForegroundColor Yellow
$url9 = "$baseUrl" + "24_386"
$output9 = "$outputDir\24_386.xml"
try {
    Invoke-WebRequest -Uri $url9 -OutFile $output9 -TimeoutSec 120
    $fileSize = (Get-Item $output9).Length / 1MB
    Write-Host "Salvato: $output9 ($($fileSize.ToString('F2')) MB)" -ForegroundColor Green
} catch {
    Write-Host "Errore download 24_386: $_" -ForegroundColor Red
}
Start-Sleep -Seconds 3

# Dataset 10: Prezzi prodotti agricoli
Write-Host "Downloading: Prezzi prodotti agricoli" -ForegroundColor Yellow
$url10 = "$baseUrl" + "101_12"
$output10 = "$outputDir\101_12.xml"
try {
    Invoke-WebRequest -Uri $url10 -OutFile $output10 -TimeoutSec 120
    $fileSize = (Get-Item $output10).Length / 1MB
    Write-Host "Salvato: $output10 ($($fileSize.ToString('F2')) MB)" -ForegroundColor Green
} catch {
    Write-Host "Errore download 101_12: $_" -ForegroundColor Red
}
Start-Sleep -Seconds 3

# Dataset 11: Iscritti universita per comune
Write-Host "Downloading: Iscritti universita per comune" -ForegroundColor Yellow
$url11 = "$baseUrl" + "56_1045"
$output11 = "$outputDir\56_1045.xml"
try {
    Invoke-WebRequest -Uri $url11 -OutFile $output11 -TimeoutSec 120
    $fileSize = (Get-Item $output11).Length / 1MB
    Write-Host "Salvato: $output11 ($($fileSize.ToString('F2')) MB)" -ForegroundColor Green
} catch {
    Write-Host "Errore download 56_1045: $_" -ForegroundColor Red
}
Start-Sleep -Seconds 3

# Dataset 12: Dottorati mobilita territoriale
Write-Host "Downloading: Dottorati mobilita territoriale" -ForegroundColor Yellow
$url12 = "$baseUrl" + "392_586"
$output12 = "$outputDir\392_586.xml"
try {
    Invoke-WebRequest -Uri $url12 -OutFile $output12 -TimeoutSec 120
    $fileSize = (Get-Item $output12).Length / 1MB
    Write-Host "Salvato: $output12 ($($fileSize.ToString('F2')) MB)" -ForegroundColor Green
} catch {
    Write-Host "Errore download 392_586: $_" -ForegroundColor Red
}
Start-Sleep -Seconds 3

# Dataset 13: Scuola dell'infanzia
Write-Host "Downloading: Scuola dell'infanzia" -ForegroundColor Yellow
$url13 = "$baseUrl" + "158_149"
$output13 = "$outputDir\158_149.xml"
try {
    Invoke-WebRequest -Uri $url13 -OutFile $output13 -TimeoutSec 120
    $fileSize = (Get-Item $output13).Length / 1MB
    Write-Host "Salvato: $output13 ($($fileSize.ToString('F2')) MB)" -ForegroundColor Green
} catch {
    Write-Host "Errore download 158_149: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Download completato!" -ForegroundColor Green
Write-Host "File salvati in: $outputDir" -ForegroundColor Cyan

# Mostra summary
Write-Host ""
Write-Host "SUMMARY DOWNLOAD:" -ForegroundColor Yellow
$files = Get-ChildItem -Path $outputDir -Filter "*.xml"
$totalSize = ($files | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "File scaricati: $($files.Count)" -ForegroundColor White
Write-Host "Dimensione totale: $($totalSize.ToString('F2')) MB" -ForegroundColor White

Write-Host ""
Write-Host "PROSSIMO PASSO:" -ForegroundColor Yellow
Write-Host "Esegui: python istat_xml_to_tableau.py" -ForegroundColor White
Write-Host "per convertire i file XML in formato Tableau" -ForegroundColor White

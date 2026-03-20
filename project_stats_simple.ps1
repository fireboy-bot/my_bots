# project_stats_simple.ps1
# Простой анализатор проекта без сложных символов

param(
    [string]$RootPath = ".",
    [string]$Filter = "*.py"
)

Write-Host "========================================"
Write-Host "  PROJECT STATS (Simple Version)"
Write-Host "========================================"
Write-Host "Path: $RootPath"
Write-Host "Filter: $Filter"
Write-Host ""

# Считаем файлы
$files = Get-ChildItem -Path $RootPath -Filter $Filter -Recurse -File | 
    Where-Object { $_.DirectoryName -notmatch "venv|__pycache__|.git|node_modules" }

$totalFiles = $files.Count
$totalLines = 0
$totalSize = 0

# Словарь для статистики по папкам
$folderStats = @{}

foreach ($file in $files) {
    # Считаем строки
    $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
    if ($content) {
        $lines = ($content -split "`r?`n").Count
        $totalLines += $lines
        
        # Размер файла
        $size = $file.Length
        $totalSize += $size
        
        # Статистика по папкам
        $folder = $file.DirectoryName
        if ($folderStats.ContainsKey($folder)) {
            $folderStats[$folder].Lines += $lines
            $folderStats[$folder].Files++
        } else {
            $folderStats[$folder] = @{ Lines = $lines; Files = 1 }
        }
    }
}

# Считаем папки
$folders = Get-ChildItem -Path $RootPath -Directory -Recurse | 
    Where-Object { $_.FullName -notmatch "venv|__pycache__|.git|node_modules" }
$totalFolders = $folders.Count

# === ВЫВОД СТАТИСТИКИ ===

Write-Host "RESULTS:"
Write-Host "--------"
Write-Host "Files:     $totalFiles"
Write-Host "Folders:   $totalFolders"
Write-Host "Lines:     $totalLines"
Write-Host "Size:      $([math]::Round($totalSize / 1MB, 2)) MB"
Write-Host ""

# Топ-5 папок по количеству кода
Write-Host "TOP 5 FOLDERS by lines:"
Write-Host "-----------------------"
$folderStats.GetEnumerator() | 
    Sort-Object Value.Lines -Descending | 
    Select-Object -First 5 | 
    ForEach-Object {
        $path = $_.Key -replace [regex]::Escape($RootPath), "."
        Write-Host "  $path : $($_.Value.Lines) lines ($($_.Value.Files) files)"
    }
Write-Host ""

# Топ-10 файлов
Write-Host "TOP 10 FILES by lines:"
Write-Host "----------------------"
$fileList = foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
    if ($content) {
        $lines = ($content -split "`r?`n").Count
        [PSCustomObject]@{
            File = $file.FullName -replace [regex]::Escape($RootPath), "."
            Lines = $lines
        }
    }
}
$fileList | Sort-Object Lines -Descending | Select-Object -First 10 | 
    Format-Table -AutoSize

# Итоговая оценка
Write-Host ""
Write-Host "PROJECT SIZE:"
Write-Host "-------------"
if ($totalLines -lt 1000) {
    Write-Host "  [SMALL] < 1000 lines" -ForegroundColor Green
} elseif ($totalLines -lt 5000) {
    Write-Host "  [MEDIUM] 1000-5000 lines" -ForegroundColor Yellow
} elseif ($totalLines -lt 20000) {
    Write-Host "  [LARGE] 5000-20000 lines" -ForegroundColor DarkYellow
} else {
    Write-Host "  [HUGE] 20000+ lines" -ForegroundColor Red
}
Write-Host ""
Write-Host "Done!"
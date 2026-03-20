<#
.SYNOPSIS
    Профессиональный анализатор проекта
.DESCRIPTION
    Считает строки, файлы, папки, комментарии, TODO, сложность и экспортирует отчёт
.AUTHOR
    Для юриста-программиста 🥕
#>

param(
    [string]$RootPath = ".",
    [string[]]$IncludeFilters = @("*.py", "*.html", "*.css", "*.js", "*.json", "*.md", "*.sql", "*.sh", "*.bat"),
    [string[]]$ExcludeFolders = @(".git", "__pycache__", "venv", "node_modules", ".venv", "idea", ".vscode", "build", "dist"),
    [switch]$ExportJSON,
    [switch]$ExportCSV,
    [string]$PreviousReport = ""
)

# ============================================================================
# НАСТРОЙКИ И ЦВЕТА
# ============================================================================

$colors = @{
    Tree = "Cyan"
    Folder = "DarkYellow"
    File = "White"
    Stat = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Blue"
    Success = "DarkGreen"
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# ============================================================================
# ФУНКЦИИ
# ============================================================================

function Show-Tree {
    param(
        [string]$Path,
        [string]$Indent = "",
        [bool]$IsLast = $true,
        [int]$Depth = 0
    )
    
    $folder = Get-Item $Path
    $prefix = if ($IsLast) { "└── " } else { "├── " }
    $color = if ($folder.PSIsContainer) { $colors.Folder } else { $colors.File }
    
    # Не показываем корень дважды
    if ($Depth -gt 0) {
        Write-Host "$Indent$prefix$($folder.Name)" -ForegroundColor $color
    }
    
    if ($folder.PSIsContainer -and $Depth -lt 3) { # Ограничим глубину дерева
        $newIndent = $Indent + $(if ($IsLast) { "    " } else { "│   " })
        $items = Get-ChildItem $Path -Force | Where-Object {
            $_.Name -notin $ExcludeFolders -and -not $_.Name.StartsWith(".")
        } | Sort-Object -Property @{Expression = {$_.PSIsContainer -eq $false}}, Name
        
        $count = $items.Count
        for ($i = 0; $i -lt $count; $i++) {
            Show-Tree -Path $items[$i].FullName -Indent $newIndent -IsLast ($i -eq $count - 1) -Depth ($Depth + 1)
        }
        
        # Если есть ещё файлы, покажем многоточие
        $allItems = Get-ChildItem $Path -Force | Where-Object {
            $_.Name -notin $ExcludeFolders -and -not $_.Name.StartsWith(".")
        }
        if ($allItems.Count -gt 10) {
            Write-Host "$newIndent    ... (+$($allItems.Count - 10) ещё)" -ForegroundColor $colors.Info
        }
    }
}

function Get-LineCount {
    param([string]$FilePath)
    try {
        $content = Get-Content $FilePath -Raw -ErrorAction SilentlyContinue
        if ($content) {
            $lines = $content -split "`r?`n"
            return @{
                Total = $lines.Count
                Empty = ($lines | Where-Object { $_.Trim() -eq "" }).Count
                Comments = ($lines | Where-Object { $_.TrimStart() -startswith "#" -or $_.TrimStart() -startswith "//" -or $_.TrimStart() -startswith "/*" }).Count
                Code = 0 # Посчитаем ниже
            }
        }
    } catch {
        return @{ Total = 0; Empty = 0; Comments = 0; Code = 0 }
    }
    return @{ Total = 0; Empty = 0; Comments = 0; Code = 0 }
}

function Get-TODOCount {
    param([string]$FilePath)
    try {
        $content = Get-Content $FilePath -Raw -ErrorAction SilentlyContinue
        if ($content) {
            $todos = ($content | Select-String -Pattern "TODO|FIXME|HACK|XXX|BUG" -CaseSensitive:$false).Count
            return $todos
        }
    } catch {
        return 0
    }
    return 0
}

function Get-PythonStats {
    param([string]$FilePath)
    try {
        $content = Get-Content $FilePath -Raw -ErrorAction SilentlyContinue
        if ($content) {
            $functions = ([regex]::Matches($content, "def\s+\w+")).Count
            $classes = ([regex]::Matches($content, "class\s+\w+")).Count
            $docstrings = ([regex]::Matches($content, '"""[\s\S]*?"""')).Count
            return @{ Functions = $functions; Classes = $classes; Docstrings = $docstrings }
        }
    } catch {
        return @{ Functions = 0; Classes = 0; Docstrings = 0 }
    }
    return @{ Functions = 0; Classes = 0; Docstrings = 0 }
}

# ============================================================================
# ОСНОВНАЯ ЛОГИКА
# ============================================================================

Write-Host "`n" + "="*80 -ForegroundColor $colors.Stat
Write-Host "🔍 ПРОФЕССИОНАЛЬНЫЙ АНАЛИЗАТОР ПРОЕКТА" -ForegroundColor $colors.Stat
Write-Host "="*80 -ForegroundColor $colors.Stat
Write-Host "Время:           $timestamp"
Write-Host "Корневая папка:  $(Resolve-Path $RootPath)"
Write-Host "Фильтры:         $($IncludeFilters -join ', ')"
Write-Host "Исключаем:       $($ExcludeFolders -join ', ')"
Write-Host "="*80 -ForegroundColor $colors.Stat

# --- 1. ДЕРЕВО ПРОЕКТА ---
Write-Host "`n🌳 СТРУКТУРА ПРОЕКТА (макс. 3 уровня):" -ForegroundColor $colors.Tree
$rootName = Split-Path $RootPath -Leaf
Write-Host "$rootName" -ForegroundColor $colors.Folder
Show-Tree -Path $RootPath -Depth 0

# --- 2. СБОР ДАННЫХ ---
Write-Host "`n⏳ Анализируем файлы..." -ForegroundColor $colors.Info

$allFiles = Get-ChildItem -Path $RootPath -Recurse -File | Where-Object {
    $_.DirectoryName -notmatch ($ExcludeFolders -join '|') -and
    $_.Name -notin $ExcludeFolders -and
    -not $_.Name.StartsWith(".")
}

$filteredFiles = $allFiles | Where-Object {
    $match = $false
    foreach ($filter in $IncludeFilters) {
        if ($_.Name -like $filter) {
            $match = $true
            break
        }
    }
    $match
}

$totalFolders = (Get-ChildItem -Path $RootPath -Recurse -Directory | Where-Object {
    $_.FullName -notmatch ($ExcludeFolders -join '|')
}).Count

$totalFiles = $filteredFiles.Count
$fileStats = @()
$languageStats = @{}
$totalTODO = 0
$totalFunctions = 0
$totalClasses = 0
$totalDocstrings = 0

foreach ($file in $filteredFiles) {
    $lines = Get-LineCount -FilePath $file.FullName
    $todos = Get-TODOCount -FilePath $file.FullName
    $ext = $file.Extension.ToLower()
    
    # Python-специфичная статистика
    $pyStats = @{ Functions = 0; Classes = 0; Docstrings = 0 }
    if ($ext -eq ".py") {
        $pyStats = Get-PythonStats -FilePath $file.FullName
        $totalFunctions += $pyStats.Functions
        $totalClasses += $pyStats.Classes
        $totalDocstrings += $pyStats.Docstrings
    }
    
    $totalTODO += $todos
    $lines.Code = $lines.Total - $lines.Empty - $lines.Comments
    
    $fileStats += [PSCustomObject]@{
        File = $file.FullName
        RelativePath = $file.FullName -replace [regex]::Escape($RootPath), "."
        Extension = $ext
        TotalLines = $lines.Total
        CodeLines = $lines.Code
        CommentLines = $lines.Comments
        EmptyLines = $lines.Empty
        TODOs = $todos
        Functions = $pyStats.Functions
        Classes = $pyStats.Classes
        Docstrings = $pyStats.Docstrings
        SizeKB = [math]::Round($file.Length / 1KB, 2)
        LastModified = $file.LastWriteTime
    }
    
    # Статистика по языкам
    if ($languageStats.ContainsKey($ext)) {
        $languageStats[$ext].Files++
        $languageStats[$ext].Lines += $lines.Total
        $languageStats[$ext].Code += $lines.Code
    } else {
        $languageStats[$ext] = @{ Files = 1; Lines = $lines.Total; Code = $lines.Code }
    }
}

# --- 3. СТАТИСТИКА ПО ЯЗЫКАМ ---
Write-Host "`n📊 РАСПРЕДЕЛЕНИЕ ПО ЯЗЫКАМ:" -ForegroundColor $colors.Stat
$languageStats.GetEnumerator() | Sort-Object Value.Lines -Descending | ForEach-Object {
    $ext = $_.Key
    $data = $_.Value
    $percent = [math]::Round($data.Lines / ($fileStats | Measure-Object -Sum TotalLines).Sum * 100, 1)
    Write-Host "  $ext : $($data.Files) файлов, $($data.Lines) строк ($percent%)" -ForegroundColor $colors.Info
}

# --- 4. ТОП-10 ФАЙЛОВ ---
Write-Host "`n📄 ТОП-10 САМЫХ БОЛЬШИХ ФАЙЛОВ:" -ForegroundColor $colors.Warning
$fileStats | Sort-Object TotalLines -Descending | Select-Object -First 10 | 
    Format-Table -Property @{Label="Файл";Expression={$_.RelativePath}}, 
                           @{Label="Строк";Expression={$_.TotalLines}}, 
                           @{Label="Код";Expression={$_.CodeLines}}, 
                           @{Label="TODO";Expression={$_.TODOs}} -AutoSize

# --- 5. ФАЙЛЫ С TODO ---
$filesWithTODO = $fileStats | Where-Object { $_.TODOs -gt 0 }
if ($filesWithTODO.Count -gt 0) {
    Write-Host "`n⚠️  ФАЙЛЫ С TODO/FIXME:" -ForegroundColor $colors.Warning
    $filesWithTODO | Sort-Object TODOs -Descending | ForEach-Object {
        Write-Host "  $($_.RelativePath) — $($_.TODOs) задач" -ForegroundColor $colors.Warning
    }
}

# --- 6. PYTHON-СТАТИСТИКА ---
if ($totalFunctions -gt 0 -or $totalClasses -gt 0) {
    Write-Host "`n🐍 PYTHON-СТАТИСТИКА:" -ForegroundColor $colors.Info
    Write-Host "  Функций:     $totalFunctions" -ForegroundColor $colors.Info
    Write-Host "  Классов:     $totalClasses" -ForegroundColor $colors.Info
    Write-Host "  Docstrings:  $totalDocstrings" -ForegroundColor $colors.Info
    if ($totalFunctions -gt 0) {
        $docPercent = [math]::Round($totalDocstrings / $totalFunctions * 100, 1)
        Write-Host "  Документация: $docPercent% функций" -ForegroundColor $(if ($docPercent -gt 50) { $colors.Success } else { $colors.Warning })
    }
}

# --- 7. СРАВНЕНИЕ С ПРОШЛЫМ ОТЧЁТОМ ---
if ($PreviousReport -and (Test-Path $PreviousReport)) {
    Write-Host "`n📈 СРАВНЕНИЕ С ПРОШЛЫМ ЗАПУСКОМ:" -ForegroundColor $colors.Stat
    $prevData = Get-Content $PreviousReport -Raw | ConvertFrom-Json
    $linesDelta = ($fileStats | Measure-Object -Sum TotalLines).Sum - $prevData.totalLines
    $filesDelta = $totalFiles - $prevData.totalFiles
    $foldersDelta = $totalFolders - $prevData.totalFolders
    
    $linesColor = if ($linesDelta -gt 0) { $colors.Warning } elseif ($linesDelta -lt 0) { $colors.Info } else { $colors.Success }
    Write-Host "  Строки:  $($linesDelta -ge 0 ? '+' : '')$linesDelta" -ForegroundColor $linesColor
    Write-Host "  Файлы:   $($filesDelta -ge 0 ? '+' : '')$filesDelta" -ForegroundColor $linesColor
    Write-Host "  Папки:   $($foldersDelta -ge 0 ? '+' : '')$foldersDelta" -ForegroundColor $linesColor
}

# --- 8. ИТОГОВАЯ СВОДКА ---
$totalLines = ($fileStats | Measure-Object -Sum TotalLines).Sum
$totalCode = ($fileStats | Measure-Object -Sum CodeLines).Sum
$totalComments = ($fileStats | Measure-Object -Sum CommentLines).Sum
$totalEmpty = ($fileStats | Measure-Object -Sum EmptyLines).Sum

Write-Host "`n" + "="*80 -ForegroundColor $colors.Stat
Write-Host "📈 ИТОГОВАЯ СВОДКА" -ForegroundColor $colors.Stat
Write-Host "="*80 -ForegroundColor $colors.Stat
Write-Host "Папок:           $totalFolders" -ForegroundColor $colors.Stat
Write-Host "Файлов:          $totalFiles" -ForegroundColor $colors.Stat
Write-Host "Строк всего:     $totalLines" -ForegroundColor $colors.Stat
Write-Host "  ├─ Код:        $totalCode ($([math]::Round($totalCode/$totalLines*100, 1))%)" -ForegroundColor $colors.Success
Write-Host "  ├─ Комментарии: $totalComments ($([math]::Round($totalComments/$totalLines*100, 1))%)" -ForegroundColor $colors.Info
Write-Host "  └─ Пустые:     $totalEmpty ($([math]::Round($totalEmpty/$totalLines*100, 1))%)" -ForegroundColor $colors.Warning
Write-Host "TODO/FIXME:      $totalTODO" -ForegroundColor $(if ($totalTODO -gt 5) { $colors.Warning } else { $colors.Success })
Write-Host "Средний размер:  $([math]::Round($totalLines / ($totalFiles + 1), 1)) строк/файл" -ForegroundColor $colors.Stat

# Оценка проекта
if ($totalLines -lt 500) { $size = "🟢 Небольшой (до 500)" }
elseif ($totalLines -lt 2000) { $size = "🟡 Средний (500-2000)" }
elseif ($totalLines -lt 10000) { $size = "🟠 Крупный (2000-10000)" }
else { $size = "🔴 Очень крупный (10000+)" }
Write-Host "Статус:          $size" -ForegroundColor $colors.Stat
Write-Host "="*80 -ForegroundColor $colors.Stat

# --- 9. РЕКОМЕНДАЦИИ ---
Write-Host "`n💡 РЕКОМЕНДАЦИИ:" -ForegroundColor $colors.Warning
$largeFiles = $fileStats | Where-Object { $_.TotalLines -gt 500 }
if ($largeFiles.Count -gt 0) {
    Write-Host "⚠️  $($largeFiles.Count) файлов >500 строк — подумай о рефакторинге" -ForegroundColor $colors.Warning
}
if ($totalLines / ($totalFolders + 1) -gt 500) {
    Write-Host "⚠️  Много кода в папках — добавь модулей" -ForegroundColor $colors.Warning
}
if ($totalFunctions -gt 0 -and $totalDocstrings / $totalFunctions -lt 0.5) {
    Write-Host "⚠️  Мало docstrings — документируй функции" -ForegroundColor $colors.Warning
}
if ($totalTODO -gt 10) {
    Write-Host "⚠️  Много TODO — разберись с техдолгом" -ForegroundColor $colors.Warning
}
Write-Host "✅  Продолжай в том же духе!" -ForegroundColor $colors.Success

# --- 10. ЭКСПОРТ ---
if ($ExportJSON -or $ExportCSV) {
    $reportData = [PSCustomObject]@{
        timestamp = $timestamp
        totalFolders = $totalFolders
        totalFiles = $totalFiles
        totalLines = $totalLines
        totalCode = $totalCode
        totalComments = $totalComments
        totalEmpty = $totalEmpty
        totalTODO = $totalTODO
        totalFunctions = $totalFunctions
        totalClasses = $totalClasses
        languageStats = $languageStats
        files = $fileStats
    }
    
    if ($ExportJSON) {
        $jsonPath = "report_$(Get-Date -Format 'yyyy-MM-dd').json"
        $reportData | ConvertTo-Json -Depth 10 | Out-File -FilePath $jsonPath -Encoding UTF8
        Write-Host "`n💾 Отчёт сохранён: $jsonPath" -ForegroundColor $colors.Success
    }
    
    if ($ExportCSV) {
        $csvPath = "report_$(Get-Date -Format 'yyyy-MM-dd').csv"
        $fileStats | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8
        Write-Host "💾 Отчёт сохранён: $csvPath" -ForegroundColor $colors.Success
    }
}

Write-Host ""
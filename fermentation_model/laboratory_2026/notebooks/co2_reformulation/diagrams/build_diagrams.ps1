param([ValidateRange(72,600)][int]$Dpi = 200)

# Sólo composición y renderizado: no ejecuta ni modifica el modelo científico.
# Dependencias existentes: TeX Live (pdflatex) y Poppler.
$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    $requiredTools = @('pdflatex', 'pdfseparate', 'pdftoppm', 'pdftocairo')
    foreach ($toolName in $requiredTools) {
        if (-not (Get-Command $toolName -ErrorAction SilentlyContinue)) {
            throw "No está disponible la herramienta requerida: $toolName"
        }
    }
    1..2 | ForEach-Object {
        & pdflatex -interaction=nonstopmode -halt-on-error diagramas_modelos.tex | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Falló la compilación de diagramas_modelos.tex' }
    }
    if (Select-String -LiteralPath diagramas_modelos.log -Pattern 'Overfull \\[hv]box' -Quiet) {
        throw 'LaTeX informa un desbordamiento; revisar diagramas_modelos.log'
    }
    $exports = @(@{ Page = 1; Name = 'modelo_actual' },
                 @{ Page = 2; Name = 'modelo_zenteno' })
    foreach ($export in $exports) {
        $pageNumber = $export.Page
        $outputName = $export.Name
        & pdfseparate -f $pageNumber -l $pageNumber diagramas_modelos.pdf "$outputName.pdf"
        if ($LASTEXITCODE -ne 0) { throw "Falló la separación PDF de $outputName" }
        & pdftoppm -singlefile -r $Dpi -png "$outputName.pdf" $outputName
        if ($LASTEXITCODE -ne 0) { throw "Falló el renderizado PNG de $outputName" }
        & pdftocairo -svg "$outputName.pdf" "$outputName.svg"
        if ($LASTEXITCODE -ne 0) { throw "Falló la exportación SVG de $outputName" }
    }
    foreach ($auxiliaryName in @('diagramas_modelos.aux', 'diagramas_modelos.out', 'diagramas_modelos.log')) {
        if (Test-Path -LiteralPath $auxiliaryName) { Remove-Item -LiteralPath $auxiliaryName }
    }
    Write-Output 'Verificados: PDF conjunto (2 páginas), dos PDF individuales, dos PNG y dos SVG.'
} finally {
    Pop-Location
}

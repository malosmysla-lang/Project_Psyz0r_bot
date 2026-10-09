$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$locator = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$installation = & $locator -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $installation) { throw 'MSVC installation not found.' }
$cmakeExe = Join-Path $installation 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
$ctestExe = Join-Path (Split-Path $cmakeExe) 'ctest.exe'
if (-not (Test-Path -LiteralPath $cmakeExe)) { throw 'Visual Studio CMake component missing.' }
Push-Location $projectRoot
try {
    & $cmakeExe --preset msvc-x64
    if ($LASTEXITCODE) { throw 'Configure failed' }
    & $cmakeExe --build --preset msvc-x64
    if ($LASTEXITCODE) { throw 'Build failed' }
    & $ctestExe --preset msvc-x64
    if ($LASTEXITCODE) { throw 'Tests failed' }
} finally { Pop-Location }

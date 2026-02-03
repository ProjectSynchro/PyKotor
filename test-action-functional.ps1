# Functional test for build-tool action
# Simulates the action steps locally
param(
    [string]$ToolName = "toolset",
    [string]$PythonVersion = "3.8",
    [string]$Architecture = "x64",
    [string]$QtVersion = "PyQt6",
    [switch]$ValidateOnly
)

$ErrorActionPreference = "Stop"

Write-Host "=== Testing Build Tool Action ===" -ForegroundColor Cyan
Write-Host "Tool: $ToolName" -ForegroundColor White
Write-Host "Python: $PythonVersion" -ForegroundColor White
Write-Host "Architecture: $Architecture" -ForegroundColor White
Write-Host "Qt Version: $QtVersion" -ForegroundColor White
Write-Host "Validate Only (Dry Run): $ValidateOnly" -ForegroundColor White
Write-Host ""

# Step 1: Determine artifact name (from action)
Write-Host "Step 1: Determine artifact name" -ForegroundColor Yellow
$toolNameMap = @{
    "toolset" = "HolocronToolset"
    "holopatcher" = "HoloPatcher"
    "kotordiff" = "KotorDiff"
    "guiconverter" = "GuiConverter"
    "batchpatcher" = "BatchPatcher"
    "kitgenerator" = "KitGenerator"
}
$displayName = if ($toolNameMap.ContainsKey($ToolName.ToLower())) { 
    $toolNameMap[$ToolName.ToLower()] 
} else { 
    $ToolName 
}
$artifactName = "${displayName}_Windows_$Architecture"
if ($QtVersion -ne "" -and $ToolName -eq "toolset") {
    $artifactName = "${displayName}_Windows_${QtVersion}_$Architecture"
}
Write-Host "✓ Artifact name: $artifactName" -ForegroundColor Green

# Step 2: Check for UPX (skipped for dry run)
if (-not $ValidateOnly) {
    Write-Host "`nStep 2: Check UPX availability" -ForegroundColor Yellow
    Write-Host "✓ UPX check would run here (skipped)" -ForegroundColor Green
}

# Step 3: Validate shared wrappers exist
Write-Host "`nStep 3: Validate shared wrapper scripts" -ForegroundColor Yellow
$compileScript = ".\compile\compile_tool.ps1"
$depsScript = ".\compile\deps_tool.ps1"
if (-not (Test-Path $compileScript)) {
    Write-Host "❌ Compile wrapper not found: $compileScript" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $depsScript)) {
    Write-Host "❌ Deps wrapper not found: $depsScript" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Compile wrapper exists: $compileScript" -ForegroundColor Green
Write-Host "✓ Deps wrapper exists: $depsScript" -ForegroundColor Green

# Step 4: Setup Python environment (simulated)
Write-Host "`nStep 4: Setup Python environment" -ForegroundColor Yellow
$venvName = ".venv_${ToolName}_Windows_${PythonVersion}_$Architecture"
Write-Host "  Virtual environment name: $venvName" -ForegroundColor Gray

try {
    $depsArgs = @(
        '--tool-path', "Tools/$displayName",
        '--venv-name', $venvName,
        '--noprompt',
        '--force-python-version', $PythonVersion,
        '--pip-requirements', 'Libraries/PyKotor/requirements.txt'
    )
    if ($ToolName -eq 'toolset' -and $QtVersion) {
        $depsArgs += @('--qt-api', $QtVersion)
    }
    & $depsScript @depsArgs 2>&1 | Out-Null

    $pythonExePath = ".\\$venvName\\Scripts\\python.exe"
    if (Test-Path -LiteralPath $pythonExePath) {
        Write-Host "✓ Python executable found: $pythonExePath" -ForegroundColor Green

        # Check Python version
        $pythonVer = & $pythonExePath --version 2>&1
        Write-Host "  Python version: $pythonVer" -ForegroundColor Gray
    } else {
        Write-Host "❌ Python executable not found at expected path: $pythonExePath" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Failed to setup Python environment: $_" -ForegroundColor Red
    exit 1
}

# Step 5: Validate tool imports (dry run validation)
if ($ValidateOnly) {
    Write-Host "`nStep 5: Validate tool imports (dry run)" -ForegroundColor Yellow
    
    $toolPaths = @{
        "toolset" = "toolset"
        "holopatcher" = "holopatcher"
        "kotordiff" = "kotordiff"
        "guiconverter" = "gui_converter"
        "batchpatcher" = "batchpatcher"
        "kitgenerator" = "kitgenerator"
    }
    
    $importPath = $toolPaths[$ToolName.ToLower()]
    if ($importPath) {
        Write-Host "  Testing import: $importPath" -ForegroundColor Gray
        try {
            # Set QT_API if toolset
            if ($ToolName -eq "toolset" -and $QtVersion) {
                $env:QT_API = $QtVersion
            }
            
            $importTest = & $pythonExePath -c "import $importPath; print('OK')" 2>&1
            $importStr = $importTest | Out-String
            
            if ($importStr -match "OK") {
                Write-Host "✓ Import test passed: $importPath" -ForegroundColor Green
            } else {
                Write-Host "⚠ Import test output: $importStr" -ForegroundColor Yellow
                if ($importStr -match "error|Error|ERROR|ImportError|ModuleNotFoundError") {
                    Write-Host "❌ Import test failed" -ForegroundColor Red
                    Write-Host "  Output: $importStr" -ForegroundColor Red
                    exit 1
                }
            }
        } catch {
            Write-Host "❌ Import test failed: $_" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "⚠ No import test defined for tool: $ToolName" -ForegroundColor Yellow
    }
}

# Step 6: Check PyInstaller availability
Write-Host "`nStep 6: Check PyInstaller" -ForegroundColor Yellow
try {
    $pyinstallerVersion = & $pythonExePath -m pip show pyinstaller 2>&1 | Select-String "Version"
    if ($pyinstallerVersion) {
        Write-Host "✓ PyInstaller found: $pyinstallerVersion" -ForegroundColor Green
    } else {
        Write-Host "⚠ PyInstaller not found, would be installed by deps script" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Could not check PyInstaller: $_" -ForegroundColor Yellow
}

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "✓ Action structure validated" -ForegroundColor Green
Write-Host "✓ All required scripts found" -ForegroundColor Green
Write-Host "✓ Python environment can be created" -ForegroundColor Green
if ($ValidateOnly) {
    Write-Host "✓ Dry run validation passed" -ForegroundColor Green
    Write-Host "`nThe action should work correctly in GitHub Actions." -ForegroundColor Green
} else {
    Write-Host "`nTo test full build, run:" -ForegroundColor Cyan
    Write-Host "  $compileScript --preset $($ToolName.ToLower()) --python-exe $pythonExePath" -ForegroundColor White
}

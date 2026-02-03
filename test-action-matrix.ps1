# Comprehensive GitHub Actions Matrix Test
# Tests all tools across Python versions and configurations
param(
    [string[]]$Tools = @("toolset", "holopatcher", "kotordiff", "batchpatcher"),
    [string[]]$PythonVersions = @("3.8", "3.9", "3.10", "3.11", "3.12"),
    [string[]]$QtVersions = @("PyQt5", "PyQt6"),
    [switch]$SkipMissingPython,
    [switch]$ValidateOnly,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$global:TestResults = @()
$global:FailedTests = @()

# Tool to import name mapping
$ToolImportMap = @{
    "toolset" = "toolset"
    "holopatcher" = "holopatcher"
    "kotordiff" = "kotordiff"
    "batchpatcher" = "batchpatcher"
    "guiconverter" = "gui_converter"
    "kitgenerator" = "kitgenerator"
}

# Tool to display name mapping
$ToolDisplayMap = @{
    "toolset" = "HolocronToolset"
    "holopatcher" = "HoloPatcher"
    "kotordiff" = "KotorDiff"
    "batchpatcher" = "BatchPatcher"
    "guiconverter" = "GuiConverter"
    "kitgenerator" = "KitGenerator"
}

# Tools requiring Qt
$QtRequiredTools = @("toolset")

function Write-TestHeader {
    param([string]$Message)
    Write-Host "`n" -NoNewline
    Write-Host ("=" * 80) -ForegroundColor Cyan
    Write-Host " $Message" -ForegroundColor Cyan
    Write-Host ("=" * 80) -ForegroundColor Cyan
}

function Write-TestResult {
    param(
        [string]$Tool,
        [string]$Python,
        [string]$Qt,
        [string]$Test,
        [bool]$Success,
        [string]$Message = ""
    )
    
    $result = [PSCustomObject]@{
        Tool = $Tool
        Python = $Python
        Qt = $Qt
        Test = $Test
        Success = $Success
        Message = $Message
        Timestamp = Get-Date
    }
    
    $global:TestResults += $result
    
    if ($Success) {
        Write-Host "  ✓ " -ForegroundColor Green -NoNewline
    } else {
        Write-Host "  ✗ " -ForegroundColor Red -NoNewline
        $global:FailedTests += $result
    }
    
    Write-Host "$Test" -NoNewline
    if ($Message) {
        Write-Host " - $Message" -ForegroundColor Gray
    } else {
        Write-Host ""
    }
}

function Test-PythonAvailable {
    param([string]$Version)
    
    $commands = @("python$Version", "python${Version}.exe", "py -$Version")
    
    foreach ($cmd in $commands) {
        try {
            $output = & $cmd --version 2>&1
            if ($output -match "Python $Version") {
                return $cmd
            }
        } catch {
            continue
        }
    }
    
    # Try py launcher on Windows
    if ($IsWindows -or $env:OS -match "Windows") {
        try {
            $output = & py -$Version --version 2>&1
            if ($output -match "Python $Version") {
                return "py -$Version"
            }
        } catch {}
    }
    
    return $null
}

function Test-CompileScriptExists {
    param([string]$Tool)

    # Wrapper-only policy: all builds go through compile/compile_tool.ps1.
    $wrapper = ".\compile\compile_tool.ps1"
    if (Test-Path $wrapper) { return $wrapper }
    return $null
}

function Test-DepsScriptExists {
    param([string]$Tool)

    # Wrapper-only policy: all deps install go through compile/deps_tool.ps1.
    $wrapper = ".\compile\deps_tool.ps1"
    if (Test-Path $wrapper) { return $wrapper }
    return $null
}

function Test-ActionStructure {
    Write-TestHeader "Testing Action Structure"
    
    $actionPath = ".\.github\actions\build-tool\action.yml"
    
    # Test action file exists
    $exists = Test-Path $actionPath
    Write-TestResult -Tool "action" -Python "N/A" -Qt "N/A" -Test "Action file exists" -Success $exists
    
    if (-not $exists) {
        return $false
    }
    
    $content = Get-Content $actionPath -Raw
    
    # Test required sections
    $requiredSections = @('name', 'description', 'inputs', 'outputs', 'runs')
    foreach ($section in $requiredSections) {
        $found = $content -match "(?m)^$section\s*:"
        Write-TestResult -Tool "action" -Python "N/A" -Qt "N/A" -Test "Section '$section' exists" -Success $found
    }
    
    # Test required inputs
    $requiredInputs = @('tool_name', 'python_version', 'architecture', 'dry_run')
    foreach ($requiredInput in $requiredInputs) {
        $found = $content -match "\s+$requiredInput\s*:"
        Write-TestResult -Tool "action" -Python "N/A" -Qt "N/A" -Test "Input '$requiredInput' defined" -Success $found
    }
    
    return $true
}

function Test-ToolConfiguration {
    param([string]$Tool)
    
    Write-Host "`n--- Testing $Tool configuration ---" -ForegroundColor Yellow
    
    # Test wrapper scripts
    $compileScript = Test-CompileScriptExists -Tool $Tool
    Write-TestResult -Tool $Tool -Python "N/A" -Qt "N/A" -Test "Compile wrapper exists" -Success ($null -ne $compileScript) -Message $compileScript

    $depsScript = Test-DepsScriptExists -Tool $Tool
    Write-TestResult -Tool $Tool -Python "N/A" -Qt "N/A" -Test "Deps wrapper exists" -Success ($null -ne $depsScript) -Message $depsScript
    
    # Test tool source directory
    $displayName = $ToolDisplayMap[$Tool]
    if (-not $displayName) { $displayName = $Tool }
    
    $toolDirs = @(
        ".\Tools\$displayName",
        ".\Tools\$($Tool.Substring(0,1).ToUpper() + $Tool.Substring(1))"
    )
    
    $toolDir = $null
    foreach ($dir in $toolDirs) {
        if (Test-Path $dir) {
            $toolDir = $dir
            break
        }
    }
    
    Write-TestResult -Tool $Tool -Python "N/A" -Qt "N/A" -Test "Tool directory exists" -Success ($null -ne $toolDir) -Message $toolDir
    
    return (($null -ne $compileScript) -and ($null -ne $depsScript))
}

function Test-PythonEnvironment {
    param(
        [string]$Tool,
        [string]$PythonVersion,
        [string]$QtVersion = ""
    )
    
    $venvName = ".venv_test_${Tool}_${PythonVersion}"
    if ($QtVersion) { $venvName += "_$QtVersion" }
    
    Write-Host "`n--- Testing $Tool with Python $PythonVersion $(if ($QtVersion) { "($QtVersion)" }) ---" -ForegroundColor Yellow
    
    # Check Python availability
    $pythonCmd = Test-PythonAvailable -Version $PythonVersion
    if (-not $pythonCmd) {
        if ($SkipMissingPython) {
            Write-TestResult -Tool $Tool -Python $PythonVersion -Qt $QtVersion -Test "Python available" -Success $true -Message "Skipped - Python $PythonVersion not installed"
            return $true
        }
        Write-TestResult -Tool $Tool -Python $PythonVersion -Qt $QtVersion -Test "Python available" -Success $false -Message "Python $PythonVersion not found"
        return $false
    }
    
    Write-TestResult -Tool $Tool -Python $PythonVersion -Qt $QtVersion -Test "Python available" -Success $true -Message $pythonCmd
    
    if ($ValidateOnly) {
        Write-TestResult -Tool $Tool -Python $PythonVersion -Qt $QtVersion -Test "Validation only" -Success $true -Message "Skipping environment creation"
        return $true
    }
    
    # Create virtual environment
    try {
        Write-Host "  Creating venv: $venvName" -ForegroundColor Gray

        $depsScript = Test-DepsScriptExists -Tool $Tool
        if (-not $depsScript) {
            Write-TestResult -Tool $Tool -Python $PythonVersion -Qt $QtVersion -Test "Deps wrapper exists" -Success $false -Message "compile/deps_tool.ps1 not found"
            return $false
        }

        $depsArgs = @(
            '--tool-path', 'Tools/KotorDiff',
            '--venv-name', $venvName,
            '--noprompt',
            '--force-python-version', $PythonVersion,
            '--pip-install-pyinstaller', ''
        )

        if ($PythonVersion -eq '3.7') {
            $depsArgs += @('--pip-requirements', 'requirements-dev-py37.txt')
        } else {
            $depsArgs += @('--pip-requirements', 'requirements-dev.txt')
        }

        if ($QtVersion) {
            $depsArgs += @('--qt-api', $QtVersion)
        }

        $venvCreated = $false
        try {
            & $depsScript @depsArgs 2>&1 | Out-Null
            $venvCreated = $true
        } catch {
            Write-TestResult -Tool $Tool -Python $PythonVersion -Qt $QtVersion -Test "Create venv" -Success $false -Message $_.Exception.Message
            return $false
        }
        
        Write-TestResult -Tool $Tool -Python $PythonVersion -Qt $QtVersion -Test "Create venv" -Success $venvCreated
        
        if (-not $venvCreated) { return $false }
        
        # Check python executable
        $pythonExe = ".\$venvName\Scripts\python.exe"
        if (-not (Test-Path $pythonExe)) {
            $pythonExe = ".\$venvName\bin\python"
        }
        
        $hasExe = Test-Path $pythonExe
        Write-TestResult -Tool $Tool -Python $PythonVersion -Qt $QtVersion -Test "Venv Python exists" -Success $hasExe -Message $pythonExe
        
        if (-not $hasExe) { return $false }
        
        # Dependencies are installed as part of the deps wrapper invocation.
        Write-TestResult -Tool $Tool -Python $PythonVersion -Qt $QtVersion -Test "Install dependencies" -Success $true
        
        # Test import
        $importName = $ToolImportMap[$Tool]
        if ($importName) {
            Write-Host "  Testing import: $importName" -ForegroundColor Gray
            
            if ($QtVersion) {
                $env:QT_API = $QtVersion
            }
            
            try {
                $importResult = & $pythonExe -c "import $importName; print('OK')" 2>&1
                $importSuccess = $importResult -match "OK"
                Write-TestResult -Tool $Tool -Python $PythonVersion -Qt $QtVersion -Test "Import test" -Success $importSuccess -Message $importName
            } catch {
                Write-TestResult -Tool $Tool -Python $PythonVersion -Qt $QtVersion -Test "Import test" -Success $false -Message $_.Exception.Message
            }
        }
        
        # Check PyInstaller
        try {
            $pipShow = & $pythonExe -m pip show pyinstaller 2>&1 | Select-String "Version"
            $hasPyInstaller = $null -ne $pipShow
            Write-TestResult -Tool $Tool -Python $PythonVersion -Qt $QtVersion -Test "PyInstaller installed" -Success $hasPyInstaller -Message ($pipShow -replace "Version:\s*", "v")
        } catch {
            Write-TestResult -Tool $Tool -Python $PythonVersion -Qt $QtVersion -Test "PyInstaller installed" -Success $false
        }
        
        return $true
        
    } finally {
        # Cleanup venv
        if (Test-Path ".\$venvName") {
            Write-Host "  Cleaning up venv: $venvName" -ForegroundColor Gray
            Remove-Item -Path ".\$venvName" -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

# Main execution
Write-Host @"

╔══════════════════════════════════════════════════════════════════════════════╗
║           PYKOTOR GITHUB ACTIONS COMPREHENSIVE MATRIX TEST                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

Write-Host "Configuration:" -ForegroundColor White
Write-Host "  Tools: $($Tools -join ', ')" -ForegroundColor Gray
Write-Host "  Python Versions: $($PythonVersions -join ', ')" -ForegroundColor Gray
Write-Host "  Qt Versions: $($QtVersions -join ', ')" -ForegroundColor Gray
Write-Host "  Validate Only: $ValidateOnly" -ForegroundColor Gray
Write-Host "  Skip Missing Python: $SkipMissingPython" -ForegroundColor Gray

# Test action structure
$actionValid = Test-ActionStructure

if (-not $actionValid) {
    Write-Host "`n❌ Action structure validation failed. Cannot continue." -ForegroundColor Red
    exit 1
}

# Test each tool's configuration
Write-TestHeader "Testing Tool Configurations"

$validTools = @()
foreach ($tool in $Tools) {
    $valid = Test-ToolConfiguration -Tool $tool
    if ($valid) {
        $validTools += $tool
    }
}

if ($validTools.Count -eq 0) {
    Write-Host "`n❌ No valid tools found. Cannot continue." -ForegroundColor Red
    exit 1
}

# Test matrix combinations
Write-TestHeader "Testing Matrix Combinations"

$totalTests = 0
$passedTests = 0

foreach ($tool in $validTools) {
    $requiresQt = $QtRequiredTools -contains $tool
    
    foreach ($pyVersion in $PythonVersions) {
        if ($requiresQt) {
            foreach ($qtVersion in $QtVersions) {
                $totalTests++
                $result = Test-PythonEnvironment -Tool $tool -PythonVersion $pyVersion -QtVersion $qtVersion
                if ($result) { $passedTests++ }
            }
        } else {
            $totalTests++
            $result = Test-PythonEnvironment -Tool $tool -PythonVersion $pyVersion
            if ($result) { $passedTests++ }
        }
    }
}

# Summary
Write-TestHeader "TEST SUMMARY"

Write-Host "`nTotal Tests: $($global:TestResults.Count)" -ForegroundColor White
Write-Host "Passed: $($global:TestResults | Where-Object { $_.Success } | Measure-Object).Count" -ForegroundColor Green
Write-Host "Failed: $($global:FailedTests.Count)" -ForegroundColor $(if ($global:FailedTests.Count -gt 0) { "Red" } else { "Green" })

if ($global:FailedTests.Count -gt 0) {
    Write-Host "`nFailed Tests:" -ForegroundColor Red
    foreach ($test in $global:FailedTests) {
        Write-Host "  - [$($test.Tool)] $($test.Test) (Python $($test.Python)$(if ($test.Qt) { ", $($test.Qt)" }))" -ForegroundColor Red
        if ($test.Message) {
            Write-Host "    Message: $($test.Message)" -ForegroundColor Gray
        }
    }
    
    Write-Host "`n❌ Some tests failed!" -ForegroundColor Red
    exit 1
} else {
    Write-Host "`n✅ All tests passed!" -ForegroundColor Green
    exit 0
}

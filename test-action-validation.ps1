# Test script to validate the build-tool action
param(
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

Write-Host "=== Validating build-tool action ===" -ForegroundColor Cyan

$actionPath = ".\.github\actions\build-tool\action.yml"

if (-not (Test-Path $actionPath)) {
    Write-Host "❌ Action file not found: $actionPath" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Action file exists" -ForegroundColor Green

# Load YAML (basic validation)
try {
    $content = Get-Content $actionPath -Raw
    Write-Host "✓ Action file is readable" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to read action file: $_" -ForegroundColor Red
    exit 1
}

# Check required sections
$requiredSections = @('name', 'description', 'inputs', 'outputs', 'runs')
foreach ($section in $requiredSections) {
    if ($content -match "(?m)^$section\s*:") {
        Write-Host "✓ Section '$section' found" -ForegroundColor Green
    } else {
        Write-Host "❌ Section '$section' missing" -ForegroundColor Red
        exit 1
    }
}

# Validate required inputs
$requiredInputs = @('tool_name', 'python_version', 'architecture')
foreach ($input in $requiredInputs) {
    if ($content -match "\s+$input\s*:") {
        Write-Host "✓ Input '$input' defined" -ForegroundColor Green
    } else {
        Write-Host "❌ Input '$input' missing" -ForegroundColor Red
        exit 1
    }
}

# Wrapper-only policy: validate shared wrappers exist (legacy per-tool scripts may exist but must not be required).
Write-Host "`n=== Validating shared wrapper scripts ===" -ForegroundColor Cyan
$compileWrapper = ".\compile\compile_tool.ps1"
$depsWrapper = ".\compile\deps_tool.ps1"

if (Test-Path $compileWrapper) {
    Write-Host "✓ Compile wrapper exists: $compileWrapper" -ForegroundColor Green
} else {
    Write-Host "❌ Compile wrapper missing: $compileWrapper" -ForegroundColor Red
    exit 1
}

if (Test-Path $depsWrapper) {
    Write-Host "✓ Deps wrapper exists: $depsWrapper" -ForegroundColor Green
} else {
    Write-Host "❌ Deps wrapper missing: $depsWrapper" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== All validations passed! ===" -ForegroundColor Green
Write-Host "The build-tool action structure appears valid." -ForegroundColor Green
Write-Host "`nNote: Full functional testing requires running on GitHub Actions or" -ForegroundColor Cyan
Write-Host "      using 'act' with elevated permissions and proper Docker setup." -ForegroundColor Cyan

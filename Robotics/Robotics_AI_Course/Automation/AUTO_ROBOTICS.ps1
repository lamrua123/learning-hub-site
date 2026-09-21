#requires -Version 5.1
<#!
Chạy từ bất kỳ thư mục nào. Python 3.10+ thực hiện controller bằng thư viện chuẩn.
Không cài lịch chạy nền. Không tự tiêu thụ reset credit.
!#>
[CmdletBinding()]
param(
    [switch]$Resume,
    [switch]$DryRun,
    [switch]$ValidateOnly,
    [switch]$ProbeUsage,
    [switch]$SelfTest,
    [ValidateRange(1, 1000)][int]$MaxUnits = 1000,
    [ValidateRange(60, 7200)][int]$UnitTimeoutSeconds = 2700,
    [string]$CodexPath = '',
    [string]$PythonPath = 'python'
)
$ErrorActionPreference = 'Stop'
$controllerPath = Join-Path $PSScriptRoot 'controller.py'
if (-not (Test-Path -LiteralPath $controllerPath -PathType Leaf)) { throw 'Thiếu controller.py.' }
$pythonCommand = Get-Command $PythonPath -ErrorAction Stop
$controllerArgs = @($controllerPath, '--root', (Split-Path -Parent $PSScriptRoot), '--max-units', "$MaxUnits", '--timeout', "$UnitTimeoutSeconds")
if ($Resume) { $controllerArgs += '--resume' }
if ($DryRun) { $controllerArgs += '--dry-run' }
if ($ValidateOnly) { $controllerArgs += '--validate-only' }
if ($ProbeUsage) { $controllerArgs += '--probe-usage' }
if ($SelfTest) { $controllerArgs += '--self-test' }
if ($CodexPath) { $controllerArgs += @('--codex', $CodexPath) }
& $pythonCommand.Source @controllerArgs
if ($LASTEXITCODE -ne 0) { throw "Controller dừng với exit code $LASTEXITCODE. Xem state và Automation/Logs." }

param([switch]$CheckOnly, [switch]$Pilot, [switch]$PredictOnly, [switch]$Rebuild)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$unix = (& wsl -d Ubuntu -- wslpath -a ($repo -replace '\\','/')).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve WSL repository' }
& wsl -d Ubuntu -- docker image inspect cvat.lab4.auto:latest --format '{{.Id}}'
if ($LASTEXITCODE -ne 0 -or $Rebuild) {
    & wsl -d Ubuntu -- docker build -t cvat.lab4.auto:latest "$unix/tools/lab4_auto"
    if ($LASTEXITCODE -ne 0) { throw 'Image build failed' }
}
$runArgs = @('docker','run','--rm','--name','lab4-auto-runner','--network','cvat_cvat',
    '-v',"${unix}:/workspace",'-v','/home/ad/sam-setup/auto-cache:/cache',
    '-v','/var/run/docker.sock:/var/run/docker.sock','cvat.lab4.auto:latest',
    'python','tools/lab4_auto/run.py')
if ($CheckOnly) { $runArgs += '--check-only' }
if ($Pilot) { $runArgs += '--pilot' }
if ($PredictOnly) { $runArgs += '--predict-only' }
& wsl -d Ubuntu -- @runArgs
if ($LASTEXITCODE -ne 0) { throw 'Day04 runner failed; see AUTOMATION_RUN_REPORT.md and console.' }

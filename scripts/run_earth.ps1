param([switch]$ReuseCaptures)
$ErrorActionPreference='Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONUTF8='1'
$python=Join-Path $PWD '.venv\Scripts\python.exe'
function Invoke-Step($program,$arguments){ & $program @arguments; if($LASTEXITCODE -ne 0){throw "Stage failed: $program $arguments"} }
$ownedEngine=$null
try {
    if(!$ReuseCaptures){
        Invoke-Step 'node' @('scripts/capture_earth.mjs')
        Invoke-Step 'node' @('scripts/capture_earth_views.mjs')
    }
    Invoke-Step $python @('scripts/register_earth.py')
    Invoke-Step $python @('scripts/fetch_portraits.py')
    Invoke-Step (Join-Path $PWD 'tools\blender-4.5.3-windows-x64\blender.exe') @('-b','-t','4','--python','scripts/render_army_sprites.py')
    try {Invoke-RestMethod 'http://127.0.0.1:50021/version' -TimeoutSec 3 | Out-Null}
    catch {
        $folder=Join-Path $PWD 'tools\voicevox\windows-cpu'
        $ownedEngine=Start-Process (Join-Path $folder 'run.exe') -ArgumentList '--host','127.0.0.1','--port','50021' -WorkingDirectory $folder -WindowStyle Hidden -PassThru
        $ready=$false
        for($i=0;$i -lt 60;$i++){
            try {Invoke-RestMethod 'http://127.0.0.1:50021/version' -TimeoutSec 2 | Out-Null; $ready=$true; break}
            catch {Start-Sleep -Milliseconds 500}
        }
        if(!$ready){throw 'VOICEVOX startup failed'}
    }
    Invoke-Step $python @('scripts/audio.py','earth')
    Invoke-Step $python @('scripts/build_earth_film.py')
    Invoke-Step $python @('scripts/verify_earth.py')
    Invoke-Step $python @('scripts/write_earth_report.py')
} finally {if($ownedEngine -and !$ownedEngine.HasExited){Stop-Process -Id $ownedEngine.Id}}

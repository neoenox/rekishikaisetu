param([switch]$SkipRender)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$python = Join-Path $PWD '.venv\Scripts\python.exe'
$blender = Join-Path $PWD 'tools\blender-4.5.3-windows-x64\blender.exe'
function Invoke-Checked { param([string]$Exe,[string[]]$Arguments) & $Exe @Arguments; if ($LASTEXITCODE -ne 0) { throw "Failed: $Exe $Arguments" } }
Invoke-Checked $python @('scripts/doctor.py')
Invoke-Checked $python @('scripts/terrain.py')
Invoke-Checked $python @('scripts/prepare_story.py')
Invoke-Checked $python @('scripts/analyze.py')
$engineProcess = $null
try {
    try { Invoke-RestMethod 'http://127.0.0.1:50021/version' | Out-Null }
    catch {
        $engineFolder = Join-Path $PWD 'tools\voicevox\windows-cpu'
        $engineProcess = Start-Process (Join-Path $engineFolder 'run.exe') -ArgumentList '--host','127.0.0.1','--port','50021' -WorkingDirectory $engineFolder -WindowStyle Hidden -PassThru
        $ready = $false
        for ($i=0; $i -lt 60; $i++) {
            Start-Sleep -Seconds 1
            try { Invoke-RestMethod 'http://127.0.0.1:50021/version' | Out-Null; $ready=$true; break } catch { }
        }
        if (!$ready) { throw 'Local VOICEVOX engine did not start' }
    }
    Invoke-Checked $python @('scripts/audio.py')
    Invoke-Checked 'npm.cmd' @('run','cards')
    Invoke-Checked 'npm.cmd' @('run','test:layout')
    foreach ($level in 1..3) {
        if (!$SkipRender) { Invoke-Checked $blender @('-b','-t','8','--python','scripts/render_blender.py','--',"$level",'comparison') }
        Invoke-Checked $python @('scripts/compose.py','comparison',"$level")
    }
    if (!$SkipRender) { Invoke-Checked $python @('scripts/render_pilot_parallel.py') }
    Invoke-Checked $python @('scripts/compose.py','pilot','2')
    Invoke-Checked $python @('scripts/export_sources.py')
    Invoke-Checked $python @('-m','pytest','scripts','-q')
    Invoke-Checked $python @('scripts/verify.py')
    Invoke-Checked $python @('scripts/write_report.py')
} finally {
    if ($engineProcess -and !$engineProcess.HasExited) { Stop-Process -Id $engineProcess.Id }
}

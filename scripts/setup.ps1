$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
foreach ($dir in @('tools','cache','logs','out','data')) { New-Item -ItemType Directory -Force $dir | Out-Null }
uv venv --python 3.12 .venv
if ($LASTEXITCODE -ne 0) { throw 'uv Python environment failed' }
uv pip install --python .venv\Scripts\python.exe -r requirements-lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed' }
foreach ($tool in @('blender','voicevox')) {
    & .venv\Scripts\python.exe scripts\download_tools.py $tool
    if ($LASTEXITCODE -ne 0) { throw "Download failed: $tool" }
}
if (!(Test-Path tools\blender-4.5.3-windows-x64\blender.exe)) { Expand-Archive -LiteralPath tools\blender-portable.zip -DestinationPath tools }
if (!(Test-Path tools\voicevox\windows-cpu\run.exe)) {
    & 'C:\Program Files\7-Zip\7z.exe' x tools\voicevox-portable.7z -otools\voicevox -y
    if ($LASTEXITCODE -ne 0) { throw 'VOICEVOX extraction failed; install 7-Zip or adjust its executable path' }
}
npm.cmd ci --no-audit --no-fund
if ($LASTEXITCODE -ne 0) { throw 'Node dependency installation failed' }

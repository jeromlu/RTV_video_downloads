Param(
    [Bool] $EditableInstall = $true
)

Set-Location $PSScriptRoot

function CheckExitCode($errormsg) {
    if ($LastExitCode -ne 0) {
        throw $errormsg
    }
}

if (Test-Path -Path venv) {
    throw "venv already exists"
}

$pythonVersion = python --version
CheckExitCode "failed to run python"

$pythonPath = (Get-Command python).Path
CheckExitCode "failed to run python"
"Python to be used:`r$pythonPath"
$pythonVersion
if (-not ($pythonVersion -ilike '*Python*3.10*'))
{
    Write-Output "Python version is not correct."
    Write-Output "If correct version is installed but not on the PATH could set it by:"
    Write-Output '$Env:PATH="path/to/python/exe;$Env:PATH"'
    Write-Output "and re-run this script."
    Write-Output "Exiting script."
    throw "Wrong version of python."
}

python -m venv venv
CheckExitCode "failed to create venv"

.\venv\Scripts\Activate.ps1

python -m pip install -U pip
CheckExitCode "failed to upgrade pip"

$PipExtraFlags = if ($EditableInstall) { ,"-e" } else { @() }
python -m pip install $PipExtraFlags .

#python -m pip install -r requirements.txt
#CheckExitCode "failed to install requirements"

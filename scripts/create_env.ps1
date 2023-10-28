Param(
    [Bool] $EditableInstall = $true
)

# It is assumed that project root is parent folder of this script. 
pwd
Write-Output  $PSScriptRoot
Write-Output  "$PSScriptRoot/.."
#Set-Location $PSScriptRoot
Push-Location $PSScriptRoot
pwd
cd ..
pwd

function CheckExitCode($errormsg) {
    if ($LastExitCode -ne 0) {
        Pop-Location
        throw $errormsg
    }
}

if (Test-Path -Path venv) {
    Pop-Location
    throw "venv already exists."
}

$pythonVersion = python --version
CheckExitCode "Failed to run python."

$pythonPath = (Get-Command python).Path
CheckExitCode "failed to run python"
Write-Output "Python to be used:`r$pythonPath"
Write-Output $pythonVersion

if (-not ($pythonVersion -ilike 'Python*3.10*'))
{
    Write-Output "Python version is not correct."
    Write-Output "If correct version is installed but not on the PATH could set it by:"
    Write-Output '$Env:PATH="path/to/python/exe;$Env:PATH"'
    Write-Output "and re-run this script."
    Write-Output "Exiting script."
    throw "Wrong version of python."
}

python -m venv venv
CheckExitCode "Failed to create virtual environment."

.\venv\Scripts\Activate.ps1

python -m pip install -U pip
CheckExitCode "Failed to upgrade pip."

# TODO(lj): Should I move to poetry for dependency management.
$PipExtraFlags = if ($EditableInstall) { ,"-e" } else { @() }
Write-Output "Running pip with extra flags:$PipExtraFlags"
python -m pip install $PipExtraFlags . -v

#python -m pip install -r requirements.txt
#CheckExitCode "failed to install requirements"
Pop-Location

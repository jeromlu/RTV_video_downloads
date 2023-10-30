$ProjectRootDir = (Get-Item $PSScriptRoot).parent.FullName
$AppDirPath = "$ProjectRootDir/dist/rtv-video-downloader"
$RelVersionFilePath = "$ProjectRootDir/pyproject.toml"
$AppPyinstallerSpecFname =  "rtv_video_downloader.spec"
$FixedVerStrPart  = "version = "

function Get-LjAppVersionString{
    param (
        [string[]]$fixedVerStrPart
    )
    $searchStringPattern = "$fixedVerStrPart`"(.*)`"$"
    $selectedString = Select-String -Path $relVersionFilePath -Pattern $searchStringPattern
    if (-not $selectedString) {
        $msg =  "Something wrong with the version.`n"
        Write-Host $msg
        throw $msg
    }
    if ($selectedString.Matches.Groups[1].Value) {
        $versionGroupString = $selectedString.Matches.Groups[1].Value
        Write-Host "Found version string=`'$versionGroupString`'"
        #return $selectedString.Matches.Groups[1].Value.Replace(".", "-")
        return $selectedString
    }
    else {
        $msg = "Something wrong with version string in python file.`n"
        Write-Host $msg
        throw $msg
    }
}

function New-VersionString {
    param (
        [string[]]$oldVersionString
    )
    $splitted = $oldVersionString.Split("-")
    #([regex]::Matches($oldVersionString, "<= goes here /" )).count
    if ($splitted.Count -ne 3) {
        $msg = "Old version of string is in wrong format."
        throw $msg
    }
    $newNumber = [int]$splitted[2] + 1
    $first = $splitted[0]
    $second = $splitted[1]
    return "$first-$second-$newNumber"
}

$version = Get-LjAppVersionString($FixedVerStrPart)
$versionString = $version.Matches.Groups[1].Value.Replace(".", "-")
$newVersionString = New-VersionString($versionString)
$outFile = "$appDirPath`_v$newVersionString.zip"

if (Test-Path -Path $outFile) {
    # PromptForChoice Args
    $title = "File with version $newVersionString already exist."
    $prompt = "Would you like to overwrite it?"
    $choices = [System.Management.Automation.Host.ChoiceDescription[]] @("&Yes", "&No")
    # No is default.
    $default = 1

    # Prompt for the choice
    $choice = $host.UI.PromptForChoice($Title, $Prompt, $Choices, $Default)

    switch($choice)
    {
        $default {
            Write-Output "Deployment stopped."
            return
        }
    }
}

$filecontent = Get-Content -Path $relVersionFilePath -Raw
$newPythonVersionString = $newVersionString.replace("-", ".")
$newFileContent = $filecontent.Replace(
    $version.Matches.Groups[0].Value,
    "$FixedVerStrPart`"$newPythonVersionString`""
    )
Set-Content -Path $relVersionFilePath -Value $newFileContent

pyinstaller -y $AppPyinstallerSpecFname

$filesToCompress = (Get-ChildItem -Path $appDirPath).FullName
Compress-Archive -Path $filesToCompress -DestinationPath $outFile -Confirm

$ProjectRootDir = (Get-Item $PSScriptRoot).parent.FullName
pwd
$AppDirPath = "$ProjectRootDir/dist/rtv-video-downloader"
$RelVersionFilePath = "$ProjectRootDir/src/rtv_video_downloader/__version__.py" 
Write-Output $RelVersionFilePath
$AppPyinstallerSpecFname =  "rtv_video_downloader.spec"
$FixedVerStrPart  = "__version__: str = "

function Get-LjAppVersionString{
    param (
        [string[]]$fixedVerStrPart
    )
    $searchStringPattern = "$fixedVerStrPart`"(.*)`"$"
    $selectedString = Select-String -Path $relVersionFilePath -Pattern $searchStringPattern
    if (-not $selectedString) {
        Write-Output "Something wrong with the version.`n"
        return ""
    }
    if ($selectedString.Matches.Groups[1].Value) {
        return $selectedString.Matches.Groups[1].Value.Replace(".", "-")
    }
    else {
        Write-Output "Something wrong with version string in python file.`n"
        return ""
    }
}

function New-VersionString {
    param (
        [string[]]$oldVersionString
    )
    $splitted = $oldVersionString.Split("-")
    #([regex]::Matches($oldVersionString, "<= goes here /" )).count
    if ($splitted.Count -ne 3) {
        "Old version of string is in wrong format."
    }
    $newNumber = [int]$splitted[2] + 1
    $first = $splitted[0]
    $second = $splitted[1]
    return "$first-$second-$newNumber"
}

$versionString = Get-LjAppVersionString($fixedVerStrPart)
$newVersionString = New-VersionString($versionString)
$outFile = "$appDirPath`_v$newVersionString.zip" 
Write-Output $outFile

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
$newFileContent = "$fixedVerStrPart`"$newPythonVersionString`""
Set-Content -Path $relVersionFilePath -Value $newFileContent

pyinstaller -y $AppPyinstallerSpecFname

$filesToCompress = (Get-ChildItem -Path $appDirPath).FullName
Compress-Archive -Path $filesToCompress -DestinationPath $outFile -Confirm



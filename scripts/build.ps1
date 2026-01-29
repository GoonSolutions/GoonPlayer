# ========================================
# GoonPlayer Build Script
# ========================================
#
# This script builds a standalone application using Nuitka.
# Builds in standalone mode (directory with EXE and dependencies).
#
# Requirements:
#   - Python 3.13 (via the 'py' launcher: py -3.13)
#   - Nuitka installed (auto-installed if missing)
#   - A C compiler (MSVC or MinGW64; Nuitka can auto-download MinGW64)
#
# Usage:
#   .\scripts\build.ps1                      # Build standalone
#   .\scripts\build.ps1 -clean               # Clean build artifacts only
#   .\scripts\build.ps1 -release             # Build standalone and create release archive
#
# Output:
#   dist/GoonPlayer.dist/ - Built application
#   release/GoonPlayer-{version}-win64.zip - Release archive (with -release)
#
# Note: The build cache is automatically removed after successful builds
#

# Parse command line arguments
param(
    [switch]$clean,
    [switch]$release,
    [string]$vlcPath = ""
)

# Get the root directory (parent of scripts folder)
$rootDir = Split-Path -Parent $PSScriptRoot

# Clean function
function Invoke-Clean {
    Write-Host "Cleaning build artifacts..." -ForegroundColor Cyan

    $foldersToRemove = @("__pycache__", "build", "dist", "release", "GoonPlayer.build", "GoonPlayer.dist", "GoonPlayer.onefile-build")
    $filesToRemove = @("*.spec", "version_info.txt", "nuitka-crash-report.xml", "GoonPlayer.config.json")
    $removedCount = 0
    $failedCount = 0

    # Remove folders
    foreach ($folder in $foldersToRemove) {
        $folderPath = Join-Path $rootDir $folder
        if (Test-Path $folderPath) {
            Write-Host "Removing $folder..." -ForegroundColor Yellow
            try {
                Remove-Item -Path $folderPath -Recurse -Force -ErrorAction Stop
                $removedCount++
            } catch {
                Write-Host "Failed to remove ${folder}: $($_.Exception.Message)" -ForegroundColor Red
                $failedCount++
            }
        } else {
            Write-Host "$folder not found (skipping)" -ForegroundColor Gray
        }
    }

    # Remove spec files and version info from root
    foreach ($filePattern in $filesToRemove) {
        $files = Get-ChildItem -Path $rootDir -Filter $filePattern -File -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            Write-Host "Removing $($file.Name)..." -ForegroundColor Yellow
            try {
                Remove-Item -Path $file.FullName -Force -ErrorAction Stop
                $removedCount++
            } catch {
                Write-Host "Failed to remove $($file.Name): $($_.Exception.Message)" -ForegroundColor Red
                $failedCount++
            }
        }
    }

    # Also check for __pycache__ folders recursively
    Write-Host "Searching for nested __pycache__ folders..." -ForegroundColor Cyan
    $pycacheFolders = Get-ChildItem -Path $rootDir -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue

    foreach ($pycache in $pycacheFolders) {
        Write-Host "Removing $($pycache.FullName)..." -ForegroundColor Yellow
        try {
            Remove-Item -Path $pycache.FullName -Recurse -Force -ErrorAction Stop
            $removedCount++
        } catch {
            Write-Host "Failed to remove $($pycache.FullName): $($_.Exception.Message)" -ForegroundColor Red
            $failedCount++
        }
    }

    Write-Host ""
    if ($removedCount -eq 0 -and $failedCount -eq 0) {
        Write-Host "Nothing to clean - workspace is already clean!" -ForegroundColor Green
    } else {
        if ($removedCount -gt 0) {
            Write-Host "Successfully removed $removedCount item(s)" -ForegroundColor Green
        }
        if ($failedCount -gt 0) {
            Write-Host "Failed to remove $failedCount item(s) - they may be in use" -ForegroundColor Red
        }
    }
    Write-Host ""
}

# Run clean-only if requested
if ($clean) {
    Invoke-Clean
    exit 0
}

# Resolve Python: prefer active venv, fall back to py -3.13
Write-Host "Checking for Python 3.13..."
$pyExe = $null
$pyArgs = @()
$venvPath = Join-Path $rootDir ".venv"

# Check if a venv is active and its Python is 3.13
if ($env:VIRTUAL_ENV) {
    try {
        $pyTest = python --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $pyTest -match "3\.13") {
            $pyExe = "python"
            Write-Host "Found: $pyTest (venv: $env:VIRTUAL_ENV)" -ForegroundColor Green
        }
    } catch { }
}

# Check if project venv exists and use it
if (-not $pyExe -and (Test-Path $venvPath)) {
    try {
        $venvPython = Join-Path $venvPath "Scripts\python.exe"
        $pyTest = & $venvPython --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $pyTest -match "3\.13") {
            $pyExe = $venvPython
            Write-Host "Found: $pyTest (project venv: $venvPath)" -ForegroundColor Green
        }
    } catch { }
}

# Create project venv if it doesn't exist and no active venv
if (-not $pyExe) {
    Write-Host "Creating project virtual environment..." -ForegroundColor Cyan

    # Use py -3.13 to create venv
    try {
        py -3.13 --version 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Error: Python 3.13 not found." -ForegroundColor Red
            Write-Host "Install Python 3.13 for the 'py' launcher." -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
    } catch {
        Write-Host "Error: Python 3.13 not found." -ForegroundColor Red
        Write-Host "Install Python 3.13 for the 'py' launcher." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }

    py -3.13 -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }

    $venvPython = Join-Path $venvPath "Scripts\python.exe"
    $pyTest = & $venvPython --version 2>&1
    $pyExe = $venvPython
    Write-Host "Created: $pyTest (project venv: $venvPath)" -ForegroundColor Green
}

# Helper to invoke python consistently
function Invoke-Python {
    param([Parameter(ValueFromRemainingArguments)]$Arguments)
    & $pyExe @pyArgs @Arguments
}

# Helper to find VLC installation directory
function Find-VLC {
    $possiblePaths = @(
        "C:\Program Files\VideoLAN\VLC",
        "C:\Program Files (x86)\VideoLAN\VLC",
        "${env:ProgramFiles}\VideoLAN\VLC",
        "${env:ProgramFiles(x86)}\VideoLAN\VLC"
    )

    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            # Verify libvlc.dll exists
            if (Test-Path (Join-Path $path "libvlc.dll")) {
                return $path
            }
        }
    }

    return $null
}

# Install runtime dependencies
Write-Host "Installing runtime dependencies..."
$requirementsFile = Join-Path $rootDir "requirements.txt"
if (Test-Path $requirementsFile) {
    Invoke-Python -m pip install -r $requirementsFile
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install runtime dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "Error: requirements.txt not found" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install build dependencies
Write-Host "Checking for build dependencies..."
$buildRequirementsFile = Join-Path $rootDir "requirements-build.txt"
if (Test-Path $buildRequirementsFile) {
    Invoke-Python -m pip show nuitka 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Build dependencies not found. Installing from requirements-build.txt..." -ForegroundColor Yellow
        Invoke-Python -m pip install -r $buildRequirementsFile
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to install build dependencies" -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
    }
} else {
    Write-Host "Error: requirements-build.txt not found" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Extract version from version.py (in root directory)
Write-Host "Reading version info..." -ForegroundColor Cyan
$versionFile = Join-Path $rootDir "version.py"
$versionContent = Get-Content -Path $versionFile -Raw
if ($versionContent -match '__version__\s*=\s*"([^"]+)"') {
    $version = $matches[1]
    # Extract base version (strip prerelease tag for Windows version fields)
    $baseVersion = ($version -split '-')[0]
    Write-Host "Version: $version (file version: $baseVersion.0)" -ForegroundColor Yellow
} else {
    Write-Host "Error: Could not extract version from version.py" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Create dist folder if it doesn't exist
$distDir = Join-Path $rootDir "dist"
if (-not (Test-Path $distDir)) {
    New-Item -ItemType Directory -Path $distDir | Out-Null
}

# Build in standalone mode
$buildMode = "standalone"
$buildFlag = "--standalone"

# Run Nuitka in specified mode (from root directory)
Write-Host "Building GoonPlayer with Nuitka ($buildMode mode)..." -ForegroundColor Cyan
Push-Location $rootDir
Invoke-Python -m nuitka `
    $buildFlag `
    --no-deployment-flag=self-execution `
    --output-dir=dist `
    --output-filename=GoonPlayer.exe `
    --windows-company-name=GoonSolutions `
    --windows-product-name=GoonPlayer `
    --windows-file-description=GoonPlayer `
    --windows-product-version="$baseVersion.0" `
    --windows-file-version="$baseVersion.0" `
    --copyright="© 2026 GoonSolutions" `
    --windows-console-mode=attach `
    --enable-plugin=pyside6 `
    --windows-icon-from-ico=icons/app.ico `
    --include-data-dir=icons=icons `
    --include-module=ctypes.util `
    --nofollow-import-to=vlc `
    --nofollow-import-to=PySide6.QtWebEngine `
    --nofollow-import-to=PySide6.QtWebEngineCore `
    --nofollow-import-to=PySide6.QtWebEngineWidgets `
    --nofollow-import-to=PySide6.QtWebChannel `
    --nofollow-import-to=PySide6.QtWebSockets `
    --nofollow-import-to=PySide6.QtNetwork `
    --nofollow-import-to=PySide6.QtNetworkAuth `
    --nofollow-import-to=PySide6.QtBluetooth `
    --nofollow-import-to=PySide6.QtMultimedia `
    --nofollow-import-to=PySide6.QtMultimediaWidgets `
    --nofollow-import-to=PySide6.QtQuick `
    --nofollow-import-to=PySide6.QtQml `
    --noinclude-dlls="Qt6WebEngine*" `
    --noinclude-dlls="Qt6WebChannel*" `
    --noinclude-dlls="Qt6WebSockets*" `
    --noinclude-dlls="Qt6Network*" `
    --noinclude-dlls="Qt6Bluetooth*" `
    --noinclude-dlls="Qt6Multimedia*" `
    --noinclude-dlls="Qt6Quick*" `
    --noinclude-dlls="Qt6Qml*" `
    --noinclude-dlls="Qt6Pdf*" `
    --noinclude-dlls="Qt6Positioning*" `
    --noinclude-dlls="Qt6SerialPort*" `
    --noinclude-dlls="Qt6Sensors*" `
    --noinclude-dlls="Qt6Test*" `
    --noinclude-dlls="Qt6Sql*" `
    --noinclude-dlls="Qt6Xml*" `
    --noinclude-dlls="Qt6Designer*" `
    --noinclude-dlls="Qt6Help*" `
    --noinclude-dlls="Qt6Charts*" `
    --noinclude-dlls="Qt6DataVisualization*" `
    --noinclude-dlls="Qt63D*" `
    --noinclude-dlls="Qt6RemoteObjects*" `
    --noinclude-dlls="Qt6Scxml*" `
    --noinclude-dlls="Qt6StateMachine*" `
    --noinclude-dlls="Qt6TextToSpeech*" `
    --noinclude-dlls="Qt6VirtualKeyboard*" `
    --noinclude-dlls="Qt6Nfc*" `
    --remove-output `
    --follow-imports `
    GoonPlayer.py

Pop-Location

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Build failed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Post-build: Copy VLC directory from system installation or use -vlcPath parameter
# Also copy the python-vlc module from site-packages
Write-Host "Post-build: Finding and copying VLC directory..." -ForegroundColor Cyan
$targetPath = Join-Path $rootDir "dist\GoonPlayer.dist"

# Determine VLC source path
$sourceVlc = $null

if ($vlcPath -and (Test-Path $vlcPath)) {
    # User provided explicit path
    $sourceVlc = $vlcPath
    Write-Host "Using VLC path provided: $vlcPath" -ForegroundColor Yellow
} else {
    # Try to find VLC from system installation
    $foundVlc = Find-VLC
    if ($foundVlc) {
        $sourceVlc = $foundVlc
        Write-Host "Found VLC installation: $foundVlc" -ForegroundColor Yellow
    }
}

if ($sourceVlc) {
    # Copy only essential VLC files to dist (DLLs and plugins)
    $targetVlc = Join-Path $targetPath "vlc"

    # Remove the old VLC directory and create fresh
    if (Test-Path $targetVlc) {
        Remove-Item -Path $targetVlc -Recurse -Force -ErrorAction SilentlyContinue
    }
    New-Item -ItemType Directory -Path $targetVlc | Out-Null

    # Copy only the essential DLLs
    $libvlcDll = Join-Path $sourceVlc "libvlc.dll"
    $libvlccoreDll = Join-Path $sourceVlc "libvlccore.dll"

    $dllStatus = "[MISSING]"
    $coreStatus = "[MISSING]"

    if (Test-Path $libvlcDll) {
        Copy-Item -Path $libvlcDll -Destination $targetVlc -Force -ErrorAction SilentlyContinue
        $dllStatus = "[OK]"
    }

    if (Test-Path $libvlccoreDll) {
        Copy-Item -Path $libvlccoreDll -Destination $targetVlc -Force -ErrorAction SilentlyContinue
        $coreStatus = "[OK]"
    }

    # Copy plugins directory
    $sourcePlugins = Join-Path $sourceVlc "plugins"
    $targetPlugins = Join-Path $targetVlc "plugins"
    $pluginStatus = "[MISSING]"

    if (Test-Path $sourcePlugins) {
        Copy-Item -Path $sourcePlugins -Destination $targetPlugins -Recurse -Force -ErrorAction SilentlyContinue
        $pluginStatus = "[OK]"
    }

    Write-Host "VLC files copied:" -ForegroundColor Green
    Write-Host "  Source: $sourceVlc" -ForegroundColor Gray
    Write-Host "  Target: $targetVlc" -ForegroundColor Gray
    Write-Host "  $dllStatus libvlc.dll" -ForegroundColor Gray
    Write-Host "  $coreStatus libvlccore.dll" -ForegroundColor Gray
    Write-Host "  $pluginStatus plugins/ directory" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "Error: VLC not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "To use the build script, install VLC or provide the path explicitly:" -ForegroundColor Yellow
    Write-Host "  1. Install VLC from: https://www.videolan.org/vlc/" -ForegroundColor Gray
    Write-Host "  2. OR use: .\scripts\build.ps1 -vlcPath 'C:\path\to\vlc'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Default search locations:" -ForegroundColor Gray
    Write-Host "  - C:\Program Files\VideoLAN\VLC" -ForegroundColor Gray
    Write-Host "  - C:\Program Files (x86)\VideoLAN\VLC" -ForegroundColor Gray
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Copy python-vlc module from site-packages
Write-Host "Post-build: Copying python-vlc module..." -ForegroundColor Cyan

# Check multiple locations for vlc.py
$pythonVlcSource = $null
$searchPaths = @()

# Add venv location if available
if ($env:VIRTUAL_ENV) {
    $searchPaths += Join-Path $env:VIRTUAL_ENV "Lib\site-packages\vlc.py"
}

# Add project root (in case it's there)
$searchPaths += Join-Path $rootDir ".venv\Lib\site-packages\vlc.py"

# Try each path
foreach ($path in $searchPaths) {
    if (Test-Path $path) {
        $pythonVlcSource = $path
        break
    }
}

if ($pythonVlcSource -and (Test-Path $pythonVlcSource)) {
    $pythonVlcDest = Join-Path $targetPath "vlc.py"
    Copy-Item -Path $pythonVlcSource -Destination $pythonVlcDest -Force
    $fileSize = (Get-Item $pythonVlcSource).Length / 1KB
    Write-Host "  Copied python-vlc module from: $pythonVlcSource" -ForegroundColor Green
    Write-Host "  Size: $([math]::Round($fileSize, 1)) KB" -ForegroundColor Gray
} else {
    Write-Host "  Error: python-vlc module (vlc.py) not found" -ForegroundColor Red
    Write-Host "  Searched in:" -ForegroundColor Gray
    foreach ($path in $searchPaths) {
        Write-Host "    - $path" -ForegroundColor Gray
    }
    Write-Host "  The application may not work without this file" -ForegroundColor Yellow
}

# Clear Windows icon cache so Explorer shows the correct icon
Write-Host "Clearing Windows icon cache..." -ForegroundColor Cyan
& ie4uinit.exe -show 2>&1 | Out-Null

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Build successful!" -ForegroundColor Green
$outputPath = "dist/GoonPlayer.dist/"
Write-Host "Output: $outputPath" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Copy documentation files to dist folder (before creating release zip)
Write-Host "Copying documentation files..." -ForegroundColor Cyan
$docsFiles = @("CHANGELOG.md", "LICENSE", "README.md")
$targetPath = Join-Path $rootDir "dist\GoonPlayer.dist"

foreach ($docFile in $docsFiles) {
    $sourcePath = Join-Path $rootDir $docFile
    if (Test-Path $sourcePath) {
        $destPath = Join-Path $targetPath $docFile
        try {
            Copy-Item -Path $sourcePath -Destination $destPath -Force
            Write-Host "  Copied $docFile" -ForegroundColor Gray
        } catch {
            Write-Host "  Warning: Could not copy $docFile - $($_.Exception.Message)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  Warning: $docFile not found in root directory" -ForegroundColor Yellow
    }
}
Write-Host ""

# Clean up Nuitka build cache folders
$cacheToClean = @("GoonPlayer.build", "GoonPlayer.dist")

foreach ($cacheFolder in $cacheToClean) {
    $cachePath = Join-Path $rootDir $cacheFolder
    if (Test-Path $cachePath) {
        Write-Host "Cleaning up $cacheFolder..." -ForegroundColor Cyan
        try {
            Remove-Item -Path $cachePath -Recurse -Force -ErrorAction Stop
            Write-Host "$cacheFolder removed" -ForegroundColor Gray
        } catch {
            Write-Host "Warning: Could not remove $cacheFolder (not critical)" -ForegroundColor Yellow
        }
    }
}
Write-Host ""

# Create release archive if -release flag is set
if ($release) {
    Write-Host "Creating release archive..." -ForegroundColor Cyan
    Write-Host "Version: $version" -ForegroundColor Yellow

    # Create release folder if it doesn't exist
    $releaseDir = Join-Path $rootDir "release"
    if (-not (Test-Path $releaseDir)) {
        New-Item -ItemType Directory -Path $releaseDir | Out-Null
        Write-Host "Created release folder" -ForegroundColor Yellow
    }

    # Create binary release zip
    $zipName = "GoonPlayer-${version}-win64.zip"
    $zipPath = Join-Path $releaseDir $zipName
    Write-Host "Creating $zipName..." -ForegroundColor Cyan

    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }

    # Check if 7-Zip is available
    $sevenZipPath = $null
    $possiblePaths = @(
        "C:\Program Files\7-Zip\7z.exe",
        "C:\Program Files (x86)\7-Zip\7z.exe",
        "${env:ProgramFiles}\7-Zip\7z.exe",
        "${env:ProgramFiles(x86)}\7-Zip\7z.exe"
    )

    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            $sevenZipPath = $path
            break
        }
    }

    if ($null -eq $sevenZipPath) {
        Write-Host "Warning: 7-Zip not found, falling back to built-in Compress-Archive" -ForegroundColor Yellow
        Write-Host "For better zip compatibility, install 7-Zip: https://www.7-zip.org/" -ForegroundColor Yellow

        # Fallback to Compress-Archive
        $distPath = Join-Path $rootDir "dist\GoonPlayer.dist"
        if (Test-Path $distPath) {
            # Create temp folder with GoonPlayer root folder for proper zip structure
            $tempDir = Join-Path $rootDir "dist\temp_zip"
            if (-not (Test-Path $tempDir)) {
                New-Item -ItemType Directory -Path $tempDir | Out-Null
            }
            Copy-Item -Path $distPath -Destination "$tempDir\GoonPlayer" -Recurse -Force
            foreach ($docFile in $docsFiles) {
                $sourceDoc = Join-Path $rootDir "dist\$docFile"
                if (Test-Path $sourceDoc) {
                    Copy-Item -Path $sourceDoc -Destination "$tempDir\GoonPlayer\$docFile" -Force
                }
            }
            Compress-Archive -Path "$tempDir\GoonPlayer\*" -DestinationPath $zipPath -CompressionLevel Optimal
            Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        } else {
            Write-Host "Error: $distPath not found" -ForegroundColor Red
        }
    } else {
        Write-Host "Using 7-Zip for archive creation..." -ForegroundColor Cyan

        # Create zip with GoonPlayer as root (not GoonPlayer.dist)
        $distPath = Join-Path $rootDir "dist\GoonPlayer.dist"
        if (Test-Path $distPath) {
            # Create temp folder with GoonPlayer root folder for proper zip structure
            $tempDir = Join-Path $rootDir "dist\temp_zip"
            if (-not (Test-Path $tempDir)) {
                New-Item -ItemType Directory -Path $tempDir | Out-Null
            }
            Copy-Item -Path $distPath -Destination "$tempDir\GoonPlayer" -Recurse -Force
            foreach ($docFile in $docsFiles) {
                $sourceDoc = Join-Path $rootDir "dist\$docFile"
                if (Test-Path $sourceDoc) {
                    Copy-Item -Path $sourceDoc -Destination "$tempDir\GoonPlayer\$docFile" -Force
                }
            }
            # Use 7-Zip with proper Windows compatibility flags
            Push-Location $tempDir
            & $sevenZipPath a -tzip -mx=5 "$zipPath" "GoonPlayer"
            $sevenZipSuccess = $LASTEXITCODE -eq 0
            Pop-Location
            if ($sevenZipSuccess) {
                Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
            } else {
                Write-Host "7-Zip failed with exit code: $LASTEXITCODE" -ForegroundColor Red
                Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
            }
        } else {
            Write-Host "Error: $distPath not found" -ForegroundColor Red
        }
    }

    if (Test-Path $zipPath) {
        $zipSize = (Get-Item $zipPath).Length / 1MB
        Write-Host "Created: $zipPath ($([math]::Round($zipSize, 2)) MB)" -ForegroundColor Green
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "Release archive created successfully!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "Failed to create $zipName" -ForegroundColor Red
        Write-Host ""
    }
}

# Display info about the built application
Write-Host "Build output:" -ForegroundColor Cyan

$appDir = Join-Path $rootDir "dist\GoonPlayer.dist"
if (Test-Path $appDir) {
    $exePath = Join-Path $appDir "GoonPlayer.exe"
    if (Test-Path $exePath) {
        Write-Host "Main executable:" -ForegroundColor Yellow
        $exeSize = (Get-Item $exePath).Length / 1MB
        Write-Host "  GoonPlayer.exe ($([math]::Round($exeSize, 2)) MB)" -ForegroundColor Gray
    }

    Write-Host ""
    Write-Host "Dependency files:" -ForegroundColor Yellow
    $files = Get-ChildItem -Path $appDir -File -Recurse | Where-Object { $_.Name -ne "GoonPlayer.exe" }
    Write-Host "  Total files: $($files.Count)" -ForegroundColor Gray
    $totalSize = ($files | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "  Total size: $([math]::Round($totalSize, 2)) MB" -ForegroundColor Gray
}

Write-Host ""
Read-Host "Press Enter to exit"

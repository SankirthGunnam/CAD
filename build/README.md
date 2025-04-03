# RF CAD Build Process

This directory contains scripts and configuration files for building the RF CAD application.

## Prerequisites

- Python 3.8 or higher
- PyInstaller (installed via requirements.txt)
- NSIS (Nullsoft Scriptable Install System) for creating the installer

## Files

- `rf_cad.spec`: PyInstaller specification file
- `installer.nsi`: NSIS script for creating the installer
- `build.bat`: Batch script to automate the build process

## Building the Application

### Option 1: Automated Build

Run the `build.bat` script to automatically:
1. Install requirements
2. Create the executable with PyInstaller
3. Create the installer with NSIS (if NSIS is installed)

```
cd build
build.bat
```

### Option 2: Manual Build

#### Step 1: Install Requirements

```
pip install -r ../requirements.txt
```

#### Step 2: Create Executable with PyInstaller

```
pyinstaller --clean rf_cad.spec
```

#### Step 3: Create Installer with NSIS

```
makensis installer.nsi
```

## Output Files

- Executable: `dist/RF_CAD.exe`
- Installer: `RF_CAD_Setup_1.0.0.exe`

## Customizing the Build

### Changing the Application Version

Edit the `PRODUCT_VERSION` variable in `installer.nsi`.

### Adding Additional Files

To include additional files in the executable, add them to the `datas` list in `rf_cad.spec`.

### Changing the Application Icon

Replace the icon file at `../gui/assets/icon.ico` with your own icon. 
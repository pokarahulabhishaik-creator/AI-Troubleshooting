# Troubleshooting Python Virtual Environment Problems

## Overview
Virtual environment errors manifest as missing dependencies, version conflicts, script execution permission blocks in PowerShell, or the shell pointing to the global operating system Python instead of the isolated project virtual environment.

## Common Error Signatures
- `activate : File C:\...\activate.ps1 cannot be loaded because running scripts is disabled on this system.`
- `The term 'uvicorn' is not recognized as the name of a cmdlet, function, script file, or operable program.`
- `Requirement already satisfied in c:\users\...\appdata\local\programs\python...` while the script still crashes with `ModuleNotFoundError`.

## Common Causes
1. **PowerShell ExecutionPolicy Restriction**: By default, Windows PowerShell restricts running unverified local `.ps1` scripts.
2. **Inactivated Virtual Environment**: Installing libraries via `pip` while the environment is not active puts libraries into global site-packages or user directories.
3. **Multiple Python Versions**: Having Python 3.10, 3.11, and 3.12 installed simultaneously where `python` defaults to a different version than the venv base interpreter.
4. **Corrupted or Moved Virtual Environment**: Moving the project folder after creating `venv` breaks hardcoded absolute paths inside `venv/pyvenv.cfg` and `venv/Scripts/python.exe`.

## Step-by-Step Resolution

### 1. Fix Windows PowerShell Script Execution Policy
If PowerShell blocks activating the environment:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Then rerun:
```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Verify Interpreter Path
Check which interpreter is active:
```powershell
# Windows PowerShell
(Get-Command python).Source
```
The output should point inside `d:\AI-Troubleshooting\venv\Scripts\python.exe`. If it points to `C:\Users\...\AppData\Local\Programs\Python`, the venv is not active.

### 3. Recreating a Clean Virtual Environment
If paths are corrupted or packages are mismatched:
```powershell
# Deactivate if active
deactivate

# Remove old environment
Remove-Item -Recurse -Force venv

# Create new environment
python -m venv venv

# Activate
.\venv\Scripts\Activate.ps1

# Upgrade pip and reinstall
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Verification Steps
Verify the installed packages in the virtual environment:
```powershell
pip list
python -c "import sys; print(sys.prefix)"
```
Ensure `sys.prefix` points to your project's `venv` folder.

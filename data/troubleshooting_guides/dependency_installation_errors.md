# Troubleshooting Dependency and Pip Installation Errors

## Overview
Installing Python packages can trigger compile failures when C/C++ build wheels are required, SSL handshake failures behind corporate proxies, or dependency version resolution conflicts.

## Common Error Signatures
- `error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools"`
- `pip._vendor.resolvelib.resolvers.ResolutionImpossible`
- `ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed`
- `ERROR: Could not find a version that satisfies the requirement`

## Common Causes
1. **Missing C++ Compilers**: Some Python packages (or older versions of libraries) provide source distributions (`sdist`) instead of pre-compiled wheels for newer Python versions (such as Python 3.12).
2. **Pip Version Incompatibility**: Older pip releases lack support for modern wheels or resolution algorithms.
3. **Conflicting Version Constraints**: Pinned version requirements in `requirements.txt` that are incompatible with each other (e.g., package A requires `pydantic<2` while package B requires `pydantic>=2`).
4. **Network and SSL Inspection**: Corporate firewalls or missing root certificate authorities intercepting HTTPS requests from pip.

## Step-by-Step Resolution

### 1. Upgrade Pip First
Always ensure your package installer is current:
```bash
python -m pip install --upgrade pip setuptools wheel
```

### 2. Resolving C++ Build Tools Requirement
- When possible, prefer pre-compiled binary packages:
  ```bash
  pip install <package> --only-binary :all:
  ```
- Or download the Microsoft C++ Build Tools from Microsoft Visual Studio official tools, selecting "Desktop development with C++".

### 3. Resolving ResolutionImpossible Conflicts
- Inspect `requirements.txt` and relax overly strict version pins (e.g., use `>=` instead of `==`).
- Run pip in dry-run mode to inspect dependency trees:
  ```bash
  pip install --dry-run -r requirements.txt
  ```

### 4. Handling SSL Certificate Verification Issues
If operating behind a custom certificate or corporate proxy:
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

## Verification Steps
Verify that all dependencies satisfy requirements without broken dependencies:
```bash
pip check
```
If no output is printed, all dependencies in the environment are satisfied and conflict-free.

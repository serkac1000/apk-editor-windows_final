# Code Signing Guide for APK Editor

## Why Code Signing Helps

Code signing reduces antivirus false positives by:
- Establishing software authenticity
- Providing a trusted publisher identity
- Reducing security warnings

## Self-Signing Options

### Option 1: PowerShell Self-Signed Certificate (Free)

```powershell
# Create a self-signed certificate
$cert = New-SelfSignedCertificate -Subject "CN=APK Editor" -Type CodeSigning -CertStoreLocation Cert:\CurrentUser\My

# Export certificate
Export-Certificate -Cert $cert -FilePath "apk-editor-cert.cer"

# Sign your Python files (example)
Set-AuthenticodeSignature -FilePath "main.py" -Certificate $cert
```

### Option 2: Commercial Code Signing Certificate

1. Purchase from providers like:
   - DigiCert
   - Sectigo (formerly Comodo)
   - GlobalSign

2. Follow their signing instructions

## Alternative: Portable Distribution

Create a portable version that doesn't require installation:

```batch
# Create portable structure
mkdir APK-Editor-Portable
copy *.py APK-Editor-Portable\
copy *.bat APK-Editor-Portable\
copy requirements.txt APK-Editor-Portable\
```

## Submission to Antivirus Vendors

If false positives persist, submit to:
- Microsoft Defender: https://www.microsoft.com/wdsi/filesubmission
- VirusTotal: https://www.virustotal.com/
- Individual antivirus vendor portals

## Best Practices

1. **Use virtual environments** for Python dependencies
2. **Minimize file system operations** outside app directory
3. **Add clear documentation** about the tool's purpose
4. **Provide source code access** for transparency
5. **Use official tool repositories** when possible
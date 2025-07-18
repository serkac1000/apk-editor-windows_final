# Antivirus Configuration Guide

## Why is APK Editor flagged as a virus?

APK Editor is flagged by antivirus software because it:
- Modifies executable files (APK files)
- Downloads external tools (APKTool)
- Creates temporary files and directories
- Performs operations similar to legitimate development tools

This is a **false positive** - the software is safe for APK development purposes.

## How to Fix Antivirus Warnings

### Windows Defender
1. Open Windows Security (Windows Defender)
2. Go to "Virus & threat protection"
3. Click "Manage settings" under "Virus & threat protection settings"
4. Click "Add or remove exclusions"
5. Add these exclusions:
   - **Folder**: Your APK Editor installation directory
   - **Folder**: `%TEMP%\apk-editor-*` (for temporary files)
   - **Process**: `python.exe` (when running APK Editor)

### Other Antivirus Software
- **Avast/AVG**: Add to exceptions in Settings > General > Exceptions
- **Norton**: Add to exclusions in Settings > Antivirus > Scans and Risks > Exclusions
- **McAfee**: Add to exclusions in Real-Time Scanning settings
- **Kaspersky**: Add to exclusions in Settings > Additional > Threats and Exclusions

## Safe Usage Guidelines

1. **Download from trusted sources only**
2. **Scan downloaded APK files** before editing
3. **Use only for legitimate development purposes**
4. **Keep your antivirus updated** but maintain exclusions
5. **Don't edit APKs from unknown sources**

## Verification

To verify the software is legitimate:
1. Check the source code (it's open source)
2. Scan individual files with multiple antivirus engines
3. Use in a virtual machine if concerned
4. Monitor network activity during use

## Support

If you continue having issues:
1. Check your antivirus documentation for exclusion setup
2. Contact your antivirus vendor about false positives
3. Consider using Windows Defender only for development
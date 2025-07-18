from app import app
import os

def print_startup_info():
    """Print startup information and antivirus notice"""
    print("=" * 60)
    print("APK Editor - Web-based APK Modification Tool")
    print("=" * 60)
    print()
    print("🔒 ANTIVIRUS NOTICE:")
    print("   If flagged as virus, it's a FALSE POSITIVE")
    print("   APK editors are flagged because they modify executable files")
    print("   See ANTIVIRUS_GUIDE.md for exclusion instructions")
    print()
    print("🌐 Server starting at: http://localhost:5000")
    print("📁 Working directory:", os.getcwd())
    print("🛠️  Tool purpose: Legitimate APK development and modification")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()

if __name__ == '__main__':
    print_startup_info()
    app.run(debug=True, host='0.0.0.0', port=5000)

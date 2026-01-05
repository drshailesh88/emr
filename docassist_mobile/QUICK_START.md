# DocAssist Mobile - Quick Start Guide

Get DocAssist Mobile running on Android/iOS in under 10 minutes.

---

## Prerequisites (5 minutes)

### 1. Install Python 3.11+

**Check version**:
```bash
python3 --version  # Should show 3.11 or higher
```

**Install if needed**:
- macOS: `brew install python@3.11`
- Linux: `sudo apt install python3.11`
- Windows: Download from python.org

### 2. Install Flet

```bash
pip install flet>=0.25.0
```

**Verify**:
```bash
flet --version
```

### 3. Install Dependencies

```bash
cd /home/user/emr/docassist_mobile
pip install -r requirements.txt
```

---

## Quick Test (2 minutes)

### Test in Desktop Mode

Before building for mobile, verify the app works:

```bash
python main.py
```

Or run the full UI test suite:

```bash
python test_mobile_ui.py
```

You should see the mobile UI in a desktop window.

---

## Build for Android (3 minutes)

### 1. Create Placeholder Assets

```bash
python create_placeholder_assets.py
```

This creates basic app icon and splash screen for testing.

### 2. Build APK

**Quick build**:
```bash
./build_android.sh
```

**Output**: `build/apk/DocAssist.apk`

### 3. Install to Device

**Via USB**:
```bash
adb install build/apk/DocAssist.apk
```

**Or transfer APK to device and install manually**

---

## Build for iOS (macOS only)

### 1. Set Team ID

```bash
export IOS_TEAM_ID="YOUR_APPLE_TEAM_ID"
```

Find Team ID at: https://developer.apple.com/account

### 2. Create Assets

```bash
python create_placeholder_assets.py
```

### 3. Build IPA

```bash
./build_ios.sh
```

**Output**: `build/ipa/DocAssist.ipa`

### 4. Install to Device

- Open Xcode → Window → Devices and Simulators
- Drag `build/ipa/DocAssist.ipa` to your device

---

## Troubleshooting

### "Flet not found"

```bash
pip install flet --upgrade
```

### "ANDROID_HOME not set" (Android)

```bash
# Install Android Studio first
export ANDROID_HOME=$HOME/Android/Sdk
```

### "No iOS team" (iOS)

1. Get Team ID from developer.apple.com
2. Set environment variable: `export IOS_TEAM_ID="YOUR_ID"`

### "Build failed"

Check full logs:
```bash
./build_android.sh --verbose
# or
./build_ios.sh --verbose
```

---

## Next Steps

### For Testing

1. **Test on emulator**:
   - Android: Android Studio → Device Manager
   - iOS: Xcode → Open Simulator

2. **Test on physical device**:
   - Enable developer mode
   - Install APK/IPA
   - Check all features work offline

### For Production

1. **Replace placeholder assets**:
   - Create professional app icon (1024x1024)
   - Design branded splash screen (2048x2048)
   - See `assets/icons/README.md` and `assets/splash/README.md`

2. **Configure for release**:
   - Update version in `pyproject.toml`
   - Create Android keystore (for signing)
   - Configure iOS provisioning profiles

3. **Build release version**:
   ```bash
   ./build_android.sh --release
   ./build_ios.sh --release
   ```

4. **Distribute**:
   - Google Play Store (Android)
   - Apple App Store (iOS)
   - See `BUILD_GUIDE.md` for full instructions

---

## Complete Documentation

- **BUILD_GUIDE.md**: Comprehensive build instructions
- **README.md**: Full project documentation
- **MOBILE_APP_COMPLETE.md**: Architecture and features
- **INTEGRATION_CHECKLIST.md**: Integration testing

---

## Support

**Issues**: tech@docassist.app

**Community**: Discord (link in desktop app)

---

**You're ready to build! 🚀**

Run `./build_android.sh` to create your first APK.

# Pre-Build Checklist

Use this checklist before building APK/IPA to ensure everything is ready.

---

## Environment Setup

### Prerequisites Installed

- [ ] Python 3.11+ installed
  ```bash
  python3 --version  # Should show 3.11+
  ```

- [ ] Flet 0.25.0+ installed
  ```bash
  flet --version
  pip show flet | grep Version
  ```

- [ ] Project dependencies installed
  ```bash
  cd /home/user/emr/docassist_mobile
  pip install -r requirements.txt
  ```

### Android Prerequisites (if building APK)

- [ ] Java JDK 17+ installed
  ```bash
  java -version  # Should show 17+
  ```

- [ ] Android Studio installed
  - Download: https://developer.android.com/studio

- [ ] Android SDK configured
  ```bash
  echo $ANDROID_HOME  # Should show SDK path
  adb --version      # Should work
  ```

- [ ] Environment variables set
  ```bash
  # Add to ~/.bashrc or ~/.zshrc
  export ANDROID_HOME=$HOME/Android/Sdk
  export PATH=$PATH:$ANDROID_HOME/platform-tools
  ```

### iOS Prerequisites (if building IPA, macOS only)

- [ ] macOS 12.0+ running
  ```bash
  sw_vers  # Check macOS version
  ```

- [ ] Xcode 14.0+ installed
  ```bash
  xcodebuild -version  # Should show 14+
  ```

- [ ] Xcode Command Line Tools installed
  ```bash
  xcode-select -p  # Should show path
  ```

- [ ] CocoaPods installed
  ```bash
  pod --version
  ```

- [ ] Apple Developer Team ID obtained
  - Get from: https://developer.apple.com/account
  - Set: `export IOS_TEAM_ID="YOUR_TEAM_ID"`

---

## Project Configuration

### Files Present

- [ ] `main.py` exists and is up to date
- [ ] `pyproject.toml` exists with correct configuration
- [ ] `requirements.txt` exists
- [ ] `build_android.sh` exists and is executable
- [ ] `build_ios.sh` exists and is executable

**Verify**:
```bash
ls -lh main.py pyproject.toml requirements.txt
ls -lh build_android.sh build_ios.sh
```

### Source Code Complete

- [ ] All screens implemented in `src/ui/screens/`
- [ ] All components implemented in `src/ui/components/`
- [ ] All services implemented in `src/services/`
- [ ] Database schemas defined in `src/models/`

**Verify**:
```bash
ls src/ui/screens/*.py | wc -l   # Should show ~11 files
ls src/ui/components/*.py | wc -l # Should show ~15 files
ls src/services/*.py | wc -l      # Should show ~10 files
```

---

## Assets Preparation

### App Icon

- [ ] Icon created or placeholder generated
  - File: `assets/icons/icon.png`
  - Size: 1024x1024 pixels
  - Format: PNG

**Create placeholder**:
```bash
# Requires Pillow: pip install Pillow
python create_placeholder_assets.py
```

**Verify**:
```bash
ls -lh assets/icons/icon.png
file assets/icons/icon.png  # Should show PNG, 1024x1024
```

### Splash Screen

- [ ] Splash screen created or placeholder generated
  - File: `assets/splash/splash.png`
  - Size: 2048x2048 pixels
  - Format: PNG

**Create placeholder**:
```bash
python create_placeholder_assets.py
```

**Verify**:
```bash
ls -lh assets/splash/splash.png
file assets/splash/splash.png  # Should show PNG, 2048x2048
```

### Optional: Android Adaptive Icon

- [ ] Adaptive foreground created (optional)
  - File: `assets/icons/adaptive_foreground.png`
  - Size: 1024x1024 pixels with transparency

---

## Code Quality

### Linting & Formatting

- [ ] No syntax errors
  ```bash
  python -m py_compile main.py
  python -m py_compile src/ui/mobile_app.py
  ```

- [ ] Import statements work
  ```bash
  python -c "from src.ui.mobile_app import DocAssistMobile"
  ```

### Testing

- [ ] Desktop mode works
  ```bash
  python main.py  # Should open window
  ```

- [ ] UI test suite passes
  ```bash
  python test_mobile_ui.py  # Should show all screens
  ```

- [ ] No runtime errors in console

---

## Configuration Review

### pyproject.toml

- [ ] App name is correct: "DocAssist"
- [ ] Version number is set: "1.0.0"
- [ ] Package name is correct:
  - Android: "app.docassist.mobile"
  - iOS: "app.docassist.mobile"

**Verify**:
```bash
grep "app_name" pyproject.toml
grep "version" pyproject.toml
grep "package_name" pyproject.toml
grep "bundle_id" pyproject.toml
```

### Permissions

- [ ] Android permissions listed in pyproject.toml
  - INTERNET (required)
  - CAMERA (optional)
  - WRITE_EXTERNAL_STORAGE
  - USE_BIOMETRIC
  - VIBRATE

- [ ] iOS permissions listed in pyproject.toml
  - NSCameraUsageDescription
  - NSMicrophoneUsageDescription
  - NSFaceIDUsageDescription

**Verify**:
```bash
grep "permissions" pyproject.toml -A 10
```

---

## Build Scripts

### Android Build Script

- [ ] `build_android.sh` is executable
  ```bash
  ls -l build_android.sh  # Should show 'x' permission
  ```

- [ ] Script runs without errors (dry run)
  ```bash
  bash -n build_android.sh  # Check syntax
  ```

### iOS Build Script

- [ ] `build_ios.sh` is executable
  ```bash
  ls -l build_ios.sh  # Should show 'x' permission
  ```

- [ ] Script runs without errors (dry run)
  ```bash
  bash -n build_ios.sh  # Check syntax
  ```

---

## Security & Legal

### Code Review

- [ ] No hardcoded API keys or secrets
- [ ] No sensitive data in source code
- [ ] No debug logging in production code
- [ ] Error handling for all network calls

**Check for secrets**:
```bash
grep -r "api_key\|password\|secret" src/ --include="*.py"
# Should only find variable names, not actual values
```

### Privacy & Compliance

- [ ] Privacy policy URL configured (if required)
- [ ] Terms of service reviewed
- [ ] Data handling complies with local laws
- [ ] Medical data encryption enabled

---

## Documentation

### User-Facing

- [ ] README.md is up to date
- [ ] App Store description prepared (if publishing)
- [ ] Screenshots captured for stores
- [ ] Release notes written

### Developer-Facing

- [ ] BUILD_GUIDE.md reviewed
- [ ] QUICK_START.md accurate
- [ ] Code comments are clear
- [ ] Architecture documented

---

## Pre-Build Tests

### Smoke Tests

Run these tests before building:

1. **App launches**:
   ```bash
   python main.py  # Should open without errors
   ```

2. **All screens render**:
   ```bash
   python test_mobile_ui.py  # Test all screens
   ```

3. **No import errors**:
   ```bash
   python -c "from src.ui.mobile_app import DocAssistMobile; print('OK')"
   ```

4. **Assets exist**:
   ```bash
   ls assets/icons/icon.png assets/splash/splash.png
   ```

### Expected Results

- ✅ No Python errors
- ✅ No import errors
- ✅ UI renders correctly
- ✅ Assets present and valid

---

## Build Commands

### Android APK

**Debug build** (for testing):
```bash
./build_android.sh
```

**Release build** (for production):
```bash
./build_android.sh --release
```

**Expected output**:
- APK file in `build/apk/`
- Size: 20-50 MB (varies)
- No build errors

### iOS IPA (macOS only)

**Debug build** (for testing):
```bash
export IOS_TEAM_ID="YOUR_TEAM_ID"
./build_ios.sh
```

**Release build** (for production):
```bash
export IOS_TEAM_ID="YOUR_TEAM_ID"
./build_ios.sh --release
```

**Expected output**:
- IPA file in `build/ipa/`
- Size: 30-60 MB (varies)
- No build errors

---

## Post-Build Verification

### APK/IPA Created

- [ ] Build completed without errors
- [ ] APK/IPA file exists
- [ ] File size is reasonable (not 0 bytes, not >100 MB)

**Verify**:
```bash
ls -lh build/apk/*.apk    # Android
ls -lh build/ipa/*.ipa    # iOS
```

### Installation Test

- [ ] APK/IPA installs on device
- [ ] App icon shows correctly
- [ ] Splash screen displays
- [ ] App launches without crashing

### Feature Test

- [ ] Login works
- [ ] Data syncs (if connected)
- [ ] Offline mode works
- [ ] All screens accessible
- [ ] No runtime errors

---

## Common Issues

### Build Fails

**Issue**: "Flet not found"
- **Fix**: `pip install flet --upgrade`

**Issue**: "ANDROID_HOME not set"
- **Fix**: Install Android Studio, set environment variable

**Issue**: "No iOS team found"
- **Fix**: Set `export IOS_TEAM_ID="YOUR_ID"`

### Assets Missing

**Issue**: "Icon not found"
- **Fix**: Run `python create_placeholder_assets.py`

**Issue**: "Pillow not installed"
- **Fix**: `pip install Pillow`

### Runtime Errors

**Issue**: App crashes on startup
- **Fix**: Check logs, rebuild clean build

**Issue**: Database not found
- **Fix**: Login and sync first

---

## Final Checklist

Before submitting to stores:

- [ ] All items in this checklist completed
- [ ] Tested on multiple devices
- [ ] Tested offline functionality
- [ ] Professional assets created (not placeholders)
- [ ] Version number updated
- [ ] Release build tested
- [ ] No known bugs
- [ ] Documentation complete

---

## Ready to Build?

If all checkboxes are ticked:

```bash
# Create assets (if needed)
python create_placeholder_assets.py

# Build for Android
./build_android.sh

# Or build for iOS (macOS only)
export IOS_TEAM_ID="YOUR_TEAM_ID"
./build_ios.sh
```

**Good luck! 🚀**

See `BUILD_GUIDE.md` for detailed instructions.

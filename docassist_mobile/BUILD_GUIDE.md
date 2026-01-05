# DocAssist Mobile - Build Guide

Complete guide to building DocAssist Mobile for Android and iOS.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Setup](#project-setup)
3. [Prepare Assets](#prepare-assets)
4. [Build for Android](#build-for-android)
5. [Build for iOS](#build-for-ios)
6. [Testing](#testing)
7. [Distribution](#distribution)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### All Platforms

**Required**:
- Python 3.11 or later
- Flet 0.25.0 or later
- Git (for version control)

**Install Flet**:
```bash
pip install flet>=0.25.0
```

**Verify Installation**:
```bash
flet --version
python --version
```

### Android Build

**Required**:
- Java Development Kit (JDK) 17+
- Android SDK
- Android Build Tools

**Installation** (via Android Studio - recommended):
1. Download Android Studio: https://developer.android.com/studio
2. Open Android Studio
3. Go to Tools → SDK Manager
4. Install:
   - Android SDK Platform 34 (or latest)
   - Android SDK Build-Tools
   - Android SDK Command-line Tools

**Environment Variables**:
```bash
# Add to ~/.bashrc or ~/.zshrc
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/platform-tools
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin
```

**Verify**:
```bash
adb --version
sdkmanager --list
```

### iOS Build (macOS only)

**Required**:
- macOS 12.0 or later
- Xcode 14.0 or later
- Apple Developer account (for release builds)
- CocoaPods

**Installation**:
1. Install Xcode from Mac App Store
2. Install Xcode Command Line Tools:
   ```bash
   xcode-select --install
   ```
3. Install CocoaPods:
   ```bash
   sudo gem install cocoapods
   ```

**Verify**:
```bash
xcodebuild -version
pod --version
```

---

## Project Setup

### 1. Clone Repository

```bash
cd /home/user/emr/docassist_mobile
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Test Locally (Desktop Mode)

Before building for mobile, test in desktop mode:

```bash
python main.py
```

Or run the UI test suite:

```bash
python test_mobile_ui.py
```

---

## Prepare Assets

### App Icon

**Required**: `assets/icons/icon.png` (1024x1024 px)

**Quick Placeholder**:
```bash
# Using ImageMagick
cd assets/icons
convert -size 1024x1024 xc:'#0066CC' \
        -gravity center -fill white -font Arial-Bold -pointsize 400 \
        -annotate +0+0 'D+' \
        icon.png
```

**Professional Icon**:
- Use Figma, Adobe Illustrator, or similar
- Follow guidelines in `assets/icons/README.md`
- Export as 1024x1024 PNG

### Splash Screen

**Required**: `assets/splash/splash.png` (2048x2048 px)

**Quick Placeholder**:
```bash
# Using ImageMagick
cd assets/splash
convert -size 2048x2048 xc:'#0066CC' \
        -gravity center -fill white \
        -font Arial-Bold -pointsize 120 -annotate +0-200 'DocAssist' \
        -pointsize 60 -annotate +0+200 'Privacy-first EMR' \
        splash.png
```

**Professional Splash**:
- Follow guidelines in `assets/splash/README.md`
- Keep design minimal for fast load times

### Verify Assets

```bash
ls -lh assets/icons/icon.png
ls -lh assets/splash/splash.png
```

Both files should exist and be reasonable sizes (icon: ~50KB, splash: ~200KB).

---

## Build for Android

### Option 1: Quick Build (Recommended)

Use the provided build script:

```bash
./build_android.sh
```

For release build:
```bash
./build_android.sh --release
```

### Option 2: Manual Build

#### Debug Build (for testing)

```bash
flet build apk \
    --org "app.docassist" \
    --project "DocAssist" \
    --verbose
```

#### Release Build (for distribution)

**Step 1: Create Keystore** (first time only)

```bash
keytool -genkey -v \
    -keystore android_keystore.jks \
    -keyalg RSA \
    -keysize 2048 \
    -validity 10000 \
    -alias docassist

# Follow prompts to set password and details
```

**Step 2: Configure Signing**

Create `android_signing.properties`:
```properties
storeFile=../android_keystore.jks
storePassword=YOUR_STORE_PASSWORD
keyAlias=docassist
keyPassword=YOUR_KEY_PASSWORD
```

**Step 3: Build Release APK**

```bash
flet build apk \
    --org "app.docassist" \
    --project "DocAssist" \
    --build-number $(date +%s) \
    --verbose
```

### Output Location

```bash
build/apk/DocAssist.apk
```

### Install to Device

**Via USB**:
```bash
# Enable USB debugging on device
adb devices  # Verify device connected
adb install build/apk/DocAssist.apk
```

**Via File Transfer**:
1. Copy `build/apk/DocAssist.apk` to device
2. Open file manager on device
3. Tap APK to install
4. Allow installation from unknown sources (if prompted)

---

## Build for iOS

### Option 1: Quick Build (Recommended)

Use the provided build script:

```bash
./build_ios.sh
```

For release build:
```bash
./build_ios.sh --release
```

### Option 2: Manual Build

#### Prerequisites

**Step 1: Set Team ID**

Find your Apple Developer Team ID:
1. Go to https://developer.apple.com/account
2. Click on "Membership" in sidebar
3. Copy "Team ID"

Set environment variable:
```bash
export IOS_TEAM_ID="YOUR_TEAM_ID"
```

**Step 2: Update pyproject.toml**

```toml
[tool.flet.ios]
bundle_id = "app.docassist.mobile"
team_id = "YOUR_TEAM_ID"
```

#### Debug Build (for testing)

```bash
flet build ipa \
    --org "app.docassist" \
    --project "DocAssist" \
    --team "$IOS_TEAM_ID" \
    --verbose
```

#### Release Build (for App Store)

**Step 1: Configure Code Signing**

In Xcode:
1. Open `build/ios/Runner.xcworkspace`
2. Select "Runner" project
3. Go to "Signing & Capabilities"
4. Select your Team
5. Choose provisioning profile

**Step 2: Archive Build**

```bash
flet build ipa \
    --org "app.docassist" \
    --project "DocAssist" \
    --build-number $(date +%s) \
    --team "$IOS_TEAM_ID" \
    --verbose
```

### Output Location

```bash
build/ipa/DocAssist.ipa
```

### Install to Device

**Via Xcode**:
1. Open Xcode
2. Window → Devices and Simulators
3. Select your device
4. Drag `DocAssist.ipa` to device

**Via TestFlight**:
1. Upload to App Store Connect
2. Add to TestFlight
3. Invite testers via email

---

## Testing

### 1. Desktop Testing (Fast)

Test UI without building for mobile:

```bash
python main.py
```

Or run the test suite:

```bash
python test_mobile_ui.py
```

This opens a desktop window showing all screens.

### 2. Android Emulator

**Create Emulator**:
```bash
# Via Android Studio
# Tools → Device Manager → Create Virtual Device
# Choose Pixel 6 with Android 13 (API 33)
```

**Run Emulator**:
```bash
emulator -avd Pixel_6_API_33
```

**Install APK**:
```bash
adb install build/apk/DocAssist.apk
```

### 3. iOS Simulator

**List Simulators**:
```bash
xcrun simctl list devices
```

**Run Simulator**:
```bash
open -a Simulator
```

**Install App**:
```bash
xcrun simctl install booted build/ios/DocAssist.app
```

### 4. Physical Devices

**Android**:
1. Enable Developer Options (tap Build Number 7 times)
2. Enable USB Debugging
3. Connect via USB
4. Run: `adb install build/apk/DocAssist.apk`

**iOS**:
1. Trust development certificate on device
2. Connect via USB or Wi-Fi
3. Install via Xcode Devices window

---

## Distribution

### Google Play Store (Android)

**Step 1: Create App Listing**

1. Go to https://play.google.com/console
2. Create new app
3. Fill in app details:
   - App name: DocAssist
   - Package: app.docassist.mobile
   - Category: Medical
   - Content rating: PEGI 3

**Step 2: Prepare Release**

Required assets:
- App icon (512x512)
- Feature graphic (1024x500)
- Screenshots (at least 2)
- Privacy policy URL
- App description

**Step 3: Upload APK**

1. Production → Releases
2. Create new release
3. Upload `DocAssist.apk` (signed release build)
4. Add release notes
5. Review and publish

**Step 4: Review**

- Google reviews in 1-3 days
- Address any policy violations
- Monitor crash reports

### Apple App Store (iOS)

**Step 1: Create App in App Store Connect**

1. Go to https://appstoreconnect.apple.com
2. My Apps → + → New App
3. Fill in app information:
   - Name: DocAssist
   - Bundle ID: app.docassist.mobile
   - SKU: DOCASSIST-MOBILE-001
   - User Access: Full Access

**Step 2: Prepare Metadata**

Required:
- App icon (1024x1024)
- Screenshots (6.5" and 5.5" displays)
- App preview video (optional)
- Description, keywords, support URL
- Privacy policy URL

**Step 3: Upload Build**

Using Transporter app:
1. Open Transporter
2. Drag `DocAssist.ipa`
3. Click "Deliver"

Or via command line:
```bash
xcrun altool --upload-app \
    --type ios \
    --file build/ipa/DocAssist.ipa \
    --username "your@email.com" \
    --password "@keychain:AC_PASSWORD"
```

**Step 4: Submit for Review**

1. Select uploaded build
2. Fill in App Review Information
3. Export Compliance: No encryption (uses HTTPS only)
4. Submit for review

**Step 5: Review**

- Apple reviews in 24-48 hours
- Address any rejections
- Monitor TestFlight feedback

### Internal Testing (Before Public Release)

**Android - Internal Testing Track**:
1. Create internal testing release
2. Add testers by email
3. Share opt-in URL

**iOS - TestFlight**:
1. Upload build to App Store Connect
2. Add internal testers (up to 100)
3. Or create public beta link

---

## Troubleshooting

### Build Errors

#### "Flet command not found"

**Solution**:
```bash
pip install flet --upgrade
```

#### "ANDROID_HOME not set"

**Solution**:
```bash
export ANDROID_HOME=$HOME/Android/Sdk
# Add to ~/.bashrc for permanent
```

#### "No iOS team found"

**Solution**:
1. Verify Team ID at developer.apple.com
2. Set environment variable: `export IOS_TEAM_ID="YOURTEAMID"`
3. Update `pyproject.toml`

#### "Keystore not found"

**Solution**:
Create keystore first (see Android Release Build section)

### Runtime Errors

#### "Database not found"

**Cause**: App hasn't synced yet

**Solution**: Login and sync first (database created after first sync)

#### "Sync failed"

**Cause**: No internet or invalid credentials

**Solution**:
1. Check internet connection
2. Verify login credentials
3. Check API_BASE_URL in `.env`

#### "App crashes on startup"

**Cause**: Missing dependencies or corrupt build

**Solution**:
1. Clean build: `rm -rf build/`
2. Rebuild: `./build_android.sh` or `./build_ios.sh`
3. Check logs: `adb logcat` (Android) or Console.app (iOS)

### Performance Issues

#### "App is slow"

**Solutions**:
- Enable ProGuard for release builds (Android)
- Optimize images (compress icons/splash)
- Test on physical device (emulators are slower)

#### "Large APK/IPA size"

**Solutions**:
- Remove unused assets
- Enable minification (Android)
- Use WebP instead of PNG for large images
- Split APKs by ABI (Android)

---

## Build Checklist

Before submitting to stores:

### Code
- [ ] All features tested on physical devices
- [ ] No hardcoded API keys or secrets
- [ ] Error handling for all network calls
- [ ] Offline mode works correctly
- [ ] Dark mode tested

### Assets
- [ ] App icon (1024x1024) created
- [ ] Splash screen (2048x2048) created
- [ ] All screenshots captured
- [ ] Feature graphic designed (Play Store)

### Configuration
- [ ] Version number updated in pyproject.toml
- [ ] Build number incremented
- [ ] Privacy policy URL added
- [ ] Support email configured

### Testing
- [ ] Tested on Android 9+ (API 28+)
- [ ] Tested on iOS 13+
- [ ] Tested on low-end devices
- [ ] Tested offline functionality
- [ ] No crashes in last 10 test sessions

### Legal
- [ ] Privacy policy reviewed
- [ ] Terms of service updated
- [ ] GDPR compliance verified (if EU users)
- [ ] Medical data handling compliant with local laws

### Distribution
- [ ] Release APK signed with release keystore
- [ ] iOS build archived with distribution certificate
- [ ] App Store screenshots prepared
- [ ] Release notes written
- [ ] Support contact configured

---

## Continuous Integration (CI/CD)

### GitHub Actions (Example)

Create `.github/workflows/mobile-build.yml`:

```yaml
name: Build Mobile Apps

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build-android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Build APK
        run: |
          pip install flet
          cd docassist_mobile
          ./build_android.sh --release
      - uses: actions/upload-artifact@v3
        with:
          name: android-apk
          path: docassist_mobile/build/apk/*.apk

  build-ios:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Build IPA
        env:
          IOS_TEAM_ID: ${{ secrets.IOS_TEAM_ID }}
        run: |
          pip install flet
          cd docassist_mobile
          ./build_ios.sh --release
      - uses: actions/upload-artifact@v3
        with:
          name: ios-ipa
          path: docassist_mobile/build/ipa/*.ipa
```

---

## Version Management

### Semantic Versioning

Use semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (e.g., 1.0.0 → 2.0.0)
- **MINOR**: New features (e.g., 1.0.0 → 1.1.0)
- **PATCH**: Bug fixes (e.g., 1.0.0 → 1.0.1)

### Update Version

Edit `pyproject.toml`:

```toml
[project]
version = "1.1.0"

[tool.flet]
app_version = "1.1.0"
app_build_number = 2  # Increment for each build
```

### Build Numbers

- Android: `versionCode` (integer, auto-incremented)
- iOS: `CFBundleVersion` (integer, auto-incremented)

Build scripts auto-generate build number from timestamp.

---

## Resources

### Documentation
- Flet docs: https://flet.dev/docs/
- Android developers: https://developer.android.com
- iOS developers: https://developer.apple.com

### Tools
- Android Studio: https://developer.android.com/studio
- Xcode: https://developer.apple.com/xcode
- Transporter (iOS): https://apps.apple.com/app/transporter/id1450874784

### Support
- DocAssist docs: See README.md
- Report issues: tech@docassist.app
- Community: Discord (link in desktop app)

---

**Built with ❤️ for Indian doctors**

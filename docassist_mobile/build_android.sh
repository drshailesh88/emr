#!/bin/bash
# Build Android APK for DocAssist Mobile
# Usage: ./build_android.sh [--release|--debug]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}DocAssist Mobile - Android Build${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if flet is installed
if ! command -v flet &> /dev/null; then
    echo -e "${RED}Error: Flet is not installed${NC}"
    echo "Install with: pip install flet"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ $(echo "$PYTHON_VERSION < 3.11" | bc) -eq 1 ]]; then
    echo -e "${RED}Error: Python 3.11+ required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

# Build type (default: debug)
BUILD_TYPE=${1:-debug}

echo -e "${YELLOW}Build type: $BUILD_TYPE${NC}"
echo ""

# Check for required assets
echo "Checking assets..."
if [ ! -f "assets/icons/icon.png" ]; then
    echo -e "${YELLOW}Warning: App icon not found at assets/icons/icon.png${NC}"
    echo "Using default Flet icon"
fi

if [ ! -f "assets/splash/splash.png" ]; then
    echo -e "${YELLOW}Warning: Splash screen not found at assets/splash/splash.png${NC}"
    echo "Using default splash screen"
fi

echo ""
echo "Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "Building APK..."
echo ""

# Build based on type
if [ "$BUILD_TYPE" = "release" ]; then
    echo -e "${YELLOW}Building RELEASE APK...${NC}"
    echo -e "${YELLOW}Note: Requires keystore for signing${NC}"
    echo ""

    # Check for keystore
    if [ ! -f "android_keystore.jks" ]; then
        echo -e "${RED}Error: Keystore not found${NC}"
        echo "Create one with:"
        echo "  keytool -genkey -v -keystore android_keystore.jks \\"
        echo "          -keyalg RSA -keysize 2048 -validity 10000 \\"
        echo "          -alias docassist"
        exit 1
    fi

    flet build apk \
        --org "app.docassist" \
        --project "DocAssist" \
        --build-number $(date +%s) \
        --verbose
else
    echo -e "${YELLOW}Building DEBUG APK...${NC}"
    echo ""

    flet build apk \
        --org "app.docassist" \
        --project "DocAssist" \
        --verbose
fi

# Check if build succeeded
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ Build successful!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    # Find the APK
    APK_PATH=$(find build -name "*.apk" | head -n 1)

    if [ -n "$APK_PATH" ]; then
        APK_SIZE=$(du -h "$APK_PATH" | cut -f1)
        echo "APK location: $APK_PATH"
        echo "APK size: $APK_SIZE"
        echo ""
        echo "Install with:"
        echo "  adb install $APK_PATH"
        echo ""
        echo "Or transfer to device and install manually"
    fi
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}✗ Build failed${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi

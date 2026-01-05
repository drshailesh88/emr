#!/bin/bash
# Build iOS IPA for DocAssist Mobile
# Usage: ./build_ios.sh [--release|--debug]
# Requirements: macOS with Xcode installed

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}DocAssist Mobile - iOS Build${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}Error: iOS builds require macOS${NC}"
    exit 1
fi

# Check if Xcode is installed
if ! command -v xcodebuild &> /dev/null; then
    echo -e "${RED}Error: Xcode is not installed${NC}"
    echo "Install from Mac App Store"
    exit 1
fi

# Check if flet is installed
if ! command -v flet &> /dev/null; then
    echo -e "${RED}Error: Flet is not installed${NC}"
    echo "Install with: pip install flet"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.11"

if [[ $(echo "$PYTHON_VERSION < $REQUIRED_VERSION" | bc) -eq 1 ]]; then
    echo -e "${RED}Error: Python $REQUIRED_VERSION+ required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

# Build type (default: debug)
BUILD_TYPE=${1:-debug}

echo -e "${YELLOW}Build type: $BUILD_TYPE${NC}"
echo ""

# Check for Team ID (required for iOS)
if [ -z "$IOS_TEAM_ID" ]; then
    echo -e "${YELLOW}Warning: IOS_TEAM_ID environment variable not set${NC}"
    echo "Set with: export IOS_TEAM_ID='YOUR_TEAM_ID'"
    echo "Find your Team ID at: https://developer.apple.com/account"
    echo ""
    read -p "Enter Team ID (or press Enter to skip): " TEAM_ID_INPUT

    if [ -n "$TEAM_ID_INPUT" ]; then
        export IOS_TEAM_ID="$TEAM_ID_INPUT"
    else
        echo -e "${YELLOW}Continuing without Team ID (build may fail)${NC}"
    fi
fi

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
echo "Building IPA..."
echo ""

# Build based on type
if [ "$BUILD_TYPE" = "release" ]; then
    echo -e "${YELLOW}Building RELEASE IPA...${NC}"
    echo -e "${YELLOW}Note: Requires Apple Developer account and provisioning profile${NC}"
    echo ""

    flet build ipa \
        --org "app.docassist" \
        --project "DocAssist" \
        --build-number $(date +%s) \
        --team "$IOS_TEAM_ID" \
        --verbose
else
    echo -e "${YELLOW}Building DEBUG IPA...${NC}"
    echo ""

    flet build ipa \
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

    # Find the IPA
    IPA_PATH=$(find build -name "*.ipa" | head -n 1)

    if [ -n "$IPA_PATH" ]; then
        IPA_SIZE=$(du -h "$IPA_PATH" | cut -f1)
        echo "IPA location: $IPA_PATH"
        echo "IPA size: $IPA_SIZE"
        echo ""
        echo "Next steps:"
        echo "1. Test with TestFlight:"
        echo "   - Upload to App Store Connect"
        echo "   - Add to TestFlight group"
        echo ""
        echo "2. Install to device via Xcode:"
        echo "   - Open Xcode > Window > Devices and Simulators"
        echo "   - Drag $IPA_PATH to device"
        echo ""
        echo "3. Submit to App Store:"
        echo "   - Use Transporter app or App Store Connect"
    fi
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}✗ Build failed${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "Common issues:"
    echo "1. Team ID not set or invalid"
    echo "2. Provisioning profile missing"
    echo "3. Code signing certificate not installed"
    echo ""
    echo "Check Xcode > Preferences > Accounts"
    exit 1
fi

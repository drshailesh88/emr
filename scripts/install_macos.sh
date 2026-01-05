#!/bin/bash
# DocAssist EMR - macOS Installation Script
# Bash script for macOS setup

set -e  # Exit on error

# Script configuration
APP_NAME="DocAssist"
APP_VERSION="1.0.0"
REQUIRED_PYTHON_VERSION="3.11"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${CYAN}→ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_banner() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  DocAssist EMR - macOS Installer${NC}"
    echo -e "${CYAN}  Version $APP_VERSION${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
    echo ""
}

# Check system requirements
check_system_requirements() {
    print_info "Checking system requirements..."

    # Check macOS version
    macos_version=$(sw_vers -productVersion)
    macos_major=$(echo "$macos_version" | cut -d '.' -f 1)

    if [ "$macos_major" -lt 12 ]; then
        print_error "macOS 12 (Monterey) or later is required. You have macOS $macos_version"
        exit 1
    fi
    print_success "macOS version: $macos_version (OK)"

    # Check Python
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version 2>&1 | cut -d ' ' -f 2)
        print_success "Python version: $python_version"

        # Check minimum version
        python_major=$(echo "$python_version" | cut -d '.' -f 1)
        python_minor=$(echo "$python_version" | cut -d '.' -f 2)

        if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 11 ]); then
            print_warning "Python $REQUIRED_PYTHON_VERSION or later is recommended. You have $python_version"
        fi
    else
        print_error "Python 3 is not installed"
        print_info "Install with: brew install python@3.11"
        print_info "Or download from: https://www.python.org/downloads/"
        exit 1
    fi

    # Check available disk space
    free_space=$(df -H "$HOME" | awk 'NR==2 {print $4}' | sed 's/G//')
    if (( $(echo "$free_space < 5" | bc -l) )); then
        print_warning "Low disk space: ${free_space}GB free. At least 5 GB recommended."
    else
        print_success "Disk space: ${free_space}GB free (OK)"
    fi

    # Check RAM
    ram_gb=$(sysctl -n hw.memsize | awk '{print $0/1073741824}')
    ram_gb_int=$(printf "%.0f" "$ram_gb")
    print_success "RAM: ${ram_gb_int} GB"

    if [ "$ram_gb_int" -lt 4 ]; then
        print_warning "Low RAM: ${ram_gb_int} GB. At least 4 GB recommended for LLM features."
    fi

    # Check for Homebrew (optional but recommended)
    if command -v brew &> /dev/null; then
        print_success "Homebrew is installed"
    else
        print_warning "Homebrew is not installed (optional but recommended)"
        print_info "Install from: https://brew.sh"
    fi

    echo ""
}

# Install Python dependencies
install_python_dependencies() {
    print_info "Installing Python dependencies..."

    # Get script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

    # Check if requirements.txt exists
    REQUIREMENTS_FILE="$PROJECT_DIR/requirements.txt"

    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        print_error "requirements.txt not found at: $REQUIREMENTS_FILE"
        exit 1
    fi

    # Upgrade pip
    python3 -m pip install --upgrade pip

    # Install dependencies
    if python3 -m pip install -r "$REQUIREMENTS_FILE"; then
        print_success "Python dependencies installed"
    else
        print_error "Failed to install Python dependencies"
        exit 1
    fi

    echo ""
}

# Create application directories
create_app_directories() {
    print_info "Creating application directories..."

    # Data directory: ~/Library/Application Support/DocAssist
    DATA_DIR="$HOME/Library/Application Support/$APP_NAME"
    if [ ! -d "$DATA_DIR" ]; then
        mkdir -p "$DATA_DIR"
        print_success "Created data directory: $DATA_DIR"
    else
        print_success "Data directory exists: $DATA_DIR"
    fi

    # Config directory: ~/Library/Preferences/DocAssist
    CONFIG_DIR="$HOME/Library/Preferences/$APP_NAME"
    if [ ! -d "$CONFIG_DIR" ]; then
        mkdir -p "$CONFIG_DIR"
        print_success "Created config directory: $CONFIG_DIR"
    else
        print_success "Config directory exists: $CONFIG_DIR"
    fi

    # Cache directory: ~/Library/Caches/DocAssist
    CACHE_DIR="$HOME/Library/Caches/$APP_NAME"
    if [ ! -d "$CACHE_DIR" ]; then
        mkdir -p "$CACHE_DIR"
        print_success "Created cache directory: $CACHE_DIR"
    else
        print_success "Cache directory exists: $CACHE_DIR"
    fi

    # Database directory
    DB_DIR="$DATA_DIR/data"
    if [ ! -d "$DB_DIR" ]; then
        mkdir -p "$DB_DIR"
        print_success "Created database directory: $DB_DIR"
    fi

    # Vector store directory
    CHROMA_DIR="$DB_DIR/chroma"
    if [ ! -d "$CHROMA_DIR" ]; then
        mkdir -p "$CHROMA_DIR"
        print_success "Created vector store directory: $CHROMA_DIR"
    fi

    # Set proper permissions
    chmod 755 "$DATA_DIR"
    chmod 755 "$CONFIG_DIR"
    chmod 755 "$CACHE_DIR"

    echo ""
}

# Create application symlink
create_app_symlink() {
    print_info "Creating application symlink..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
    MAIN_PY="$PROJECT_DIR/main.py"

    if [ ! -f "$MAIN_PY" ]; then
        print_warning "main.py not found at: $MAIN_PY. Skipping symlink creation."
        return
    fi

    # Create /Applications symlink (requires sudo for /Applications)
    # Or create user Applications symlink
    USER_APPS="$HOME/Applications"
    if [ ! -d "$USER_APPS" ]; then
        mkdir -p "$USER_APPS"
    fi

    # Create wrapper script
    WRAPPER_SCRIPT="$USER_APPS/DocAssist"

    cat > "$WRAPPER_SCRIPT" << EOF
#!/bin/bash
# DocAssist EMR Launcher
cd "$PROJECT_DIR"
exec python3 "$MAIN_PY" "\$@"
EOF

    chmod +x "$WRAPPER_SCRIPT"
    print_success "Created launcher: $WRAPPER_SCRIPT"

    # Offer to add to system Applications (requires sudo)
    if [ "$EUID" -eq 0 ] || sudo -n true 2>/dev/null; then
        print_info "Creating symlink in /Applications (requires sudo)..."

        if sudo ln -sf "$WRAPPER_SCRIPT" "/Applications/DocAssist" 2>/dev/null; then
            print_success "Created symlink in /Applications"
        else
            print_warning "Could not create symlink in /Applications (permission denied)"
        fi
    fi

    echo ""
}

# Install Ollama
install_ollama() {
    if [ "$INSTALL_OLLAMA" != "true" ]; then
        return
    fi

    print_info "Installing Ollama..."

    # Check if Ollama is already installed
    if command -v ollama &> /dev/null; then
        ollama_version=$(ollama --version 2>&1)
        print_success "Ollama is already installed: $ollama_version"
        return
    fi

    # Install via Homebrew if available
    if command -v brew &> /dev/null; then
        print_info "Installing Ollama via Homebrew..."

        if brew install ollama; then
            print_success "Ollama installed via Homebrew"
            print_info "Start Ollama with: brew services start ollama"
            print_info "Or run manually with: ollama serve"
        else
            print_warning "Failed to install Ollama via Homebrew"
        fi
    else
        # Download and install manually
        print_info "Downloading Ollama installer..."

        OLLAMA_URL="https://ollama.ai/download/Ollama-darwin.zip"
        TEMP_DIR=$(mktemp -d)
        INSTALLER_PATH="$TEMP_DIR/Ollama.zip"

        if curl -L -o "$INSTALLER_PATH" "$OLLAMA_URL"; then
            print_success "Downloaded Ollama"
            print_info "Please install Ollama manually from: $INSTALLER_PATH"
            print_info "Or install via Homebrew: brew install ollama"
        else
            print_warning "Failed to download Ollama"
            print_info "You can manually download from: https://ollama.ai/download"
        fi

        rm -rf "$TEMP_DIR"
    fi

    echo ""
}

# Create .env file
create_env_file() {
    print_info "Checking .env file..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
    ENV_FILE="$PROJECT_DIR/.env"
    ENV_EXAMPLE="$PROJECT_DIR/.env.example"

    if [ -f "$ENV_FILE" ]; then
        print_success ".env file already exists"
    elif [ -f "$ENV_EXAMPLE" ]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        print_success "Created .env file from .env.example"
    else
        print_warning ".env.example not found. Skipping .env creation."
    fi

    echo ""
}

# Create launch agent (optional)
create_launch_agent() {
    if [ "$CREATE_LAUNCH_AGENT" != "true" ]; then
        return
    fi

    print_info "Creating launch agent..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
    MAIN_PY="$PROJECT_DIR/main.py"

    LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
    PLIST_FILE="$LAUNCH_AGENTS_DIR/com.docassist.emr.plist"

    mkdir -p "$LAUNCH_AGENTS_DIR"

    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.docassist.emr</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$MAIN_PY</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>RunAtLoad</key>
    <false/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
EOF

    print_success "Created launch agent: $PLIST_FILE"
    print_info "Load with: launchctl load $PLIST_FILE"
    print_info "Unload with: launchctl unload $PLIST_FILE"

    echo ""
}

# Display post-installation instructions
show_post_install_instructions() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Installation Complete!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}Next Steps:${NC}"
    echo ""
    echo -e "${NC}1. Configure Ollama (if not already done):${NC}"
    echo -e "   ${NC}ollama pull qwen2.5:3b${NC}"
    echo ""
    echo -e "${NC}2. Start DocAssist EMR:${NC}"
    echo -e "   ${NC}python3 main.py${NC}"
    echo -e "   ${NC}OR use: ~/Applications/DocAssist${NC}"
    echo ""
    echo -e "${NC}3. Data locations:${NC}"
    echo -e "   ${NC}Data:   ~/Library/Application Support/$APP_NAME${NC}"
    echo -e "   ${NC}Config: ~/Library/Preferences/$APP_NAME${NC}"
    echo -e "   ${NC}Cache:  ~/Library/Caches/$APP_NAME${NC}"
    echo ""

    if [ "$INSTALL_OLLAMA" == "true" ]; then
        echo -e "${NC}4. Start Ollama:${NC}"
        echo -e "   ${NC}ollama serve${NC}"
        echo -e "   ${NC}OR: brew services start ollama${NC}"
        echo ""
    fi

    echo -e "${NC}For help, visit: https://github.com/docassist/emr${NC}"
    echo ""
}

# Parse command line arguments
INSTALL_OLLAMA="false"
CREATE_LAUNCH_AGENT="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        --install-ollama)
            INSTALL_OLLAMA="true"
            shift
            ;;
        --create-launch-agent)
            CREATE_LAUNCH_AGENT="true"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --install-ollama         Install Ollama via Homebrew"
            echo "  --create-launch-agent    Create macOS launch agent"
            echo "  --help                   Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Main installation flow
main() {
    print_banner

    # Check for root
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root. Some features may install system-wide."
        echo ""
    fi

    # Run installation steps
    check_system_requirements
    install_python_dependencies
    create_app_directories
    create_app_symlink
    install_ollama
    create_env_file
    create_launch_agent

    show_post_install_instructions
}

# Run main function
main "$@"

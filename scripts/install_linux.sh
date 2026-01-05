#!/bin/bash
# DocAssist EMR - Linux Installation Script
# Bash script for Linux setup (Ubuntu 20.04+, Fedora, Arch, etc.)

set -e  # Exit on error

# Script configuration
APP_NAME="DocAssist"
APP_NAME_LOWER="docassist"
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
    echo -e "${CYAN}  DocAssist EMR - Linux Installer${NC}"
    echo -e "${CYAN}  Version $APP_VERSION${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
    echo ""
}

# Detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        DISTRO_VERSION=$VERSION_ID
    else
        DISTRO="unknown"
        DISTRO_VERSION="unknown"
    fi

    print_info "Detected distribution: $DISTRO $DISTRO_VERSION"
}

# Check system requirements
check_system_requirements() {
    print_info "Checking system requirements..."

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

        case $DISTRO in
            ubuntu|debian)
                print_info "Install with: sudo apt install python3 python3-pip"
                ;;
            fedora)
                print_info "Install with: sudo dnf install python3 python3-pip"
                ;;
            arch)
                print_info "Install with: sudo pacman -S python python-pip"
                ;;
            *)
                print_info "Please install Python 3.11 or later"
                ;;
        esac
        exit 1
    fi

    # Check pip
    if command -v pip3 &> /dev/null; then
        print_success "pip3 is installed"
    else
        print_warning "pip3 is not installed"

        case $DISTRO in
            ubuntu|debian)
                print_info "Install with: sudo apt install python3-pip"
                ;;
            fedora)
                print_info "Install with: sudo dnf install python3-pip"
                ;;
            arch)
                print_info "Install with: sudo pacman -S python-pip"
                ;;
        esac
    fi

    # Check available disk space
    free_space=$(df -BG "$HOME" | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$free_space" -lt 5 ]; then
        print_warning "Low disk space: ${free_space}GB free. At least 5 GB recommended."
    else
        print_success "Disk space: ${free_space}GB free (OK)"
    fi

    # Check RAM
    if [ -f /proc/meminfo ]; then
        ram_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        ram_gb=$((ram_kb / 1024 / 1024))
        print_success "RAM: ${ram_gb} GB"

        if [ "$ram_gb" -lt 4 ]; then
            print_warning "Low RAM: ${ram_gb} GB. At least 4 GB recommended for LLM features."
        fi
    fi

    echo ""
}

# Install system dependencies
install_system_dependencies() {
    if [ "$INSTALL_SYSTEM_DEPS" != "true" ]; then
        return
    fi

    print_info "Installing system dependencies..."

    case $DISTRO in
        ubuntu|debian)
            print_info "Installing dependencies via apt..."
            sudo apt update
            sudo apt install -y \
                python3-dev \
                python3-pip \
                build-essential \
                libsqlite3-dev \
                curl \
                git
            print_success "System dependencies installed"
            ;;

        fedora)
            print_info "Installing dependencies via dnf..."
            sudo dnf install -y \
                python3-devel \
                python3-pip \
                gcc \
                gcc-c++ \
                make \
                sqlite-devel \
                curl \
                git
            print_success "System dependencies installed"
            ;;

        arch)
            print_info "Installing dependencies via pacman..."
            sudo pacman -S --noconfirm \
                python \
                python-pip \
                base-devel \
                sqlite \
                curl \
                git
            print_success "System dependencies installed"
            ;;

        *)
            print_warning "Unknown distribution. Please install dependencies manually."
            print_info "Required: python3, pip3, build-essential, sqlite3"
            ;;
    esac

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
    python3 -m pip install --upgrade pip --user

    # Install dependencies
    if python3 -m pip install -r "$REQUIREMENTS_FILE" --user; then
        print_success "Python dependencies installed"
    else
        print_error "Failed to install Python dependencies"
        exit 1
    fi

    echo ""
}

# Create application directories (XDG compliant)
create_app_directories() {
    print_info "Creating application directories (XDG compliant)..."

    # Data directory: ~/.local/share/docassist
    DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/$APP_NAME_LOWER"
    if [ ! -d "$DATA_DIR" ]; then
        mkdir -p "$DATA_DIR"
        chmod 755 "$DATA_DIR"
        print_success "Created data directory: $DATA_DIR"
    else
        print_success "Data directory exists: $DATA_DIR"
    fi

    # Config directory: ~/.config/docassist
    CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/$APP_NAME_LOWER"
    if [ ! -d "$CONFIG_DIR" ]; then
        mkdir -p "$CONFIG_DIR"
        chmod 755 "$CONFIG_DIR"
        print_success "Created config directory: $CONFIG_DIR"
    else
        print_success "Config directory exists: $CONFIG_DIR"
    fi

    # Cache directory: ~/.cache/docassist
    CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/$APP_NAME_LOWER"
    if [ ! -d "$CACHE_DIR" ]; then
        mkdir -p "$CACHE_DIR"
        chmod 755 "$CACHE_DIR"
        print_success "Created cache directory: $CACHE_DIR"
    else
        print_success "Cache directory exists: $CACHE_DIR"
    fi

    # Database directory
    DB_DIR="$DATA_DIR/data"
    if [ ! -d "$DB_DIR" ]; then
        mkdir -p "$DB_DIR"
        chmod 755 "$DB_DIR"
        print_success "Created database directory: $DB_DIR"
    fi

    # Vector store directory
    CHROMA_DIR="$DB_DIR/chroma"
    if [ ! -d "$CHROMA_DIR" ]; then
        mkdir -p "$CHROMA_DIR"
        chmod 755 "$CHROMA_DIR"
        print_success "Created vector store directory: $CHROMA_DIR"
    fi

    echo ""
}

# Create .desktop file
create_desktop_file() {
    print_info "Creating .desktop file..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
    MAIN_PY="$PROJECT_DIR/main.py"

    if [ ! -f "$MAIN_PY" ]; then
        print_warning "main.py not found at: $MAIN_PY. Skipping .desktop file creation."
        return
    fi

    # Desktop file location
    DESKTOP_FILE_DIR="$HOME/.local/share/applications"
    mkdir -p "$DESKTOP_FILE_DIR"

    DESKTOP_FILE="$DESKTOP_FILE_DIR/docassist.desktop"

    # Create .desktop file
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=DocAssist EMR
Comment=Local-First AI-Powered EMR for Indian Doctors
Exec=python3 "$MAIN_PY"
Path=$PROJECT_DIR
Icon=$APP_NAME_LOWER
Terminal=false
Categories=Office;Medical;Science;
Keywords=EMR;medical;healthcare;doctor;patient;
StartupNotify=true
EOF

    chmod 644 "$DESKTOP_FILE"
    print_success "Created .desktop file: $DESKTOP_FILE"

    # Update desktop database
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$DESKTOP_FILE_DIR" 2>/dev/null || true
        print_success "Updated desktop database"
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

    # Download and install Ollama
    print_info "Downloading Ollama installer..."

    if curl -fsSL https://ollama.ai/install.sh | sh; then
        print_success "Ollama installed successfully"
        print_info "Start Ollama with: ollama serve"
    else
        print_warning "Failed to install Ollama"
        print_info "You can manually install from: https://ollama.ai/download"
    fi

    echo ""
}

# Create systemd user service (optional)
create_systemd_service() {
    if [ "$CREATE_SYSTEMD_SERVICE" != "true" ]; then
        return
    fi

    print_info "Creating systemd user service..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
    MAIN_PY="$PROJECT_DIR/main.py"

    SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
    mkdir -p "$SYSTEMD_USER_DIR"

    SERVICE_FILE="$SYSTEMD_USER_DIR/docassist.service"

    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=DocAssist EMR
After=network.target

[Service]
Type=simple
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/python3 $MAIN_PY
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
EOF

    print_success "Created systemd service: $SERVICE_FILE"
    print_info "Enable with: systemctl --user enable docassist"
    print_info "Start with: systemctl --user start docassist"
    print_info "Status: systemctl --user status docassist"

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

# Create launcher script in ~/.local/bin
create_launcher_script() {
    print_info "Creating launcher script..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
    MAIN_PY="$PROJECT_DIR/main.py"

    LOCAL_BIN="$HOME/.local/bin"
    mkdir -p "$LOCAL_BIN"

    LAUNCHER="$LOCAL_BIN/docassist"

    cat > "$LAUNCHER" << EOF
#!/bin/bash
# DocAssist EMR Launcher
cd "$PROJECT_DIR"
exec python3 "$MAIN_PY" "\$@"
EOF

    chmod +x "$LAUNCHER"
    print_success "Created launcher: $LAUNCHER"

    # Check if ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
        print_warning "~/.local/bin is not in your PATH"
        print_info "Add to your ~/.bashrc or ~/.zshrc:"
        print_info "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    else
        print_success "~/.local/bin is in PATH. You can run: docassist"
    fi

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
    echo -e "   ${NC}OR: docassist (if ~/.local/bin is in PATH)${NC}"
    echo -e "   ${NC}OR: Launch from applications menu${NC}"
    echo ""
    echo -e "${NC}3. Data locations (XDG compliant):${NC}"
    echo -e "   ${NC}Data:   ${XDG_DATA_HOME:-$HOME/.local/share}/$APP_NAME_LOWER${NC}"
    echo -e "   ${NC}Config: ${XDG_CONFIG_HOME:-$HOME/.config}/$APP_NAME_LOWER${NC}"
    echo -e "   ${NC}Cache:  ${XDG_CACHE_HOME:-$HOME/.cache}/$APP_NAME_LOWER${NC}"
    echo ""

    if [ "$INSTALL_OLLAMA" == "true" ]; then
        echo -e "${NC}4. Start Ollama:${NC}"
        echo -e "   ${NC}ollama serve${NC}"
        echo ""
    fi

    if [ "$CREATE_SYSTEMD_SERVICE" == "true" ]; then
        echo -e "${NC}5. Manage systemd service:${NC}"
        echo -e "   ${NC}systemctl --user enable docassist${NC}"
        echo -e "   ${NC}systemctl --user start docassist${NC}"
        echo ""
    fi

    echo -e "${NC}For help, visit: https://github.com/docassist/emr${NC}"
    echo ""
}

# Parse command line arguments
INSTALL_OLLAMA="false"
CREATE_SYSTEMD_SERVICE="false"
INSTALL_SYSTEM_DEPS="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        --install-ollama)
            INSTALL_OLLAMA="true"
            shift
            ;;
        --create-systemd-service)
            CREATE_SYSTEMD_SERVICE="true"
            shift
            ;;
        --install-system-deps)
            INSTALL_SYSTEM_DEPS="true"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --install-ollama            Install Ollama"
            echo "  --create-systemd-service    Create systemd user service"
            echo "  --install-system-deps       Install system dependencies (requires sudo)"
            echo "  --help                      Show this help message"
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

    # Detect distribution
    detect_distro

    # Check for root
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root. Installation will be system-wide."
        echo ""
    fi

    # Run installation steps
    check_system_requirements
    install_system_dependencies
    install_python_dependencies
    create_app_directories
    create_desktop_file
    create_launcher_script
    install_ollama
    create_systemd_service
    create_env_file

    show_post_install_instructions
}

# Run main function
main "$@"

#!/bin/bash
# Artha Stock Market Learning Simulator - One-Click Installer
# This script sets up the complete development environment automatically

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
}

# Check Python version
check_python() {
    print_info "Checking Python version..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.12 or higher."
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]); then
        print_error "Python 3.12+ is required. Found: Python $PYTHON_VERSION"
        exit 1
    fi

    print_success "Python $PYTHON_VERSION detected"
}

# Setup or verify virtual environment
setup_venv() {
    print_header "Setting up Virtual Environment"

    if [ -d ".venv" ]; then
        print_info "Virtual environment already exists at .venv"
    else
        print_info "Creating virtual environment..."
        python3 -m venv .venv
        print_success "Virtual environment created"
    fi
}

# Activate virtual environment
activate_venv() {
    print_info "Activating virtual environment..."

    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        print_success "Virtual environment activated"
    else
        print_error "Failed to find virtual environment activation script"
        exit 1
    fi
}

# Ensure pip is available and up to date
ensure_pip() {
    print_header "Ensuring pip is available"

    if ! command -v pip &> /dev/null; then
        print_info "Installing pip..."
        python -m ensurepip --upgrade
    fi

    print_info "Upgrading pip to latest version..."
    pip install --upgrade pip
    print_success "pip is ready"
}

# Install UV package manager
install_uv() {
    print_header "Installing UV Package Manager"

    if command -v uv &> /dev/null; then
        print_info "UV is already installed"
        UV_VERSION=$(uv --version)
        print_success "$UV_VERSION"
    else
        print_info "Installing UV..."
        pip install uv
        print_success "UV installed successfully"
    fi
}

# Install dependencies using UV
install_dependencies() {
    print_header "Installing Project Dependencies"

    if [ -f "requirements.txt" ]; then
        print_info "Installing dependencies from requirements.txt using UV..."

        # Use uv pip install for faster installation
        uv pip install -r requirements.txt

        print_success "All dependencies installed successfully"
    else
        print_error "requirements.txt not found!"
        exit 1
    fi
}

# Verify installation
verify_installation() {
    print_header "Verifying Installation"

    # Check key dependencies
    DEPS=("textual" "dspy" "sqlalchemy" "yfinance" "pandas" "numpy")

    for dep in "${DEPS[@]}"; do
        if python -c "import $dep" 2>/dev/null; then
            print_success "$dep is installed"
        else
            print_warning "$dep might not be installed correctly"
        fi
    done
}

# Setup data directories
setup_directories() {
    print_header "Setting up Data Directories"

    mkdir -p data
    mkdir -p data/cache

    print_success "Data directories created"
}

# Optional: Check for Ollama
check_ollama() {
    print_header "Checking Optional Dependencies"

    if command -v ollama &> /dev/null; then
        print_success "Ollama is installed (AI Coach will work)"

        # Check if qwen3:8b model is available
        if ollama list | grep -q "qwen3:8b"; then
            print_success "qwen3:8b model is available"
        else
            print_warning "qwen3:8b model not found. AI Coach will use fallback mode."
            print_info "To install: ollama pull qwen3:8b"
        fi
    else
        print_warning "Ollama is not installed (AI Coach will use fallback mode)"
        print_info "To install Ollama: curl -fsSL https://ollama.ai/install.sh | sh"
    fi
}

# Print success message and next steps
print_next_steps() {
    print_header "Installation Complete!"

    echo -e "${GREEN}Artha is ready to run!${NC}"
    echo ""
    echo "To start playing:"
    echo "  1. Activate the virtual environment:"
    echo -e "     ${BLUE}source .venv/bin/activate${NC}"
    echo ""
    echo "  2. Run the game:"
    echo -e "     ${BLUE}python -m src.main${NC}"
    echo ""
    echo "Optional - For AI Coach support:"
    echo "  1. Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "  2. Pull model: ollama pull qwen3:8b"
    echo "  3. Start Ollama: ollama serve"
    echo ""
    echo -e "${GREEN}Happy trading! 📈${NC}"
    echo ""
}

# Main installation flow
main() {
    print_header "Artha Stock Market Simulator - Installer"

    # Change to script directory
    cd "$(dirname "$0")"

    # Run installation steps
    check_python
    setup_venv
    activate_venv
    ensure_pip
    install_uv
    install_dependencies
    verify_installation
    setup_directories
    check_ollama

    # Done!
    print_next_steps
}

# Run the installer
main

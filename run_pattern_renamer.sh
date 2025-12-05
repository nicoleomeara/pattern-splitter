#!/bin/bash
# Pattern Renamer - Easy Runner Script
# Double-click this file or run from terminal to rename PDF pattern files

# Colors for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}🏷️  Pattern Renamer - Easy Runner${NC}"
echo -e "${BLUE}===================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo "Please run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if pattern_renamer_gui.py exists
if [ ! -f "pattern_renamer_gui.py" ]; then
    echo -e "${RED}❌ pattern_renamer_gui.py not found!${NC}"
    read -p "Press Enter to exit..."
    exit 1
fi

echo -e "${GREEN}✅ Environment ready!${NC}"
echo ""
echo -e "${BLUE}🚀 Starting Pattern Renamer GUI...${NC}"
echo ""

# Run the pattern renamer
.venv/bin/python pattern_renamer_gui.py

exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ An error occurred.${NC}"
    echo ""
    read -p "Press Enter to exit..."
fi
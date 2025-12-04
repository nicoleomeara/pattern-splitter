#!/bin/bash
# Pattern Splitter - Easy Runner Script
# Double-click this file or run from terminal to easily split PDF patterns

# Colors for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}🎨 Pattern Splitter - Easy Runner${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo "Please run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if pattern_splitter_fixed.py exists
if [ ! -f "pattern_splitter_fixed.py" ]; then
    echo -e "${RED}❌ pattern_splitter_fixed.py not found!${NC}"
    read -p "Press Enter to exit..."
    exit 1
fi

echo -e "${GREEN}✅ Environment ready!${NC}"
echo ""

# Prompt for PDF file path
echo -e "${YELLOW}📁 Enter the path to your PDF file:${NC}"
echo "   (You can drag and drop the file here, or type/paste the path)"
echo ""
read -p "PDF Path: " pdf_path

# Remove quotes if user added them
pdf_path=$(echo "$pdf_path" | sed 's/^"//;s/"$//')

# Check if file exists
if [ ! -f "$pdf_path" ]; then
    echo -e "${RED}❌ File not found: $pdf_path${NC}"
    read -p "Press Enter to exit..."
    exit 1
fi

echo ""
echo -e "${BLUE}🚀 Processing PDF...${NC}"
echo ""

# Run the pattern splitter
.venv/bin/python pattern_splitter_fixed.py "$pdf_path"

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}🎉 Pattern splitting completed successfully!${NC}"
else
    echo -e "${RED}❌ An error occurred during processing.${NC}"
fi

echo ""
read -p "Press Enter to exit..."
#!/bin/bash
# Script to organize all INSTANT series files into the instant directory

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Finding all INSTANT series files...${NC}"

# Create the instant directory structure
echo -e "${BLUE}📁 Creating instant directory structure...${NC}"
mkdir -p instant/{contracts,archive,docs,scripts,configs,workflows,tests,src,legacy}

# Counter for moved files
MOVED_COUNT=0

# Find all INSTANT files (case insensitive) and process
find . -type f \( -iname "*instant*" -o -iname "*INSTANT*" \) 2>/dev/null | sort | while read file; do
    # Skip files already in instant directory or this script
    if [[ "$file" == ./instant/* ]] || [[ "$file" == ./organize_instant_files.sh ]]; then
        continue
    fi
    
    # Get just the filename
    filename=$(basename "$file")
    
    # Determine destination subdirectory based on file type and location
    if [[ "$file" == *".github/workflows"* ]]; then
        dest="instant/workflows/"
    elif [[ "$file" == *"scripts"* ]] || [[ "$filename" == *".sh" ]] || [[ "$filename" == *".py" ]]; then
        dest="instant/scripts/"
    elif [[ "$file" == *"docs"* ]] || [[ "$filename" == *"README"* ]] || [[ "$filename" == *"GUIDE"* ]]; then
        dest="instant/docs/"
    elif [[ "$file" == *"config"* ]] || [[ "$filename" == *"config"* ]] || [[ "$filename" == *"MANIFEST"* ]]; then
        dest="instant/configs/"
    elif [[ "$file" == *"tests"* ]] || [[ "$filename" == *"test"* ]]; then
        dest="instant/tests/"
    elif [[ "$file" == *"src"* ]] || [[ "$filename" == *"engine"* ]] || [[ "$filename" == *"pipeline"* ]]; then
        dest="instant/src/"
    elif [[ "$file" == *"archive"* ]] || [[ "$file" == *"legacy"* ]]; then
        dest="instant/archive/"
    elif [[ "$file" == *"contracts"* ]]; then
        dest="instant/contracts/"
    else
        dest="instant/legacy/"
    fi
    
    # Move the file
    echo -e "${GREEN}✓ Moving${NC} $file -> $dest$filename"
    mv "$file" "$dest$filename"
    ((MOVED_COUNT++))
done

echo -e "${GREEN}✅ Organization complete!${NC}"
echo ""
echo "📊 Directory structure:"
find instant -type d | sort

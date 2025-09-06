#!/bin/bash

# Install Claude Launcher - Creates a global command to launch Claude from anywhere
# ==================================================================================

set -euo pipefail

HOOKS_REPO="/Users/sam/claude-code-hooks-mastery"
SCRIPT_PATH="$HOOKS_REPO/scripts/claude-secure-launch-portable.sh"
LINK_PATH="/usr/local/bin/claude-launch"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}📦 Claude Launcher Installer${NC}"
echo "=============================="
echo ""

# Check if script exists
if [[ ! -f "$SCRIPT_PATH" ]]; then
    echo -e "${RED}Error: Portable script not found at:${NC}"
    echo "  $SCRIPT_PATH"
    exit 1
fi

# Check if /usr/local/bin exists
if [[ ! -d "/usr/local/bin" ]]; then
    echo -e "${YELLOW}Creating /usr/local/bin directory...${NC}"
    sudo mkdir -p /usr/local/bin
fi

# Remove old link if exists
if [[ -L "$LINK_PATH" ]]; then
    echo -e "${YELLOW}Removing old launcher...${NC}"
    sudo rm "$LINK_PATH"
fi

# Create symbolic link
echo -e "${BLUE}Installing launcher to: $LINK_PATH${NC}"
sudo ln -s "$SCRIPT_PATH" "$LINK_PATH"

# Verify installation
if [[ -L "$LINK_PATH" ]]; then
    echo -e "${GREEN}✅ Installation successful!${NC}"
    echo ""
    echo -e "${GREEN}You can now launch Claude from any directory with:${NC}"
    echo -e "  ${BLUE}claude-launch${NC}"
    echo ""
    echo "Example usage:"
    echo "  cd /path/to/any/project"
    echo "  claude-launch"
else
    echo -e "${RED}Installation failed!${NC}"
    exit 1
fi
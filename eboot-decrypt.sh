#!/bin/bash

# PS3 EBOOT.BIN Batch "Decrypter" using RPCS3 compatibility
# This script helps prepare games for RPCS3 without manual decryption

# Configuration
PS3_GAMES_DIR="/run/media/games-2tb/emu/ps3"
RPCS3_COMPAT_DIR="/run/media/games-2tb/emu/rpcs3 game data/dev_hdd0/game"
LOG_FILE="rpcs3_prepare.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Initialize counters
total_games=0
prepared_games=0
already_prepared=0
failed_prepare=0

# Function to create RPCS3 game directory structure
prepare_for_rpcs3() {
    local game_path="$1"
    local game_name="$2"

    # Extract game ID from PARAM.SFO if available
    local game_id=""
    local param_sfo=$(find "$game_path" -name "PARAM.SFO" -type f | head -1)

    if [ -f "$param_sfo" ]; then
        game_id=$(strings "$param_sfo" | grep -E '^[BCUS|NPEB|NPUA|BLES|BLUS][0-9]{5}' | head -1)
    fi

    if [ -z "$game_id" ]; then
        # Generate a fake ID based on game name
        game_id="FAKE${game_name:0:8}" | tr '[:lower:]' '[:upper:]' | tr -cd '[:alnum:]'
        game_id="${game_id:0:9}"
    fi

    # Create RPCS3 game directory
    local rpcs3_game_dir="$RPCS3_COMPAT_DIR/$game_id"
    mkdir -p "$rpcs3_game_dir"

    # Copy game files (excluding already decrypted ones)
    echo "Preparing $game_name for RPCS3 (ID: $game_id)..." >> "$LOG_FILE"

    # Create USRDIR and copy EBOOT.BIN
    mkdir -p "$rpcs3_game_dir/PS3_GAME/USRDIR"
    cp "$game_path/PS3_GAME/USRDIR/EBOOT.BIN" "$rpcs3_game_dir/PS3_GAME/USRDIR/" 2>> "$LOG_FILE"

    # Copy other necessary files
    if [ -f "$game_path/PS3_GAME/ICON0.PNG" ]; then
        cp "$game_path/PS3_GAME/ICON0.PNG" "$rpcs3_game_dir/PS3_GAME/" 2>> "$LOG_FILE"
    fi

    if [ -f "$param_sfo" ]; then
        cp "$param_sfo" "$rpcs3_game_dir/PS3_GAME/" 2>> "$LOG_FILE"
    fi

    echo "Created RPCS3 compatibility directory: $rpcs3_game_dir" >> "$LOG_FILE"
    return 0
}

# Main execution
echo -e "${BLUE}PS3 Game Preparation for RPCS3${NC}"
echo "======================================"
echo "This script prepares games for RPCS3 without manual decryption"
echo "RPCS3 will handle decryption automatically when needed"
echo "Games directory: $PS3_GAMES_DIR"
echo "RPCS3 compat directory: $RPCS3_COMPAT_DIR"
echo ""

# Create RPCS3 compatibility directory
mkdir -p "$RPCS3_COMPAT_DIR"

# Find all game directories
echo -e "${BLUE}Scanning for PS3 games...${NC}"
mapfile -d '' game_dirs < <(find "$PS3_GAMES_DIR" -maxdepth 1 -type d -name "*" -print0 2>/dev/null)
total_games=${#game_dirs[@]}

if [ $total_games -eq 0 ]; then
    echo -e "${YELLOW}No game directories found in the specified directory${NC}"
    exit 1
fi

echo -e "${GREEN}Found $total_games game directories to process${NC}"

# Process each game directory
for ((i=0; i<total_games; i++)); do
    game_path="${game_dirs[i]}"
    game_name=$(basename "$game_path")

    echo -e "\n${YELLOW}[$((i+1))/$total_games] Processing: $game_name${NC}"
    echo "Path: $game_path"

    # Check if game has EBOOT.BIN
    if [ ! -f "$game_path/PS3_GAME/USRDIR/EBOOT.BIN" ]; then
        echo -e "${YELLOW}  Status: Skipped (no EBOOT.BIN found)${NC}"
        continue
    fi

    # Check if already prepared for RPCS3 - remove 'local' keyword
    game_id=""
    param_sfo=$(find "$game_path" -name "PARAM.SFO" -type f | head -1)

    if [ -f "$param_sfo" ]; then
        game_id=$(strings "$param_sfo" | grep -E '^[BCUS|NPEB|NPUA|BLES|BLUS][0-9]{5}' | head -1)
    fi

    if [ -z "$game_id" ]; then
        game_id="FAKE${game_name:0:8}"
        game_id=$(echo "$game_id" | tr '[:lower:]' '[:upper:]' | tr -cd '[:alnum:]')
        game_id="${game_id:0:9}"
    fi
    if [ -f "$param_sfo" ]; then
        game_id=$(strings "$param_sfo" | grep -E '^[BCUS|NPEB|NPUA|BLES|BLUS][0-9]{5}' | head -1)
    fi

    if [ -z "$game_id" ]; then
        game_id="FAKE${game_name:0:8}" | tr '[:lower:]' '[:upper:]' | tr -cd '[:alnum:]'
        game_id="${game_id:0:9}"
    fi

    if [ -d "$RPCS3_COMPAT_DIR/$game_id" ]; then
        echo -e "${GREEN}  Status: Already prepared for RPCS3${NC}"
        ((already_prepared++))
        continue
    fi

    # Prepare game for RPCS3
    echo "  Preparing for RPCS3..."
    if prepare_for_rpcs3 "$game_path" "$game_name"; then
        echo -e "${GREEN}  Successfully prepared for RPCS3!${NC}"
        ((prepared_games++))
    else
        echo -e "${RED}  Failed to prepare for RPCS3${NC}"
        ((failed_prepare++))
    fi
done

# Summary
echo ""
echo -e "${BLUE}================================="
echo "PREPARATION SUMMARY"
echo "=================================${NC}"
echo "Total games found: $total_games"
echo "Already prepared: $already_prepared"
echo -e "${GREEN}Successfully prepared: $prepared_games${NC}"
echo -e "${RED}Failed to prepare: $failed_prepare${NC}"
echo ""
echo "Detailed log saved to: $LOG_FILE"
echo ""

if [ $prepared_games -gt 0 ]; then
    echo -e "${GREEN}Excellent! $prepared_games games were prepared for RPCS3.${NC}"
    echo "Next steps:"
    echo "1. Open RPCS3"
    echo "2. Go to Manage > Game Directories"
    echo "3. Add your games directory: $PS3_GAMES_DIR"
    echo "4. RPCS3 will automatically detect and decrypt games as needed"
    echo ""
    echo "Note: RPCS3 handles decryption internally when it has the proper keys"
fi

if [ $failed_prepare -gt 0 ]; then
    echo -e "${YELLOW}Note: $failed_prepare games failed to prepare.${NC}"
    echo "This could mean:"
    echo "1. The game directories are missing required files"
    echo "2. There were permission issues"
fi

echo -e "${GREEN}Done!${NC}"

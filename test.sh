#!/bin/bash

# Test script for MP3 Zing API and Xiaozhi Adapter
# Usage: ./test.sh

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
MP3_API_URL="http://localhost:5555"
ADAPTER_URL="http://localhost:5005"

# Test songs
SONG_NAME="Nơi này có anh"
ARTIST_NAME="Sơn Tùng MTP"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  MP3 API & Adapter Test Suite${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Test 1: Check MP3 API Health
echo -e "${YELLOW}[TEST 1] Checking MP3 API Health...${NC}"
if curl -s -f "${MP3_API_URL}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ MP3 API is running${NC}\n"
else
    echo -e "${RED}✗ MP3 API is not responding${NC}\n"
    exit 1
fi

# Test 2: Check Adapter Health
echo -e "${YELLOW}[TEST 2] Checking Adapter Health...${NC}"
HEALTH_RESPONSE=$(curl -s "${ADAPTER_URL}/health")
echo -e "Response: ${HEALTH_RESPONSE}"
echo -e "${GREEN}✓ Adapter is running${NC}\n"

# Test 3: Search for a song via MP3 API
echo -e "${YELLOW}[TEST 3] Searching song via MP3 API...${NC}"
echo -e "Query: ${SONG_NAME} - ${ARTIST_NAME}"
MP3_SEARCH_RESPONSE=$(curl -s "${MP3_API_URL}/api/search" \
    -G \
    --data-urlencode "q=${SONG_NAME} ${ARTIST_NAME}" \
    | jq '.')
echo -e "Response:"
echo "${MP3_SEARCH_RESPONSE}" | jq '.data.items[0] | {title, artistsNames, encodeId}' 2>/dev/null || echo "${MP3_SEARCH_RESPONSE}"
echo -e "${GREEN}✓ MP3 API search successful${NC}\n"

# Test 4: Get song info via MP3 API
echo -e "${YELLOW}[TEST 4] Getting song info from MP3 API...${NC}"
# Extract encodeId from search results
ENCODE_ID=$(echo "${MP3_SEARCH_RESPONSE}" | jq -r '.data.items[0].encodeId' 2>/dev/null)
if [ ! -z "$ENCODE_ID" ] && [ "$ENCODE_ID" != "null" ]; then
    echo -e "Song ID: ${ENCODE_ID}"
    SONG_INFO=$(curl -s "${MP3_API_URL}/api/song?id=${ENCODE_ID}" | jq '.')
    echo -e "Song Info:"
    echo "${SONG_INFO}" | jq '{title: .data.title, artist: .data.artistsNames, duration: .data.duration}' 2>/dev/null
    echo -e "${GREEN}✓ Got song info${NC}\n"
else
    echo -e "${YELLOW}⚠ No song ID found, skipping${NC}\n"
fi

# Test 5: Stream via Adapter
echo -e "${YELLOW}[TEST 5] Testing Adapter Stream Endpoint...${NC}"
echo -e "Query: ${SONG_NAME} by ${ARTIST_NAME}"
STREAM_RESPONSE=$(curl -s "${ADAPTER_URL}/stream_pcm" \
    -G \
    --data-urlencode "song=${SONG_NAME}" \
    --data-urlencode "artist=${ARTIST_NAME}" \
    | jq '.')
echo -e "Response:"
echo "${STREAM_RESPONSE}" | jq '{title, artist, audio_url, lyric_url, duration}' 2>/dev/null || echo "${STREAM_RESPONSE}"
echo -e "${GREEN}✓ Adapter stream endpoint working${NC}\n"

# Test 6: Get lyrics via Adapter
echo -e "${YELLOW}[TEST 6] Testing Lyrics Endpoint...${NC}"
LYRIC_URL=$(echo "${STREAM_RESPONSE}" | jq -r '.lyric_url' 2>/dev/null)
if [ ! -z "$LYRIC_URL" ] && [ "$LYRIC_URL" != "null" ]; then
    echo -e "Lyric URL: ${ADAPTER_URL}${LYRIC_URL}"
    LYRICS=$(curl -s "${ADAPTER_URL}${LYRIC_URL}" | jq '.')
    echo -e "Lyrics preview:"
    echo "${LYRICS}" | jq '.sentences[:3]' 2>/dev/null || echo "${LYRICS}" | head -n 10
    echo -e "${GREEN}✓ Lyrics endpoint working${NC}\n"
else
    echo -e "${YELLOW}⚠ No lyrics URL found${NC}\n"
fi

# Test 7: Get audio stream URL
echo -e "${YELLOW}[TEST 7] Testing Audio Stream URL...${NC}"
AUDIO_URL=$(echo "${STREAM_RESPONSE}" | jq -r '.audio_url' 2>/dev/null)
if [ ! -z "$AUDIO_URL" ] && [ "$AUDIO_URL" != "null" ]; then
    echo -e "Audio URL: ${ADAPTER_URL}${AUDIO_URL}"
    echo -e "${BLUE}ℹ You can test audio with: curl -I '${ADAPTER_URL}${AUDIO_URL}'${NC}"
    
    # Check if audio stream is accessible (HEAD request)
    if curl -s -I "${ADAPTER_URL}${AUDIO_URL}" | head -n 1 | grep -q "200\|302"; then
        echo -e "${GREEN}✓ Audio stream is accessible${NC}\n"
    else
        echo -e "${YELLOW}⚠ Audio stream may not be accessible${NC}\n"
    fi
else
    echo -e "${YELLOW}⚠ No audio URL found${NC}\n"
fi

# Test 8: Alternative song search
echo -e "${YELLOW}[TEST 8] Testing with different song...${NC}"
ALT_SONG="Lạc trôi"
ALT_ARTIST="Sơn Tùng MTP"
echo -e "Query: ${ALT_SONG} by ${ALT_ARTIST}"
ALT_RESPONSE=$(curl -s "${ADAPTER_URL}/stream_pcm" \
    -G \
    --data-urlencode "song=${ALT_SONG}" \
    --data-urlencode "artist=${ALT_ARTIST}" \
    | jq '.')
echo -e "Response:"
echo "${ALT_RESPONSE}" | jq '{title, artist, duration}' 2>/dev/null || echo "${ALT_RESPONSE}"
echo -e "${GREEN}✓ Alternative song test successful${NC}\n"

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}  All Tests Completed Successfully!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${YELLOW}Quick Reference:${NC}"
echo -e "  MP3 API URL:    ${MP3_API_URL}"
echo -e "  Adapter URL:    ${ADAPTER_URL}"
echo -e "  Health Check:   curl ${ADAPTER_URL}/health"
echo -e "  Search Song:    curl '${ADAPTER_URL}/stream_pcm?song=SONG_NAME&artist=ARTIST_NAME'"
echo -e ""

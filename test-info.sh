#!/bin/bash

# Test script for Financial and Weather MCP Tools
# Usage: ./test-info.sh

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Testing MCP Info Tools APIs${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Test 1: Gold Price API (BTMC)
echo -e "${YELLOW}[TEST 1] Testing Gold Price API (BTMC)...${NC}"
GOLD_RESPONSE=$(curl -s "http://api.btmc.vn/api/BTMCAPI/getpricebtmc?key=3kd8ub1llcg9t45hnoh8hmn7t5kc2v")
if [ $? -eq 0 ] && [[ $GOLD_RESPONSE == "["* ]]; then
    echo -e "${GREEN}✓ BTMC Gold Price API is working${NC}"
    echo "Response (first 5 items):"
    echo "${GOLD_RESPONSE}" | jq '.[0:5] | .[] | {"name": .["@n"], "type": .["@t"], "buy": .["@pb"], "sell": .["@ps"]}' 2>/dev/null || echo "${GOLD_RESPONSE}" | head -c 500
    echo -e "\n"
else
    echo -e "${RED}✗ BTMC API failed${NC}"
    echo "Response: ${GOLD_RESPONSE}"
    echo -e "\n"
fi

# Test 2: USD/VND Rate API
echo -e "${YELLOW}[TEST 2] Testing USD/VND Rate API (Vietcombank)...${NC}"
USD_RESPONSE=$(curl -s "https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx?b=10")
if [ $? -eq 0 ] && [[ $USD_RESPONSE == *"<Exrate"* ]]; then
    echo -e "${GREEN}✓ Vietcombank API is working${NC}"
    echo "Sample response (first 300 chars):"
    echo "${USD_RESPONSE}" | head -c 300
    echo -e "\n"
else
    echo -e "${RED}✗ Vietcombank API failed${NC}"
    echo -e "${YELLOW}Trying fallback API...${NC}"
    FALLBACK_USD=$(curl -s "https://api.exchangerate-api.com/v4/latest/USD" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Fallback API working${NC}"
        echo "${FALLBACK_USD}" | jq '{base: .base, vnd_rate: .rates.VND, date: .date}' 2>/dev/null || echo "${FALLBACK_USD}" | head -c 200
    fi
    echo -e "\n"
fi

# Test 3: Bitcoin Price API
echo -e "${YELLOW}[TEST 3] Testing Bitcoin Price API (CoinGecko)...${NC}"
BTC_RESPONSE=$(curl -s "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,vnd&include_24hr_change=true&include_market_cap=true")
if [ $? -eq 0 ] && [[ $BTC_RESPONSE == *"bitcoin"* ]]; then
    echo -e "${GREEN}✓ Bitcoin API is working${NC}"
    echo "${BTC_RESPONSE}" | jq '.' 2>/dev/null || echo "${BTC_RESPONSE}"
    echo -e ""
else
    echo -e "${RED}✗ Bitcoin API failed${NC}"
    echo "Response: ${BTC_RESPONSE}"
    echo -e "\n"
fi

# Test 4: Weather API - Ho Chi Minh
echo -e "${YELLOW}[TEST 4] Testing Weather API (Ho Chi Minh)...${NC}"
HCM_WEATHER=$(curl -s "https://api.open-meteo.com/v1/forecast?latitude=10.8231&longitude=106.6297&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&timezone=Asia/Bangkok&forecast_days=1")
if [ $? -eq 0 ] && [[ $HCM_WEATHER == *"current"* ]]; then
    echo -e "${GREEN}✓ Weather API is working for Ho Chi Minh${NC}"
    echo "${HCM_WEATHER}" | jq '.current | {time, temperature: .temperature_2m, humidity: .relative_humidity_2m, wind_speed: .wind_speed_10m, weather_code}' 2>/dev/null || echo "${HCM_WEATHER}" | head -c 400
    echo -e "\n"
else
    echo -e "${RED}✗ Weather API failed${NC}"
    echo -e "\n"
fi

# Test 5: Weather API - Cao Lãnh
echo -e "${YELLOW}[TEST 5] Testing Weather API (Cao Lãnh)...${NC}"
CL_WEATHER=$(curl -s "https://api.open-meteo.com/v1/forecast?latitude=10.4606&longitude=105.6328&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&timezone=Asia/Bangkok&forecast_days=1")
if [ $? -eq 0 ] && [[ $CL_WEATHER == *"current"* ]]; then
    echo -e "${GREEN}✓ Weather API is working for Cao Lãnh${NC}"
    echo "${CL_WEATHER}" | jq '.current | {time, temperature: .temperature_2m, humidity: .relative_humidity_2m, wind_speed: .wind_speed_10m, weather_code}' 2>/dev/null || echo "${CL_WEATHER}" | head -c 400
    echo -e "\n"
else
    echo -e "${RED}✗ Weather API failed${NC}"
    echo -e "\n"
fi

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}  API Tests Completed!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${YELLOW}Available APIs:${NC}"
echo -e "  💰 Gold Price:  http://api.btmc.vn/api/BTMCAPI/getpricebtmc"
echo -e "  💵 USD/VND:     https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx"
echo -e "  ₿  Bitcoin:     https://api.coingecko.com/api/v3/simple/price"
echo -e "  🌤️  Weather:     https://api.open-meteo.com/v1/forecast"
echo -e ""

echo -e "${YELLOW}MCP Tools Available:${NC}"
echo -e "  1. get_gold_price    - Giá vàng BTMC (Bảo Tín Minh Châu)"
echo -e "  2. get_usd_rate      - Tỷ giá USD/VND Vietcombank"
echo -e "  3. get_bitcoin_price - Giá Bitcoin (USD & VND)"
echo -e "  4. get_weather       - Thời tiết Cao Lãnh / HCM"
echo -e ""

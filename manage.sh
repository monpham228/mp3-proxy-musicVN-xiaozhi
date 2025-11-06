#!/bin/bash

# Xiaozhi Music MCP Server - Docker Management Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Commands
case "$1" in
    build)
        print_info "Building Docker images..."
        docker-compose build
        print_info "Build completed!"
        ;;
    
    start)
        print_info "Starting all services..."
        docker-compose up -d
        print_info "Services started!"
        docker-compose ps
        ;;
    
    stop)
        print_info "Stopping all services..."
        docker-compose down
        print_info "Services stopped!"
        ;;
    
    restart)
        print_info "Restarting all services..."
        docker-compose restart
        print_info "Services restarted!"
        ;;
    
    logs)
        SERVICE=${2:-mcp-server}
        print_info "Showing logs for $SERVICE..."
        docker-compose logs -f "$SERVICE"
        ;;
    
    status)
        print_info "Service status:"
        docker-compose ps
        ;;
    
    shell)
        SERVICE=${2:-mcp-server}
        print_info "Opening shell in $SERVICE..."
        docker-compose exec "$SERVICE" /bin/bash || docker-compose exec "$SERVICE" /bin/sh
        ;;
    
    rebuild)
        print_info "Rebuilding and restarting MCP server..."
        docker-compose stop mcp-server
        docker-compose build mcp-server
        docker-compose up -d mcp-server
        print_info "MCP server rebuilt and restarted!"
        ;;
    
    clean)
        print_warning "This will remove all containers and volumes. Continue? (y/N)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            print_info "Cleaning up..."
            docker-compose down -v
            print_info "Cleanup completed!"
        else
            print_info "Cleanup cancelled."
        fi
        ;;
    
    test)
        print_info "Testing MCP server connection..."
        docker-compose exec mcp-server python3 -c "import httpx; print('Dependencies OK')" || print_error "Dependencies check failed"
        ;;
    
    *)
        echo "Xiaozhi Music MCP Server - Docker Management"
        echo ""
        echo "Usage: $0 {command} [options]"
        echo ""
        echo "Commands:"
        echo "  build          - Build Docker images"
        echo "  start          - Start all services"
        echo "  stop           - Stop all services"
        echo "  restart        - Restart all services"
        echo "  logs [service] - Show logs (default: mcp-server)"
        echo "  status         - Show service status"
        echo "  shell [service]- Open shell in container (default: mcp-server)"
        echo "  rebuild        - Rebuild and restart MCP server"
        echo "  clean          - Remove all containers and volumes"
        echo "  test           - Test MCP server dependencies"
        echo ""
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 logs mcp-server"
        echo "  $0 shell xiaozhi-adapter"
        exit 1
        ;;
esac
#!/bin/bash

# 🚀 Production Setup Script for Raspberry Pi
# Spelling Game - Gunicorn + Nginx Setup
# Run this on your Raspberry Pi server

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Spelling Game Production Setup (Raspberry Pi)                ║"
echo "║  Gunicorn + Nginx Configuration                               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect the current user and project directory
CURRENT_USER=$(whoami)
PROJECT_DIR=$(pwd)

echo -e "${BLUE}Detected user: ${CURRENT_USER}${NC}"
echo -e "${BLUE}Project directory: ${PROJECT_DIR}${NC}"
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ Don't run this script as root!${NC}"
   echo "Run as your normal user. The script will ask for sudo password when needed."
   exit 1
fi

# Verify we're in the right directory
if [[ ! -f "manage.py" ]]; then
    echo -e "${RED}❌ Error: manage.py not found!${NC}"
    echo "Please run this script from the Spelling-Game directory."
    exit 1
fi

# Check if gunicorn is installed
if ! python3 -c "import gunicorn" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Gunicorn not installed. Installing via apt...${NC}"
    
    # Try to install via apt first (Debian/Raspberry Pi OS way)
    if sudo apt install -y python3-gunicorn 2>/dev/null; then
        echo -e "${GREEN}✓ Gunicorn installed via apt${NC}"
    else
        # Fallback: use pip with --break-system-packages for Pi OS Bookworm
        echo -e "${YELLOW}Installing via pip (with --break-system-packages)...${NC}"
        pip3 install --break-system-packages gunicorn
        echo -e "${GREEN}✓ Gunicorn installed${NC}"
    fi
    echo ""
fi

# Check Django settings
echo -e "${YELLOW}Step 1: Checking Django settings...${NC}"
if grep -q "STATIC_ROOT" spelling_game/settings.py; then
    echo -e "${GREEN}✓ STATIC_ROOT already configured${NC}"
else
    echo -e "${YELLOW}⚠️  STATIC_ROOT not found in settings.py${NC}"
    echo -e "${YELLOW}   Please add this line to spelling_game/settings.py:${NC}"
    echo -e "${BLUE}   STATIC_ROOT = BASE_DIR / 'staticfiles'${NC}"
    echo ""
    read -p "Press Enter after you've added it, or Ctrl+C to exit..."
fi

if grep -q "CONN_MAX_AGE" spelling_game/settings.py; then
    echo -e "${GREEN}✓ Database connection pooling configured${NC}"
else
    echo -e "${YELLOW}⚠️  Consider adding CONN_MAX_AGE to DATABASES for better performance${NC}"
fi
echo ""

echo -e "${YELLOW}Step 2: Creating log directory...${NC}"
mkdir -p "${PROJECT_DIR}/logs"
echo -e "${GREEN}✓ Log directory created${NC}"
echo ""

echo -e "${YELLOW}Step 3: Collecting static files...${NC}"
python3 manage.py collectstatic --noinput
echo -e "${GREEN}✓ Static files collected to ${PROJECT_DIR}/staticfiles/${NC}"
echo ""

echo -e "${YELLOW}Step 4: Creating Gunicorn systemd service...${NC}"

# Update the service file with actual paths
cat > /tmp/spelling-game.service << EOF
[Unit]
Description=Spelling Game Gunicorn daemon
After=network.target

[Service]
User=${CURRENT_USER}
Group=www-data
WorkingDirectory=${PROJECT_DIR}
Environment="PATH=${PROJECT_DIR}/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/gunicorn \\
    --workers 3 \\
    --bind unix:${PROJECT_DIR}/gunicorn.sock \\
    --access-logfile ${PROJECT_DIR}/logs/gunicorn-access.log \\
    --error-logfile ${PROJECT_DIR}/logs/gunicorn-error.log \\
    --timeout 60 \\
    spelling_game.wsgi:application

Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

sudo cp /tmp/spelling-game.service /etc/systemd/system/
rm /tmp/spelling-game.service
sudo systemctl daemon-reload
echo -e "${GREEN}✓ Systemd service created${NC}"
echo ""

echo -e "${YELLOW}Step 5: Starting Gunicorn service...${NC}"
sudo systemctl stop spelling-game 2>/dev/null || true
sudo systemctl start spelling-game
sudo systemctl enable spelling-game
sleep 2

if sudo systemctl is-active --quiet spelling-game; then
    echo -e "${GREEN}✓ Gunicorn service is running${NC}"
else
    echo -e "${RED}❌ Gunicorn service failed to start!${NC}"
    echo "Check logs: sudo journalctl -u spelling-game -n 50"
    exit 1
fi
echo ""

echo -e "${YELLOW}Step 6: Creating Nginx configuration...${NC}"

# Update the nginx config with actual paths
cat > /tmp/spelling-game.nginx << EOF
server {
    listen 80;
    server_name eduflows.org www.eduflows.org;

    client_max_body_size 10M;

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # Static files (CSS, JS, images)
    location /static/ {
        alias ${PROJECT_DIR}/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files (if you add them later)
    location /media/ {
        alias ${PROJECT_DIR}/media/;
    }

    # Proxy all other requests to Gunicorn
    location / {
        proxy_pass http://unix:${PROJECT_DIR}/gunicorn.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

sudo cp /tmp/spelling-game.nginx /etc/nginx/sites-available/spelling-game
rm /tmp/spelling-game.nginx
echo -e "${GREEN}✓ Nginx configuration created${NC}"
echo ""

echo -e "${YELLOW}Step 7: Enabling Nginx site...${NC}"
sudo ln -sf /etc/nginx/sites-available/spelling-game /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
echo -e "${GREEN}✓ Site enabled, default site disabled${NC}"
echo ""

echo -e "${YELLOW}Step 8: Testing Nginx configuration...${NC}"
if sudo nginx -t; then
    echo -e "${GREEN}✓ Nginx configuration is valid${NC}"
else
    echo -e "${RED}❌ Nginx configuration has errors!${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}Step 9: Setting permissions...${NC}"
# Add current user to www-data group
sudo usermod -a -G ${CURRENT_USER} www-data

# Set proper permissions
chmod 755 "${HOME}"
chmod 755 "${PROJECT_DIR}"
chmod 755 "${PROJECT_DIR}/staticfiles" 2>/dev/null || true

# Wait for socket to be created
sleep 2

# Set socket permissions if it exists
if [ -S "${PROJECT_DIR}/gunicorn.sock" ]; then
    sudo chown ${CURRENT_USER}:www-data "${PROJECT_DIR}/gunicorn.sock"
    chmod 660 "${PROJECT_DIR}/gunicorn.sock"
    echo -e "${GREEN}✓ Socket permissions set${NC}"
else
    echo -e "${YELLOW}⚠️  Socket not created yet - permissions will be set on first run${NC}"
fi
echo ""

echo -e "${YELLOW}Step 10: Restarting Nginx...${NC}"
sudo systemctl restart nginx

if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx is running${NC}"
else
    echo -e "${RED}❌ Nginx failed to start!${NC}"
    echo "Check logs: sudo tail -f /var/log/nginx/error.log"
    exit 1
fi
echo ""

# Final status check
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✅ SETUP COMPLETE!                                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Your spelling game is now running in production mode on Raspberry Pi!${NC}"
echo ""
echo "🌐 Access your site at: ${BLUE}http://eduflows.org${NC}"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📊 Service Status:"
echo "═══════════════════════════════════════════════════════════════"

echo -ne "Gunicorn: "
if sudo systemctl is-active --quiet spelling-game; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Not running${NC}"
fi

echo -ne "Nginx:    "
if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Not running${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📝 Useful Commands:"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Check Gunicorn status:"
echo "  ${BLUE}sudo systemctl status spelling-game${NC}"
echo ""
echo "Check Nginx status:"
echo "  ${BLUE}sudo systemctl status nginx${NC}"
echo ""
echo "View Gunicorn logs:"
echo "  ${BLUE}tail -f ${PROJECT_DIR}/logs/gunicorn-error.log${NC}"
echo "  ${BLUE}tail -f ${PROJECT_DIR}/logs/gunicorn-access.log${NC}"
echo ""
echo "View Nginx logs:"
echo "  ${BLUE}sudo tail -f /var/log/nginx/error.log${NC}"
echo "  ${BLUE}sudo tail -f /var/log/nginx/access.log${NC}"
echo ""
echo "Restart after code changes:"
echo "  ${BLUE}sudo systemctl restart spelling-game${NC}"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🧪 Performance Testing:"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Test from your local machine (not on the Pi):"
echo "  ${BLUE}locust -f load_test.py --headless --users 25 --spawn-rate 3 --run-time 2m --host http://eduflows.org${NC}"
echo ""
echo "Expected improvements over dev server:"
echo "  • Response times: 2-5x faster"
echo "  • Capacity: 10-50x more concurrent users"
echo "  • CPU usage: More efficient (uses all cores)"
echo ""
echo -e "${GREEN}Setup completed successfully! 🎉${NC}"
echo ""

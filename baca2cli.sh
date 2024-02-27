#!/bin/bash

# ANSI color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

APACHE_LOG='/var/log/baca2_access.log'
GUNICORN_LOG='/home/www/BaCa2/BaCa2/logs/info.log'
BROKER_LOG='/home/www/BaCa2-broker/logs/broker.log'

# Function to display script usage
usage() {
    echo "Usage: $0 [--reboot --migrate --status --status-offset <offset>]" 1>&2
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --migrate)
            MIGRATE=true
            shift
            ;;
        --reboot)
            REBOOT=true
            shift
            ;;
        --status)
            STATUS=true
            shift
            ;;
        --status-offset)
          STATUS=true
          shift
          if [[ $1 =~ ^[0-9]+$ ]]; then
            OFFSET=$1
            shift
          else
            echo "Invalid offset value"
            exit 1
          fi
          ;;
        *)
            usage
            ;;
    esac
done

print_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}done${NC}"
    else
        echo -e "${RED}error${NC}"
    fi
}

print_status() {
    state=$(systemctl is-active apache2)
    if [ "$state" = "active" ]; then
        echo -e "    apache2 -------- ${GREEN}$state${NC}"
    else
        echo -e "    apache2 -------- ${RED}$state${NC}"
    fi

    status=$(systemctl is-active baca2_gunicorn)
    if [ "$status" = "active" ]; then
        echo -e "    baca2 web app -- ${GREEN}$status${NC}"
    else
        echo -e "    baca2 web app -- ${RED}$status${NC}"
    fi

    status=$(systemctl is-active baca2_broker)
    if [ "$status" = "active" ]; then
        echo -e "    baca2 broker --- ${GREEN}$status${NC}"
    else
        echo -e "    baca2 broker --- ${RED}$status${NC}"
    fi
}

print_extensive_status() {
  total_lines=0

  status=$(systemctl is-active apache2)
      if [ "$status" = "active" ]; then
          echo -e "    apache2 -------- ${GREEN}$status${NC}"
      else
          echo -e "    apache2 -------- ${RED}$status${NC}"
      fi

    lines=$(tail $APACHE_LOG -n4 | wc -l)
    echo -e "$(tail $APACHE_LOG -n4)"
    total_lines=$((total_lines + lines))

    echo ""
      status=$(systemctl is-active baca2_gunicorn)
      if [ "$status" = "active" ]; then
          echo -e "    baca2 web app -- ${GREEN}$status${NC}"
      else
          echo -e "    baca2 web app -- ${RED}$status${NC}"
      fi
    lines=$(tail $GUNICORN_LOG -n4 | wc -l)
    echo -e "$(tail $GUNICORN_LOG -n4)"
    total_lines=$((total_lines + lines))

    echo ""
      status=$(systemctl is-active baca2_broker)
      if [ "$status" = "active" ]; then
          echo -e "    baca2 broker --- ${GREEN}$status${NC}"
      else
          echo -e "    baca2 broker --- ${RED}$status${NC}"
      fi
    lines=$(tail $BROKER_LOG -n4 | wc -l)
    echo -e "$(tail $BROKER_LOG -n4)"
    total_lines=$((total_lines + lines))

    total_lines=$((total_lines + 5))
    total_lines=$((total_lines + OFFSET))

    sleep 1

    tput cuu $total_lines
    tput el
}

# Parse command line options

if [ "$REBOOT" = true ]; then
    echo -n "Stopping services..."

    systemctl stop baca2_broker
    systemctl stop baca2_gunicorn
    systemctl stop apache2

    print_result

    echo ""
fi



# If --migrate flag is provided, perform migration
if [ "$MIGRATE" = true ]; then
    echo -n "Creating migrations..."
    /home/www/.cache/pypoetry/virtualenvs/baca2-pMI66htX-py3.11/bin/python3.11 /home/www/BaCa2/BaCa2/manage.py makemigrations > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}done${NC}"
        echo -n "Migrating..."
        /home/www/.cache/pypoetry/virtualenvs/baca2-pMI66htX-py3.11/bin/python3.11 /home/www/BaCa2/BaCa2/manage.py migrate > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}done${NC}"
        else
            echo -e "${RED}error occurred during migration${NC}"
        fi

    else
        echo -e "${GREEN}error occurred during migration${NC}"
    fi
    echo ""
fi

# If --reboot flag is provided, start services
if [ "$REBOOT" = true ]; then

  echo -n "Starting apache2..."
  systemctl start apache2
  print_result

  echo -n "Starting baca2 web app..."
  systemctl start baca2_gunicorn
  print_result

  echo -n "Starting baca2 broker..."
  systemctl start baca2_broker
  print_result

  echo -e -n "\nStatus check"

  for ((i=0; i<3; i++)); do
      echo -n "."
      sleep 0.5
  done
  echo ""

  print_status

fi

if [ "$STATUS" = true ]; then
  echo -e "BaCa2 status:"
  while true; do
    print_extensive_status
  done
fi

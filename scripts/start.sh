#!/bin/bash
set -e
echo "Starting Photo Printing Management System..."
docker compose up --build -d
echo "Waiting for services to be ready..."
sleep 10
echo ""
echo "Application is running!"
echo "  Frontend:  http://localhost"
echo "  API Docs:  http://localhost/docs"
echo "  Health:    http://localhost/health"
echo ""
echo "Default credentials:"
echo "  Admin:    admin@system.com / Admin123!"
echo "  Manager:  manager@system.com / Manager123!"
echo "  Employee: employee@system.com / Employee123!"

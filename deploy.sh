#!/bin/sh
pwd
cd /webapps/TheRook || exit 1
pwd
sudo git pull origin main
/webapps/TheRook/venv/bin/pip install -r requirements.txt
sudo systemctl restart therook
sudo systemctl restart nginx

#!/bin/sh
pwd
sudo git pull origin main
/webapps/TheRook/venv/bin/pip install -r requirements.txt
sudo systemctl restart restart
sudo systemctl restart nginx

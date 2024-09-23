#!/bin/sh
sudo git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart restart
sudo systemctl restart nginx

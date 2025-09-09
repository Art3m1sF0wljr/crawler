#!/bin/bash
#python3 -m venv myenv
source /home/art3m1sf0wl/program/exploit_db/myenv/bin/activate
# Activate the virtual environment
#source myenv/bin/activate
pip install requests beautifulsoup4
# Install librosa in the virtual environment
python3 /home/art3m1sf0wl/program/exploit_db/app.py "http://art.net/lile/pics/" --output-dir my_downloads

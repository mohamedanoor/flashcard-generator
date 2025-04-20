#!/usr/bin/env bash
# Install system dependencies for WeasyPrint
apt-get update
apt-get install -y build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

# Continue with the normal pip install
pip install -r requirements.txt
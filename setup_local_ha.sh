#!/bin/bash

# Create a virtual environment with Python 3.14
python3.14 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install Home Assistant Core and known missing dependencies
pip install homeassistant numpy PyQRCode pyotp hassil home-assistant-frontend

# Create config directory if it doesn't exist
mkdir -p config

# Link custom_components to the config directory
# Note: We use a symlink so changes in the repo are reflected in HA immediately
mkdir -p config/custom_components
rm -rf config/custom_components/ipbuilding
ln -s "$(pwd)/custom_components/ipbuilding" config/custom_components/ipbuilding

echo "Setup complete. To run Home Assistant:"
echo "source venv/bin/activate"
echo "hass -c config"

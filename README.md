# Unofficial Aton Green Storage integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

This is an unofficial Home Assistant integration for the Aton Green Storage inverter.

### Data provided:
- Self sufficiency percentage
- Battery percentage
- House consumption
- Battery power
- Grid power
- Solar production
- Self consumed energy
- Bought energy
- Total consumed energy
- Solar energy
- Sold energy
- All power directions (grid to house, battery to house, solar to battery, ecc...)

## How to intall:

#### Using HACS:

Go to HACS > Integrations, open the 3 dot menu and select "Custom repositories".
Paste this repository link in the "Repository" field and select "Integration" as the 
category then click add.

At this point you should be able to just search for "Aton Green Storage" in the HACS Integrations
and install it.


#### Manual install:

Copy the custom_components/aton_storage folder in your custom_components folder and
reboot Home Assistant.

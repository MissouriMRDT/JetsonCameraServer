# JetsonCameraServer

An RTP camera system for use with a Jetson Xavier on MRDT Rovers

## Setup on Jetson

- Install Jetpack to the SSD (Not SD Card, there's not enough space)
- Recursively clone this repo
- Install python, make, and cmake if needed
- Install Jetson-Utils
  - Clone [Jetson-Utils](https://github.com/dusty-nv/jetson-utils)
  - Make a build directory in the Jetson-Utils repo
  - `cmake ..` in the build directory
  - `make`
  - `sudo make install`
  - `sudo ldconfig`

## Running

- `python3 Camera.py`

## Basestation

- run the Cameras.bat file on the desktop
- Switch camera feeds in RED

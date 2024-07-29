#!/bin/sh
docker run -d --name mqtt-server -p 1883:1883 -p 9001:9001 -v ./mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf eclipse-mosquitto:2.0.10

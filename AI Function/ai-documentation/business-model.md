# BUSINESS MODEL

This document define what the system should be, and what the system should do.

---

## TITLE

The title of the project is Flood Detection and Rain Monitoring System

## WHAT THE SYSTEM SHOULD BE

The system should be a tool that is connected to the IoT system called `node` that contains Piezoelectronic Sensor, Ultrasonic Sensor and Raindrop Sensor.

- Piezo is used to determined the rain intensity
- Ultrasonic is used to determined the water level
- Rain Sensor is used to detect rain

The system should be a man-in-the-middle tool that receive API incoming from `node` and process the data from `node`, store it in Google Sheets (as a database) and do a trend analysis based on the existing dataset to track the incoming rain and predict flood way before it happen.

## WHAT THE SYSTEM SHOULD DO

The system should:

1. Receive API from `node`
2. Process API from `node` and store it inside the Google Sheet
3. Use AI to train make a prediction based on the existing dataset from database and the latest data from `node`
4. Use AI (using API) and send the prediction in a form of API

## TECH STACK

- Python with FastAPI
- OpenLLM (model of your choice)
- RestAPI

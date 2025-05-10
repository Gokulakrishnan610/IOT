import os
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import tensorflow as tf
from sklearn.preprocessing import StandardScaler

# Load models
model_north = tf.keras.models.load_model('traffic_signal_model_north.h5')
model_south = tf.keras.models.load_model('traffic_signal_model_south.h5')
model_east = tf.keras.models.load_model('traffic_signal_model_east.h5')
model_west = tf.keras.models.load_model('traffic_signal_model_west.h5')

# ESP32 server IP
ESP32_SERVER_URL = "http://192.168.211.229/update_timings"

# Load and fit scaler
df = pd.read_csv('traffic_signal_data_directions.csv')
X = df[['time_of_day', 'day_of_week', 'vehicle_count_north', 'vehicle_count_south', 'vehicle_count_east', 'vehicle_count_west']]
scaler = StandardScaler()
scaler.fit(X)

def get_vehicle_count_south():
    try:
        with open("vehicle_count_south.txt", 'r') as f:
            content = f.read().strip()
            parts = content.split()
            vehicle_info = parts[0]
            vehicle_count = int(vehicle_info.split(',')[0].replace("Vehicle", ""))
            ambulance_status = parts[-1].lower() == 'true'
            return vehicle_count, ambulance_status
    except Exception as e:
        print(f"⚠️ Error reading file: {e}")
        return 0, False

def get_user_input():
    now = datetime.now()
    time_of_day = now.hour + now.minute / 60
    day_of_week = now.isoweekday()

    vehicle_count_north = float(input("Enter vehicle count (north): "))
    vehicle_count_south, ambulance_detected = get_vehicle_count_south()
    vehicle_count_east = float(input("Enter vehicle count (east): "))
    vehicle_count_west = float(input("Enter vehicle count (west): "))

    ambulance_direction = "south" if ambulance_detected else None

    user_data = pd.DataFrame({
        'time_of_day': [time_of_day],
        'day_of_week': [day_of_week],
        'vehicle_count_north': [vehicle_count_north],
        'vehicle_count_south': [vehicle_count_south],
        'vehicle_count_east': [vehicle_count_east],
        'vehicle_count_west': [vehicle_count_west]
    })

    return user_data, ambulance_direction

def predict_signal_times(user_data, ambulance_direction):
    scaled = scaler.transform(user_data)

    g_north = float(model_north.predict(scaled)[0][0])
    g_south = float(model_south.predict(scaled)[0][0])
    g_east = float(model_east.predict(scaled)[0][0])
    g_west = float(model_west.predict(scaled)[0][0])

    yellow = 5.0
    total_cycle = 120.0

    if ambulance_direction == 'south':
        print("\n🚨 Ambulance detected on SOUTH side. Giving full green cycle to south direction.")
        g_south = total_cycle
        g_north = g_east = g_west = 0
    else:
        g_south += 5.0  # Buffer time

    return {
        "north": {"green": g_north, "yellow": yellow, "red": total_cycle - (g_north + yellow)},
        "south": {"green": g_south, "yellow": yellow, "red": total_cycle - (g_south + yellow)},
        "east": {"green": g_east, "yellow": yellow, "red": total_cycle - (g_east + yellow)},
        "west": {"green": g_west, "yellow": yellow, "red": total_cycle - (g_west + yellow)}
    }

def send_to_esp32(data):
    clean_data = {d: {k: int(round(v[k])) for k in v} for d, v in data.items()}
    print("\n📡 Sending to ESP32:", clean_data)
    try:
        response = requests.post(ESP32_SERVER_URL, json=clean_data)
        if response.status_code == 200:
            print("✅ Timings sent successfully.")
        else:
            print("❌ Failed. Status code:", response.status_code)
    except Exception as e:
        print("❌ Exception:", e)

def main():
    user_data, ambulance_direction = get_user_input()
    timings = predict_signal_times(user_data, ambulance_direction)
    send_to_esp32(timings)

if __name__ == "__main__":
    main()

import json
import requests

def send_data_to_thingsboard(telemetry_data, device_token):
    thingsboard_url = f"http://rt.ugr.es:8953/api/v1/{device_token}/telemetry"
    
    print("Enviando datos:", telemetry_data)

    try:
        headers = {
            "Content-Type": "application/json",
            "X-Authorization": f"Bearer {device_token}"
        }
        response = requests.post(thingsboard_url, headers=headers, json=telemetry_data)
        #print("Data posted to ThingsBoard:", response.text)
    except Exception as e:
        print("Exception:", e)

def save_json_to_file(telemetry_data, filename="data.json"):
    with open(filename, "a") as file:
        file.write(json.dumps(telemetry_data) + "\n")

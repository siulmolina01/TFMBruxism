import time
from datetime import datetime
from bitalino import BITalino
from thingsboard import send_data_to_thingsboard, save_json_to_file

if __name__ == '__main__':
    device = BITalino()

    macAddress = "84:BA:20:AE:B8:4B"
    samplingRate = 1000
    nSamples = 10
    device_token = "VXtaqkTAamdm2Bg7c19X"

    if device.open(macAddress, samplingRate) == -1:
        print("Failed to open device")
        exit(1)

    if device.battery(20) == -1:
        print("Failed to set battery threshold")
        exit(1)

    BITversion = device.version()
    print("version: ", BITversion)

    if device.start([0, 1, 2, 3, 5]) == -1:
        print("Failed to start acquisition")
        exit(1)

    try:
        while True:
            dataAcquired = device.read(nSamples)
            
            for i in range(nSamples):
                telemetry_data = {
                    "timestamp": datetime.now().isoformat(),
                    "A0": int(dataAcquired[i][5]),  # Canal A1 analógico
                    #"A1": int(dataAcquired[i][6]),  # Canal A2 analógico
                    #"A2": int(dataAcquired[i][7]),  # Canal A3 analógico
                    #"A3": int(dataAcquired[i][8]),  # Canal A4 analógico
                    #"A5": int(dataAcquired[i][10])  # Canal A6 analógico
                }
                print ("A1:", dataAcquired[i][5])

                #send_data_to_thingsboard(telemetry_data, device_token)
                save_json_to_file(telemetry_data, filename="data.json")
                
                
                
                time.sleep(1)

    except KeyboardInterrupt:
        device.stop()
        device.close()
        print("Acquisition stopped and device closed")

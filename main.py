import time
from datetime import datetime
from bitalino import BITalino
from thingsboard import send_data_to_thingsboard, save_json_to_file

if __name__ == '__main__':
	device = BITalino()
    
	macAddress = "84:BA:20:AE:B8:4B"
	SamplingRate = 1000
	nSamples = 1000
	device_token = "qwv8wf2eoulea0tgx0qg"
    
	# Connect to bluetooth device and set Sampling Rate
	device.open(macAddress, SamplingRate)
    
	#set battery threshold
	th = device.battery(20)
	print ("battery: ", th)
    
	#get BITalino version
	BITversion = device.version()
	print ("version: ", BITversion)
    
	#Start Acquisition in Analog Channels 0 and 3
	device.start([0, 1, 2, 3, 4, 5])

	try:
		while True:
			dataAcquired = device.read(nSamples)
			collected_data = []
			maximoA0 = 0
			maximoA1 = 0
			maximoA2 = 0
			maximoA3 = 0
			
			print(f"Shape of dataAcquired: {dataAcquired.shape}")
			
			A0 = dataAcquired[5, :]
			for i in range(nSamples):
				if int(dataAcquired[5][i]) > maximoA0:
					maximoA0 =  int(dataAcquired[5][i])
				if int(dataAcquired[6][i]) > maximoA0:
					maximoA1 =  int(dataAcquired[6][i])
				if int(dataAcquired[7][i]) > maximoA0:
					maximoA2 =  int(dataAcquired[7][i])
				if int(dataAcquired[8][i]) > maximoA0:
					maximoA3 =  int(dataAcquired[8][i])
					
            
			
			telemetry_data = {
				#"timestamp": datetime.now().isoformat(),
				"A0": maximoA0,  # Canal A1 analógico
				"A1": maximoA1,  # Canal A2 analógico
				"A2": maximoA2,  # Canal A3 analógico
				"A3": maximoA3,  # Canal A4 analógico
				#"A5": maximo,  # Canal A6 analógico
				"A5": 0.2
			}
			send_data_to_thingsboard(telemetry_data, device_token)
			"""
			
			for i in range(nSamples):
				telemetry_data = {
					#"timestamp": datetime.now().isoformat(),
					"A0": int(dataAcquired[5][i]),  # Canal A1 analógico
					"A1": int(dataAcquired[6][i]),  # Canal A2 analógico
					"A2": int(dataAcquired[7][i]),  # Canal A3 analógico
					"A3": int(dataAcquired[8][i]),  # Canal A4 analógico
					#"A5": int(dataAcquired[10][i]),  # Canal A6 analógico
					"A5": 0.2
				}
				send_data_to_thingsboard(telemetry_data, device_token)
			"""

	except KeyboardInterrupt:
		device.stop()
		device.close()
		print("Acquisition stopped and device closed")

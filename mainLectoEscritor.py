import threading
import time
from datetime import datetime
from bitalino import BITalino
from thingsboard import send_data_to_thingsboard, save_json_to_file
import csv
import queue

# Tamaño del buffer circular
BUFFER_SIZE = 10000

def read_bitalino_data(device, data_queue, condition, sampling_rate, n_samples):
    while True:
        start_time = time.time()
        data_acquired = device.read(n_samples)
        with condition:
            for i in range(n_samples):
                if data_queue.full():
                    condition.wait()  # Espera hasta que haya espacio disponible en la queue
                data_queue.put((datetime.now().isoformat(), data_acquired[5, i], data_acquired[6, i], data_acquired[7, i], data_acquired[8, i], data_acquired[9, i]))
                condition.notify()  # Notifica que hay un nuevo dato disponible
        elapsed_time = time.time() - start_time
        print(f"Read thread elapsed time: {elapsed_time:.4f} seconds")
        #time.sleep(1)  

def write_data_to_csv(data_queue, condition):
    measurement_number = 1
    with open('data.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Measurement", "Timestamp", "A0", "A1", "A2", "A3", "A5"])
        while True:
            start_time = time.time()
            with condition:
                while data_queue.empty():
                    condition.wait()  # Espera hasta que haya datos disponibles en la queue
                timestamp, A0, A1, A2, A3, A5 = data_queue.get()
                writer.writerow([measurement_number, timestamp, A0, A1, A2, A3, A5])
                measurement_number += 1
                condition.notify()  # Notifica que se ha eliminado un dato de la queue
            elapsed_time = time.time() - start_time
            print(f"Write thread elapsed time: {elapsed_time:.4f} seconds")
            #time.sleep(1)  

if __name__ == '__main__':
	device = BITalino()
    
	macAddress = "84:BA:20:AE:B8:4B"
	sampling_rate = 1000
	n_samples = 1000
    
	# Connect to bluetooth device and set Sampling Rate
	device.open(macAddress, sampling_rate)
    
	#set battery threshold
	th = device.battery(20)
	print ("battery: ", th)
    
	#get BITalino version
	BITversion = device.version()
	print ("version: ", BITversion)
    
	#Start Acquisition in Analog Channels 0 and 3
	device.start([0, 1, 2, 3, 4])

	data_queue = queue.Queue(maxsize=BUFFER_SIZE)
	condition = threading.Condition()

	read_thread = threading.Thread(target=read_bitalino_data, args=(device, data_queue, condition, sampling_rate, n_samples))
	write_thread = threading.Thread(target=write_data_to_csv, args=(data_queue, condition))

	read_thread.start()
	write_thread.start()

	try:
		read_thread.join()
		write_thread.join()
	except KeyboardInterrupt:
		device.stop()
		device.close()
		print("Acquisition stopped and device closed")

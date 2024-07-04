import threading
import time
from datetime import datetime
from bitalino import BITalino
from thingsboard import send_data_to_thingsboard, save_json_to_file
import csv
import queue

# Tamaño del buffer circular
BUFFER_SIZE = 10000
ITERATIONS = 1000  # Número de iteraciones a ejecutar

def read_bitalino_data(device, data_queue, condition, sampling_rate, n_samples, iterations):
	start_time = time.time()
	data_acquired = device.read(n_samples)
	with condition:
		for i in range(n_samples):
			while data_queue.full():
				condition.wait()  # Espera hasta que haya espacio disponible en la queue
			data_queue.put((datetime.now().isoformat(), data_acquired[5, i], data_acquired[6, i], data_acquired[7, i], data_acquired[8, i], data_acquired[10, i]))
			condition.notify()  # Notifica que hay un nuevo dato disponible
			time.sleep(0.001)  # Espera 1 ms antes de la próxima iteración
	elapsed_time = time.time() - start_time
	print(f"Read thread elapsed time: {elapsed_time:.4f} seconds")

def write_data_to_csv(data_queue, condition, csv_processed_set, iterations):
	measurement_number = 1
	with open('data.csv', mode='w', newline='') as file:
		writer = csv.writer(file)
		writer.writerow(["Measurement", "Timestamp", "A0", "A1", "A2", "A3", "A5"])
		start_time = time.time()
		for _ in range(iterations):
			with condition:
				while data_queue.empty():
					condition.wait()  # Espera hasta que haya datos disponibles en la queue
				timestamp, A0, A1, A2, A3, A5 = data_queue.queue[0]
				writer.writerow([measurement_number, timestamp, A0, A1, A2, A3, A5])
				measurement_number += 1
				csv_processed_set.add(timestamp)
				condition.notify()  # Notifica que se ha procesado un dato
		elapsed_time = time.time() - start_time
		print(f"Write thread elapsed time: {elapsed_time:.4f} seconds")

def send_data_to_thingsboard_task(data_queue, condition, device_token, tb_processed_set, iterations):
	start_time = time.time()
	for i in range(iterations):
		with condition:
			while data_queue.empty():
				condition.wait()  # Espera hasta que haya datos disponibles en la queue
			timestamp, A0, A1, A2, A3, A5 = data_queue.queue[0]
			telemetry_data = {
				"A0": A0,
				"A1": A1,
				"A2": A2,
				"A3": A3,
				"A5": A5
			}
			send_data_to_thingsboard(telemetry_data, device_token)
			tb_processed_set.add(timestamp)
			condition.notify()  # Notifica que se ha enviado un dato
	elapsed_time = time.time() - start_time
	print(f"Thingsboard thread elapsed time: {elapsed_time:.4f} seconds")
		

def remove_processed_data(data_queue, condition, csv_processed_set, tb_processed_set, iterations):
	for _ in range(iterations):
		with condition:
			while data_queue.empty() or data_queue.queue[0][0] not in csv_processed_set or data_queue.queue[0][0] not in tb_processed_set:
				condition.wait()  # Espera hasta que haya datos procesados por ambas hebras
			timestamp = data_queue.get()[0]
			csv_processed_set.remove(timestamp)
			tb_processed_set.remove(timestamp)
			condition.notify()  # Notifica que se ha eliminado un dato procesado
	print("Remove thread completed its iterations")

if __name__ == '__main__':
	device = BITalino()

	mac_address = "84:BA:20:AE:B8:4B"
	sampling_rate = 1000
	n_samples = 1000
	device_token = "qwv8wf2eoulea0tgx0qg"

	device.open(mac_address, sampling_rate)
	device.battery(20)
	bit_version = device.version()
	print("version: ", bit_version)
	device.start([0, 1, 2, 3, 4, 5])

	data_queue = queue.Queue(maxsize=BUFFER_SIZE)
	condition = threading.Condition()
	csv_processed_set = set()
	tb_processed_set = set()

	read_thread = threading.Thread(target=read_bitalino_data, args=(device, data_queue, condition, sampling_rate, n_samples, ITERATIONS))
	write_thread = threading.Thread(target=write_data_to_csv, args=(data_queue, condition, csv_processed_set, ITERATIONS))
	thingsboard_thread = threading.Thread(target=send_data_to_thingsboard_task, args=(data_queue, condition, device_token, tb_processed_set, ITERATIONS))
	remove_thread = threading.Thread(target=remove_processed_data, args=(data_queue, condition, csv_processed_set, tb_processed_set, ITERATIONS))

	read_thread.start()
	write_thread.start()
	thingsboard_thread.start()
	remove_thread.start()

	try:
		read_thread.join()
		write_thread.join()
		thingsboard_thread.join()
		remove_thread.join()
	except KeyboardInterrupt:
		device.stop()
		device.close()
		print("Acquisition stopped and device closed")

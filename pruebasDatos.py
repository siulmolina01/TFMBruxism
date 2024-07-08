import threading
import time
from datetime import datetime
from bitalino import BITalino
from thingsboard import send_data_to_thingsboard
import csv
import queue

# Tamaño del buffer circular
BUFFER_SIZE = 10000

# Estructura para almacenar los datos y sus estados
class DataRecord:
    def __init__(self, timestamp, A0, A1, A2, A3, A5):
        self.timestamp = timestamp
        self.A0 = A0
        self.A1 = A1
        self.A2 = A2
        self.A3 = A3
        self.A5 = A5
        self.csv_written = False
        self.tb_sent = False

def read_bitalino_data(device, data_queue, condition, n_samples):
    start_time = time.time()
    data_acquired = device.read(n_samples)
    with condition:
        for i in range(n_samples):
			while data_queue.full():
				condition.wait()  # Espera hasta que haya espacio disponible en la queue
			data_record = DataRecord(
				datetime.now().isoformat(),
				data_acquired[5, i],
				data_acquired[6, i],
				data_acquired[7, i],
				data_acquired[8, i],
				0.3
			)
			data_queue.put(data_record)
			condition.notify()  # Notifica que hay un nuevo dato disponible
			time.sleep(0.001)  # Espera 1 ms antes de la próxima iteración
    elapsed_time = time.time() - start_time
    print(f"Read thread elapsed time: {elapsed_time:.4f} seconds")

def write_data_to_csv(data_queue, condition):
    measurement_number = 1
    with open('data.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Measurement", "Timestamp", "A0", "A1", "A2", "A3", "A5"])
        start_time = time.time()
        for _ in range(BUFFER_SIZE):
            with condition:
                while data_queue.empty() or data_status[data_queue.queue[0][0]]['written']:
                    condition.wait()  # Espera hasta que haya datos disponibles en la queue y no hayan sido escritos
                timestamp, A0, A1, A2, A3, A5 = data_queue.queue[0]
                writer.writerow([measurement_number, timestamp, A0, A1, A2, A3, A5])
                measurement_number += 1
                data_status[timestamp]['written'] = True
                condition.notify()  # Notifica que se ha procesado un dato
        elapsed_time = time.time() - start_time
        print(f"Write thread elapsed time: {elapsed_time:.4f} seconds")

def send_data_to_thingsboard_task(data_queue, condition, device_token):
    start_time = time.time()
    for _ in range(BUFFER_SIZE):
        with condition:
            while data_queue.empty() or data_status[data_queue.queue[0][0]]['sent']:
                condition.wait()  # Espera hasta que haya datos disponibles en la queue y no hayan sido enviados
            timestamp, A0, A1, A2, A3, A5 = data_queue.queue[0]
            telemetry_data = {
                "A0": A0,
                "A1": A1,
                "A2": A2,
                "A3": A3,
                "A5": A5
            }
            send_data_to_thingsboard(telemetry_data, device_token)
            data_status[timestamp]['sent'] = True
            condition.notify()  # Notifica que se ha enviado un dato
    elapsed_time = time.time() - start_time
    print(f"Thingsboard thread elapsed time: {elapsed_time:.4f} seconds")

def remove_processed_data(data_queue, condition):
    for _ in range(BUFFER_SIZE):
        with condition:
            while data_queue.empty() or not data_status[data_queue.queue[0][0]]['written'] or not data_status[data_queue.queue[0][0]]['sent']:
                condition.wait()  # Espera hasta que haya datos procesados por ambas hebras
            timestamp = data_queue.get()[0]
            del data_status[timestamp]
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

    read_thread = threading.Thread(target=read_bitalino_data, args=(device, data_queue, condition, n_samples))
    write_thread = threading.Thread(target=write_data_to_csv, args=(data_queue, condition))
    thingsboard_thread = threading.Thread(target=send_data_to_thingsboard_task, args=(data_queue, condition, device_token))
    remove_thread = threading.Thread(target=remove_processed_data, args=(data_queue, condition))

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

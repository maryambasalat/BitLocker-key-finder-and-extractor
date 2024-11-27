import os
import re
import time
import random
import psutil
import platform
import threading
import shutil
import ctypes
import PySimpleGUI as sg

# Pattern for BitLocker key (for searching files)
pattern = re.compile(r"\d{6}-\d{6}-\d{6}-\d{6}-\d{6}-\d{6}-\d{6}-\d{6}")

# Admin check function
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

# Function to simulate extracting BitLocker keys from RAM
def extract_from_ram(window):
    fake_key = generate_fake_key()
    progress_bar = window['PROGRESS']
    total_steps = 100
    progress_bar.update(0)

    for step in range(total_steps):
        time.sleep(0.05)
        progress_bar.update_bar(step + 1)

    return f"BitLocker Key: {fake_key}"

# Function to simulate scanning a partition for BitLocker keys
def search_partition_for_keys(window, partition):
    found_keys = [(partition, [generate_fake_key()])]
    progress_bar = window['PROGRESS']
    total_steps = 100
    progress_bar.update(0)

    for step in range(total_steps):
        time.sleep(0.05)
        progress_bar.update_bar(step + 1)

    return found_keys

# Function to generate a fake BitLocker key
def generate_fake_key():
    return '-'.join([f"{random.randint(100000, 999999)}" for _ in range(8)])

# Function to copy key files
def copy_key_files(files, destination):
    for file, _ in files:
        try:
            shutil.copy(file, destination)
        except Exception as e:
            sg.popup_error(f"Error copying {file}: {e}")

# Function to store keys and system specs in a file
def store_keys_and_specs(found_keys, output_dir):
    output_file_path = os.path.join(output_dir, "found_keys_and_specs.txt")
    system_info = get_system_info()

    with open(output_file_path, 'w') as f:
        f.write(f"System Specifications:\n")
        for key, value in system_info.items():
            f.write(f"{key}: {value}\n")
        f.write("\n\nMock BitLocker Keys:\n")
        for file, keys in found_keys:
            f.write(f"File: {file}\n")
            for key in keys:
                f.write(f"  Key: {key}\n")
    
    return f"Keys and system specifications stored at: {output_file_path}"

# Function to get system information
def get_system_info():
    system_info = {
        'OS': f"{platform.system()} {platform.release()} ({platform.architecture()[0]})",
        'CPU': f"{psutil.cpu_count(logical=True)} CPUs, {psutil.cpu_percent()}% usage",
        'RAM': f"Total: {psutil.virtual_memory().total / (1024**3):.2f} GB, Available: {psutil.virtual_memory().available / (1024**3):.2f} GB, Usage: {psutil.virtual_memory().percent}%",
        'Disk': '\n'.join([f"Partition: {p.device}, Total: {psutil.disk_usage(p.mountpoint).total / (1024**3):.2f} GB" for p in psutil.disk_partitions()])
    }
    return system_info

# Function to handle partition scan in a separate thread
def handle_partition_scan(window, partition, output_dir):
    found_keys = search_partition_for_keys(window, partition)
    if found_keys:
        if output_dir:
            store_message = store_keys_and_specs(found_keys, output_dir)
            window.write_event_value('STORE_MESSAGE', store_message)
            copy_key_files(found_keys, output_dir)
        else:
            window.write_event_value('NO_OUTPUT_DIR', "No output directory specified.")
    else:
        window.write_event_value('NO_KEYS', "No BitLocker keys found.")

# GUI Layout
layout = [
    [sg.Text('BitLocker Key Extraction Tool', font=('Impact', 25))],
    [sg.Text('Select a Partition to Search for BitLocker Keys:')],
    [sg.Input(key='PARTITION'), sg.FolderBrowse()],
    [sg.Checkbox('Extract BitLocker keys from RAM (Admin Required)', key='RAM_EXTRACT')],
    [sg.Text('Select Output Directory to Save Files:')],
    [sg.Input(key='OUTPUT'), sg.FolderBrowse()],
    [sg.Button('Start'), sg.Button('Exit')],
    [sg.Text('Progress:')],
    [sg.ProgressBar(100, orientation='h', size=(20, 20), key='PROGRESS')],
    [sg.Output(size=(80, 20))]
]

window = sg.Window('BitLocker Key Extraction Tool', layout)

while True:
    event, values = window.read()
    
    if event == sg.WINDOW_CLOSED or event == 'Exit':
        break

    if event == 'Start':
        window['PROGRESS'].update(0)
        if values['RAM_EXTRACT']:
            print(extract_from_ram(window))
        if values['PARTITION']:
            threading.Thread(
                target=handle_partition_scan, 
                args=(window, values['PARTITION'], values['OUTPUT']), 
                daemon=True
            ).start()

    if event == 'STORE_MESSAGE':
        sg.popup(values['STORE_MESSAGE'], title="Keys and Specs Stored")
    if event == 'NO_KEYS':
        sg.popup("No BitLocker keys found.", title="No Keys Found")
    if event == 'NO_OUTPUT_DIR':
        sg.popup(values['NO_OUTPUT_DIR'], title="Warning")

window.close()

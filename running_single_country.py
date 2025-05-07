import yaml
import subprocess
import time
import os

countries = ['ZM'] #'AO', 'BW', 'CD', 'LS', 'MW', 'MZ', 'NM', 'SZ', 'TZ', 'ZM', 'ZW',
year = 2030
folder_dir = f'solutions/SAPP-single-country-limited-technology-{year}-ssp5'
config_file_path = 'config.yaml'
data_file_path = f'./data/input_data/TEMBA_SSP5-Baseline.xlsx'

problems_dir = os.path.join(folder_dir, 'problems')
outputs_dir = os.path.join(folder_dir, 'outputs')

os.makedirs(problems_dir, exist_ok=True)
os.makedirs(outputs_dir, exist_ok=True)

for country in countries:
    #Step 1: Modify the YAML configuration file
    with open(config_file_path, 'r') as file:
        config = yaml.safe_load(file)

    print(f"Running for {country}...")
    config['config']['name'] = f'{country}_limited'
    config['config']['outline']['countries'] = [country]
    config['config']['output_file_path'] = f'{folder_dir}/problems/{country}_limited_output.xml'
    config['config']['outline']['year'] = year
    config['config']['outline']['data_file_path'] = data_file_path 
    print(f"data_file_path: {data_file_path}")

    with open(config_file_path, 'w') as file:
        yaml.safe_dump(config, file)
        print(f"Config file updated for {country}.")

    # Step 2: Run main.py and wait for it to finish
    main_script_path = 'main.py'
    process = subprocess.Popen(['python', main_script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("Running main.py...")
    stdout, stderr = process.communicate()

    if process.returncode == 0:
        print("main.py finished successfully.")
    else:
        print(f"main.py encountered an error:\n{stderr.decode()}")

    # Step 3: Run the Java Virtual Machine
    java_command = [
        'java', 
        '-Xmx2G', 
        '-cp', 
        'frodo2.18.1.jar:junit-4.13.2.jar:hamcrest-core-1.3.jar', 
        'frodo2.algorithms.AgentFactory', 
        '-timeout', 
        '7200000', 
        f'{folder_dir}/problems/{country}_limited_output.xml', 
        'agents/DPOP/DPOPagentJaCoP.xml', 
        '-o', 
        f'{folder_dir}/outputs/solution_{country}.xml'
    ]
    print(f"Starting Java Virtual Machine for {country}...")
    java_process = subprocess.Popen(java_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = java_process.communicate()

    if java_process.returncode == 0:
        print(f"Java program finished successfully for {country}.")
    else:
        print(f"Java program encountered an error for {country}:\n{stderr.decode()}")

    
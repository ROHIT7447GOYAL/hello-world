import subprocess
import time

# List of Python files to run
files = ['mostbuys-1-step1.py', 'investing-data-1-step2.py', 'combine_data-step3.py', 'tickertape.py' ,'valuereaserch.py' , 'stock-select.py','t1.py', 'csvtohtml.py']

# Run each file sequentially with a 10-second delay
for file in files:
    subprocess.run(['python', file])
    time.sleep(10)
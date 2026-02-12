import json
import os

from .constants import BARE, BARF

def save_to_file(result, save_path):
    json_result = json.dumps(result, indent=4)
    save_path = os.path.join(save_path, 'simulation_results.json')
    with open(save_path, 'w') as f:
        f.write(json_result)
        print(f"\n{BARF}Simulation results saved to {save_path}{BARE}")
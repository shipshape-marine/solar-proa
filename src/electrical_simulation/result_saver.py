import json

def save_to_file(result, save_path, constants=None):
    
    json_result = json.dumps(result, indent=4)
    with open(save_path, 'w') as f:
        f.write(json_result)
        print(f"\n{constants['BARF']}Simulation results saved to {save_path}{constants['BARE']}")
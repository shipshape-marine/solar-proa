import json
import re

def parse_simulation_result(analysis, result, struc, SIMULATION_LOGGING=False, SHOW_PANELS=False, constants=None):
    if analysis is None:
        return
    
    if SIMULATION_LOGGING:
        print(f"{constants['BARF']}Simulation Results:{constants['BARE']}")
    
    # Node voltages
    for node_name, node in analysis.nodes.items():
        if "measured" in node_name:
            continue
        matched = False
        
        for dic in result.values():
            if matched:
                break
            if 'ignore' in node_name:
                matched = True
                break
            
            if dic.get("keyword", 'None') in node_name:
                matched = True
                matches = dict(re.findall(constants["ARRAY_DECODER_PATTERN"], node_name))
                if matches.get('arr') is not None:
                    arr_no = int(matches['arr'])
                    if arr_no + 1 > len(dic["data"]):
                        dic["data"].extend(eval(struc) for _ in range(arr_no - len(dic["data"]) + 1))
                        dic["array_count"] = len(dic["data"])

                    dic["data"][arr_no]["voltage"][node_name.replace(f"arr{arr_no}_", "")] = float(node.as_ndarray()[0])
                    dic["data"][arr_no]["array_index"] = arr_no
                else:
                    if len(dic["data"]) == 0:
                        dic["data"].append(eval(struc))
                        dic["array_count"] += 1
                    dic["data"][0]["voltage"][node_name] = float(node.as_ndarray()[0])

        if not matched:
            print(f"Missing node ({node_name}): {float(node.as_ndarray()[0]):.2f} V")

    # Branch currents
    for branch_name, branch in analysis.branches.items():
        if branch_name.startswith("v"):
            branch_name = branch_name[1:]  # Remove 'v' prefix
        
        if "measured" in branch_name:
            continue
        
        matched = False
        
        for dic in result.values():
            if matched:
                break
            if dic.get("keyword", 'None') in branch_name:
                matched = True
                
                matches = dict(re.findall(constants["ARRAY_DECODER_PATTERN"], branch_name))
                if matches.get('arr') is not None:
                    arr_no = int(matches['arr'])
                    # Add to data list at index i of i:name
                    if arr_no + 1 > len(dic["data"]):
                        dic["data"].extend(eval(struc) for _ in range(arr_no - len(dic["data"]) + 1))
                        dic["array_count"] = len(dic["data"])
                        
                    dic["data"][arr_no]["current"][branch_name.replace(f"arr{arr_no}_", "")] = float(branch.as_ndarray()[0])
                    dic["data"][arr_no]["array_index"] = arr_no
                else:
                    if len(dic["data"]) == 0:
                        dic["data"].append(eval(struc))
                        dic["array_count"] += 1
                        
                    dic["data"][0]["current"][branch_name] = float(branch.as_ndarray()[0])
        if not matched:
            print(f"Branch {branch_name}: {float(branch.as_ndarray()[0]):.2f} A")

    if SIMULATION_LOGGING:
        for key in result.keys():
            if key == "panel_result" and not SHOW_PANELS:
                continue
            if key in ["error", "warning", "info"]:
                continue

            count = result[key]['array_count']
            print(f"\n{result[key]['keyword'].capitalize()} Results (Count: {count}):")
            for index, data in enumerate(result[key]['data']):
                print(f"{result[key]['keyword'].capitalize()} {index}:") if count > 1 else None
                
                print("\t"*min(1, count) + "Voltages:")
                for node, voltage in data['voltage'].items():
                    print("\t"*min(1, count) + f"\t{node}: {voltage:.2f} V")
                print("\t"*min(1, count) + "Currents:")
                for branch, current in data['current'].items():
                    print("\t"*min(1, count) + f"\t{branch}: {current:.2f} A")
            print(constants['BARE'])
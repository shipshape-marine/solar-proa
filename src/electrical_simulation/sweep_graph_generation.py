import json
import matplotlib.pyplot as plt
import numpy as np
import os
from typing import List, Dict

from .constants import EPSILON


MARKER_SIZE = 0
MARKER_STYLE = 'o'  #'o', 's', '^', 'D', '*', 'P', 'X', etc.
DOTTED_STYLE = ":"     #'-', '--', '-.', ':', 'None', ' ', '', 'solid', 'dashed', 'dashdot', 'dotted'

IMG_FILE_NAME = "sweep_simulation_results.png"
WARNING_FILE_NAME = "sweep_simulation_warnings.json"

def generate_graph(results: list, x_axis: list, x_label: str = "",
                   voltage_display_choice: list = [], 
                   current_display_choice: list = [], 
                   power_display_choice: list = [],
                   battery_capacity: list = [],
                   save_path: str = None,
                   show_plot: bool = False):
    display_graph = show_plot
    
    num_plots = sum([len(voltage_display_choice) > 0, 
                     len(current_display_choice) > 0, 
                     len(power_display_choice) > 0,
                     len(battery_capacity) > 0])
    
    if num_plots == 0:
        print("No display choices selected")
        return
    
    _, axes = plt.subplots(num_plots, 1, figsize=(10, 5 * num_plots))
    if num_plots == 1:
        axes = [axes]
    
    # Adjust spacing between subplots
    plt.subplots_adjust(hspace=20, bottom=0.1)
    

    warning_points = []
    equilibrium_points = []
    
    for i, result in enumerate(results):
        if 'warning' in result and result['warning']['array_count'] > 0:
            warning_points.append({
                'x': x_axis[i],
                'warnings': result['warning']['data']
            })
        for array in result['summary']['data']:
            current = array['current']['total_battery_input_current']
            if current < 1:
                equilibrium_points.append(x_axis[i])
    
    # Color cycles for different traces
    colors = plt.cm.tab10(np.linspace(0, 1, 10))
    
    plot_idx = 0
    
    # Plot Voltage
    if voltage_display_choice:
        ax = axes[plot_idx]
        color_idx = 0
        
        for category in voltage_display_choice:
            voltages = extract_traces(results, category, 'voltage')
            
            for label, values in voltages.items():
                """ if 'battery' in label:
                    print(sum(values) / len(values))
                    if sum(values) / len(values) < EPSILON:
                        continue """
                ax.plot(x_axis, values, marker=MARKER_STYLE, markersize=MARKER_SIZE, 
                       label=f"{category} - {label}", 
                       color=colors[color_idx % len(colors)])
                color_idx += 1
        
        ax.set_xlabel(x_label)
        ax.set_ylabel('Voltage (V)')
        ax.set_title(f'Voltage vs {x_label}')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        draw_warning_points(warning_points, ax)
        draw_equilibrium_points(equilibrium_points, ax)
        
        plot_idx += 1
    
    # Plot Current
    if current_display_choice:
        ax = axes[plot_idx]
        color_idx = 0
        
        for category in current_display_choice:
            currents = extract_traces(results, category, 'current')
            for label, values in currents.items():
                ax.plot(x_axis, values, marker=MARKER_STYLE, markersize=MARKER_SIZE,
                       label=f"{category} - {label}",
                       color=colors[color_idx % len(colors)])
                color_idx += 1
        
        ax.set_xlabel(x_label)
        ax.set_ylabel('Current (A)')
        ax.set_title(f'Current vs {x_label}')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        draw_warning_points(warning_points, ax)
        draw_equilibrium_points(equilibrium_points, ax) 
        
        plot_idx += 1
    
    # Plot Power
    if power_display_choice:
        ax = axes[plot_idx]
        color_idx = 0
        
        for category in power_display_choice:
            power_traces = extract_power_traces(results, category)
            
            for label, values in power_traces.items():
                ax.plot(x_axis, values, marker=MARKER_STYLE, markersize=MARKER_SIZE,
                       label=f"{category} - {label}",
                       color=colors[color_idx % len(colors)])
                color_idx += 1
        
        ax.set_xlabel(x_label)
        ax.set_ylabel('Power (W)')
        ax.set_title(f'Power vs {x_label}')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        draw_warning_points(warning_points, ax)
        draw_equilibrium_points(equilibrium_points, ax)
        plot_idx += 1

    if battery_capacity:
        ax = axes[plot_idx]
        ax.plot(x_axis, battery_capacity, marker=MARKER_STYLE, markersize=MARKER_SIZE,
               label="Battery Capacity (Ah)", color='orange')
        ax.set_xlabel(x_label)
        ax.set_ylabel('Battery Capacity (Ah)')
        ax.set_title(f'Battery Capacity vs {x_label}')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        draw_equilibrium_points(equilibrium_points, ax)
        draw_warning_points(warning_points, ax)
    
    plt.tight_layout(rect=[0, 0.05, 1, 1])  # Leave space at bottom for warnings

    for i, ax in enumerate(axes):
        fig_single, ax_single = plt.subplots()

        for line in ax.get_lines():
            x = line.get_xdata()
            y = line.get_ydata()

            if len(x) <= 2 or len(y) <= 2:
                continue
            
            ax_single.plot(x, y, label=line.get_label())
            
        draw_warning_points(warning_points, ax_single)
        draw_equilibrium_points(equilibrium_points, ax_single)
        
        color_idx += 1

        ax_single.set_title(ax.get_title())
        ax_single.set_xlabel(ax.get_xlabel())
        ax_single.set_ylabel(ax.get_ylabel())

        save_file = os.path.join(save_path, f"{ax.get_title()}.png")
        fig_single.savefig(save_file, bbox_inches="tight")
        plt.close(fig_single)
    
    if save_path:
        with open(os.path.join(save_path, WARNING_FILE_NAME), 'w') as f:
            json.dump(warning_points, f, indent=4)
            print(f"Warning points saved to {os.path.join(save_path, WARNING_FILE_NAME)}")
            
        save_file = os.path.join(save_path, IMG_FILE_NAME)
        plt.savefig(save_file, dpi=300, bbox_inches='tight')
        print(f"Graph saved to {save_file}")
    
    if display_graph:
        plt.show()     

def draw_warning_points(warning_points: list, ax):
    if warning_points:
        for wp in warning_points:
            ax.axvline(x=wp['x'], color='red', linestyle=DOTTED_STYLE, alpha=0.3, zorder=5)
            ax.relim()
            ax.autoscale_view()
            
def draw_equilibrium_points(equilibrium_points: list, ax):
    if equilibrium_points:
        ax.axvline(x=equilibrium_points[len(equilibrium_points)//2], color='lime', linestyle=DOTTED_STYLE, alpha=1, zorder=5)
        ax.relim()
        ax.autoscale_view()
        
def extract_traces(results: list, category: str, data_type: str) -> Dict[str, List[float]]:
    """
    Extract voltage or current traces from results.
    
    Returns a dictionary where keys are trace names and values are lists of measurements.
    """
    traces = {}
    
    for result in results:
        if category not in result:
            continue
        
        category_data = result[category]
        
        # Handle different data structures
        if 'data' in category_data:
            for array_item in category_data['data']:
                if data_type not in array_item:
                    continue
                
                for key, value in array_item[data_type].items():
                    # Skip metadata keys
                    if key in ['array_index']:
                        continue
                    
                    # Create trace name
                    trace_name = key
                    if 'array_index' in array_item:
                        trace_name = f"Arr{array_item['array_index']}_{key}"
                    
                    # Initialize trace if needed
                    if trace_name not in traces:
                        traces[trace_name] = []
                        
                    # Append value
                    traces[trace_name].append(value)
    
    return traces


def extract_power_traces(results: list, category: str) -> Dict[str, List[float]]:
    """
    Extract power traces (P = V * I) from results.
    """
    power_traces = {}
    
    for result in results:
        if category not in result:
            continue
        
        category_data = result[category]
        
        if 'data' in category_data:
            for array_item in category_data['data']:
                voltages = array_item.get('voltage', {})
                currents = array_item.get('current', {})
                
                # Match voltage and current keys to compute power
                for v_key, v_value in voltages.items():
                    # Try to find matching current key
                    c_key = v_key.rstrip('_positive').rstrip('_negative')
                    if c_key in currents:
                        trace_name = v_key
                        if 'array_index' in array_item:
                            trace_name = f"Arr{array_item['array_index']}_{v_key}"
                        
                        if trace_name not in power_traces:
                            power_traces[trace_name] = []
                        
                        power = v_value * currents[c_key]
                        power_traces[trace_name].append(power)
    
    return power_traces
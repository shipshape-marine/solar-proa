## Note:

Spice identifier name should not start with number or 'v'

- Number used to indicate array index for MPPT and solar panels
- v prefix added by ngspice removed for result output

<br>

# Intepreting Simulation Results

Decoding of s & p can be found using the regex key in [this file](../../constant/electrical/constants.json)

## Errors 

```json
    "error": {
        "keyword": "error",
        "array_count": 2,
        "data": [
            "(Array 0) Panel input current (18.2 A) exceeds max MPPT input current (5.0 A)",
            "(Array 1) Panel input current (18.2 A) exceeds max MPPT input current (5.0 A)"
        ]
    },
```

Errors are important issues that must be fixed before deploying the vessel. These errors if not fixed, is a hazzard in regards to fire and electrical safety.

## Warnings

```json
    "warning": {
        "keyword": "warning",
        "array_count": 1,
        "data": [
            "Battery array is being over-discharged. Motor 0 has been restricted to 129.04% instead of 1000.00% throttle level."
        ]
    },
```

Warnings are restrictions on the components due to limitations (i.e. Max battery discharge rate). They may cause issues such as pre-mature shutdown of the components as a safety features by the manufacturer. This is not an indicator that the vessel is unsafe but a simple warning that the components will not run as expected.

## Quick Summary 

```json
    "summary": {
        "keyword": "total",
        "array_count": 1,
        "data": [
            {
                "array_index": 0,
                "voltage": {
                    "total_mppt_output": 58.18912913606731,
                    "total_dc_bus_voltage": 58.18912813606731
                },
                "current": {
                    "total_mppt_output_current": 37.48509485,
                    "total_battery_input_current": -30.542116090829495
                }
            }
        ]
    },
```

A general overview of the system's status.

## MPPT (Array)

```json
    "mppt_result": {
        "keyword": "mppt",
        "array_count": 2,
        "data": [
            {
                "array_index": 0,
                "voltage": {
                    "mppt_output": 58.376555610317304
                },
                "current": {
                    "mppt_output": 18.742547425
                }
            },
            {
                "array_index": 1,
                "voltage": {
                    "mppt_output": 58.376555610317304
                },
                "current": {
                    "mppt_output": 18.742547425
                }
            }
        ]
    },
```

Depending on how many MPPT-Solar arrays are configured. RP2 will have 2 of it. Naming is from PySpice netlist but since MPPTs should not connect in series in any configurations due to safety issue, there will only ever be one voltage and current reading per array.


## Batteries
```json
    "battery_result": {
        "keyword": "battery",
        "array_count": 1,
        "data": [
            {
                "array_index": 0,
                "voltage": {
                    "p0_s1_battery_negative": 29.094548296975614,
                    "p0_s1_battery_positive": 58.494548296975616,
                    "p0_s0_battery_negative": -3.054211609082995e-05,
                    "p0_s0_battery_positive": 29.399969457883913
                },
                "current": {
                    "p0_s0_battery": -30.54211609082995,
                    "p0_s1_battery": -30.54211609082995
                }
            }
        ]
    },
```

Batteries only has 1 array count, but can be configured into series and parallel connection (Indicated by p & s). Can be decoded using the above regex key. Positive current: charging, Negative current: discharging.

## Solar Panel (Array)

```json
    "solar_result": {
        "keyword": "solar_array",
        "array_count": 2,
        "data": [
            {
                "array_index": 0,
                "voltage": {
                    "solar_array_output": 79.95455269744532
                },
                "current": {
                    "solar_array_output": 18.18966051116881
                }
            },
            {
                "array_index": 1,
                "voltage": {
                    "solar_array_output": 80.045449302557
                },
                "current": {
                    "solar_array_output": 18.210339488831718
                }
            }
        ]
    },
```

Following the MPPT_Solar array setup, each array corresponds to the array before. This section will be the input into their respective MPPT.

## Individual Solar Panels

```json
    "panel_result": {
        "keyword": "panel",
        "array_count": 2,
        "data": [
            {
                "array_index": 0,
                "voltage": {
                    "p1_s0_panel_positive": -9.100000000000001e-06,
                    "p1_1_panel_positive": 80.04550100000117,
                    "p1_1_panel_negative": -9.1e-06,
                    "p1_0_panel_positive": 9.1,
                    "p1_0_panel_negative": -9.1e-06,
                    "p0_s0_panel_positive": -9.100000000000001e-06,
                    "p0_1_panel_positive": 80.04550100000117,
                    "p0_1_panel_negative": -9.1e-06,
                    "p0_0_panel_positive": 9.1,
                    "p0_0_panel_negative": -9.1e-06
                },
                "current": {}
            },
            {
                "array_index": 1,
                "voltage": {
                    "p1_s0_panel_positive": -9.100000000000001e-06,
                    "p1_1_panel_positive": 80.136449302557,
                    "p1_1_panel_negative": -9.1e-06,
                    "p1_0_panel_positive": 9.1,
                    "p1_0_panel_negative": -9.1e-06,
                    "p0_s0_panel_positive": -9.100000000000001e-06,
                    "p0_1_panel_positive": 80.136449302557,
                    "p0_1_panel_negative": -9.1e-06,
                    "p0_0_panel_positive": 9.1,
                    "p0_0_panel_negative": -9.1e-06
                },
                "current": {}
            }
        ]
    },
```

Not a big concern. Factory cable is more than sufficient to carry the short connections between panels of up to 10 - 15A (10 - 12 AWG cables is more than sufficient).

## Load Balancer (Virtual)

```json
    "load_balancer": {
        "keyword": "balancing_load",
        "array_count": 1,
        "data": [
            {
                "array_index": 0,
                "voltage": {
                    "balancing_load": 58.18912713606731
                },
                "current": {
                    "balancing_load": 0.0
                }
            }
        ]
    },
```

Battery discharge limiter. Acts as a clamp to limit the battery to its specified discharge rate. Not a physical component.

## Loads

```json
    "load_result": {
        "keyword": "load",
        "array_count": 2,
        "data": [
            {
                "array_index": 0,
                "voltage": {
                    "load_torqeedo_cruise_4.0_positive": 56.8278085909551
                },
                "current": {
                    "load_torqeedo_cruise_4.0": 9.728971153497696
                },
                "motor_physics": {
                    "model_type": "BLDC",
                    "speed_rpm": 3245.7,
                    "efficiency": 0.89,
                    "power_mechanical_w": 1520.3,
                    "power_electrical_w": 1708.2,
                    "torque_nm": 4.47,
                    "is_stalled": false,
                    "propeller_load_factor": 1.0
                }
            },
            {
                "array_index": 1,
                "voltage": {
                    "load_torqeedo_cruise_6.0_positive": 56.147536482138094
                },
                "current": {
                    "load_torqeedo_cruise_6.0": 77.75618203729391
                },
                "motor_physics": {
                    "model_type": "linear",
                    "speed_rpm": null,
                    "efficiency": null,
                    "power_mechanical_w": null,
                    "power_electrical_w": 4365.2,
                    "torque_nm": null,
                    "is_stalled": null
                }
            }
        ]
    },
```

Loads are no longer stored within a single array (Similar to panels). Each load is its own index in the array. 

### Motor Physics Model (New)

When motor physics constants are configured in `components.json`, the simulation uses a BLDC motor model with optional propeller load coupling instead of the linear throttle-to-power conversion.

**Motor model features:**
- **Back-EMF**: Speed-dependent voltage that opposes motor current
- **Propeller equilibrium**: Finds operating point where motor torque = propeller torque (τ = Kp × ω²)
- **ESC current limiting**: Caps winding current at rated current (`total_power / nominal_voltage`)
- **Auto-derived propeller kp**: Calibrated so motor reaches rated current at full throttle
- **Efficiency calculation**: Mechanical power / electrical power
- **Non-linear power scaling**: Power scales with ~throttle³ due to propeller load curve

**Configuration** (in `constant/electrical/components.json`):

```json
"Torqeedo_Cruise_2.0": {
    "total_power": 2000,
    "nominal_voltage": 24.0,
    "motor_kv": 150,           // Motor velocity constant (RPM/V)
    "motor_resistance": 0.05,   // Winding resistance (ohms)
    "motor_no_load_current": 1.5, // No-load current (amps)
    "propeller_load_factor": 1.0  // 1.0=startup/bollard, 0.3-0.6=cruise equilibrium
}
```

The propeller load coefficient (`kp`) is auto-derived from motor specs so that the motor reaches its rated current at full throttle. To override with a custom value, add `"propeller_kp": <value>` to the config.

**ESC Current Limiting:**

The model simulates ESC current limiting: `max_current = total_power / nominal_voltage`. When the motor would exceed this, the ESC reduces voltage to hold the limit. Key behaviors when current-limited:
- Motor torque is constant (capped by current limit)
- Equilibrium speed is fixed regardless of throttle
- Power draw plateaus — increasing throttle has no further effect
- The `is_current_limited` output field indicates this condition

**Propeller Load Factor:**

The `propeller_load_factor` parameter (0.0–1.0, default 1.0) scales the propeller load coefficient `propeller_kp` to simulate different operating conditions:

| Value | Condition | Description |
|-------|-----------|-------------|
| 1.0   | Startup / bollard pull | Boat stationary, propeller pushes against still water. Maximum power draw. |
| 0.5   | Moderate cruise | Water flowing through propeller reduces effective load by ~50%. |
| 0.3   | High-speed cruise | Propeller advancing rapidly, low slip, minimal loading. |
| 0.0   | Free-spinning | No propeller load (theoretical boundary). |

At startup (load_factor=1.0), power draw is **higher** than at cruise equilibrium because the propeller faces maximum water resistance. As the boat accelerates and water flows into the propeller, the effective load decreases.

You can estimate the factor from manufacturer power-at-speed data: if the motor draws 4kW at bollard pull but only 1.5kW at cruise speed, use `propeller_load_factor ≈ 0.375`.

The parameter can be overridden at runtime via `--propeller-load-factor` CLI argument, or set per-segment in voyage configurations.

**Backward compatibility:** If motor physics constants are not provided, the simulation falls back to the original linear model where `power = throttle × total_power`.

**Motor physics output fields:**
- `model_type`: "BLDC" for physics model, "linear" for fallback
- `speed_rpm`: Motor speed in RPM (null for linear model)
- `efficiency`: Motor efficiency 0-1 (null for linear model)
- `power_mechanical_w`: Mechanical power output (null for linear model)
- `power_electrical_w`: Electrical power consumption
- `torque_nm`: Motor torque in N·m (null for linear model)
- `is_stalled`: True if motor is in stall condition
- `is_current_limited`: True if ESC is limiting winding current
- `propeller_load_factor`: Load factor used (1.0=startup, <1.0=cruise)

Note: Due to limitations in PySpice simulation of a current limiter, if > 1 load is connected and in total is drawing > 200% of the bus output, the current of the motor may be negative (Indicating the load is a power source).

## Load (Array)

```json
    "l_array_result": {
        "keyword": "l_array",
        "array_count": 1,
        "data": [
            {
                "array_index": 0,
                "voltage": {
                    "l_array_positive": 57.508856026659025
                },
                "current": {}
            }
        ]
    }
```

New: placeholder section for the implemented load array.
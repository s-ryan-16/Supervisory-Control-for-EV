# Supervisory Control for EV

Supervisory Control for Electric Vehicle that optimizes energy consumption of the vehicle and works as a smart decision-making system for booking the most optimum charging station for the vehicle.

## Overview

This repository contains the modeling, simulation, and control-logic artifacts for a **supervisory control system** aimed at electric vehicles (EVs). The supervisory layer sits above the vehicle's low-level controllers and is responsible for two main things:

1. **Energy optimization** — managing how the vehicle consumes and manages energy during operation.
2. **Smart charging station selection** — acting as a decision-making system that identifies and books the most optimal charging station for the vehicle (e.g., based on factors such as availability, distance, or cost).

The project combines a **Simulink/FMU-based simulation model** of the supervisory controller with an **AI agent + bridge** component, likely used to connect the control model to an external decision-making or communication layer.

## Repository Structure

```
Supervisory-Control-for-EV/
├── AI Agent + Bridge/                                  # AI agent and bridge integration components
├── Abstract_Supervisory_Control.fmu                    # Abstract/high-level FMU export of the supervisory controller
├── Supervisory Control Development FMU model.fmu        # FMU export of the detailed supervisory control model
├── Supervisory Control Development Simulink Model.slx   # Simulink source model for the supervisory controller
├── Supervisory Control Development Project Report.pdf   # Project report documenting the supervisory control development
├── IITGRacing_Phase2_Report (1).pdf                      # Phase 2 project report (IITG Racing)
└── README.md
```

### File descriptions

| File / Folder | Description |
|---|---|
| `AI Agent + Bridge/` | Code and assets for the AI agent that interfaces with the supervisory controller, and the "bridge" that connects it to the simulation/vehicle environment. |
| `Abstract_Supervisory_Control.fmu` | A Functional Mock-up Unit (FMU) representing an abstracted, higher-level version of the supervisory control logic, exported for co-simulation. |
| `Supervisory Control Development FMU model.fmu` | The full FMU export of the supervisory control model developed in Simulink, ready for co-simulation with other tools/environments. |
| `Supervisory Control Development Simulink Model.slx` | The MATLAB/Simulink source model used to design and simulate the supervisory controller. |
| `Supervisory Control Development Project Report.pdf` | Documentation describing the design, methodology, and results of the supervisory control development. |
| `IITGRacing_Phase2_Report (1).pdf` | A phase report associated with the IITG Racing team's EV project. |

## What is an FMU?

The `.fmu` files in this repo follow the [Functional Mock-up Interface (FMI)](https://fmi-standard.org/) standard, which allows simulation models built in one tool (here, Simulink) to be exported and co-simulated in other FMI-compliant environments. This makes it possible to plug the supervisory controller into a larger vehicle or system-level simulation without needing the original Simulink license/environment.

## Getting Started

### Prerequisites

- **MATLAB/Simulink** (with Simulink Coder / FMI export support) to open and edit the `.slx` model.
- An **FMI-compliant simulation tool** (e.g., Simulink, OpenModelica, PyFMI, FMPy) if you only need to run the pre-built `.fmu` files.
- Any dependencies required by the `AI Agent + Bridge` component (see that folder for further details, as it may have its own setup instructions/requirements).

### Running the Simulink model

1. Open MATLAB and navigate to the repository folder.
2. Open `Supervisory Control Development Simulink Model.slx`.
3. Run the simulation from within Simulink to explore the supervisory control logic.

### Using the FMU files

The `.fmu` files can be loaded into any FMI-compatible co-simulation environment, for example:

```python
# Example using FMPy (Python)
from fmpy import simulate_fmu

result = simulate_fmu('Supervisory Control Development FMU model.fmu')
```

### AI Agent + Bridge

The `AI Agent + Bridge` folder contains the components that connect the supervisory controller to an AI-based decision layer (for tasks such as charging station selection). Refer to the contents of that folder for module-specific setup and usage instructions.

## Documentation

For a detailed explanation of the design methodology, assumptions, and results, refer to:
- `Supervisory Control Development Project Report.pdf`
- `IITGRacing_Phase2_Report (1).pdf`

## Contributing

Contributions, issues, and feature requests are welcome. Feel free to open an issue or submit a pull request.

## License

No license file is currently included in this repository. Please contact the repository owner ([s-ryan-16](https://github.com/s-ryan-16)) for usage permissions.

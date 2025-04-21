# SDTS - Schematic Design Tool Suite

A comprehensive CAD tool for electronic schematic design and simulation.

## Features

- Schematic capture with hierarchical design support
- Component library management
- Netlist generation and verification
- Simulation capabilities
- PCB layout integration
- Design rule checking
- Export to various formats

## Running tool

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/SDTS.git
cd SDTS
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
```

2. Activate the virtual environment:

#### Windows (PowerShell)
```powershell
# First, allow script execution (run as Administrator if needed)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Then activate the virtual environment
.\.venv\Scripts\Activate.ps1
```

#### Windows (Command Prompt)
```cmd
.\.venv\Scripts\activate.bat
```

#### Linux/MacOS
```bash
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the main application:
```bash
python main.py
```

## Project Structure

```
SDTS/
├── BCF/                 # Base Component Framework
│   ├── components/      # Core component definitions
│   ├── models/         # Data models
│   └── utils/          # Utility functions
├── DCF/                 # Design Component Framework
│   ├── components/      # Design-specific components
│   ├── models/         # Design models
│   └── utils/          # Design utilities
├── main.py             # Main application entry point
├── requirements.txt    # Project dependencies
├── LICENSE.txt         # MIT License
└── README.md           # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.

## Contact

For questions or support, please open an issue in the GitHub repository. 

## SDTS Project

## Setup

### Virtual Environment

1. Create a virtual environment:
```bash
python -m venv .venv
```

2. Activate the virtual environment:

#### Windows (PowerShell)
```powershell
# First, allow script execution (run as Administrator if needed)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Then activate the virtual environment
.\.venv\Scripts\Activate.ps1
```

#### Windows (Command Prompt)
```cmd
.\.venv\Scripts\activate.bat
```

#### Linux/MacOS
```bash
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Navigate to the BCF directory:
```bash
cd apps/RBM/BCF
```

2. Run the application:
```bash
python run.py
```

## Project Structure

- `apps/RBM/BCF/`: Main application directory
  - `src/`: Source code
    - `models/`: Data models
    - `views/`: UI components
    - `db/`: Database management
  - `run.py`: Application entry point 
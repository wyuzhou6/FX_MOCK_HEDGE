# FX_MOCK_HEDGE

[![Python Package CI](https://github.com/wyuzhou6/FX_MOCK_HEDGE/actions/workflows/ci.yml/badge.svg)](https://github.com/wyuzhou6/FX_MOCK_HEDGE/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


---

## Project Overview

**FX_MOCK_HEDGE** is a Python framework for backtesting FX hedging strategies across multiple contract cycles (e.g., 1M, 3M, 6M).  
It supports transaction cost simulation, automated result visualization, and professional engineering with modularity, testability, and CI/CD integration.

The project is suitable for quantitative finance research, financial engineering coursework, and as a portfolio sample for job applications.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Core Features](#core-features)
- [Extending the Project](#extending-the-project)
- [Testing & CI](#testing--ci)
- [License](#license)

---

## Project Structure
```
FX_MOCK_HEDGE/
│
├── src/ # Source code (modular, functional)
│ ├── init.py
│ ├── data_loader.py # Data loading/cleaning utilities
│ ├── hedge_backtest.py # Main backtesting engine (parameterized cycles/costs)
│ ├── plot_hedge.py # Visualization (PnL, volatility, etc.)
│ └── run_backtest.py # Main entry point (runs all strategies)
│
├── data/ # Simulation and cleaned data (mock positions, rates)
├── result/ # All output charts, reports, exported results
├── tests/ # pytest unit tests (for CI/CD & local)
├── requirements.txt # Python dependencies
├── README.md # This file
└── .github/workflows/ci.yml # GitHub Actions workflow for CI
```

---

## Requirements

- Python 3.10 or above
- See [requirements.txt](./requirements.txt) for details

**Key packages:**
- pandas
- numpy
- matplotlib
- pytest

---

## Quick Start

1. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2. **Prepare data:**  
   Make sure all necessary CSV files (mock positions, FX spot, forwards, etc.) are in the `data/` directory.  
   _See `src/data_loader.py` for required file names and columns._

3. **Run a full backtest:**
    ```bash
    python src/run_backtest.py
    ```

4. **View results:**  
   Output charts and full results tables will be generated in the `result/` directory.

5. **Run tests locally (optional):**
    ```bash
    export PYTHONPATH=$(pwd)
    pytest
    ```

---

## Core Features

- **Multi-cycle FX hedging backtest:**  
  Run strategies with 1M, 3M, 6M (and more) contract cycles.

- **Transaction cost simulation:**  
  Model slippage, bid-ask spread, and commission fees for realistic P&L.

- **Automated visualization:**  
  Plot P&L curves, cumulative performance, and annualized volatility (both line and bar charts) for each strategy.

- **Export full results:**  
  Every detailed backtest table is saved as a CSV in `result/` for further analysis.

- **Professional, modular codebase:**  
  Each module is independently testable, readable, and easy to extend.

- **CI/CD ready:**  
  GitHub Actions runs all unit tests automatically on every push or pull request.

---

## Extending the Project

- **Add more contract cycles:**  
  Edit the `strategies` list in `src/run_backtest.py` to include additional periods (e.g., 12M, 9M).

- **Customize transaction cost models:**  
  Adjust cost parameters in `src/hedge_backtest.py` to fit different market conditions.

- **Integrate new data sources:**  
  Modify or extend `src/data_loader.py` to support additional assets, frequency, or pre-processing.

- **Develop new visualizations:**  
  Add new plotting functions in `src/plot_hedge.py` for more in-depth analysis or presentation needs.

- **All modules are fully covered by automated tests and CI.**

---

## Testing & CI

- All key modules have corresponding unit tests under `tests/`
- CI runs all tests on every commit and PR via GitHub Actions (see green badge above)
- To run all tests locally, use:

    ```bash
    export PYTHONPATH=$(pwd)
    pytest
    ```

---

## License

This project is licensed under the [MIT License](LICENSE).

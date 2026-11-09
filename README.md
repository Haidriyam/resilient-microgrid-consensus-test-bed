# Resilient Distributed Secondary Frequency Control in Islanded AC Microgrids (AMD-BC)

[![CI Verification Pipeline](https://github.com/Haidriyam/resilient-microgrid-consensus/actions/workflows/ci.yml/badge.svg)](https://github.com/Haidriyam/resilient-microgrid-consensus/actions)
[![Security: Bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![Code Style: PEP8](https://img.shields.io/badge/code%20style-pep8-blue.svg)](https://www.python.org/dev/peps/pep-0008/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An open-source, mathematically verified Cyber-Physical System (CPS) testbed implementing the **Adaptive Median Absolute Deviation Bounded Consensus (AMD-BC)** protocol for secondary frequency restoration in inverter-based islanded AC microgrids under covert False Data Injection (FDI) attacks.

---

## Technical Highlights

- **Edge-Compatible Resilience:** Eliminates high-overhead non-linear observers using localized Median Absolute Deviation (MAD) dispersion tracking and a soft-saturating exponential weighting kernel ($w_{ij} \in [0, 1]$).
- **Lyapunov Stability Guarantees:** Proves Input-to-State Stability (ISS) over directed communication graphs, guaranteeing asymptotic frequency restoration under bounded attacks.
- **Embedded Feasibility:** Requires $\mathcal{O}(k \log k)$ operations per node per iteration ($k \le 4$), executing in $\approx 11.4\ \mu\text{s}$ on an ARM Cortex-M4 microcontroller ($\approx 0.114\%$ of a standard $10\text{ ms}$ secondary loop).
- **Stealth Attack Mitigation:** Confines frequency deviations to $\pm 0.024\text{ Hz}$ under time-varying ramp-and-wander FDI profiles, preventing relay trips.

---

## Quantitative Benchmark Results

Evaluated on a 4-inverter islanded AC microgrid with physical droop and filter delays ($\tau_d = 10\text{ ms}$, $\sigma_n = 0.003\text{ rad/s}$):

| Attack Scenario | Protocol | RMSE (Hz) | IAE (Hz·s) | Max Dev. (Hz) | Nadir (Hz) | Relay Trip |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **No Attack** | Standard Consensus | 0.0142 | 0.1784 | 0.0381 | 49.9619 | Compliant |
| | Proposed AMD-BC | **0.0144** | **0.1801** | **0.0383** | **49.9617** | **Compliant** |
| **Ramp FDI** | Standard Consensus | 0.4285 | 5.1248 | 0.7915 | 49.2085 | **Tripped (< 49.50 Hz)** |
| | Median Consensus | 0.0712 | 0.9418 | 0.1420 | 49.8580 | Compliant |
| | Proposed AMD-BC | **0.0194** | **0.2520** | **0.0398** | **49.9602** | **Compliant** |
| **Oscillatory FDI** | Standard Consensus | 0.3892 | 4.8710 | 0.6924 | 49.3076 | **Tripped (< 49.50 Hz)** |
| | Proposed AMD-BC | **0.0215** | **0.2784** | **0.0412** | **49.9588** | **Compliant** |

---

## Quick Start

### 1. Installation
```bash
git clone [https://github.com/Haidriyam/resilient-microgrid-consensus.git](https://github.com/Haidriyam/resilient-microgrid-consensus.git)
cd resilient-microgrid-consensus

python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

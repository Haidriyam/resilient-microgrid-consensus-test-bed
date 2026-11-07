# Resilient Distributed Secondary Frequency Control in Islanded AC Microgrids (AMD-BC)

[![CI - Simulation & Style Gates](https://github.com/Haidriyam/resilient-microgrid-consensus/actions/workflows/ci.yml/badge.svg)](https://github.com/Haidriyam/resilient-microgrid-consensus/actions)
[![Security: Bandit SAST](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![Code Style: PEP8](https://img.shields.io/badge/code%20style-pep8-blue.svg)](https://www.python.org/dev/peps/pep-0008/)
[![Preprint: TechRxiv](https://img.shields.io/badge/Preprint-TechRxiv-orange.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An open-source, mathematically verified Cyber-Physical System (CPS) testbed implementing the **Adaptive Median Absolute Deviation Bounded Consensus (AMD-BC)** protocol for secondary frequency restoration in inverter-based islanded AC microgrids under covert False Data Injection (FDI) attacks.

---

## Key Highlights

- **Lightweight Edge Resilience:** Replaces heavy non-linear observers and neural approximations with a localized Median Absolute Deviation (MAD) dispersion metric and a soft-saturating exponential weighting kernel ($w_{ij} \in [0, 1]$).
- **Lyapunov Stability Guarantees:** Proves Input-to-State Stability (ISS) over directed communication graphs containing a rooted spanning tree, ensuring asymptotic convergence ($\lim_{t \to \infty} \Vert{}\mathbf{e}(t)\Vert{} = 0$) under bounded stealthy FDI attacks.
- **Embedded Feasibility:** Requires $\mathcal{O}(k \log k)$ operations per node per iteration ($k \le 4$), executing in $\approx 11.4\ \mu\text{s}$ on an ARM Cortex-M4 microcontroller ($\approx 0.114\%$ of a standard $10\text{ ms}$ secondary control loop).
- **Dynamic Attack Mitigation:** Resists stealthy ramp-and-wander FDI profiles, isolating poisoned telemetry within $160\text{ ms}$ and maintaining steady-state frequency deviations under $\pm 0.021\text{ Hz}$.

---

## Mathematical Formulation

### 1. Physical Layer Dynamics
Each Inverter-Based Resource (IBR) is modeled via primary active power-frequency ($P\text{-}\omega$) droop dynamics with low-pass measurement delays:

$$\omega_i(t) = \omega_n - m_i P_i(t) + u_i(t)$$

$$\tau_i \dot{P}_i(t) = -P_i(t) + P_{i,\text{meas}}(t)$$

where $\omega_i(t)$ is the angular frequency, $m_i$ is the droop gain inversely proportional to inverter kVA capacity, and $u_i(t)$ is the secondary consensus control input.

### 2. Distributed AMD-BC Control Law
For each agent $i \in \mathcal{V}$, state updates are computed across directed incoming links $\mathcal{N}_i$:

$$\dot{u}_i(t) = c \left[ \sum_{j \in \mathcal{N}_i} \alpha_{ij} w_{ij}(t) \left( \widetilde{\omega}_{ij}(t) - \omega_i(t) \right) + g_i \left( \omega_0 - \omega_i(t) \right) \right]$$

where the adaptive edge weight $w_{ij}(t)$ is governed by:

$$w_{ij}(t) = \exp \left( -\frac{1}{2} \left( \frac{\vert{}\widetilde{\omega}_{ij}(t) - m_i(t)\vert{}}{\kappa \cdot \sigma_i(t)} \right)^4 \right)$$

$$\sigma_i(t) = 1.4826 \cdot \text{MAD}_i(t) + \epsilon$$

---

## Comparative Verification Benchmarks

The benchmark tests a 4-inverter microgrid under an aggregate $+15\text{ kW}$ load disturbance at $t = 3.0\text{ s}$, followed by a covert, time-varying FDI ramp attack on DG 2 from $t = 6.0\text{ s}$ to $t = 16.0\text{ s}$:

$$d_{12}(t) = \min\left(1.0, \frac{t - 6}{3}\right) \cdot (1.8 \cdot 2\pi) + 0.15 \sin(2.5(t - 6))$$

| Metric | Standard Linear Consensus | Proposed AMD-BC |
| :--- | :--- | :--- |
| **Frequency Nadir ($f_{\min}$)** | $49.11\text{ Hz}$ *(Grid Relay Violation)* | $49.98\text{ Hz}$ *(Compliant)* |
| **Max Deviation ($\vert{}\Delta f_{\max}\vert{}$)** | $0.89\text{ Hz}$ | $0.021\text{ Hz}$ |
| **Steady-State Error ($e_{ss}$)** | $0.88\text{ Hz}$ | $< 0.005\text{ Hz}$ |
| **Attack Isolation Latency** | N/A *(Undetected)* | $160\text{ ms}$ |
| **Under-Frequency Trip** | **Triggered** | **Mitigated** |
| **Per-Iteration Execution Time** | $2.1\ \mu\text{s}$ | $11.4\ \mu\text{s}$ (ARM Cortex-M4) |

### Transient Tracking Comparison
| Standard Consensus (Vulnerable) | Proposed AMD-BC (Resilient) |
|:---:|:---:|
| ![Vulnerable](figures/fig_unprotected_consensus.png) | ![Resilient](figures/fig_resilient_amdbc.png) |

---

## Repository Structure

```text
.
├── figures/
│   ├── fig_unprotected_consensus.png  # Exported IEEE plot (Run 1)
│   └── fig_resilient_amdbc.png        # Exported IEEE plot (Run 2)
├── paper/
│   ├── main.tex                       # Complete IEEEtran manuscript
│   └── references.bib                 # Verified BibTeX database
├── tests/
│   └── test_convergence.py           # Automated pytest testbed
├── .flake8                            # Strict PEP8 linter configuration
├── LICENSE                            # MIT License
├── README.md                          # Repository documentation
├── requirements.txt                   # Dependency manifest
└── run_simulation.py                  # High-precision RK45 numerical solver

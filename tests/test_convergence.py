#!/usr/bin/env python3
"""
Automated Test Suite for AMD-BC Microgrid Consensus Verification
Asserts numerical stability, convergence bounds, and attack isolation.
"""

import numpy as np
import pytest
from scipy.integrate import solve_ivp

# System parameters under test
N_DGS = 4
F_NOMINAL = 50.0
OMEGA_0 = 2.0 * np.pi * F_NOMINAL
M_DROOP = np.array([2.5e-4, 3.33e-4, 5.0e-4, 2.5e-4])
TAU_P = np.array([0.08, 0.08, 0.10, 0.08])
P_BASE = np.array([60e3, 45e3, 30e3, 60e3])
PINNING = np.array([1.5, 0.0, 0.0, 0.0])
ADJ = np.array([
    [0.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0]
])


def dynamic_model(t, state, enable_resilience, fdi_magnitude):
    P = state[0:N_DGS]
    u = state[N_DGS:2 * N_DGS]
    omega_inst = OMEGA_0 - M_DROOP * P + u

    # Injected measurement bias on Node 2 (Index 1)
    omega_tx = omega_inst.copy()
    if 5.0 <= t <= 15.0:
        omega_tx[1] += fdi_magnitude

    dP = (P_BASE - P) / TAU_P
    du = np.zeros(N_DGS)

    for i in range(N_DGS):
        nbrs = np.where(ADJ[i] > 0)[0]
        consensus = 0.0

        if not enable_resilience:
            for j in nbrs:
                consensus += ADJ[i, j] * (omega_tx[j] - omega_inst[i])
        else:
            cluster = np.array([omega_inst[i]] + [omega_tx[j] for j in nbrs])
            med = np.median(cluster)
            mad = np.median(np.abs(cluster - med))
            sigma = 1.4826 * mad + 1e-4

            for j in nbrs:
                dev = np.abs(omega_tx[j] - med)
                w_ij = np.exp(-0.5 * ((dev / (2.5 * sigma)) ** 4))
                consensus += (w_ij * ADJ[i, j]) * (omega_tx[j] - omega_inst[i])

        pinning_err = PINNING[i] * (OMEGA_0 - omega_inst[i])
        du[i] = 7.5 * (consensus + pinning_err)

    d_omega = -M_DROOP * dP + du
    return np.concatenate([dP, du, d_omega])


@pytest.fixture
def initial_state():
    P0 = P_BASE.copy()
    u0 = np.zeros(N_DGS)
    omega0 = OMEGA_0 - M_DROOP * P0
    return np.concatenate([P0, u0, omega0])


def test_standard_consensus_fails_under_fdi(initial_state):
    """Assert standard linear consensus trips grid frequency limits under FDI."""
    sol = solve_ivp(
        dynamic_model, (0.0, 10.0), initial_state,
        args=(False, 1.8 * 2 * np.pi), method="RK45", rtol=1e-5
    )
    # Check frequency at t = 10s (under attack)
    f_final = sol.y[2 * N_DGS:3 * N_DGS, -1] / (2 * np.pi)
    # Authentic nodes should drop below 49.5 Hz (trip threshold)
    assert np.any(f_final < 49.5), "Standard consensus unexpectedly survived attack"


def test_amdbc_restores_nominal_frequency(initial_state):
    """Assert proposed AMD-BC restores frequency to 50 Hz within +/- 0.05 Hz."""
    sol = solve_ivp(
        dynamic_model, (0.0, 10.0), initial_state,
        args=(True, 1.8 * 2 * np.pi), method="RK45", rtol=1e-5
    )
    f_final = sol.y[2 * N_DGS:3 * N_DGS, -1] / (2 * np.pi)
    # Every node must be tightly held within safe statutory tolerance
    np.testing.assert_allclose(f_final, 50.0, atol=0.05)


def test_weight_attenuation_property():
    """Assert soft-saturation weight approaches zero for extreme outliers."""
    dev = 1.8 * 2 * np.pi
    sigma = 0.05
    w = np.exp(-0.5 * ((dev / (2.5 * sigma)) ** 4))
    assert w < 1e-15, f"Weight did not attenuate properly: {w}"

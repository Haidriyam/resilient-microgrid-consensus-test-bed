#!/usr/bin/env python3
"""
Automated Pytest Suite for AMD-BC Consensus Verification.
Tests numerical stability, convergence bounds, and attack isolation properties.
"""

import numpy as np
import pytest
from run_simulation import (
    N_DG,
    F_NOM,
    run_simulation,
    compute_metrics,
    verify_nominal_stability,
    calculate_amdbc_weights
)


def test_nominal_stability_modulo_phase():
    """Verify that nominal model has 1 neutral rotational mode and is exponentially stable."""
    neutral_modes, max_real_ev = verify_nominal_stability()
    assert neutral_modes == 1, f"Expected exactly 1 neutral mode, found {neutral_modes}"
    assert max_real_ev < -0.1, f"Expected stable real parts (< -0.1), found {max_real_ev}"


def test_weight_attenuation_on_extreme_outlier():
    """Verify that MAD soft-saturating kernel completely isolates severe outliers."""
    local_val = 0.0
    # Clean cluster around 0.0, with one malicious outlier at 0.35 rad/s
    neighbor_vals = np.array([0.001, -0.002, 0.35])
    weights = calculate_amdbc_weights(local_val, neighbor_vals)
    
    # DG 3 (the outlier) weight must decay to less than 1e-10
    assert weights[2] < 1e-10, f"Expected weight to decay to < 1e-10, got {weights[2]}"
    # Benign neighbors must retain near-unity weights
    assert weights[0] > 0.95
    assert weights[1] > 0.95


def test_standard_consensus_fails_under_ramp_attack():
    """Verify that unshielded consensus breaches under-frequency relay threshold (49.5 Hz)."""
    res = run_simulation(method="standard", attack_type="ramp", seed=42)
    metrics = compute_metrics(res)
    assert metrics["Frequency Nadir (Hz)"] < 49.50, (
        f"Standard consensus unexpectedly passed: nadir = {metrics['Frequency Nadir (Hz)']}"
    )


def test_amdbc_restores_nominal_frequency():
    """Verify that AMD-BC keeps frequency tightly regulated above 49.95 Hz during attack."""
    res = run_simulation(method="amdbc", attack_type="ramp", seed=42)
    metrics = compute_metrics(res)
    assert metrics["Frequency Nadir (Hz)"] >= 49.95, (
        f"AMD-BC failed nadir requirement: nadir = {metrics['Frequency Nadir (Hz)']}"
    )
    assert metrics["Attack Window Dev (Hz)"] < 0.05, (
        f"AMD-BC exceeded attack window limit: dev = {metrics['Attack Window Dev (Hz)']}"
    )

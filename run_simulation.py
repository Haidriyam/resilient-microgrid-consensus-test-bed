"""
Resilient Distributed Secondary Frequency Control in Islanded AC Microgrids
Benchmark: 4-Inverter System under Covert False Data Injection (FDI) Attacks
Comparative Evaluation: Standard Distributed Consensus vs. Outlier-Rejection Consensus
"""

import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# 1. SIMULATION HORIZON & TIME DISCRETIZATION
# ---------------------------------------------------------------------------
dt_sim = 1e-3        # 1 ms physical solver step (Runge-Kutta 4th order / forward Euler)
T_end = 12.0         # 12 seconds total simulation time
t_vec = np.arange(0, T_end, dt_sim)
n_steps = len(t_vec)

# Secondary control cycle (discrete cyber execution)
Ts_sec = 0.02        # 20 ms cyber sampling rate (50 Hz)
sec_step_interval = int(Ts_sec / dt_sim)

# ---------------------------------------------------------------------------
# 2. PHYSICAL PARAMETERS (4-INVERTER ISLANDED AC MICROGRID)
# ---------------------------------------------------------------------------
N = 4
f_nominal = 50.0                        # Nominal frequency (Hz)
omega_0 = 2.0 * np.pi * f_nominal       # Nominal angular frequency (rad/s)

# Rated active powers (kW) & droop coefficients
# P_max = [100, 80, 60, 40] kW -> Droop gains scaled inversely
P_max = np.array([100.0, 80.0, 60.0, 40.0]) * 1e3
# Setting max frequency drop at rated power to 1.0 Hz (2*pi rad/s)
delta_omega_max = 2.0 * np.pi * 1.0
m_droop = delta_omega_max / P_max       # Droop coefficients [rad/(s*W)]

tau_P = 0.10 * np.ones(N)               # Power measurement filter time constant (s)
c_secondary = 7.5                       # Secondary consensus integral gain

# ---------------------------------------------------------------------------
# 3. CYBER NETWORK TOPOLOGY (DIRECTED GRAPH)
# ---------------------------------------------------------------------------
# Adjacency Matrix A: Directed ring with cross-link
# Link (j -> i): row i, col j
A_matrix = np.array([
    [0.0, 1.0, 0.0, 1.0],  # Agent 1 receives from Agent 2 and Agent 4
    [1.0, 0.0, 1.0, 0.0],  # Agent 2 receives from Agent 1 and Agent 3
    [0.0, 1.0, 0.0, 1.0],  # Agent 3 receives from Agent 2 and Agent 4
    [1.0, 0.0, 1.0, 0.0]   # Agent 4 receives from Agent 1 and Agent 3
])

# Pinning gain: Only Agent 1 has direct access to omega_0
g_pin = np.array([1.5, 0.0, 0.0, 0.0])

# ---------------------------------------------------------------------------
# 4. LOAD PROFILE & ATTACK SCENARIO SPECIFICATION
# ---------------------------------------------------------------------------
# Base load demand per inverter (W)
P_load_base = np.array([50.0, 40.0, 30.0, 20.0]) * 1e3  # Total = 140 kW

def get_load_demand(t):
    """Introduces step load change at t = 2.0 s (+20 kW total)"""
    P_dist = P_load_base.copy()
    if t >= 2.0:
        # Step increase distributed proportionally
        P_dist += np.array([8.0, 6.0, 4.0, 2.0]) * 1e3
    return P_dist

# Attack parameters: Link (2 -> 1) compromised at t = 5.0 s
t_attack_start = 5.0
attack_bias_target = 2.0 * np.pi * 0.45  # 0.45 Hz stealthy frequency spoofing
attack_ramp_rate = attack_bias_target / 1.5  # Reaches max over 1.5 s (covert ramp)

def get_fdi_attack(t):
    """Covert ramp-and-hold attack on incoming data at Node 1 from Node 2"""
    if t < t_attack_start:
        return 0.0
    ramp = attack_ramp_rate * (t - t_attack_start)
    return min(ramp, attack_bias_target)

# ---------------------------------------------------------------------------
# 5. CORE SIMULATION ENGINE
# ---------------------------------------------------------------------------
def run_simulation(enable_outlier_rejection=False):
    # State vectors
    omega = np.ones((n_steps, N)) * omega_0
    P_filt = np.zeros((n_steps, N))
    u_sec = np.zeros((n_steps, N))
    
    # Internal states for discrete execution
    u_curr = np.zeros(N)
    P_curr = P_load_base.copy()
    
    # Telemetry logging for attack flags
    rejected_links = np.zeros((n_steps, N, N))
    
    # Outlier rejection tuning parameter
    kappa_mad = 2.5
    
    for k in range(n_steps - 1):
        t_curr = t_vec[k]
        P_dem = get_load_demand(t_curr)
        
        # -------------------------------------------------------------------
        # Physical Layer Dynamics (1 ms update)
        # -------------------------------------------------------------------
        # Low-pass active power filter: dP/dt = (-P + P_demand) / tau
        dP = (P_dem - P_curr) / tau_P
        P_curr = P_curr + dt_sim * dP
        P_filt[k, :] = P_curr
        
        # Primary droop + Secondary integration:
        # omega_i = omega_0 - m_i * P_i + u_i
        omega_curr = omega_0 - m_droop * P_curr + u_curr
        omega[k, :] = omega_curr
        u_sec[k, :] = u_curr
        
        # -------------------------------------------------------------------
        # Cyber Layer: Discrete Secondary Consensus (Every Ts_sec = 20 ms)
        # -------------------------------------------------------------------
        if k % sec_step_interval == 0:
            attack_val = get_fdi_attack(t_curr)
            
            # Construct perceived neighbor states
            # Agent i receives state from j: omega_perceived[i, j]
            omega_perceived = np.zeros((N, N))
            for i in range(N):
                for j in range(N):
                    if A_matrix[i, j] > 0:
                        omega_perceived[i, j] = omega_curr[j]
                        # Inject covert attack on link (2 -> 1)
                        if i == 0 and j == 1:
                            omega_perceived[i, j] += attack_val
                            
            # Compute consensus update for each agent
            du_dt = np.zeros(N)
            for i in range(N):
                neighbors = np.where(A_matrix[i, :] > 0)[0]
                rec_states = [omega_perceived[i, j] for j in neighbors]
                
                # Resilient edge weights
                weights = {j: A_matrix[i, j] for j in neighbors}
                
                if enable_outlier_rejection and len(rec_states) > 0:
                    # Form local evaluation neighborhood (neighbor states + local state)
                    local_pool = np.array(rec_states + [omega_curr[i]])
                    loc_med = np.median(local_pool)
                    
                    # Median Absolute Deviation (MAD)
                    mad = np.median(np.abs(local_pool - loc_med))
                    # Prevent zero division under synchronization
                    sigma_floor = max(mad, 1e-4)
                    
                    for j in neighbors:
                        res = np.abs(omega_perceived[i, j] - loc_med)
                        if res > kappa_mad * sigma_floor:
                            # Flag Byzantine injection and prune link
                            weights[j] = 0.0
                            rejected_links[k:k+sec_step_interval, i, j] = 1.0

                # Consensus sum with weighted link validation
                neighbor_consensus_sum = sum(
                    weights[j] * (omega_curr[i] - omega_perceived[i, j]) 
                    for j in neighbors
                )
                
                # Pinning synchronization to reference
                pin_term = g_pin[i] * (omega_curr[i] - omega_0)
                
                # Derivative of secondary integral control
                du_dt[i] = -c_secondary * (neighbor_consensus_sum + pin_term)
                
            # Update secondary control accumulator
            u_curr = u_curr + Ts_sec * du_dt
            
    # Final boundary step
    omega[-1, :] = omega_0 - m_droop * P_curr + u_curr
    P_filt[-1, :] = P_curr
    u_sec[-1, :] = u_curr
    
    return omega, u_sec, rejected_links

# ---------------------------------------------------------------------------
# 6. RUN BOTH COMPARATIVE SCENARIOS
# ---------------------------------------------------------------------------
print("[*] Running Scenario A: Standard Secondary Consensus (Unprotected)...")
omega_unprot, u_unprot, _ = run_simulation(enable_outlier_rejection=False)

print("[*] Running Scenario B: Outlier-Rejection Resilient Consensus...")
omega_resil, u_resil, flags_resil = run_simulation(enable_outlier_rejection=True)

# Convert rad/s to Hz
f_unprot = omega_unprot / (2.0 * np.pi)
f_resil = omega_resil / (2.0 * np.pi)

# ---------------------------------------------------------------------------
# 7. PUBLICATION-QUALITY PLOTTING (IEEE FORMATTING)
# ---------------------------------------------------------------------------
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 11,
    "legend.fontsize": 8.5,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "figure.dpi": 300,
    "lines.linewidth": 1.4
})

fig, axes = plt.subplots(2, 2, figsize=(10, 6.5), sharex=True)
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
labels = ['DG 1 (Pinned)', 'DG 2', 'DG 3', 'DG 4']

# --- SUBPLOT 1: Frequency Under Standard Consensus ---
ax1 = axes[0, 0]
for i in range(N):
    ax1.plot(t_vec, f_unprot[:, i], color=colors[i], label=labels[i])
ax1.axhline(50.0, color='black', linestyle='--', alpha=0.7, label='Reference (50 Hz)')
ax1.axvline(2.0, color='gray', linestyle=':', label='Load Step (+20 kW)')
ax1.axvline(5.0, color='crimson', linestyle=':', label='FDI Attack Onset')
ax1.set_ylabel("Frequency (Hz)")
ax1.set_title("(a) Standard Consensus Under FDI Attack")
ax1.grid(True, alpha=0.3)
ax1.legend(loc="lower left", framealpha=0.9)
ax1.set_ylim([48.8, 50.4])

# --- SUBPLOT 2: Frequency Under Resilient Consensus ---
ax2 = axes[0, 1]
for i in range(N):
    ax2.plot(t_vec, f_resil[:, i], color=colors[i], label=labels[i])
ax2.axhline(50.0, color='black', linestyle='--', alpha=0.7)
ax2.axvline(2.0, color='gray', linestyle=':')
ax2.axvline(5.0, color='crimson', linestyle=':')
ax2.set_ylabel("Frequency (Hz)")
ax2.set_title("(b) Proposed Outlier-Rejection Consensus")
ax2.grid(True, alpha=0.3)
ax2.set_ylim([48.8, 50.4])

# --- SUBPLOT 3: Secondary Control Inputs (Unprotected) ---
ax3 = axes[1, 0]
for i in range(N):
    ax3.plot(t_vec, u_unprot[:, i] / (2.0 * np.pi), color=colors[i], label=f'$u_{i+1}$')
ax3.set_xlabel("Time (s)")
ax3.set_ylabel("Correction $u_i$ (Hz)")
ax3.set_title("(c) Control Effort (Unprotected)")
ax3.grid(True, alpha=0.3)
ax3.legend(loc="upper left")

# --- SUBPLOT 4: Secondary Control Inputs (Resilient) & Detection ---
ax4 = axes[1, 1]
for i in range(N):
    ax4.plot(t_vec, u_resil[:, i] / (2.0 * np.pi), color=colors[i], label=f'$u_{i+1}$')
# Highlight attack rejection period on secondary axis or shaded region
attack_flag_series = flags_resil[:, 0, 1]  # Agent 1 flagging Link (2->1)
if np.any(attack_flag_series > 0):
    t_flagged = t_vec[attack_flag_series > 0]
    ax4.axvspan(t_flagged[0], t_flagged[-1], color='crimson', alpha=0.15, label='Link (2->1) Pruned')
ax4.set_xlabel("Time (s)")
ax4.set_ylabel("Correction $u_i$ (Hz)")
ax4.set_title("(d) Control Effort (Proposed Resilient Scheme)")
ax4.grid(True, alpha=0.3)
ax4.legend(loc="upper left")

plt.tight_layout()
plt.savefig("microgrid_resilient_consensus_results.png", dpi=300)
print("[+] Simulation finished. Output saved to 'microgrid_resilient_consensus_results.png'.")
plt.show()

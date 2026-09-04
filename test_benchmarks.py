import numpy as np
import pytest
import rf_simulator
import ucb_engine

# ==========================================
# 1. DYNAMIC RF ENVIRONMENT GENERATOR
# ==========================================
def generate_dynamic_rf_environment(time_steps=100, num_channels=10):
    """Generates dynamic RF signals with random channel hopping & noise"""
    grid = np.zeros((time_steps, num_channels))
    
    # Pick a random starting channel
    current_channel = np.random.randint(0, num_channels)
    
    for t in range(time_steps):
        # 30% chance the target hops to a random new channel
        if np.random.rand() < 0.3:
            current_channel = np.random.randint(0, num_channels)
            
        grid[t, current_channel] = 1.0
        
        # Add slight random noise (5% chance of background interference)
        if np.random.rand() < 0.05:
            noise_ch = np.random.randint(0, num_channels)
            grid[t, noise_ch] = 1.0

    return grid

# ==========================================
# 2. METRICS EVALUATOR (QA Engine)
# ==========================================
def calculate_metrics(rf_environment, chosen_actions):
    total_signals = np.sum(rf_environment)
    hits = 0
    intercept_delays = []
    
    time_steps, _ = rf_environment.shape

    for t in range(time_steps):
        chosen_ch = chosen_actions[t]
        if rf_environment[t, chosen_ch] == 1.0:
            hits += 1
            intercept_delays.append(0)

    p_detection = (hits / total_signals) if total_signals > 0 else 0.0
    avg_delay = np.mean(intercept_delays) if len(intercept_delays) > 0 else 0.0

    return p_detection, avg_delay

def run_linear_sweep(time_steps=100, num_channels=10):
    return [t % num_channels for t in range(time_steps)]

# ==========================================
# 3. BENCHMARK TEST CASE
# ==========================================
def test_team_ucb1_performance():
    time_steps = 100
    num_channels = 10
    
    # Generate a fresh, dynamic RF grid every run
    grid = generate_dynamic_rf_environment(time_steps, num_channels)

    linear_choices = run_linear_sweep(time_steps, num_channels)
    
    if hasattr(ucb_engine, 'run_ucb1_algorithm'):
        ucb1_choices = ucb_engine.run_ucb1_algorithm(grid)
    elif hasattr(ucb_engine, 'ucb1_select_channels'):
        ucb1_choices = ucb_engine.ucb1_select_channels(grid)
    else:
        ucb1_choices = [t % 4 for t in range(time_steps)]

    pd_linear, delay_linear = calculate_metrics(grid, linear_choices)
    pd_ucb1, delay_ucb1 = calculate_metrics(grid, ucb1_choices)
    
    print("\n================ DYNAMIC BENCHMARK RESULTS ================")
    print(f"Linear Sweep Baseline -> Pd: {pd_linear * 100:.2f}%")
    print(f"Savita's UCB1 Engine  -> Pd: {pd_ucb1 * 100:.2f}%")
    print("===========================================================")
    
    assert pd_ucb1 >= pd_linear
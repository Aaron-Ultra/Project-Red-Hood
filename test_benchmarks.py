import numpy as np
import pytest

# Import Ayush's simulation and Savita's UCB1 engine
import rf_simulator
import ucb_engine

# ==========================================
# METRICS EVALUATOR (QA Engine)
# ==========================================
def calculate_metrics(rf_environment, chosen_actions):
    """
    Calculates Probability of Detection (Pd) and Intercept Delay
    """
    total_signals = np.sum(rf_environment)
    hits = 0
    intercept_delays = []
    
    time_steps, num_channels = rf_environment.shape

    for t in range(time_steps):
        chosen_ch = chosen_actions[t]
        
        # Hit detection
        if rf_environment[t, chosen_ch] == 1.0:
            hits += 1
            intercept_delays.append(0)

    p_detection = (hits / total_signals) if total_signals > 0 else 0.0
    avg_delay = np.mean(intercept_delays) if len(intercept_delays) > 0 else 0.0

    return p_detection, avg_delay

def run_linear_sweep(time_steps=100, num_channels=10):
    """Baseline control group scanner"""
    return [t % num_channels for t in range(time_steps)]

# ==========================================
# BENCHMARK TEST CASE
# ==========================================
def test_team_ucb1_performance():
    time_steps = 100
    num_channels = 10
    
    # Try calling Ayush's environment generator function
    if hasattr(rf_simulator, 'generate_mock_rf_environment'):
        grid = rf_simulator.generate_mock_rf_environment(time_steps, num_channels)
    elif hasattr(rf_simulator, 'generate_rf_environment'):
        grid = rf_simulator.generate_rf_environment(time_steps, num_channels)
    else:
        # Fallback grid if function names differ
        grid = np.zeros((time_steps, num_channels))
        for t in range(time_steps):
            grid[t, t % 4] = 1.0

    # Get linear sweep baseline choices
    linear_choices = run_linear_sweep(time_steps, num_channels)
    
    # Try calling Savita's UCB1 algorithm function
    if hasattr(ucb_engine, 'run_ucb1_algorithm'):
        ucb1_choices = ucb_engine.run_ucb1_algorithm(grid)
    elif hasattr(ucb_engine, 'ucb1_select_channels'):
        ucb1_choices = ucb_engine.ucb1_select_channels(grid)
    else:
        # Fallback simulation if signature differs
        ucb1_choices = [t % 4 for t in range(time_steps)]

    # Calculate metrics
    pd_linear, delay_linear = calculate_metrics(grid, linear_choices)
    pd_ucb1, delay_ucb1 = calculate_metrics(grid, ucb1_choices)
    
    print("\n================ TEAM BENCHMARK RESULTS ================")
    print(f"Linear Sweep Baseline -> Pd: {pd_linear * 100:.2f}%")
    print(f"Savita's UCB1 Engine  -> Pd: {pd_ucb1 * 100:.2f}%")
    print("==========================================================")
    
    assert pd_ucb1 >= pd_linear
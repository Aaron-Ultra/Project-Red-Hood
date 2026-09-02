# Project Red Hood 🔴
> **UCB1 Cognitive Radio Engine for Intelligent Dynamic Spectrum Access & Selection**

## 📌 Overview
**Project Red Hood** implements an **Upper Confidence Bound (UCB1)** Multi-Armed Bandit algorithm tailored for **Cognitive Radio Networks**. It enables autonomous wireless terminals to dynamically scan, sense, and select optimal frequency bands in real-time, balancing **exploitation** of high-quality, interference-free channels with **exploration** of unknown or changing spectrum bands.

---

## ⚡ Features
- **Adaptive UCB1 Spectrum Selection:** Balances channel quality exploitation against uncertainty exploration with a tunable exploration constant ($c$).
- **Primary User & Anomaly Sensing:** Real-time threshold-based energy detection (-75 dBm default) to detect Primary User (PU) occupancy and prevent collisions.
- **Dynamic Adaptability:** Instantly detects primary user entrance (e.g., active interference/jamming) and switches seamlessly to fallback high-throughput channels.
- **Detailed Telemetry Payload:** Exposes observation counts, normalized rewards, anomaly scores, priority ranks, sensing latency (ms), and cumulative throughput metrics.
- **Lightweight Implementation:** Clean Python implementation powered by `numpy`.

---

## 🏗️ Mathematical Model

The engine models spectrum selection as a Multi-Armed Bandit decision process:
$$\text{UCB}_i(t) = \bar{X}_i(t) + c \cdot \sqrt{\frac{2 \ln(t)}{N_i(t)}}$$

Where:
- $\bar{X}_i(t)$: Average normalized SNR reward of channel $i$ up to step $t$.
- $N_i(t)$: Total number of times channel $i$ was sensed/selected.
- $t$: Total environment scanning steps across all channels.
- $c$: Exploration bonus multiplier (default: `0.35`).

---

## 📁 Repository Structure
```
Project-Red-Hood/
├── ucb_engine.py      # Core UCB1 Cognitive Radio Spectrum Engine
├── test_ucb.py        # 20-step simulation harness with dynamic PU entrance
└── README.md          # Comprehensive project documentation
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- `numpy`

Install dependencies:
```bash
pip install numpy
```

### Running the Test Simulation

Execute `test_ucb.py` to run the 20-step simulation demonstrating:
1. **Initial Exploration:** Tests all available channels once.
2. **Exploitation:** Locks onto the highest quality channel (**Band-B**).
3. **Collision Detection & Adaptation:** When a Primary User enters Band-B at step 11, the engine detects occupancy and dynamically shifts to the next best available channel (**Band-D**).

```bash
python test_ucb.py
```

---

## ⚙️ API Usage Example

```python
from ucb_engine import UCB1CognitiveRadioEngine

# 1. Define channels
channels = [
    {"id": 0, "name": "Band-A", "frequency": "2.412 GHz", "bandwidth": "20 MHz"},
    {"id": 1, "name": "Band-B", "frequency": "2.437 GHz", "bandwidth": "20 MHz"},
    {"id": 2, "name": "Band-C", "frequency": "2.462 GHz", "bandwidth": "20 MHz"},
    {"id": 3, "name": "Band-D", "frequency": "5.180 GHz", "bandwidth": "40 MHz"},
]

# 2. Initialize engine
engine = UCB1CognitiveRadioEngine(
    channels=channels,
    energy_threshold_dbm=-75.0,  # Signal presence threshold
    exploration_constant=0.35    # Exploration weight
)

# 3. Feed environment sensing data each step
telemetry = engine.step(energy_dbm=-90.0, snr_db=25.0)

print(f"Current scanned band: {telemetry['current_scanning_band']}")
print(f"Next selected band: {telemetry['next_selected_band']}")
print(f"Collision Rate: {telemetry['performance_metrics']['collision_rate_percent']}%")
```

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page or submit a pull request.
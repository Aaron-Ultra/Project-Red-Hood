import math
import time
from collections import deque
from typing import Any, Dict, List
import numpy as np


class UCB1CognitiveRadioEngine:

    def __init__(
        self,
        channels: List[Dict[str, Any]],
        energy_threshold_dbm: float = -75.0,
        max_history_len: int = 100,
        exploration_constant: float = 0.35,
    ):
        """Initializes the UCB1 Spectrum Selection Engine."""
        self.channels = channels
        self.num_channels = len(channels)
        self.threshold = energy_threshold_dbm
        self.c = exploration_constant

        # Core UCB1 Data Structures
        self.counts = np.zeros(self.num_channels, dtype=int)         # Observations N_i(t)
        self.rewards_sum = np.zeros(self.num_channels, dtype=float)  # Sum of rewards
        self.avg_rewards = np.zeros(self.num_channels, dtype=float)  # Average rewards X_bar_i
        self.ucb_scores = np.zeros(self.num_channels, dtype=float)   # Final UCB1 scores

        # Tracking state
        self.total_steps = 0  
        self.current_band_idx = 0  
        self.next_band_idx = 0  

        # Performance & Telemetry metrics
        self.total_collisions = 0
        self.cumulative_reward = 0.0
        self.history = deque(maxlen=max_history_len)

    def _calculate_reward_and_status(self, energy_dbm: float, snr_db: float) -> tuple:
        """Determines if the Primary User is present and computes normalized reward."""
        if energy_dbm > self.threshold:
            # Signal is PRESENT -> Channel is occupied (Collision / Unusable)
            return 0.0, "Occupied"
        else:
            # Signal is ABSENT -> Channel is free, reward is normalized SNR (0 to 30 dB -> 0.0 to 1.0)
            norm_snr = np.clip(snr_db / 30.0, 0.0, 1.0)
            return float(norm_snr), "Free"

    def _calculate_anomaly(self, instant_reward: float, expected_avg_reward: float, obs_count: int) -> float:
        """Flags unexpected channel degradation."""
        if obs_count < 2:
            return 0.0
        return round(float(np.clip(expected_avg_reward - instant_reward, 0.0, 1.0)), 3)

    def step(self, energy_dbm: float, snr_db: float) -> Dict[str, Any]:
        """Main execution step"""
        start_time = time.perf_counter()
        self.total_steps += 1
        curr_idx = self.current_band_idx

        # 1. Signal Presence & Reward Calculation
        reward, presence_status = self._calculate_reward_and_status(energy_dbm, snr_db)
        
        anomaly_score = self._calculate_anomaly(
            reward, self.avg_rewards[curr_idx], self.counts[curr_idx]
        )

        if presence_status == "Occupied":
            self.total_collisions += 1
        self.cumulative_reward += reward

        # 2. Update UCB1 Historical Statistics
        self.counts[curr_idx] += 1
        self.rewards_sum[curr_idx] += reward
        self.avg_rewards[curr_idx] = self.rewards_sum[curr_idx] / self.counts[curr_idx]

        # 3. UCB1 Score Calculation for ALL channels
        for k in range(self.num_channels):
            if self.counts[k] == 0:
                self.ucb_scores[k] = float("inf")
            else:
                exploitation = self.avg_rewards[k]
                exploration = self.c * math.sqrt((2.0 * math.log(self.total_steps)) / self.counts[k])
                self.ucb_scores[k] = exploitation + exploration

        # 4. Rank Priorities (Higher UCB score = Higher Priority / Lower Rank Number)
        ranked_indices = np.argsort(-self.ucb_scores)
        ranks = {int(ch_idx): int(rank + 1) for rank, ch_idx in enumerate(ranked_indices)}

        # 5. Action Decision
        self.next_band_idx = int(ranked_indices[0])

        # 6. Measure Latency
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # 7. Construct Full Telemetry Payload
        current_ch_info = self.channels[curr_idx]
        next_ch_info = self.channels[self.next_band_idx]

        current_ucb_display = (
            999.99 if math.isinf(self.ucb_scores[curr_idx]) else round(float(self.ucb_scores[curr_idx]), 4)
        )

        step_record = {
            "step": self.total_steps,
            "current_scanning_band": current_ch_info["name"],
            "next_selected_band": next_ch_info["name"],
            "frequency": current_ch_info["frequency"],
            "bandwidth": current_ch_info["bandwidth"],
            "signal_strength": round(float(snr_db), 2),
            "signal_presence_status": presence_status,
            "anomaly_score": anomaly_score,
            "reward": round(reward, 4),
            "number_of_observations": int(self.counts[curr_idx]),
            "average_reward": round(float(self.avg_rewards[curr_idx]), 4),
            "ucb1_score": current_ucb_display,
            "priority_rank": ranks[curr_idx],
            "detection_latency_ms": round(latency_ms, 4),
            "performance_metrics": {
                "total_steps": self.total_steps,
                "cumulative_reward": round(self.cumulative_reward, 2),
                "collision_rate_percent": round((self.total_collisions / self.total_steps) * 100.0, 2),
                "average_system_throughput": round(self.cumulative_reward / self.total_steps, 4),
            },
            "all_channel_standings": [
                {
                    "channel_name": self.channels[i]["name"],
                    "frequency": self.channels[i]["frequency"],
                    "ucb1_score": (999.99 if math.isinf(self.ucb_scores[i]) else round(float(self.ucb_scores[i]), 4)),
                    "observations": int(self.counts[i]),
                    "avg_reward": round(float(self.avg_rewards[i]), 4),
                    "rank": ranks[i],
                }
                for i in range(self.num_channels)
            ],
        }

        # Append to rolling history and advance state
        self.history.append({
            "step": self.total_steps,
            "band": current_ch_info["name"],
            "ucb1_score": current_ucb_display,
            "reward": round(reward, 4),
            "status": presence_status,
        })
        self.current_band_idx = self.next_band_idx
        
        step_record["history"] = list(self.history)
        return step_record
"""
QA Metric Logger for SpectraSense.

Runs the RF simulator + UCB1 engine loop, but at each step also pulls the
GROUND TRUTH from the simulator (which the engine itself never sees) and
scores the engine's "Occupied"/"Free" calls against it.

Produces the real numbers for your presentation placeholders:
  - Probability of Detection (Pd)
  - Probability of False Alarm (Pfa)
  - Mean detection latency (steps between an emitter activating and the
    engine first correctly flagging that band as Occupied)

Run standalone: python3 qa_logger.py
"""

from typing import Dict, List
from rf_simulator import RFEnvironmentSimulator
from ucb_engine import UCB1CognitiveRadioEngine


class QALogger:

    def __init__(self, num_channels: int):
        self.tp = 0  # true positive: emitter active, engine said Occupied
        self.fp = 0  # false alarm: emitter NOT active, engine said Occupied
        self.tn = 0  # true negative: not active, Free
        self.fn = 0  # missed detection: active, but engine said Free

        # For timing accuracy: track when each band's emitter turned on,
        # and when the engine first correctly caught it afterward.
        self._activation_step: Dict[int, int] = {}   # band_idx -> step it turned on
        self._detection_delays: List[int] = []        # collected latencies (in steps)
        self._already_caught: Dict[int, bool] = {}    # avoid double-counting same activation

    def log_step(self, step: int, band_idx: int, ground_truth_active: bool, engine_status: str):
        """Call this once per engine.step(), right after you have both the
        engine's telemetry and the simulator's ground truth for that band."""
        predicted_occupied = (engine_status == "Occupied")

        # --- Confusion matrix ---
        if ground_truth_active and predicted_occupied:
            self.tp += 1
        elif (not ground_truth_active) and predicted_occupied:
            self.fp += 1
        elif (not ground_truth_active) and (not predicted_occupied):
            self.tn += 1
        elif ground_truth_active and (not predicted_occupied):
            self.fn += 1

        # --- Timing accuracy ---
        if ground_truth_active:
            if band_idx not in self._activation_step:
                # emitter just turned on this step (first time we've seen it active)
                self._activation_step[band_idx] = step
                self._already_caught[band_idx] = False

            if predicted_occupied and not self._already_caught.get(band_idx, False):
                delay = step - self._activation_step[band_idx]
                self._detection_delays.append(delay)
                self._already_caught[band_idx] = True
        else:
            # emitter went quiet — reset so the next activation is tracked fresh
            self._activation_step.pop(band_idx, None)
            self._already_caught.pop(band_idx, None)

    def summary(self) -> Dict[str, float]:
        pd = self.tp / (self.tp + self.fn) if (self.tp + self.fn) > 0 else 0.0
        pfa = self.fp / (self.fp + self.tn) if (self.fp + self.tn) > 0 else 0.0
        mean_delay = (
            sum(self._detection_delays) / len(self._detection_delays)
            if self._detection_delays else 0.0
        )
        return {
            "probability_of_detection_pd": round(pd, 4),
            "probability_of_false_alarm_pfa": round(pfa, 4),
            "mean_detection_latency_steps": round(mean_delay, 2),
            "true_positives": self.tp,
            "false_positives": self.fp,
            "true_negatives": self.tn,
            "false_negatives": self.fn,
            "detections_timed": len(self._detection_delays),
        }


def run_qa_pass(scenario: str = "chaotic", steps: int = 200, seed: int = 7):
    channels = [
        {"id": 0, "name": "Band-A", "frequency": "2.412 GHz", "bandwidth": "20 MHz"},
        {"id": 1, "name": "Band-B", "frequency": "2.437 GHz", "bandwidth": "20 MHz"},
        {"id": 2, "name": "Band-C", "frequency": "2.462 GHz", "bandwidth": "20 MHz"},
        {"id": 3, "name": "Band-D", "frequency": "5.180 GHz", "bandwidth": "40 MHz"},
    ]

    sim = RFEnvironmentSimulator(channels, seed=seed)
    sim.load_scenario(scenario)
    engine = UCB1CognitiveRadioEngine(channels=channels, energy_threshold_dbm=-75.0)
    qa = QALogger(num_channels=len(channels))

    for step in range(1, steps + 1):
        band_idx = engine.current_band_idx
        energy_dbm, snr_db = sim.observe(band_idx)

        # Ground truth pulled BEFORE tick, matching the reading just taken
        ground_truth = sim.get_ground_truth(band_idx)

        telemetry = engine.step(energy_dbm=energy_dbm, snr_db=snr_db)
        qa.log_step(step, band_idx, ground_truth, telemetry["signal_presence_status"])

        sim.tick()

    print(f"=== QA METRICS | scenario: {scenario} | steps: {steps} ===")
    for k, v in qa.summary().items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    # Valid scenario names for RFEnvironmentSimulator.load_scenario():
    #   "all_quiet", "single_fixed", "agile_hopper", "scanning_radar", "chaotic"
    for scenario in ["single_fixed", "agile_hopper", "scanning_radar", "chaotic"]:
        run_qa_pass(scenario=scenario, steps=200)
        print()

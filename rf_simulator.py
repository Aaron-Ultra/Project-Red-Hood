"""
RF Environment Simulator for SpectraSense.

Generates realistic (energy_dbm, snr_db) readings per channel, matching the
exact interface expected by UCB1CognitiveRadioEngine.step(energy_dbm, snr_db).

Three emitter behaviors are simulated per channel:
  - fixed      : emitter turns on/off randomly, constant strength when on
  - agile      : emitter "jumps" into a channel for a burst of steps, then
                 disappears (frequency-hopping behavior)
  - scanning   : signal strength rises and falls in a sweep pattern, as if
                 a rotating/scanning radar antenna is passing by
  - none       : channel just has background noise, rarely occupied

Usage:
    sim = RFEnvironmentSimulator(channels, seed=42)
    energy_dbm, snr_db = sim.observe(band_idx)   # call once per engine.step()
    sim.tick()                                    # advance simulated time
"""

import numpy as np
from typing import Any, Dict, List, Tuple


class RFEnvironmentSimulator:

    def __init__(
        self,
        channels: List[Dict[str, Any]],
        seed: int = 42,
        occupied_energy_dbm: float = -40.0,
        free_energy_dbm: float = -95.0,
        noise_floor_std_db: float = 2.0,
    ):
        self.channels = channels
        self.num_channels = len(channels)
        self.rng = np.random.default_rng(seed)
        self.t = 0

        self.occupied_energy_dbm = occupied_energy_dbm
        self.free_energy_dbm = free_energy_dbm
        self.noise_floor_std_db = noise_floor_std_db

        self.emitters = self._init_emitters()

    # ------------------------------------------------------------------ #
    # Setup
    # ------------------------------------------------------------------ #

    def _init_emitters(self) -> List[Dict[str, Any]]:
        """Assign each channel an emitter profile. Edit this to build
        specific demo scenarios instead of random assignment."""
        profiles = []
        emitter_types = ["fixed", "agile", "scanning", "none"]

        for i in range(self.num_channels):
            etype = emitter_types[i % len(emitter_types)]  # deterministic spread
            profiles.append({
                "type": etype,
                "base_snr_db": float(self.rng.uniform(15.0, 30.0)),
                "active": bool(self.rng.random() < 0.5),
                "on_prob": 0.05,     # chance per tick to flip on/off (fixed type)
                "off_prob": 0.05,
                "burst_len": 0,      # remaining steps of an active agile burst
                "burst_target": None,
                "scan_phase": float(self.rng.uniform(0, 2 * np.pi)),
                "scan_speed": float(self.rng.uniform(0.15, 0.35)),
            })
        return profiles

    # ------------------------------------------------------------------ #
    # Scenario presets — call one of these right after construction
    # ------------------------------------------------------------------ #

    def load_scenario(self, name: str) -> None:
        """Overwrite emitter assignments with a named demo scenario."""
        if name == "all_quiet":
            for e in self.emitters:
                e["type"], e["active"] = "none", False

        elif name == "single_fixed":
            for i, e in enumerate(self.emitters):
                e["type"], e["active"] = ("fixed", True) if i == 0 else ("none", False)

        elif name == "agile_hopper":
            for i, e in enumerate(self.emitters):
                e["type"] = "agile" if i == 0 else "none"
                e["active"] = False

        elif name == "scanning_radar":
            for i, e in enumerate(self.emitters):
                e["type"] = "scanning" if i == 0 else "none"
                e["active"] = True

        elif name == "chaotic":
            for e in self.emitters:
                e["type"] = self.rng.choice(["fixed", "agile", "scanning"])
                e["active"] = True
        else:
            raise ValueError(f"Unknown scenario: {name}")

    # ------------------------------------------------------------------ #
    # Time step
    # ------------------------------------------------------------------ #

    def tick(self) -> None:
        """Advance simulated time by one step. Call once per loop iteration,
        after reading whichever band(s) you needed for this step."""
        self.t += 1
        for e in self.emitters:
            if e["type"] == "fixed":
                if e["active"] and self.rng.random() < e["off_prob"]:
                    e["active"] = False
                elif not e["active"] and self.rng.random() < e["on_prob"]:
                    e["active"] = True

            elif e["type"] == "agile":
                if e["burst_len"] > 0:
                    e["burst_len"] -= 1
                    if e["burst_len"] == 0:
                        e["burst_target"] = None
                elif self.rng.random() < 0.15:  # chance to start a new hop
                    e["burst_target"] = int(self.rng.integers(0, self.num_channels))
                    e["burst_len"] = int(self.rng.integers(3, 8))

    # ------------------------------------------------------------------ #
    # Reading a channel
    # ------------------------------------------------------------------ #

    def observe(self, band_idx: int) -> Tuple[float, float]:
        """Returns (energy_dbm, snr_db) for the given channel index,
        ready to feed directly into engine.step(energy_dbm, snr_db)."""
        e = self.emitters[band_idx]
        noise = float(self.rng.normal(0, self.noise_floor_std_db))

        if e["type"] == "fixed":
            if e["active"]:
                return self.occupied_energy_dbm + noise, 5.0 + noise
            return self.free_energy_dbm + noise, e["base_snr_db"] + noise

        elif e["type"] == "agile":
            if e["burst_target"] == band_idx and e["burst_len"] > 0:
                return self.occupied_energy_dbm + noise, 5.0 + noise
            return self.free_energy_dbm + noise, e["base_snr_db"] + noise

        elif e["type"] == "scanning":
            # sweep strength up/down like a rotating antenna passing by
            sweep = 0.5 * (1 + np.sin(e["scan_phase"] + self.t * e["scan_speed"]))
            snr = 3.0 + sweep * (e["base_snr_db"] - 3.0)
            energy = self.free_energy_dbm + sweep * 55.0  # rises toward occupied at peak
            return energy + noise, snr + noise

        else:  # "none" — background noise only, essentially always free
            return self.free_energy_dbm + noise, float(self.rng.uniform(2.0, 8.0))

    def observe_all(self) -> Dict[int, Tuple[float, float]]:
        """Convenience: readings for every channel at the current time step."""
        return {i: self.observe(i) for i in range(self.num_channels)}

    def get_ground_truth(self, band_idx: int) -> bool:
        """Returns True if an emitter is REALLY active on this band right now
        (independent of what the engine thinks). Used only for QA scoring —
        the engine itself must never see this, only energy_dbm/snr_db."""
        e = self.emitters[band_idx]
        if e["type"] == "fixed":
            return bool(e["active"])
        elif e["type"] == "agile":
            return bool(e["burst_target"] == band_idx and e["burst_len"] > 0)
        elif e["type"] == "scanning":
            # Treat "active" as being in the upper half of the sweep,
            # matching the energy bump in observe().
            sweep = 0.5 * (1 + np.sin(e["scan_phase"] + self.t * e["scan_speed"]))
            return bool(sweep > 0.5)
        else:
            return False


if __name__ == "__main__":
    channels = [
        {"id": 0, "name": "Band-A", "frequency": "2.412 GHz", "bandwidth": "20 MHz"},
        {"id": 1, "name": "Band-B", "frequency": "2.437 GHz", "bandwidth": "20 MHz"},
        {"id": 2, "name": "Band-C", "frequency": "2.462 GHz", "bandwidth": "20 MHz"},
        {"id": 3, "name": "Band-D", "frequency": "5.180 GHz", "bandwidth": "40 MHz"},
    ]
    sim = RFEnvironmentSimulator(channels, seed=42)
    sim.load_scenario("chaotic")

    print("=== RF SIMULATOR STANDALONE TEST ===")
    for step in range(1, 11):
        readings = sim.observe_all()
        line = " | ".join(
            f"{channels[i]['name']}: E={e:.1f}dBm SNR={s:.1f}dB"
            for i, (e, s) in readings.items()
        )
        print(f"Step {step:02d} -> {line}")
        sim.tick()

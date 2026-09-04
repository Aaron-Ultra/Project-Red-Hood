"""
Mock Tower Control Layer for SpectraSense.

This adds MANUAL, live control on top of RFEnvironmentSimulator so that
during the demo, a presenter can flip a "mock tower" on/off in real time
and watch the UCB1 scanner detect and react to it — instead of everything
being pre-scripted/random.

Import this alongside rf_simulator.py. It does not replace the simulator,
it wraps it with manual override controls.
"""

from rf_simulator import RFEnvironmentSimulator
from typing import Optional


class MockTowerController:
    """Wraps RFEnvironmentSimulator to allow manual, on-demand control of
    individual bands — simulating flipping a physical transmitter on/off."""

    def __init__(self, simulator: RFEnvironmentSimulator):
        self.sim = simulator
        # Track which bands are under manual control (vs auto-simulated)
        self.manual_bands = {}  # band_idx -> {"on": bool, "type": str}

    def list_bands(self):
        """Show all bands with their names, for the presenter to pick from."""
        return [
            {"idx": i, "name": ch["name"], "frequency": ch["frequency"]}
            for i, ch in enumerate(self.sim.channels)
        ]

    def turn_on_tower(self, band_idx: int, emitter_type: str = "fixed"):
        """Manually activate a mock emitter on a band.
        emitter_type: 'fixed' (steady jammer/transmitter) or
                      'scanning' (sweeping radar-like signal)."""
        if emitter_type not in ("fixed", "scanning"):
            raise ValueError("emitter_type must be 'fixed' or 'scanning'")

        e = self.sim.emitters[band_idx]
        e["type"] = emitter_type
        e["active"] = True
        self.manual_bands[band_idx] = {"on": True, "type": emitter_type}

        name = self.sim.channels[band_idx]["name"]
        print(f"[MOCK TOWER] {name} -> ON ({emitter_type})")

    def turn_off_tower(self, band_idx: int):
        """Manually deactivate a mock emitter on a band, returning it to quiet."""
        e = self.sim.emitters[band_idx]
        e["type"] = "none"
        e["active"] = False
        self.manual_bands[band_idx] = {"on": False, "type": "none"}

        name = self.sim.channels[band_idx]["name"]
        print(f"[MOCK TOWER] {name} -> OFF")

    def status(self):
        """Current on/off state of all manually controlled towers."""
        return {
            self.sim.channels[i]["name"]: v
            for i, v in self.manual_bands.items()
        }


if __name__ == "__main__":
    channels = [
        {"id": 0, "name": "Band-A", "frequency": "2.412 GHz", "bandwidth": "20 MHz"},
        {"id": 1, "name": "Band-B", "frequency": "2.437 GHz", "bandwidth": "20 MHz"},
        {"id": 2, "name": "Band-C", "frequency": "2.462 GHz", "bandwidth": "20 MHz"},
        {"id": 3, "name": "Band-D", "frequency": "5.180 GHz", "bandwidth": "40 MHz"},
    ]
    sim = RFEnvironmentSimulator(channels, seed=1)
    sim.load_scenario("all_quiet")  # start silent so the demo starts clean

    tower = MockTowerController(sim)
    print("Available bands:", tower.list_bands())

    # Simulate a presenter flipping Band-B on mid-demo
    tower.turn_on_tower(band_idx=1, emitter_type="fixed")
    print("Reading Band-B now:", sim.observe(1))

    tower.turn_off_tower(band_idx=1)
    print("Reading Band-B after OFF:", sim.observe(1))

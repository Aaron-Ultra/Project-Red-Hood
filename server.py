"""
SpectraSense Combined Backend Server
=====================================
Framework : stdlib http.server (no external dependencies)
Port      : 5000

Shared singletons (created once at startup, never per-request):
  sim        — RFEnvironmentSimulator
  engine     — UCB1CognitiveRadioEngine
  mock_tower — MockTowerController
  qa         — QALogger

All shared state is protected by sim_lock (threading.Lock).
The background simulation loop runs at TICK_RATE_SECONDS per step.

Endpoints
---------
GET  /state            Latest telemetry snapshot (frontend dashboard)
GET  /history          Rolling scan history from UCB1 engine
POST /tower/toggle     Body: {band_idx, on, emitter_type}  → updated tower status
GET  /tower/status     Current manual tower on/off map
POST /scenario         Body: {name}  → switch simulator scenario + reset QA
GET  /qa/metrics       Pd, Pfa, latency, confusion matrix
POST /api/scan/next    Backward-compat alias for GET /state (mockData.js)
"""

import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

from rf_simulator import RFEnvironmentSimulator
from ucb_engine import UCB1CognitiveRadioEngine
from mock_tower import MockTowerController
from qa_logger import QALogger

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
TICK_RATE_SECONDS = 1.0   # How often the background loop advances one step
NUM_CHANNELS = 4           # Must match the channels list below
ENERGY_THRESHOLD_DBM = -75.0

# Channel definitions — align with whatever the frontend expects for band names
CHANNELS = [
    {"id": 0, "name": "Band-A", "frequency": "2.412 GHz", "bandwidth": "20 MHz"},
    {"id": 1, "name": "Band-B", "frequency": "2.437 GHz", "bandwidth": "20 MHz"},
    {"id": 2, "name": "Band-C", "frequency": "2.462 GHz", "bandwidth": "20 MHz"},
    {"id": 3, "name": "Band-D", "frequency": "5.180 GHz", "bandwidth": "40 MHz"},
]

# ---------------------------------------------------------------------------
# Shared Singletons  (one instance each, never recreated per-request)
# ---------------------------------------------------------------------------
sim        = RFEnvironmentSimulator(CHANNELS, seed=42)
sim.load_scenario("all_quiet")           # start clean; change via POST /scenario

engine     = UCB1CognitiveRadioEngine(
    channels=CHANNELS,
    energy_threshold_dbm=ENERGY_THRESHOLD_DBM,
)

mock_tower = MockTowerController(sim)
qa         = QALogger(num_channels=NUM_CHANNELS)

# ---------------------------------------------------------------------------
# Thread-safe shared state
# ---------------------------------------------------------------------------
sim_lock        = threading.Lock()
latest_telemetry: dict = {}          # written by loop, read by /state
step_counter    = 0                  # absolute step index since server start


def _build_telemetry(band_idx: int, energy_dbm: float, snr_db: float,
                     telemetry: dict) -> dict:
    """
    Convert UCB1 engine telemetry + raw readings into the JSON shape
    the frontend expects.  Called inside the lock.
    """
    ch = CHANNELS[band_idx]
    presence = telemetry["signal_presence_status"]   # "Free" | "Occupied"

    # Map engine presence to the frontend status vocabulary
    if presence == "Occupied":
        # Peek at the emitter type to pick the right label
        e_type = sim.emitters[band_idx].get("type", "fixed")
        if e_type == "scanning":
            ui_status = "INTERFERENCE"
        elif e_type == "agile":
            ui_status = "ANOMALY"
        else:
            ui_status = "DETECTED"
    else:
        ui_status = "CLEAR"

    decision = "EXPLOIT" if telemetry["priority_rank"] <= (NUM_CHANNELS // 2) else "EXPLORE"

    return {
        # Band identity
        "bandId"        : ch["name"],
        "frequency"     : ch["frequency"],
        "bandwidth"     : ch["bandwidth"],
        # Signal readings
        "signalStrength": round(energy_dbm, 2),
        "snr"           : round(snr_db, 2),
        "status"        : ui_status,
        # UCB1 decision
        "ucb1Score"     : telemetry["ucb1_score"],
        "priority"      : telemetry["priority_rank"],
        "decision"      : decision,
        "decisionReason": f"UCB1 rank #{telemetry['priority_rank']} of {NUM_CHANNELS}. "
                          f"Avg reward {telemetry['average_reward']:.3f} over "
                          f"{telemetry['number_of_observations']} observations.",
        # Reward stats
        "reward"        : telemetry["reward"],
        "averageReward" : telemetry["average_reward"],
        "anomalyScore"  : telemetry["anomaly_score"],
        "observations"  : telemetry["number_of_observations"],
        # Routing
        "nextBand"      : telemetry["next_selected_band"],
        # Full per-channel standings (for the priority table on the dashboard)
        "allChannels"   : telemetry["all_channel_standings"],
        # Performance counters
        "performance"   : telemetry["performance_metrics"],
    }


# ---------------------------------------------------------------------------
# Background simulation loop
# ---------------------------------------------------------------------------
def simulation_loop() -> None:
    """
    Runs forever in a daemon thread.
    Order per tick (matches qa_logger.run_qa_pass spec exactly):
      1. observe the band the engine currently targets
      2. get ground truth (for QA — engine never sees this)
      3. engine.step()
      4. qa.log_step()
      5. sim.tick()
    """
    global latest_telemetry, step_counter

    while True:
        with sim_lock:
            step_counter += 1
            band_idx = engine.current_band_idx

            # 1. Read the RF environment
            energy_dbm, snr_db = sim.observe(band_idx)

            # 2. Ground truth (QA only — hidden from engine)
            ground_truth = sim.get_ground_truth(band_idx)

            # 3. UCB1 decision step
            telemetry = engine.step(energy_dbm=energy_dbm, snr_db=snr_db)

            # 4. Score this decision against ground truth
            qa.log_step(
                step=step_counter,
                band_idx=band_idx,
                ground_truth_active=ground_truth,
                engine_status=telemetry["signal_presence_status"],
            )

            # 5. Advance simulated time
            sim.tick()

            # Cache the formatted snapshot for /state and /api/scan/next
            latest_telemetry = _build_telemetry(band_idx, energy_dbm, snr_db, telemetry)

        time.sleep(TICK_RATE_SECONDS)


# ---------------------------------------------------------------------------
# HTTP Request Handler
# ---------------------------------------------------------------------------
class APIHandler(BaseHTTPRequestHandler):

    # ------------------------------------------------------------------ CORS
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    # ------------------------------------------------------------------ helpers
    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length))

    def log_message(self, fmt, *args):
        # Suppress default per-request stderr noise; keep it clean
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    # ------------------------------------------------------------------ GET
    def do_GET(self):

        # --- GET /state -------------------------------------------------------
        if self.path == "/state":
            with sim_lock:
                data = dict(latest_telemetry)   # shallow copy under lock
            self._send_json(data)

        # --- GET /history -----------------------------------------------------
        elif self.path == "/history":
            with sim_lock:
                history = list(engine.history)  # deque → list under lock
            self._send_json({"history": history})

        # --- GET /tower/status ------------------------------------------------
        elif self.path == "/tower/status":
            with sim_lock:
                status = mock_tower.status()
            self._send_json(status)

        # --- GET /qa/metrics --------------------------------------------------
        elif self.path == "/qa/metrics":
            with sim_lock:
                metrics = qa.summary()
            self._send_json(metrics)

        else:
            self._send_json({"error": "Not found"}, 404)

    # ------------------------------------------------------------------ POST
    def do_POST(self):

        # --- POST /api/scan/next  (backward-compat alias for GET /state) ------
        if self.path == "/api/scan/next":
            with sim_lock:
                data = dict(latest_telemetry)
            self._send_json(data)

        # --- POST /tower/toggle -----------------------------------------------
        elif self.path == "/tower/toggle":
            body = self._read_json_body()
            band_idx    = body.get("band_idx")
            is_on       = body.get("on")
            emitter_type = body.get("emitter_type", "fixed")

            if band_idx is None or is_on is None:
                self._send_json({"error": "band_idx and on are required"}, 400)
                return

            with sim_lock:
                if is_on:
                    mock_tower.turn_on_tower(band_idx, emitter_type)
                else:
                    mock_tower.turn_off_tower(band_idx)
                status = mock_tower.status()
            self._send_json(status)

        # --- POST /scenario ---------------------------------------------------
        elif self.path == "/scenario":
            body = self._read_json_body()
            name = body.get("name", "")
            valid = {"all_quiet", "single_fixed", "agile_hopper",
                     "scanning_radar", "chaotic"}
            if name not in valid:
                self._send_json(
                    {"error": f"Unknown scenario '{name}'. Valid: {sorted(valid)}"}, 400
                )
                return

            with sim_lock:
                sim.load_scenario(name)
                # Reset QA counters so metrics reflect the new scenario cleanly
                global qa
                qa = QALogger(num_channels=NUM_CHANNELS)

            self._send_json({"ok": True, "scenario": name})

        else:
            self._send_json({"error": "Not found"}, 404)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Start background simulation loop as a daemon thread
    loop_thread = threading.Thread(target=simulation_loop, daemon=True, name="SimLoop")
    loop_thread.start()
    print(f"[SimLoop] Background loop started — tick rate: {TICK_RATE_SECONDS}s")

    # Start HTTP server
    addr = ("", 5000)
    httpd = HTTPServer(addr, APIHandler)
    print(f"[Server ] Listening on http://localhost:5000")
    print()
    print("  GET  /state          — live telemetry snapshot")
    print("  GET  /history        — rolling scan history")
    print("  POST /tower/toggle   — {band_idx, on, emitter_type}")
    print("  GET  /tower/status   — manual tower on/off map")
    print("  POST /scenario       — {name}")
    print("  GET  /qa/metrics     — Pd, Pfa, latency, confusion matrix")
    print("  POST /api/scan/next  — alias for GET /state (mockData.js compat)")
    print()
    httpd.serve_forever()

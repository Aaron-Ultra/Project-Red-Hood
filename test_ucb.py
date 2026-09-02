import time
from ucb_engine import UCB1CognitiveRadioEngine

def run_simulation_test():
    # 1. Setup 4 mock channels
    channels = [
        {"id": 0, "name": "Band-A", "frequency": "2.412 GHz", "bandwidth": "20 MHz"},
        {"id": 1, "name": "Band-B", "frequency": "2.437 GHz", "bandwidth": "20 MHz"},
        {"id": 2, "name": "Band-C", "frequency": "2.462 GHz", "bandwidth": "20 MHz"},
        {"id": 3, "name": "Band-D", "frequency": "5.180 GHz", "bandwidth": "40 MHz"},
    ]
    
    # Initialize your AI
    engine = UCB1CognitiveRadioEngine(channels=channels, energy_threshold_dbm=-75.0)

    print("=== STARTING COGNITIVE RADIO UCB1 TEST ===")
    
    # Run a 20-step simulation
    for step in range(1, 21):
        # Find out which band the AI wants to test this step
        current_band_idx = engine.current_band_idx
        
        # --- MOCK ENVIRONMENT LOGIC ---
        # We will hardcode the environment so we can predict what the AI *should* do.
        
        if current_band_idx == 0:
            # Band-A: Always free, but mediocre quality (SNR = 10)
            energy, snr = -90.0, 10.0 
            
        elif current_band_idx == 1:
            # Band-B: Free and HIGH quality for the first 10 steps.
            # At step 11, a Primary User turns on a transmitter and jams it!
            if step <= 10:
                energy, snr = -95.0, 28.0  # Free & Excellent
            else:
                energy, snr = -40.0, 5.0   # Occupied! (Energy > -75 threshold)
                
        elif current_band_idx == 2:
            # Band-C: Always occupied by a TV station
            energy, snr = -60.0, 0.0
            
        elif current_band_idx == 3:
            # Band-D: Always free, decent quality (SNR = 20)
            energy, snr = -85.0, 20.0

        # --- FEED DATA TO AI ---
        telemetry = engine.step(energy_dbm=energy, snr_db=snr)
        
        # --- PRINT THE RESULTS ---
        print(f"\nStep {step:02d} | Scanned: {telemetry['current_scanning_band']}")
        print(f"  -> Environment: {telemetry['signal_presence_status']} | SNR: {telemetry['signal_strength']} dB")
        print(f"  -> UCB1 Scores: {[ch['ucb1_score'] for ch in telemetry['all_channel_standings']]}")
        
        if step == 4:
            print("  >>> CHECK 1: Did it explore all 4 bands? (Should have tested A, B, C, D once)")
        if step == 10:
            print(f"  >>> CHECK 2: Is it exploiting Band-B? Next selected is: {telemetry['next_selected_band']}")
        if step == 11:
            print("  >>> PRIMARY USER ENTERS BAND-B! COLLISION DETECTED!")
        if step == 15:
            print(f"  >>> CHECK 3: Did it adapt? Next selected is: {telemetry['next_selected_band']} (Should be Band-D now)")

if __name__ == "__main__":
    run_simulation_test()

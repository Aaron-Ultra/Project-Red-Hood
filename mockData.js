/**
 * SMART SCAN STRATEGY - ELECTRONIC WARFARE SURVEILLANCE
 * Dedicated Mock Data Module & API Integration Bridge
 * 
 * ROLE BOUNDARY:
 * This module strictly acts as the data provider for the Frontend UI.
 * Backend / Algorithm developers can replace the internal state or methods
 * with fetch('/api/scan') or WebSocket calls without changing any UI component.
 */

class MockDataStore {
  constructor() {
    this.listeners = [];
    this.autoScanInterval = null;
    this.isAutoScanning = false;
    this.scanStepCount = 142;
    this.sessionNumber = "#1042";

    // Initial 16 Frequency Bands covering 1.0 GHz to 6.0 GHz spectrum
    this.bands = [
      {
        bandId: "B01",
        frequency: 1.10,
        freqRange: "1.05 - 1.15 GHz",
        signalStrength: -72,
        bandwidth: 10,
        status: "CLEAR",
        anomalyScore: 0.12,
        observations: 45,
        reward: 0.35,
        averageReward: 0.41,
        ucb1Score: 0.52,
        priority: 12,
        decision: "EXPLORE",
        decisionReason: "Low active signal strength; routine exploration.",
        explorationVal: 0.3
      },
      {
        bandId: "B02",
        frequency: 1.45,
        freqRange: "1.40 - 1.50 GHz",
        signalStrength: -68,
        bandwidth: 15,
        status: "CLEAR",
        anomalyScore: 0.21,
        observations: 38,
        reward: 0.42,
        averageReward: 0.48,
        ucb1Score: 0.61,
        priority: 9,
        decision: "EXPLORE",
        decisionReason: "Moderate reward history; periodic check required.",
        explorationVal: 0.4
      },
      {
        bandId: "B03",
        frequency: 1.80,
        freqRange: "1.75 - 1.85 GHz",
        signalStrength: -61,
        bandwidth: 20,
        status: "DETECTED",
        anomalyScore: 0.54,
        observations: 31,
        reward: 0.71,
        averageReward: 0.71,
        ucb1Score: 0.76,
        priority: 3,
        decision: "EXPLOIT",
        decisionReason: "Stable signal presence with good historical reward.",
        explorationVal: 0.75
      },
      {
        bandId: "B04",
        frequency: 2.15,
        freqRange: "2.10 - 2.20 GHz",
        signalStrength: -80,
        bandwidth: 10,
        status: "CLEAR",
        anomalyScore: 0.08,
        observations: 12,
        reward: 0.22,
        averageReward: 0.30,
        ucb1Score: 0.58,
        priority: 11,
        decision: "EXPLORE",
        decisionReason: "Low observation count creates high exploration bonus.",
        explorationVal: 0.2
      },
      {
        bandId: "B05",
        frequency: 2.40,
        freqRange: "2.35 - 2.45 GHz",
        signalStrength: -48,
        bandwidth: 20,
        status: "DETECTED",
        anomalyScore: 0.78,
        observations: 23,
        reward: 0.84,
        averageReward: 0.79,
        ucb1Score: 0.91,
        priority: 2,
        decision: "EXPLOIT",
        decisionReason: "Band B05 has consistently produced a high average reward and strong signal presence.",
        explorationVal: 0.85
      },
      {
        bandId: "B06",
        frequency: 2.70,
        freqRange: "2.65 - 2.75 GHz",
        signalStrength: -75,
        bandwidth: 15,
        status: "CLEAR",
        anomalyScore: 0.15,
        observations: 19,
        reward: 0.31,
        averageReward: 0.36,
        ucb1Score: 0.55,
        priority: 14,
        decision: "EXPLORE",
        decisionReason: "Baseline noise scan level.",
        explorationVal: 0.25
      },
      {
        bandId: "B07",
        frequency: 3.10,
        freqRange: "3.05 - 3.15 GHz",
        signalStrength: -55,
        bandwidth: 25,
        status: "INTERFERENCE",
        anomalyScore: 0.62,
        observations: 54,
        reward: 0.65,
        averageReward: 0.68,
        ucb1Score: 0.74,
        priority: 5,
        decision: "EXPLOIT",
        decisionReason: "High spectral activity with broadband interference.",
        explorationVal: 0.68
      },
      {
        bandId: "B08",
        frequency: 3.45,
        freqRange: "3.40 - 3.50 GHz",
        signalStrength: -82,
        bandwidth: 10,
        status: "CLEAR",
        anomalyScore: 0.05,
        observations: 9,
        reward: 0.18,
        averageReward: 0.25,
        ucb1Score: 0.51,
        priority: 15,
        decision: "EXPLORE",
        decisionReason: "Low observation uncertainty check.",
        explorationVal: 0.15
      },
      {
        bandId: "B09",
        frequency: 3.80,
        freqRange: "3.75 - 3.85 GHz",
        signalStrength: -64,
        bandwidth: 20,
        status: "DETECTED",
        anomalyScore: 0.49,
        observations: 27,
        reward: 0.62,
        averageReward: 0.64,
        ucb1Score: 0.72,
        priority: 6,
        decision: "EXPLOIT",
        decisionReason: "Confirmed radar pulse emission candidate.",
        explorationVal: 0.65
      },
      {
        bandId: "B10",
        frequency: 4.15,
        freqRange: "4.10 - 4.20 GHz",
        signalStrength: -78,
        bandwidth: 15,
        status: "CLEAR",
        anomalyScore: 0.14,
        observations: 16,
        reward: 0.29,
        averageReward: 0.33,
        ucb1Score: 0.53,
        priority: 13,
        decision: "EXPLORE",
        decisionReason: "Quiescent band sweep.",
        explorationVal: 0.22
      },
      {
        bandId: "B11",
        frequency: 4.50,
        freqRange: "4.45 - 4.55 GHz",
        signalStrength: -58,
        bandwidth: 20,
        status: "DETECTED",
        anomalyScore: 0.66,
        observations: 41,
        reward: 0.74,
        averageReward: 0.72,
        ucb1Score: 0.79,
        priority: 4,
        decision: "EXPLOIT",
        decisionReason: "Persistent military comms frequency.",
        explorationVal: 0.72
      },
      {
        bandId: "B12",
        frequency: 4.85,
        freqRange: "4.80 - 4.90 GHz",
        signalStrength: -52,
        bandwidth: 30,
        status: "ANOMALY",
        anomalyScore: 0.94,
        observations: 8,
        reward: 0.88,
        averageReward: 0.88,
        ucb1Score: 0.98,
        priority: 1,
        decision: "EXPLORE",
        decisionReason: "Band B12 was selected for exploration because it has limited observations (8) and extremely high uncertainty coupled with a massive anomaly spike.",
        explorationVal: 0.15
      },
      {
        bandId: "B13",
        frequency: 5.15,
        freqRange: "5.10 - 5.20 GHz",
        signalStrength: -76,
        bandwidth: 20,
        status: "CLEAR",
        anomalyScore: 0.19,
        observations: 22,
        reward: 0.36,
        averageReward: 0.38,
        ucb1Score: 0.54,
        priority: 10,
        decision: "EXPLORE",
        decisionReason: "Upper band surveillance check.",
        explorationVal: 0.3
      },
      {
        bandId: "B14",
        frequency: 5.40,
        freqRange: "5.35 - 5.45 GHz",
        signalStrength: -63,
        bandwidth: 25,
        status: "DETECTED",
        anomalyScore: 0.58,
        observations: 36,
        reward: 0.69,
        averageReward: 0.67,
        ucb1Score: 0.73,
        priority: 7,
        decision: "EXPLOIT",
        decisionReason: "High duty-cycle frequency target.",
        explorationVal: 0.64
      },
      {
        bandId: "B15",
        frequency: 5.75,
        freqRange: "5.70 - 5.80 GHz",
        signalStrength: -70,
        bandwidth: 20,
        status: "CLEAR",
        anomalyScore: 0.28,
        observations: 29,
        reward: 0.45,
        averageReward: 0.44,
        ucb1Score: 0.57,
        priority: 8,
        decision: "EXPLORE",
        decisionReason: "Periodic upper-spectrum monitoring.",
        explorationVal: 0.42
      },
      {
        bandId: "B16",
        frequency: 6.00,
        freqRange: "5.95 - 6.05 GHz",
        signalStrength: -85,
        bandwidth: 10,
        status: "CLEAR",
        anomalyScore: 0.04,
        observations: 6,
        reward: 0.10,
        averageReward: 0.18,
        ucb1Score: 0.48,
        priority: 16,
        decision: "EXPLORE",
        decisionReason: "Spectrum boundary scan.",
        explorationVal: 0.1
      }
    ];

    // Selected state
    this.currentBandId = "B05";
    this.nextBandId = "B12";
    this.selectedBandId = "B05";

    // Scan History Log
    this.historyLog = [
      { step: 142, timestamp: "18:03:52", bandId: "B05", frequency: "2.40 GHz", signal: "-48 dBm", decision: "EXPLOIT", reward: 0.84, ucb1: 0.91, anomaly: "NORMAL" },
      { step: 141, timestamp: "18:03:49", bandId: "B12", frequency: "4.85 GHz", signal: "-52 dBm", decision: "EXPLORE", reward: 0.88, ucb1: 0.98, anomaly: "ANOMALY DETECTED" },
      { step: 140, timestamp: "18:03:45", bandId: "B03", frequency: "1.80 GHz", signal: "-61 dBm", decision: "EXPLOIT", reward: 0.71, ucb1: 0.76, anomaly: "NORMAL" },
      { step: 139, timestamp: "18:03:40", bandId: "B11", frequency: "4.50 GHz", signal: "-58 dBm", decision: "EXPLOIT", reward: 0.74, ucb1: 0.79, anomaly: "NORMAL" },
      { step: 138, timestamp: "18:03:36", bandId: "B07", frequency: "3.10 GHz", signal: "-55 dBm", decision: "EXPLOIT", reward: 0.65, ucb1: 0.74, anomaly: "INTERFERENCE" },
      { step: 137, timestamp: "18:03:31", bandId: "B09", frequency: "3.80 GHz", signal: "-64 dBm", decision: "EXPLOIT", reward: 0.62, ucb1: 0.72, anomaly: "NORMAL" },
      { step: 136, timestamp: "18:03:26", bandId: "B02", frequency: "1.45 GHz", signal: "-68 dBm", decision: "EXPLORE", reward: 0.42, ucb1: 0.61, anomaly: "NORMAL" },
      { step: 135, timestamp: "18:03:20", bandId: "B14", frequency: "5.40 GHz", signal: "-63 dBm", decision: "EXPLOIT", reward: 0.69, ucb1: 0.73, anomaly: "NORMAL" }
    ];

    // Key Operational EW Performance Metrics
    this.performanceMetrics = {
      detectionLatency: "14 ms",
      probDetection: "96.4%",
      probFalseAlarm: "1.2%",
      interceptRate: "45.2 scans/s",
      avgReward: "0.82",
      scanningEfficiency: "91.8%",
      cumulativeRewardTrend: [0.35, 0.48, 0.56, 0.64, 0.72, 0.78, 0.82, 0.84],
      bandExplorationDistribution: {
        exploitCount: 89,
        exploreCount: 53,
        exploitRatio: "62.7%",
        exploreRatio: "37.3%"
      }
    };
  }

  /**
   * Return complete UI State object expected by components
   */
  getState() {
    const currentBand = this.getBandById(this.currentBandId) || this.bands[4];
    const nextBand = this.getBandById(this.nextBandId) || this.bands[11];
    const selectedBand = this.getBandById(this.selectedBandId) || currentBand;

    // Rank bands by UCB1 Score descending
    const sortedBands = [...this.bands].sort((a, b) => b.ucb1Score - a.ucb1Score);
    const rankedBands = sortedBands.map((b, idx) => ({
      ...b,
      priority: idx + 1
    }));

    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0];

    return {
      systemStatus: {
        status: "SYSTEM ONLINE",
        session: this.sessionNumber,
        lastUpdate: timeStr,
        backendSource: "MOCK DATA (API READY)",
        scanCount: this.scanStepCount
      },
      currentBand,
      nextBand,
      selectedBand,
      bands: rankedBands,
      history: this.historyLog,
      performance: this.performanceMetrics,
      isAutoScanning: this.isAutoScanning
    };
  }

  getBandById(bandId) {
    return this.bands.find(b => b.bandId === bandId);
  }

  selectBand(bandId) {
    if (this.getBandById(bandId)) {
      this.selectedBandId = bandId;
      this.notifyListeners();
    }
  }

  /**
   * Advance to the next scanning target step.
   * Simulates real-time spectrum feedback & UCB1 re-evaluation.
   */
  async triggerNextScan() {
    try {
      const response = await fetch('http://localhost:5000/api/scan/next', { method: 'POST' });
      if (!response.ok) throw new Error('API Error');
      const data = await response.json();
      
      this.scanStepCount++;
      
      // The API tells us what band it just scanned
      this.currentBandId = data.bandId;
      
      const currBandObj = this.getBandById(this.currentBandId);
      if (currBandObj) {
        currBandObj.observations = data.observations;
        currBandObj.signalStrength = data.signalStrength;
        currBandObj.reward = data.reward;
        currBandObj.averageReward = data.averageReward;
        currBandObj.status = data.status;
        currBandObj.anomalyScore = data.anomalyScore;
        currBandObj.ucb1Score = data.ucb1Score;
        currBandObj.priority = data.priority;
        currBandObj.decision = data.decision;
        currBandObj.decisionReason = data.decisionReason;
      }
      
      this.nextBandId = data.nextBand || "B01";
      this.selectedBandId = this.currentBandId;
      
      const now = new Date();
      const timeStr = now.toTimeString().split(' ')[0];
      
      this.historyLog.unshift({
        step: this.scanStepCount,
        timestamp: timeStr,
        bandId: data.bandId,
        frequency: `${data.frequency.toFixed(2)} GHz`,
        signal: `${data.signalStrength} dBm`,
        decision: data.decision,
        reward: data.reward,
        ucb1: data.ucb1Score,
        anomaly: data.status === "ANOMALY" ? "ANOMALY DETECTED" : data.status
      });

      if (this.historyLog.length > 50) this.historyLog.pop();

      this.notifyListeners();
    } catch (e) {
      console.error("Failed to fetch from API:", e);
    }
  }

  toggleAutoScan() {
    this.isAutoScanning = !this.isAutoScanning;
    if (this.isAutoScanning) {
      this.autoScanInterval = setInterval(() => {
        this.triggerNextScan();
      }, 2500);
    } else {
      if (this.autoScanInterval) {
        clearInterval(this.autoScanInterval);
        this.autoScanInterval = null;
      }
    }
    this.notifyListeners();
  }

  /**
   * Pre-set Demonstration Scenarios for Judges / Presenter
   */
  switchScenario(scenarioKey) {
    if (scenarioKey === 'high_anomaly') {
      const b12 = this.getBandById('B12');
      if (b12) {
        b12.status = 'ANOMALY';
        b12.anomalyScore = 0.98;
        b12.signalStrength = -38;
        b12.decision = 'EXPLORE';
        b12.decisionReason = 'Critical anomaly detected in Band B12 with low observation count (8). Immediate exploration recommended.';
      }
      this.currentBandId = 'B12';
      this.nextBandId = 'B05';
    } else if (scenarioKey === 'high_reward_exploit') {
      const b05 = this.getBandById('B05');
      if (b05) {
        b05.status = 'DETECTED';
        b05.anomalyScore = 0.82;
        b05.decision = 'EXPLOIT';
        b05.decisionReason = 'Band B05 has consistently produced a high average reward (0.79) over 23 observations.';
      }
      this.currentBandId = 'B05';
      this.nextBandId = 'B03';
    } else if (scenarioKey === 'dense_rf') {
      this.bands.forEach(b => {
        if (['B03', 'B05', 'B07', 'B09', 'B11', 'B12', 'B14'].includes(b.bandId)) {
          b.signalStrength = Math.round(-45 - Math.random() * 15);
          b.status = 'DETECTED';
        }
      });
    }
    this.notifyListeners();
  }

  subscribe(listener) {
    this.listeners.push(listener);
    // Initial emission
    listener(this.getState());
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  notifyListeners() {
    const state = this.getState();
    this.listeners.forEach(l => l(state));
  }
}

// Global Singleton Export for Frontend Application
window.mockData = new MockDataStore();

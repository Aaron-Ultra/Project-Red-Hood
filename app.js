/**
 * SMART SCAN STRATEGY - ELECTRONIC WARFARE SURVEILLANCE
 * Frontend Controller & UI Renderer (Projector-Optimized)
 */

document.addEventListener('DOMContentLoaded', () => {
  // Ensure mockData store is initialized
  if (!window.mockData) {
    console.error("mockData store not found!");
    return;
  }

  // DOM Caches
  const elements = {
    // Header Metadata
    sysStatus: document.getElementById('sys-status'),
    sysSession: document.getElementById('sys-session'),
    sysTime: document.getElementById('sys-time'),
    sysSource: document.getElementById('sys-source'),
    btnToggleProjector: document.getElementById('btn-toggle-projector'),

    // Navigation Tabs
    navTabBtns: document.querySelectorAll('.nav-tab-btn'),
    tabPanels: document.querySelectorAll('.tab-content-panel'),

    // Hero Spectrum Container
    spectrumGridContainer: document.getElementById('spectrum-grid-container'),

    // Current Observation Card
    obsFreq: document.getElementById('obs-freq'),
    obsSignal: document.getElementById('obs-signal'),
    obsBw: document.getElementById('obs-bw'),
    obsStatusContainer: document.getElementById('obs-status-container'),
    obsAnomaly: document.getElementById('obs-anomaly'),
    obsCount: document.getElementById('obs-count'),

    // UCB1 Decision Panel
    ucb1HeroBadge: document.getElementById('ucb1-hero-badge'),
    ucb1DecisionText: document.getElementById('ucb1-decision-text'),
    ucb1Score: document.getElementById('ucb1-score'),
    ucb1Priority: document.getElementById('ucb1-priority'),
    ucb1Reward: document.getElementById('ucb1-reward'),
    ucb1AvgReward: document.getElementById('ucb1-avg-reward'),
    expScalePin: document.getElementById('exp-scale-pin'),
    expStanceText: document.getElementById('exp-stance-text'),

    // Why This Band
    whyText: document.getElementById('why-text'),
    scenarioSelect: document.getElementById('scenario-select'),

    // Workflow Card
    wfCurrentId: document.getElementById('wf-current-id'),
    wfCurrentFreq: document.getElementById('wf-current-freq'),
    wfNextId: document.getElementById('wf-next-id'),
    wfNextFreq: document.getElementById('wf-next-freq'),
    btnScanNext: document.getElementById('btn-scan-next'),
    btnAutoScan: document.getElementById('btn-auto-scan'),

    // Tables
    priorityTableBody: document.getElementById('priority-table-body'),
    historyTableBody: document.getElementById('history-table-body')
  };

  /**
   * Main Render Function - Triggered on state changes
   */
  function render(state) {
    const { systemStatus, currentBand, nextBand, selectedBand, bands, history, isAutoScanning } = state;

    // 1. Render Header Metadata
    if (elements.sysStatus) elements.sysStatus.textContent = systemStatus.status;
    if (elements.sysSession) elements.sysSession.textContent = systemStatus.session;
    if (elements.sysTime) elements.sysTime.textContent = systemStatus.lastUpdate;
    if (elements.sysSource) elements.sysSource.textContent = systemStatus.backendSource;

    // 2. Render Hero Frequency Spectrum
    renderSpectrum(bands, currentBand.bandId, nextBand.bandId, selectedBand.bandId);

    // 3. Render Current Observation Panel (Using selected/current band)
    const activeBand = selectedBand || currentBand;
    if (elements.obsFreq) elements.obsFreq.textContent = `${activeBand.frequency.toFixed(2)} GHz`;
    if (elements.obsSignal) elements.obsSignal.textContent = `${activeBand.signalStrength} dBm`;
    if (elements.obsBw) elements.obsBw.textContent = `${activeBand.bandwidth} MHz`;
    if (elements.obsAnomaly) elements.obsAnomaly.textContent = activeBand.anomalyScore.toFixed(2);
    if (elements.obsCount) elements.obsCount.textContent = activeBand.observations;

    // Signal Status Badge with Symbol
    if (elements.obsStatusContainer) {
      let statusClass = 'detected';
      let statusSymbol = '● DETECTED';
      if (activeBand.status === 'ANOMALY') {
        statusClass = 'anomaly';
        statusSymbol = '⚠️ ANOMALY';
      } else if (activeBand.status === 'CLEAR') {
        statusClass = 'clear';
        statusSymbol = '◯ CLEAR';
      } else if (activeBand.status === 'INTERFERENCE') {
        statusClass = 'detected';
        statusSymbol = '⚡ INTERFERENCE';
      }
      elements.obsStatusContainer.innerHTML = `<span class="status-badge ${statusClass}">${statusSymbol}</span>`;
    }

    // 4. Render UCB1 Decision Panel
    const decision = activeBand.decision || 'EXPLORE';
    if (elements.ucb1DecisionText) {
      elements.ucb1DecisionText.textContent = decision === 'EXPLOIT' ? '⚡ EXPLOIT' : '🔍 EXPLORE';
    }
    if (elements.ucb1HeroBadge) {
      if (decision === 'EXPLOIT') {
        elements.ucb1HeroBadge.className = 'ucb1-hero-badge exploit';
      } else {
        elements.ucb1HeroBadge.className = 'ucb1-hero-badge explore';
      }
    }

    if (elements.ucb1Score) elements.ucb1Score.textContent = activeBand.ucb1Score.toFixed(2);
    if (elements.ucb1Priority) elements.ucb1Priority.textContent = `#${activeBand.priority}`;
    if (elements.ucb1Reward) elements.ucb1Reward.textContent = activeBand.reward.toFixed(2);
    if (elements.ucb1AvgReward) elements.ucb1AvgReward.textContent = activeBand.averageReward.toFixed(2);

    // Exploration vs Exploitation Scale Position
    if (elements.expScalePin) {
      const pinPercent = Math.min(95, Math.max(5, activeBand.explorationVal * 100));
      elements.expScalePin.style.left = `${pinPercent}%`;
    }
    if (elements.expStanceText) {
      elements.expStanceText.textContent = decision === 'EXPLOIT' ? 'EXPLOITATION HEAVY' : 'EXPLORATION HEAVY';
    }

    // 5. Render "Why This Band?" Rationale
    if (elements.whyText) {
      elements.whyText.textContent = `"${activeBand.decisionReason}"`;
    }

    // 6. Render Workflow Transition Card
    if (elements.wfCurrentId) elements.wfCurrentId.textContent = currentBand.bandId;
    if (elements.wfCurrentFreq) elements.wfCurrentFreq.textContent = `${currentBand.frequency.toFixed(2)} GHz`;
    if (elements.wfNextId) elements.wfNextId.textContent = nextBand.bandId;
    if (elements.wfNextFreq) elements.wfNextFreq.textContent = `${nextBand.frequency.toFixed(2)} GHz`;

    if (elements.btnAutoScan) {
      if (isAutoScanning) {
        elements.btnAutoScan.innerHTML = '<span>⏸️ AUTO-SCAN: ON</span>';
        elements.btnAutoScan.classList.add('is-active');
      } else {
        elements.btnAutoScan.innerHTML = '<span>▶️ AUTO-SCAN: OFF</span>';
        elements.btnAutoScan.classList.remove('is-active');
      }
    }

    // 7. Render Band Priority Table
    renderPriorityTable(bands, currentBand.bandId, nextBand.bandId, selectedBand.bandId);

    // 8. Render History Log Table
    renderHistoryTable(history);
  }

  /**
   * Render Frequency Spectrum Columns
   */
  function renderSpectrum(bands, currentId, nextId, selectedId) {
    if (!elements.spectrumGridContainer) return;

    // Sort by frequency for natural spectrum display
    const freqSorted = [...bands].sort((a, b) => a.frequency - b.frequency);

    elements.spectrumGridContainer.innerHTML = freqSorted.map(b => {
      const isCurrent = b.bandId === currentId;
      const isNext = b.bandId === nextId;
      const isSelected = b.bandId === selectedId;

      let colClasses = 'spectrum-band-col';
      if (isCurrent) colClasses += ' is-current';
      else if (isNext) colClasses += ' is-next';
      if (isSelected) colClasses += ' is-selected';

      // Height calculation for signal strength bar
      const normSignal = Math.max(10, Math.min(100, (b.signalStrength + 100) * 1.5));
      const isHighSignal = b.signalStrength > -60;

      let topBadgeHtml = '';
      if (isCurrent) topBadgeHtml = `<span class="band-top-badge badge-current-scan">CURRENT SCAN</span>`;
      else if (isNext) topBadgeHtml = `<span class="band-top-badge badge-next-target">NEXT TARGET</span>`;
      else topBadgeHtml = `<span class="band-top-badge">&nbsp;</span>`;

      return `
        <div class="${colClasses}" data-band-id="${b.bandId}" title="Band ${b.bandId}: ${b.frequency.toFixed(2)} GHz (${b.signalStrength} dBm)">
          ${topBadgeHtml}
          <span class="band-id">${b.bandId}</span>
          <span class="band-freq">${b.frequency.toFixed(2)}G</span>
          <div class="signal-bar-outer">
            <div class="signal-bar-inner ${isHighSignal ? 'high-signal' : ''}" style="height: ${normSignal}%;"></div>
          </div>
          <span class="band-dbm">${b.signalStrength}dB</span>
        </div>
      `;
    }).join('');

    // Attach click listeners to spectrum columns
    elements.spectrumGridContainer.querySelectorAll('.spectrum-band-col').forEach(col => {
      col.addEventListener('click', () => {
        const bandId = col.getAttribute('data-band-id');
        window.mockData.selectBand(bandId);
      });
    });
  }

  /**
   * Render Band Priority Ranking Table
   */
  function renderPriorityTable(bands, currentId, nextId, selectedId) {
    if (!elements.priorityTableBody) return;

    elements.priorityTableBody.innerHTML = bands.map(b => {
      const isCurrent = b.bandId === currentId;
      const isNext = b.bandId === nextId;

      let rowClass = '';
      if (isCurrent) rowClass = 'is-current-row';
      else if (isNext) rowClass = 'is-next-row';

      const decisionBadge = b.decision === 'EXPLOIT' 
        ? `<span style="color: var(--text-primary); font-weight: 900;">⚡ EXPLOIT</span>` 
        : `<span style="color: var(--text-secondary); font-weight: 900;">🔍 EXPLORE</span>`;

      return `
        <tr class="${rowClass}" data-band-id="${b.bandId}">
          <td class="table-rank">#${b.priority}</td>
          <td class="table-band-id">${b.bandId} ${isCurrent ? '⭐' : ''}</td>
          <td class="table-mono">${b.frequency.toFixed(2)} GHz</td>
          <td class="table-mono">${b.signalStrength} dBm</td>
          <td class="table-mono">${b.observations}</td>
          <td class="table-mono">${b.averageReward.toFixed(2)}</td>
          <td class="table-mono" style="font-weight: 900;">${b.ucb1Score.toFixed(2)}</td>
          <td>${decisionBadge}</td>
        </tr>
      `;
    }).join('');

    // Attach row click listeners
    elements.priorityTableBody.querySelectorAll('tr').forEach(row => {
      row.addEventListener('click', () => {
        const bandId = row.getAttribute('data-band-id');
        window.mockData.selectBand(bandId);
      });
    });
  }

  /**
   * Render Scan History Log Table
   */
  function renderHistoryTable(history) {
    if (!elements.historyTableBody) return;

    elements.historyTableBody.innerHTML = history.map(h => {
      const isExploit = h.decision === 'EXPLOIT';
      return `
        <tr>
          <td class="table-mono">#${h.step}</td>
          <td class="table-mono">${h.timestamp}</td>
          <td class="table-band-id">${h.bandId}</td>
          <td class="table-mono">${h.frequency}</td>
          <td class="table-mono">${h.signal}</td>
          <td>${isExploit ? '⚡ EXPLOIT' : '🔍 EXPLORE'}</td>
          <td class="table-mono">${h.reward}</td>
          <td class="table-mono">${h.ucb1}</td>
          <td style="font-weight: 800;">${h.anomaly}</td>
        </tr>
      `;
    }).join('');
  }

  // ==========================================================================
  // EVENT LISTENERS & NAVIGATION
  // ==========================================================================

  // 1. Tab Navigation Handler
  elements.navTabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');

      elements.navTabBtns.forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
      });
      elements.tabPanels.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');

      const targetPanel = document.getElementById(`tab-${targetTab}`);
      if (targetPanel) targetPanel.classList.add('active');
    });
  });

  // 2. Projector Test Mode Toggle
  if (elements.btnToggleProjector) {
    elements.btnToggleProjector.addEventListener('click', () => {
      document.body.classList.toggle('projector-grayscale-mode');
      const isGrayscale = document.body.classList.contains('projector-grayscale-mode');
      elements.btnToggleProjector.innerHTML = isGrayscale 
        ? '<span>☀️ NORMAL LIGHT MODE</span>' 
        : '<span>📽️ PROJECTOR TEST MODE</span>';
    });
  }

  // 3. Workflow Buttons
  if (elements.btnScanNext) {
    elements.btnScanNext.addEventListener('click', () => {
      window.mockData.triggerNextScan();
    });
  }

  if (elements.btnAutoScan) {
    elements.btnAutoScan.addEventListener('click', () => {
      window.mockData.toggleAutoScan();
    });
  }

  // 4. Scenario Selector
  if (elements.scenarioSelect) {
    elements.scenarioSelect.addEventListener('change', (e) => {
      window.mockData.switchScenario(e.target.value);
    });
  }

  // Subscribe to state updates
  window.mockData.subscribe(render);
});

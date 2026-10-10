// ==========================================================================
// TIGERTRACE AI - COMMAND CENTER JAVASCRIPT CONTROLLER (v2.5)
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  loadTelemetry();
  loadAvailableSDCards();
  loadReviewQueue();
  loadAlerts();
  loadTigerCatalogue();
  loadInteractiveMap();
  loadBehaviorPredictions();
  loadQuarantineBlanks();

  setInterval(loadTelemetry, 15000);
});

// -------------------------------------------------------------
// 1. Navigation Controller
// -------------------------------------------------------------
function initNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      navItems.forEach(i => i.classList.remove('active'));
      item.classList.add('active');

      const targetTab = item.getAttribute('data-tab');
      document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
      });

      const activePane = document.getElementById(targetTab);
      if (activePane) {
        activePane.classList.add('active');
      }

      if (targetTab === 'map-tab') loadInteractiveMap();
      if (targetTab === 'predictive-tab') {
        loadBehaviorPredictions();
        loadInteractiveMap();
      }
      if (targetTab === 'review-tab') loadReviewQueue();
      if (targetTab === 'alerts-tab') loadAlerts();
      if (targetTab === 'catalogue-tab') loadTigerCatalogue();
      if (targetTab === 'quarantine-tab') loadQuarantineBlanks();
    });
  });
}

// -------------------------------------------------------------
// 2. Telemetry Metrics Loader
// -------------------------------------------------------------
async function loadTelemetry() {
  try {
    const res = await fetch('/api/telemetry');
    const data = await res.json();

    document.getElementById('stat-total-frames').innerText = data.total_frames || 0;
    document.getElementById('stat-blanks-pct').innerText = (data.blank_percentage || 0) + '%';
    document.getElementById('stat-mb-saved').innerText = (data.mb_saved || 0).toFixed(1) + ' MB';
    document.getElementById('stat-hours-saved').innerText = (data.staff_hours_saved || 0).toFixed(1) + ' hrs';
    document.getElementById('stat-active-tigers').innerText = data.resident_tigers_count || 0;
    
    const badge = document.getElementById('review-badge');
    if (badge) {
      badge.innerText = data.pending_reviews_count || 0;
      badge.style.display = data.pending_reviews_count > 0 ? 'inline-block' : 'none';
    }
  } catch (err) {
    console.error('Failed to load telemetry:', err);
  }
}

// -------------------------------------------------------------
// 3. Available SD Cards Dropdown Loader
// -------------------------------------------------------------
async function loadAvailableSDCards() {
  const select = document.getElementById('sd-dropdown-select');
  if (!select) return;

  try {
    const res = await fetch('/api/available_sd_cards');
    const cards = await res.json();

    select.innerHTML = '<option value="">-- Or Choose Existing Camera Station Drop --</option>';
    cards.forEach(c => {
      select.innerHTML += `<option value="${c.path}">📷 ${c.name} (${c.image_count} photos)</option>`;
    });
  } catch (err) {
    console.error('Failed to load available SD cards:', err);
  }
}

function selectSDFromDropdown() {
  const select = document.getElementById('sd-dropdown-select');
  if (select.value) {
    document.getElementById('sd-folder-input').value = select.value;
  }
}

// -------------------------------------------------------------
// 4. Batch SD Ingestion with Animated Tiger Loader & Visual Results
// -------------------------------------------------------------
async function startSDProcessing() {
  const folderInput = document.getElementById('sd-folder-input').value.trim();
  const loaderWrapper = document.getElementById('tiger-loader-box');
  const progressBar = document.getElementById('tiger-progress-bar');
  const statusText = document.getElementById('loader-status-text');
  const runBtn = document.getElementById('start-process-btn');

  loaderWrapper.style.display = 'block';
  runBtn.disabled = true;
  runBtn.innerHTML = '⚡ Processing Batch...';

  // Step 1: Ingestion & EXIF
  progressBar.style.width = '25%';
  statusText.innerText = 'Scanning SD Card & Reading Camera EXIF Timestamps...';
  await delay(800);

  // Step 2: Blank Triage
  progressBar.style.width = '50%';
  statusText.innerText = 'Executing Phase 1 Triage & Staging Blank Frames into Quarantine...';
  await delay(900);

  try {
    const res = await fetch('/api/process_sd', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sd_card_path: folderInput })
    });
    const report = await res.json();

    // Step 3: SIFT Re-ID
    progressBar.style.width = '78%';
    statusText.innerText = 'Extracting CLAHE Flank Crops & Running HotSpotter SIFT Stripe Matcher...';
    await delay(900);

    // Step 4: Map & Alerts
    progressBar.style.width = '95%';
    statusText.innerText = 'Calculating Home Ranges (MCP), Overlap Polygons & Deviation Alerts...';
    await delay(700);

    // Complete
    progressBar.style.width = '100%';
    statusText.innerText = `Batch Complete! Processed ${report.total_frames} frames in ${report.execution_duration_sec}s.`;
    
    showProcessingSummary(report);
    loadTelemetry();
    loadInteractiveMap();
    loadAlerts();
    loadReviewQueue();
    loadQuarantineBlanks();
    loadAvailableSDCards();

  } catch (err) {
    statusText.innerText = 'Processing Error: ' + err.message;
    progressBar.style.background = '#e74c3c';
  } finally {
    runBtn.disabled = false;
    runBtn.innerHTML = '⚡ Execute Triage & Re-ID Pipeline';
  }
}

// Direct File/Folder Upload Handler
async function handleFolderUpload(input) {
  if (!input.files || input.files.length === 0) return;

  const stationId = prompt("Enter Camera Station ID for this uploaded folder (e.g. PTR_STN_01, PTR_STN_03, PTR_STN_10):", "PTR_STN_03");
  if (!stationId) return;

  const formData = new FormData();
  for (let i = 0; i < input.files.length; i++) {
    formData.append("files", input.files[i]);
  }
  formData.append("station_id", stationId);

  const loaderWrapper = document.getElementById('tiger-loader-box');
  const progressBar = document.getElementById('tiger-progress-bar');
  const statusText = document.getElementById('loader-status-text');

  loaderWrapper.style.display = 'block';
  progressBar.style.width = '30%';
  statusText.innerText = `Uploading ${input.files.length} images for ${stationId}...`;

  try {
    const res = await fetch('/api/upload_batch', {
      method: 'POST',
      body: formData
    });
    const report = await res.json();

    progressBar.style.width = '100%';
    statusText.innerText = `Upload & Processing Complete! Processed ${report.total_frames} frames.`;
    showProcessingSummary(report);
    loadTelemetry();
    loadInteractiveMap();
    loadAlerts();
    loadReviewQueue();
    loadQuarantineBlanks();
    loadAvailableSDCards();
  } catch (err) {
    statusText.innerText = 'Upload failed: ' + err.message;
  }
}

function showProcessingSummary(report) {
  const summaryBox = document.getElementById('batch-summary-result');
  summaryBox.style.display = 'block';

  let html = `
    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:14px; margin-bottom:20px;">
      <div style="background:rgba(0,0,0,0.3); padding:14px; border-radius:10px; text-align:center;">
        <p style="font-size:11px; color:#95a5a6;">Photos Scanned</p>
        <h4 style="font-size:22px; color:#fff;">${report.total_frames}</h4>
      </div>
      <div style="background:rgba(0,0,0,0.3); padding:14px; border-radius:10px; text-align:center;">
        <p style="font-size:11px; color:#95a5a6;">Quarantined Blanks</p>
        <h4 style="font-size:22px; color:#f39c12;">${report.blank_quarantined}</h4>
      </div>
      <div style="background:rgba(0,0,0,0.3); padding:14px; border-radius:10px; text-align:center;">
        <p style="font-size:11px; color:#95a5a6;">Disk Storage Saved</p>
        <h4 style="font-size:22px; color:#2ecc71;">${report.triage_savings.mb_saved.toFixed(1)} MB</h4>
      </div>
      <div style="background:rgba(0,0,0,0.3); padding:14px; border-radius:10px; text-align:center;">
        <p style="font-size:11px; color:#95a5a6;">Pipeline Duration</p>
        <h4 style="font-size:22px; color:#3498db;">${report.execution_duration_sec}s</h4>
      </div>
    </div>

    <h4 style="margin:20px 0 12px 0; color:#2ecc71; font-size:16px;">🐾 Individual Tiger Detections & Spatial Sightings:</h4>
    <div class="sightings-visual-grid" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:18px;">
  `;

  const results = report.reid_results || [];
  if (results.length === 0) {
    html += `
      <div style="grid-column:1/-1; background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:20px; text-align:center;">
        <p style="color:#95a5a6; font-size:13px; margin:0;">No tiger stripe re-identification candidates identified in this batch (non-tiger or blank frames).</p>
      </div>
    `;
  } else {
    results.forEach(r => {
      const isHigh = r.confidence >= 0.70;
      const confPct = Math.round(r.confidence * 100);
      const isAuto = r.decision === 'auto_matched' || r.decision === 'matched';
      html += `
        <div class="sighting-card" style="background:linear-gradient(145deg, #0e1e16 0%, #07130c 100%); border:1.5px solid rgba(46, 204, 113, 0.35); border-radius:14px; overflow:hidden; box-shadow:0 8px 24px rgba(0,0,0,0.6);">
          <div class="sighting-thumb-wrapper" style="position:relative; width:100%; height:180px; background:#000;">
            <img src="${r.image_url}" alt="Tiger Sighting" style="width:100%; height:100%; object-fit:cover;">
            <span class="sighting-tag-badge" style="position:absolute; top:10px; left:10px; background:rgba(0,0,0,0.75); color:#2ecc71; padding:4px 8px; border-radius:6px; font-size:11px; font-weight:700; border:1px solid rgba(46,204,113,0.4);">
              📍 ${r.station_id}
            </span>
            <span class="sighting-score-badge" style="position:absolute; top:10px; right:10px; background:${isHigh ? '#2ecc71' : '#f39c12'}; color:#fff; padding:4px 8px; border-radius:6px; font-size:11px; font-weight:800;">
              ${confPct}% ${r.method ? r.method.toUpperCase() : 'MATCH'}
            </span>
          </div>
          <div class="sighting-body" style="padding:16px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
              <h4 class="sighting-tiger-name" style="font-size:16px; font-weight:800; color:#fff; margin:0;">🐅 ${r.tiger_id}</h4>
              <span style="background:${isAuto ? 'rgba(46,204,113,0.15)' : 'rgba(243,156,18,0.15)'}; color:${isAuto ? '#2ecc71' : '#f39c12'}; border:1px solid ${isAuto ? 'rgba(46,204,113,0.4)' : 'rgba(243,156,18,0.4)'}; font-size:10px; font-weight:700; padding:2px 8px; border-radius:10px; text-transform:uppercase;">
                ${r.decision}
              </span>
            </div>
            <div class="sighting-meta-row" style="display:flex; justify-content:space-between; font-size:11.5px; color:#bdc3c7; margin-bottom:4px;">
              <span>Range: <b style="color:#fff;">${r.range}</b></span>
              <span>Zone: <b style="color:#2ecc71;">${r.zone.toUpperCase()}</b></span>
            </div>
            <div class="sighting-meta-row" style="display:flex; justify-content:space-between; font-size:11.5px; color:#95a5a6; border-top:1px solid rgba(255,255,255,0.06); padding-top:6px; margin-top:6px;">
              <span>GPS: ${r.lat.toFixed(4)}°N, ${r.lon.toFixed(4)}°E</span>
              <span>File: <i>${r.image}</i></span>
            </div>
          </div>
        </div>
      `;
    });
  }

  html += `
    </div>
    <div style="margin-top:28px; padding-top:20px; border-top:1px solid rgba(255,255,255,0.08);">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <h4 style="color:#2ecc71; font-size:16px; margin:0;">🗺️ Live Reserve Map (Updated with Batch Detections & Trajectories):</h4>
        <button class="btn-secondary" onclick="loadInteractiveMap();">🔄 Refresh Map</button>
      </div>
      <div class="map-frame-wrapper" style="height:540px;">
        <iframe id="batch-map-iframe" src="/api/map?t=${new Date().getTime()}"></iframe>
      </div>
    </div>
  `;
  summaryBox.innerHTML = html;
}

// -------------------------------------------------------------
// 5. Interactive Reserve Map & Predictive Heatmap Loader
// -------------------------------------------------------------
async function loadInteractiveMap() {
  const ts = new Date().getTime();
  const iframe1 = document.getElementById('pench-map-iframe');
  if (iframe1) {
    iframe1.src = '/api/map?t=' + ts;
  }
  const iframe2 = document.getElementById('predictive-map-iframe');
  if (iframe2) {
    iframe2.src = '/api/map?t=' + ts;
  }
  const iframe3 = document.getElementById('batch-map-iframe');
  if (iframe3) {
    iframe3.src = '/api/map?t=' + ts;
  }
}

// -------------------------------------------------------------
// 5.5 Behavioral Movement Predictions Loader
// -------------------------------------------------------------
window.behaviorDataCache = null;

async function loadBehaviorPredictions() {
  const container = document.getElementById('predictive-cards-container');
  if (!container) return;

  try {
    const res = await fetch('/api/behavior_predictions');
    const predictions = await res.json();
    window.behaviorDataCache = predictions;
    renderPredictiveCards(predictions);
  } catch (err) {
    container.innerHTML = '<p style="color:#e74c3c; padding:16px;">Failed to load behavioral predictions: ' + err.message + '</p>';
  }
}

function renderPredictiveCards(predictions, filterType = 'all') {
  const container = document.getElementById('predictive-cards-container');
  if (!container) return;

  if (!predictions || Object.keys(predictions).length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1/-1; text-align:center; padding:30px; background:rgba(0,0,0,0.3); border-radius:12px; border:1px solid rgba(255,255,255,0.1);">
        <p style="color:#95a5a6; font-size:14px;">No resident tiger telemetry available to compute movement predictions.</p>
      </div>
    `;
    return;
  }

  let html = '';
  for (const [tigerId, pred] of Object.entries(predictions)) {
    const nextStns = pred.predicted_next_stations || [];
    const trend = pred.directional_trend || {};
    const heading = trend.compass_heading || 'STATIONARY';
    const dispKm = trend.displacement_km || 0.0;
    const approaching = trend.approaching_villages || [];
    const isHighConf = pred.status === 'success';

    // Apply Filter
    if (filterType === 'high' && (!isHighConf || nextStns.length === 0)) continue;
    if (filterType === 'alert' && approaching.length === 0) continue;

    let nextStnsHtml = '';
    if (nextStns.length > 0) {
      nextStnsHtml = nextStns.map(([stn, prob], idx) => {
        const pct = Math.round(prob * 100);
        return `
          <div style="margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; align-items:center; font-size:12px; margin-bottom:4px;">
              <span style="color:#fff;"><b>${stn}</b> <span style="color:#95a5a6; font-size:10px;">(Rank #${idx+1})</span></span>
              <span style="color:#2ecc71; font-weight:800; font-family:var(--font-mono); font-size:13px;">${pct}%</span>
            </div>
            <div style="background:rgba(255,255,255,0.08); border-radius:6px; height:8px; overflow:hidden;">
              <div style="background:linear-gradient(90deg, #3498db, #2ecc71); width:${pct}%; height:100%; border-radius:6px;"></div>
            </div>
          </div>
        `;
      }).join('');
    } else {
      nextStnsHtml = `<p style="font-size:11.5px; color:#95a5a6; font-style:italic; margin:4px 0;">Single station capture (${pred.current_station || 'N/A'}). Transition model active once dispersal occurs.</p>`;
    }

    let villageWarnHtml = '';
    if (approaching.length > 0) {
      villageWarnHtml = `
        <div style="background:rgba(231,76,60,0.18); border:1px solid rgba(231,76,60,0.45); border-radius:10px; padding:10px 12px; margin-bottom:12px; display:flex; align-items:center; gap:10px;">
          <span style="font-size:22px;">⚠️</span>
          <div>
            <div style="color:#e74c3c; font-size:12px; font-weight:800;">Converging toward ${approaching[0].village_name}</div>
            <div style="font-size:11px; color:#f0f7f3; margin-top:2px;">Distance closed: <b>${approaching[0].distance_closed_km} km</b> (Current: ${approaching[0].current_distance_km} km)</div>
          </div>
        </div>
      `;
    }

    html += `
      <div class="pred-card" style="background:linear-gradient(145deg, #0e1e16 0%, #07130c 100%); border:1.5px solid rgba(46, 204, 113, 0.35); border-radius:16px; padding:20px; box-shadow:0 10px 30px rgba(0,0,0,0.6); display:flex; flex-direction:column; position:relative; overflow:hidden;">
        <div style="position:absolute; top:0; left:0; right:0; height:3.5px; background:linear-gradient(90deg, #9b59b6, #3498db, #2ecc71);"></div>
        
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
          <div style="display:flex; align-items:center; gap:10px;">
            <div style="width:36px; height:36px; background:rgba(46,204,113,0.15); border:1px solid rgba(46,204,113,0.4); border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:20px;">
              🐅
            </div>
            <h4 style="font-size:17px; font-weight:800; color:#fff; margin:0; letter-spacing:0.3px;">${tigerId}</h4>
          </div>
          <span style="background:rgba(46,204,113,0.15); color:#2ecc71; font-size:11px; font-weight:700; padding:4px 10px; border-radius:14px; border:1px solid rgba(46,204,113,0.35);">
            ${pred.sighting_count} Sightings
          </span>
        </div>

        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin-bottom:14px;">
          <div style="background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:8px 10px;">
            <div style="font-size:10px; color:#95a5a6; text-transform:uppercase; font-weight:700; letter-spacing:0.5px;">📍 Last Station</div>
            <div style="font-size:12.5px; font-weight:800; color:#2ecc71; margin-top:2px;">${pred.current_station || 'Unknown'}</div>
          </div>
          <div style="background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:8px 10px;">
            <div style="font-size:10px; color:#95a5a6; text-transform:uppercase; font-weight:700; letter-spacing:0.5px;">🧭 Trajectory</div>
            <div style="font-size:12.5px; font-weight:800; color:#f39c12; margin-top:2px;">${heading} <span style="font-size:10.5px; color:#95a5a6; font-weight:normal;">(${dispKm} km)</span></div>
          </div>
        </div>

        <div style="background:rgba(0, 0, 0, 0.35); border:1px solid rgba(255, 255, 255, 0.08); border-radius:10px; padding:12px 14px; margin-bottom:12px;">
          <div style="font-size:10.5px; color:#95a5a6; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:8px; font-weight:800;">
            🎯 Markov Next Transitions:
          </div>
          ${nextStnsHtml}
        </div>

        ${villageWarnHtml}

        <div style="font-size:11px; color:#7f8c8d; line-height:1.4; margin-top:auto; border-top:1px solid rgba(255, 255, 255, 0.06); padding-top:10px;">
          ℹ️ ${pred.confidence_note}
        </div>
      </div>
    `;
  }

  if (!html) {
    html = `<div style="grid-column: 1/-1; text-align:center; padding:30px; color:#95a5a6;">No tigers match the selected filter.</div>`;
  }

  container.innerHTML = html;
}

function filterPredictiveCards(filterType, btn) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  if (window.behaviorDataCache) {
    renderPredictiveCards(window.behaviorDataCache, filterType);
  }
}

// -------------------------------------------------------------
// 6. Quarantined Blanks Gallery Loader
// -------------------------------------------------------------
async function loadQuarantineBlanks() {
  const container = document.getElementById('quarantine-cards-container');
  if (!container) return;

  try {
    const res = await fetch('/api/quarantine_blanks');
    const blanks = await res.json();

    if (!blanks || blanks.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1/-1; text-align:center; padding:30px; background:rgba(0,0,0,0.2); border-radius:12px;">
          <p style="color:#95a5a6;">No quarantined blank frames in current session.</p>
        </div>
      `;
      return;
    }

    let html = '';
    blanks.forEach(b => {
      html += `
        <div class="quarantine-card">
          <img src="${b.image_url}" alt="Blank Frame">
          <div class="quarantine-tag">${b.reason}</div>
          <div style="display:flex; justify-content:space-between; font-size:11px; color:#95a5a6; margin-top:4px;">
            <span>${b.filename}</span>
            <span>${b.size_mb} MB</span>
          </div>
        </div>
      `;
    });
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = '<p style="color:#e74c3c;">Failed to load quarantine gallery: ' + err.message + '</p>';
  }
}

// -------------------------------------------------------------
// 7. Human Review Queue Loader & Actions
// -------------------------------------------------------------
async function loadReviewQueue() {
  const container = document.getElementById('review-cards-container');
  try {
    const res = await fetch('/api/review_queue');
    const items = await res.json();

    if (!items || items.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1/-1; text-align:center; padding:40px; background:rgba(0,0,0,0.2); border-radius:12px;">
          <p style="color:#2ecc71; font-size:16px; font-weight:700;">✅ Review Queue is Clear!</p>
          <p style="color:#95a5a6; font-size:12px; margin-top:4px;">All camera trap tiger stripe matches are auto-verified with high confidence.</p>
        </div>
      `;
      return;
    }

    let html = '';
    items.forEach(item => {
      const vizImg = item.sift_match_viz_path ? `/api/image?path=${encodeURIComponent(item.sift_match_viz_path)}` : (item.flank_crop_path ? `/api/image?path=${encodeURIComponent(item.flank_crop_path)}` : '');
      html += `
        <div class="review-card">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-size:12px; color:#f39c12; font-weight:700;">ID #${item.review_id} | ${item.station_id}</span>
            <span class="score-badge amber">${(item.suggested_score * 100).toFixed(0)}% SIFT Match</span>
          </div>
          <img src="${vizImg}" class="review-preview-img" alt="SIFT Stripe Match Visualization">
          <p style="font-size:13px; margin-bottom:4px;"><b>Suggested Candidate:</b> <span style="color:#2ecc71; font-weight:700;">${item.suggested_tiger_id}</span></p>
          <p style="font-size:11px; color:#95a5a6;">Ambiguous stripe bifurcation pattern flagged for field officer audit.</p>
          <div class="action-btn-group">
            <button class="btn-approve" onclick="handleReviewAction(${item.review_id}, 'approve', '${item.suggested_tiger_id}')">✓ Confirm ID</button>
            <button class="btn-reassign" onclick="handleReviewAction(${item.review_id}, 'enroll_new', 'NEW_TIGER')">🐾 Enroll New</button>
          </div>
        </div>
      `;
    });
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = '<p style="color:#e74c3c;">Failed to load review queue: ' + err.message + '</p>';
  }
}

async function handleReviewAction(reviewId, action, tigerId) {
  try {
    const res = await fetch(`/api/review_queue/${reviewId}/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: action, tiger_id: tigerId })
    });
    const result = await res.json();
    alert(result.message || 'Action executed successfully.');
    loadReviewQueue();
    loadTelemetry();
  } catch (err) {
    alert('Action failed: ' + err.message);
  }
}

// -------------------------------------------------------------
// 8. Threat & Deviation Alert Center
// -------------------------------------------------------------
async function loadAlerts() {
  const container = document.getElementById('alerts-list-container');
  try {
    const res = await fetch('/api/alerts');
    const alerts = await res.json();

    if (!alerts || alerts.length === 0) {
      container.innerHTML = '<p style="color:#2ecc71; padding:16px;">✅ No critical behavioral deviations or village dispersal threats detected.</p>';
      return;
    }

    let html = '';
    alerts.forEach(a => {
      const isCritical = a.severity === 'CRITICAL';
      const itemClass = isCritical ? 'critical' : 'warning';
      const icon = isCritical ? '🔴' : '🟡';
      html += `
        <div class="alert-item ${itemClass}">
          <div style="font-size:24px;">${icon}</div>
          <div style="flex:1;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <h4 style="color:#fff; font-size:14px; font-weight:700;">${a.alert_type} - Tiger: ${a.tiger_id}</h4>
              <span style="font-size:11px; color:#95a5a6;">${a.created_at || ''}</span>
            </div>
            <p style="font-size:13px; color:#f0f7f3; margin:4px 0;">${a.detected_change}</p>
            <p style="font-size:11px; color:#95a5a6;">${a.supporting_evidence}</p>
          </div>
        </div>
      `;
    });
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = '<p style="color:#e74c3c;">Failed to load alerts: ' + err.message + '</p>';
  }
}

// -------------------------------------------------------------
// 9. Tiger Catalogue & Sightings Explorer
// -------------------------------------------------------------
async function loadTigerCatalogue() {
  const tbody = document.getElementById('catalogue-table-body');
  try {
    const res = await fetch('/api/tigers');
    const tigers = await res.json();

    let html = '';
    tigers.forEach(t => {
      html += `
        <tr>
          <td><b style="color:#2ecc71;">${t.tiger_id}</b></td>
          <td>${t.name || t.tiger_id}</td>
          <td>${t.status.toUpperCase()}</td>
          <td><b>${t.sighting_count || 0}</b> sightings</td>
          <td>${t.last_seen_date || 'N/A'}</td>
        </tr>
      `;
    });
    tbody.innerHTML = html;
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:#e74c3c;">Error: ${err.message}</td></tr>`;
  }
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

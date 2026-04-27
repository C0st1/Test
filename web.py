"""
PHANTOM MAILER — Web Interface
Flask-based web UI for running campaigns from a browser.
"""

import os
import sys
import json
import time
import threading
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import Flask, render_template_string, request, jsonify, Response
from flask_cors import CORS

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import PhantomEngine, SendResult
from templates import TEMPLATES, get_template_names, get_all_categories, template_summary
from renderer import MessageRenderer
from temp_mail import TempMailManager

app = Flask(__name__)
CORS(app)

# ── Global Campaign State ─────────────────────────────────────

campaign_state = {
    "running": False,
    "results": [],
    "stats": {"sent": 0, "failed": 0, "dry_run": 0, "total": 0, "progress": 0},
    "log": [],
    "engine": None,
    "thread": None,
}


def reset_state():
    campaign_state["running"] = False
    campaign_state["results"] = []
    campaign_state["stats"] = {"sent": 0, "failed": 0, "dry_run": 0, "total": 0, "progress": 0}
    campaign_state["log"] = []


def run_campaign(config: dict):
    """Run campaign in background thread."""
    global campaign_state

    try:
        engine = PhantomEngine(config)
        campaign_state["engine"] = engine

        def on_send(result: SendResult):
            campaign_state["results"].append({
                "index": result.index,
                "target": result.target,
                "subject": result.subject,
                "sender": result.sender,
                "template": result.template,
                "status": result.status,
                "error": result.error,
                "duration": round(result.duration, 3),
                "timestamp": datetime.now().isoformat(),
            })
            if result.status == "sent":
                campaign_state["stats"]["sent"] += 1
            elif result.status == "failed":
                campaign_state["stats"]["failed"] += 1
            elif result.status == "dry_run":
                campaign_state["stats"]["dry_run"] += 1

            campaign_state["stats"]["progress"] = (
                campaign_state["stats"]["sent"]
                + campaign_state["stats"]["failed"]
                + campaign_state["stats"]["dry_run"]
            )

            campaign_state["log"].append(
                f"[{result.status.upper()}] #{result.index} → {result.target} | {result.template} | {result.subject[:50]}..."
            )
            # Keep log manageable
            if len(campaign_state["log"]) > 200:
                campaign_state["log"] = campaign_state["log"][-200:]

        def on_progress(current, total):
            pass

        def on_status(msg):
            campaign_state["log"].append(str(msg))

        engine.on_send = on_send
        engine.on_progress = on_progress
        engine.on_status = on_status

        state = engine.run()

    except Exception as e:
        campaign_state["log"].append(f"[ERROR] {str(e)}")
    finally:
        campaign_state["running"] = False
        campaign_state["log"].append("[DONE] Campaign finished.")


# ═══════════════════════════════════════════════════════════════
#  HTML TEMPLATE
# ═══════════════════════════════════════════════════════════════

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>♨ PHANTOM MAILER</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;500;600;700&display=swap');

  * { margin: 0; padding: 0; box-sizing: border-box; }

  :root {
    --bg: #0a0a0f;
    --surface: #12121a;
    --surface2: #1a1a25;
    --border: #2a2a3a;
    --red: #ff3355;
    --red-dim: #ff335544;
    --green: #00ff88;
    --green-dim: #00ff8844;
    --yellow: #ffcc00;
    --yellow-dim: #ffcc0044;
    --cyan: #00ccff;
    --purple: #aa66ff;
    --text: #e0e0e8;
    --text-dim: #888898;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* Animated background */
  body::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background:
      radial-gradient(ellipse at 20% 20%, var(--red-dim) 0%, transparent 50%),
      radial-gradient(ellipse at 80% 80%, var(--purple) 0%, transparent 50%);
    opacity: 0.15;
    z-index: -1;
    animation: bgPulse 8s ease-in-out infinite alternate;
  }

  @keyframes bgPulse {
    0% { opacity: 0.1; }
    100% { opacity: 0.2; }
  }

  .header {
    text-align: center;
    padding: 30px 20px 20px;
    border-bottom: 1px solid var(--border);
  }

  .header h1 {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2rem;
    color: var(--red);
    text-shadow: 0 0 30px var(--red-dim);
    letter-spacing: 4px;
  }

  .header p {
    color: var(--text-dim);
    margin-top: 6px;
    font-size: 0.85rem;
    letter-spacing: 2px;
  }

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 24px;
    display: grid;
    grid-template-columns: 380px 1fr;
    gap: 24px;
  }

  @media (max-width: 900px) {
    .container { grid-template-columns: 1fr; }
  }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    position: relative;
    overflow: hidden;
  }

  .card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--red), var(--purple), var(--cyan));
  }

  .card h2 {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1rem;
    color: var(--red);
    margin-bottom: 16px;
    letter-spacing: 1px;
  }

  .form-group {
    margin-bottom: 14px;
  }

  .form-group label {
    display: block;
    font-size: 0.8rem;
    color: var(--text-dim);
    margin-bottom: 5px;
    letter-spacing: 0.5px;
  }

  .form-group input,
  .form-group select,
  .form-group textarea {
    width: 100%;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 12px;
    color: var(--text);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    outline: none;
    transition: border-color 0.2s;
  }

  .form-group input:focus,
  .form-group select:focus,
  .form-group textarea:focus {
    border-color: var(--red);
    box-shadow: 0 0 0 3px var(--red-dim);
  }

  .form-group textarea {
    resize: vertical;
    min-height: 60px;
  }

  .row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }

  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.9rem;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.2s;
    letter-spacing: 1px;
    width: 100%;
  }

  .btn-launch {
    background: var(--red);
    color: #fff;
    box-shadow: 0 4px 20px var(--red-dim);
  }

  .btn-launch:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 30px var(--red-dim);
  }

  .btn-launch:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }

  .btn-stop {
    background: var(--surface2);
    color: var(--yellow);
    border: 1px solid var(--yellow);
  }

  .btn-stop:hover {
    background: var(--yellow-dim);
  }

  .btn-dryrun {
    background: var(--surface2);
    color: var(--cyan);
    border: 1px solid var(--cyan);
  }

  .btn-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-top: 16px;
  }

  /* Stats */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 20px;
  }

  .stat-card {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    text-align: center;
  }

  .stat-card .value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.8rem;
    font-weight: 700;
  }

  .stat-card .label {
    font-size: 0.7rem;
    color: var(--text-dim);
    margin-top: 4px;
    letter-spacing: 1px;
    text-transform: uppercase;
  }

  .stat-sent .value { color: var(--green); }
  .stat-failed .value { color: var(--red); }
  .stat-dryrun .value { color: var(--yellow); }
  .stat-total .value { color: var(--cyan); }

  /* Progress bar */
  .progress-container {
    margin-bottom: 20px;
  }

  .progress-bar-bg {
    background: var(--surface2);
    border-radius: 8px;
    height: 28px;
    overflow: hidden;
    position: relative;
  }

  .progress-bar-fill {
    height: 100%;
    border-radius: 8px;
    background: linear-gradient(90deg, var(--red), var(--purple));
    transition: width 0.5s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 700;
    color: #fff;
    min-width: 40px;
  }

  .progress-label {
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
    font-size: 0.75rem;
    color: var(--text-dim);
  }

  /* Log */
  .log-container {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px;
    max-height: 300px;
    overflow-y: auto;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    line-height: 1.7;
  }

  .log-container::-webkit-scrollbar {
    width: 6px;
  }

  .log-container::-webkit-scrollbar-track {
    background: transparent;
  }

  .log-container::-webkit-scrollbar-thumb {
    background: var(--border);
    border-radius: 3px;
  }

  .log-entry-sent { color: var(--green); }
  .log-entry-failed { color: var(--red); }
  .log-entry-dry_run { color: var(--yellow); }
  .log-entry-error { color: var(--red); }
  .log-entry-done { color: var(--cyan); }

  /* Results table */
  .results-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8rem;
    margin-top: 12px;
  }

  .results-table th {
    text-align: left;
    padding: 8px 10px;
    border-bottom: 1px solid var(--border);
    color: var(--text-dim);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 1px;
    text-transform: uppercase;
  }

  .results-table td {
    padding: 6px 10px;
    border-bottom: 1px solid var(--border);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
  }

  .results-table tr:hover td {
    background: var(--surface2);
  }

  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.5px;
  }

  .badge-sent { background: var(--green-dim); color: var(--green); }
  .badge-failed { background: var(--red-dim); color: var(--red); }
  .badge-dry_run { background: var(--yellow-dim); color: var(--yellow); }

  /* Template cards */
  .templates-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 10px;
  }

  .template-card {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .template-card:hover {
    border-color: var(--red);
    box-shadow: 0 0 15px var(--red-dim);
  }

  .template-card.selected {
    border-color: var(--red);
    background: var(--red-dim);
  }

  .template-name {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    color: var(--cyan);
    margin-bottom: 4px;
  }

  .template-category {
    font-size: 0.7rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .template-urgency {
    margin-top: 4px;
    font-size: 0.8rem;
  }

  /* Tabs */
  .tabs {
    display: flex;
    gap: 0;
    margin-bottom: 20px;
  }

  .tab {
    padding: 10px 20px;
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text-dim);
    cursor: pointer;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    letter-spacing: 0.5px;
    transition: all 0.2s;
  }

  .tab:first-child { border-radius: 8px 0 0 8px; }
  .tab:last-child { border-radius: 0 8px 8px 0; }

  .tab.active {
    background: var(--red);
    color: #fff;
    border-color: var(--red);
  }

  .tab-content { display: none; }
  .tab-content.active { display: block; }

  /* Pool status */
  .pool-bar {
    display: flex;
    gap: 2px;
    margin-top: 8px;
  }

  .pool-segment {
    height: 6px;
    border-radius: 3px;
    flex: 1;
  }

  .pool-alive { background: var(--green); }
  .pool-dead { background: var(--red); opacity: 0.3; }

  .checkbox-group {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 4px;
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.8rem;
    color: var(--text);
    cursor: pointer;
  }

  .checkbox-label input[type="checkbox"] {
    accent-color: var(--red);
    width: 16px;
    height: 16px;
  }
</style>
</head>
<body>

<div class="header">
  <h1>♨ PHANTOM MAILER</h1>
  <p>EMAIL SPAM FRAMEWORK v2.0</p>
</div>

<div class="container">
  <!-- LEFT: Config Panel -->
  <div>
    <div class="card">
      <h2>⚙ CAMPAIGN CONFIG</h2>

      <div class="form-group">
        <label>TARGET EMAIL(S) — one per line</label>
        <textarea id="targets" placeholder="target@example.com&#10;another@corp.com">target@example.com</textarea>
      </div>

      <div class="row">
        <div class="form-group">
          <label>EMAIL COUNT</label>
          <input type="number" id="sendCount" value="20" min="1" max="10000">
        </div>
        <div class="form-group">
          <label>WORKERS</label>
          <input type="number" id="workers" value="3" min="1" max="20">
        </div>
      </div>

      <div class="row">
        <div class="form-group">
          <label>MIN DELAY (s)</label>
          <input type="number" id="minDelay" value="2" min="0" step="0.5">
        </div>
        <div class="form-group">
          <label>MAX DELAY (s)</label>
          <input type="number" id="maxDelay" value="8" min="0" step="0.5">
        </div>
      </div>

      <div class="form-group">
        <label>TEMPLATE</label>
        <select id="template">
          <option value="random">🎲 Random (Recommended)</option>
        </select>
      </div>

      <div class="form-group">
        <label>TEMP MAIL PROVIDER</label>
        <select id="tempProvider">
          <option value="all">🔄 All (Rotate)</option>
          <option value="guerrilla">Guerrilla Mail</option>
          <option value="mail.tm">Mail.tm</option>
          <option value="1secmail">1secmail</option>
        </select>
      </div>

      <div class="form-group">
        <label>OPTIONS</label>
        <div class="checkbox-group">
          <label class="checkbox-label">
            <input type="checkbox" id="addTypo" checked> Typos
          </label>
          <label class="checkbox-label">
            <input type="checkbox" id="addSignature" checked> Signatures
          </label>
          <label class="checkbox-label">
            <input type="checkbox" id="addUrgency" checked> Urgency
          </label>
          <label class="checkbox-label">
            <input type="checkbox" id="addDisclaimer" checked> Disclaimers
          </label>
        </div>
      </div>

      <div class="btn-row">
        <button class="btn btn-dryrun" onclick="launchCampaign(true)">👁 DRY RUN</button>
        <button class="btn btn-launch" onclick="launchCampaign(false)">🚀 LAUNCH</button>
      </div>
      <div style="margin-top: 10px;">
        <button class="btn btn-stop" id="stopBtn" onclick="stopCampaign()" disabled>⏹ STOP</button>
      </div>
    </div>

    <!-- Template Gallery -->
    <div class="card" style="margin-top: 16px;">
      <h2>📋 TEMPLATE GALLERY</h2>
      <div class="templates-grid" id="templateGrid"></div>
    </div>
  </div>

  <!-- RIGHT: Dashboard -->
  <div>
    <div class="card">
      <h2>📊 LIVE DASHBOARD</h2>

      <div class="stats-grid">
        <div class="stat-card stat-sent">
          <div class="value" id="statSent">0</div>
          <div class="label">Sent</div>
        </div>
        <div class="stat-card stat-failed">
          <div class="value" id="statFailed">0</div>
          <div class="label">Failed</div>
        </div>
        <div class="stat-card stat-dryrun">
          <div class="value" id="statDryRun">0</div>
          <div class="label">Dry Run</div>
        </div>
        <div class="stat-card stat-total">
          <div class="value" id="statTotal">0</div>
          <div class="label">Total</div>
        </div>
      </div>

      <div class="progress-container">
        <div class="progress-label">
          <span id="progressText">0 / 0</span>
          <span id="progressPct">0%</span>
        </div>
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" id="progressBar" style="width: 0%"></div>
        </div>
      </div>

      <!-- Pool status -->
      <div style="margin-bottom: 16px;">
        <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-dim);">
          <span>TEMP MAIL POOL</span>
          <span id="poolStatus">0 alive / 0 total</span>
        </div>
        <div class="pool-bar" id="poolBar"></div>
      </div>

      <div class="tabs">
        <div class="tab active" onclick="switchTab('log')">📡 LOG</div>
        <div class="tab" onclick="switchTab('results')">📋 RESULTS</div>
      </div>

      <div id="tab-log" class="tab-content active">
        <div class="log-container" id="logContainer">
          <div style="color: var(--text-dim);">Waiting for campaign...</div>
        </div>
      </div>

      <div id="tab-results" class="tab-content">
        <div style="overflow-x: auto; max-height: 350px; overflow-y: auto;">
          <table class="results-table" id="resultsTable">
            <thead>
              <tr>
                <th>#</th>
                <th>Status</th>
                <th>Template</th>
                <th>Target</th>
                <th>Subject</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody id="resultsBody"></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
// ── Populate templates ──────────────────────────────────────
const TEMPLATES = {{ templates_json|safe }};

function populateTemplates() {
  const select = document.getElementById('template');
  const grid = document.getElementById('templateGrid');

  TEMPLATES.forEach(t => {
    // Dropdown
    const opt = document.createElement('option');
    opt.value = t.name;
    opt.textContent = `${t.category.toUpperCase()} — ${t.name}`;
    select.appendChild(opt);

    // Card
    const card = document.createElement('div');
    card.className = 'template-card';
    card.dataset.name = t.name;
    card.innerHTML = `
      <div class="template-name">${t.name}</div>
      <div class="template-category">${t.category}</div>
      <div class="template-urgency">${'🔥'.repeat(t.urgency)}</div>
    `;
    card.onclick = () => {
      document.querySelectorAll('.template-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      select.value = t.name;
    };
    grid.appendChild(card);
  });
}

// ── Tab switching ───────────────────────────────────────────
function switchTab(tab) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById(`tab-${tab}`).classList.add('active');
}

// ── Campaign launch ────────────────────────────────────────
async function launchCampaign(dryRun) {
  const targets = document.getElementById('targets').value
    .split('\n').map(s => s.trim()).filter(s => s.length > 0);

  if (targets.length === 0) {
    alert('Enter at least one target email');
    return;
  }

  const config = {
    core: {
      send_count: parseInt(document.getElementById('sendCount').value),
      targets: targets,
      max_workers: parseInt(document.getElementById('workers').value),
      dry_run: dryRun,
    },
    timing: {
      min_delay: parseFloat(document.getElementById('minDelay').value),
      max_delay: parseFloat(document.getElementById('maxDelay').value),
      coffee_break_interval: 15,
      coffee_break_min: 30,
      coffee_break_max: 120,
      jitter: 0.3,
    },
    temp_mail: {
      provider: document.getElementById('tempProvider').value,
      pre_generate: 8,
      rotate_every: 3,
    },
    smtp: { enabled: false, servers: [], rotate: true },
    proxy: { enabled: false, list: [], rotate_every: 5, file: "" },
    message: {
      template_mode: document.getElementById('template').value,
      locale: "en_US",
      add_typo: document.getElementById('addTypo').checked,
      add_signature: document.getElementById('addSignature').checked,
      add_disclaimer: document.getElementById('addDisclaimer').checked,
      add_urgency: document.getElementById('addUrgency').checked,
    },
    subject: { mutate: true, add_prefix: true, add_emoji: true, emoji_probability: 0.3 },
    campaign: { auto_save_interval: 10, resume_file: "", name: "web_campaign" },
    analytics: { enabled: true, live_dashboard: true, save_report: true, report_format: "json" },
    logging: { level: "INFO", save_to_file: false, log_file: "phantom.log" },
  };

  try {
    const resp = await fetch('/api/launch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    const data = await resp.json();
    if (data.ok) {
      document.getElementById('stopBtn').disabled = false;
      startPolling();
    }
  } catch (e) {
    console.error(e);
  }
}

async function stopCampaign() {
  try {
    await fetch('/api/stop', { method: 'POST' });
    document.getElementById('stopBtn').disabled = true;
  } catch (e) {}
}

// ── Polling ─────────────────────────────────────────────────
let pollInterval = null;

function startPolling() {
  if (pollInterval) clearInterval(pollInterval);
  pollInterval = setInterval(pollStatus, 1000);
}

async function pollStatus() {
  try {
    const resp = await fetch('/api/status');
    const data = await resp.json();

    // Stats
    document.getElementById('statSent').textContent = data.stats.sent;
    document.getElementById('statFailed').textContent = data.stats.failed;
    document.getElementById('statDryRun').textContent = data.stats.dry_run;
    document.getElementById('statTotal').textContent = data.stats.total;

    // Progress
    const pct = data.stats.total > 0 ? (data.stats.progress / data.stats.total * 100) : 0;
    document.getElementById('progressBar').style.width = pct + '%';
    document.getElementById('progressBar').textContent = pct.toFixed(0) + '%';
    document.getElementById('progressText').textContent = `${data.stats.progress} / ${data.stats.total}`;
    document.getElementById('progressPct').textContent = pct.toFixed(1) + '%';

    // Pool
    if (data.pool) {
      document.getElementById('poolStatus').textContent =
        `${data.pool.alive} alive / ${data.pool.total} total`;
      const poolBar = document.getElementById('poolBar');
      poolBar.innerHTML = '';
      for (let i = 0; i < data.pool.total; i++) {
        const seg = document.createElement('div');
        seg.className = `pool-segment ${i < data.pool.alive ? 'pool-alive' : 'pool-dead'}`;
        poolBar.appendChild(seg);
      }
    }

    // Log
    const logEl = document.getElementById('logContainer');
    const wasAtBottom = logEl.scrollTop + logEl.clientHeight >= logEl.scrollHeight - 10;
    logEl.innerHTML = data.log.slice(-100).map(entry => {
      let cls = '';
      if (entry.includes('[SENT]')) cls = 'log-entry-sent';
      else if (entry.includes('[FAILED]')) cls = 'log-entry-failed';
      else if (entry.includes('[DRY_RUN]')) cls = 'log-entry-dry_run';
      else if (entry.includes('[ERROR]')) cls = 'log-entry-error';
      else if (entry.includes('[DONE]')) cls = 'log-entry-done';
      return `<div class="${cls}">${escapeHtml(entry)}</div>`;
    }).join('');
    if (wasAtBottom) logEl.scrollTop = logEl.scrollHeight;

    // Results table
    const tbody = document.getElementById('resultsBody');
    const latest = data.results.slice(-50);
    tbody.innerHTML = latest.map(r => `
      <tr>
        <td>${r.index}</td>
        <td><span class="badge badge-${r.status}">${r.status.toUpperCase()}</span></td>
        <td>${r.template}</td>
        <td>${r.target}</td>
        <td title="${escapeHtml(r.subject)}">${escapeHtml(r.subject.substring(0, 40))}...</td>
        <td>${r.duration}s</td>
      </tr>
    `).join('');

    // Stop polling if done
    if (!data.running) {
      document.getElementById('stopBtn').disabled = true;
      if (pollInterval && data.stats.progress > 0) {
        clearInterval(pollInterval);
        pollInterval = null;
      }
    }
  } catch (e) {
    console.error('Poll error:', e);
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ── Init ────────────────────────────────────────────────────
populateTemplates();
</script>

</body>
</html>
"""


# ═══════════════════════════════════════════════════════════════
#  FLASK ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route("/")
def index():
    templates_json = json.dumps([
        {"name": t.name, "category": t.category, "urgency": t.urgency_level}
        for t in TEMPLATES
    ])
    return render_template_string(HTML_TEMPLATE, templates_json=templates_json)


@app.route("/api/launch", methods=["POST"])
def launch():
    global campaign_state

    if campaign_state["running"]:
        return jsonify({"ok": False, "error": "Campaign already running"})

    config = request.get_json()
    reset_state()
    campaign_state["running"] = True
    campaign_state["stats"]["total"] = config.get("core", {}).get("send_count", 0)

    thread = threading.Thread(target=run_campaign, args=(config,), daemon=True)
    thread.start()

    return jsonify({"ok": True})


@app.route("/api/stop", methods=["POST"])
def stop():
    if campaign_state.get("engine"):
        campaign_state["engine"].stop()
    campaign_state["running"] = False
    return jsonify({"ok": True})


@app.route("/api/status")
def status():
    stats = campaign_state["stats"]
    pool = {}
    if campaign_state.get("engine"):
        try:
            pool = campaign_state["engine"].temp_manager.pool_status()
        except Exception:
            pass

    return jsonify({
        "running": campaign_state["running"],
        "stats": stats,
        "results": campaign_state["results"][-50:],
        "log": campaign_state["log"][-100:],
        "pool": pool,
    })


@app.route("/api/templates")
def templates_api():
    return jsonify([
        {"name": t.name, "category": t.category, "urgency": t.urgency_level,
         "subjects": len(t.subject_pool)}
        for t in TEMPLATES
    ])


@app.route("/api/preview/<template_name>")
def preview_template(template_name):
    target = request.args.get("target", "preview@example.com")
    renderer = MessageRenderer()
    from templates import get_template as gt
    tmpl = gt(name=template_name)
    subject, body_html, sender_email = renderer.render(tmpl, target)
    return jsonify({
        "template": tmpl.name,
        "category": tmpl.category,
        "subject": subject,
        "sender": sender_email,
        "body_html": body_html,
        "urgency": tmpl.urgency_level,
    })


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n♨ PHANTOM MAILER Web UI running at http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)

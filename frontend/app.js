/* ════════════════════════════════════════════════════════════════
   AI DEBUGGER — Application Logic (Premium Edition)
   API endpoints:
     POST /debug/session         → create SSE session
     GET  /debug/stream/:id      → SSE event stream
     POST /debug/?session_id=:id → run debug pipeline
     GET  /health/               → health check
     GET  /evaluation/summary    → eval metrics
   ════════════════════════════════════════════════════════════════ */

const API = (window.location.port === '8000' || window.location.port === '') ? '' : 'http://localhost:8000';

// ── DOM helpers ─────────────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const dom = {
  // Header
  statusDot:       $('.status-dot'),
  statusLabel:     $('.status-label'),

  // Input
  repoInput:       $('#repo-url'),
  bugInput:        $('#bug-desc'),
  btnStart:        $('#btn-start'),

  // Panels
  inputPanel:      $('#input-panel'),
  resultsPanel:    $('#results-container'),
  errorPanel:      $('#error-panel'),

  // Results header
  resultRepo:      $('#result-repo-url'),
  resultProblem:   $('#result-problem'),

  // Grid
  fileList:        $('#file-list'),
  diagPlaceholder: $('#diagnosis-placeholder'),
  diagContent:     $('#diagnosis-content'),
  diagText:        $('#diagnosis-text'),
  evidenceSection: $('#evidence-section'),
  evidenceList:    $('#evidence-list'),
  activityTimeline:$('#activity-timeline'),
  eventCount:      $('#event-count'),

  // Metrics
  metricsBar:      $('#metrics-bar'),
  mIterations:     $('#m-iterations'),
  mToolCalls:      $('#m-tool-calls'),
  mFiles:          $('#m-files'),
  mChunks:         $('#m-chunks'),
  mTokens:         $('#m-tokens'),
  mCost:           $('#m-cost'),

  // Terminal
  terminalLog:     $('#terminal-log'),
  terminalCount:   $('#terminal-count'),

  // Error
  errorMessage:    $('#error-message'),
  errorDetails:    $('#error-details'),

  // Actions
  btnReset:        $('#btn-reset'),
  btnRetry:        $('#btn-retry'),

  // Evaluation
  evalLoading:     $('#eval-loading'),
  evalContent:     $('#eval-content'),
  evalMeta:        $('#eval-meta'),
  evalTbody:       $('#eval-tbody'),
  evalNotes:       $('#eval-notes'),
  evalError:       $('#eval-error'),
};

// ── Particle Canvas ──────────────────────────────────────────────
(function initParticles() {
  const canvas = document.getElementById('particle-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let W, H, particles = [];

  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function randomParticle() {
    return {
      x: Math.random() * W,
      y: Math.random() * H,
      r: Math.random() * 1.5 + 0.3,
      dx: (Math.random() - 0.5) * 0.3,
      dy: -(Math.random() * 0.4 + 0.1),
      alpha: Math.random() * 0.5 + 0.1,
      color: Math.random() > 0.5 ? '124,58,237' : '6,182,212',
    };
  }

  function init() {
    resize();
    particles = Array.from({ length: 80 }, randomParticle);
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    for (const p of particles) {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${p.color},${p.alpha})`;
      ctx.fill();

      p.x += p.dx;
      p.y += p.dy;
      p.alpha -= 0.0008;

      if (p.y < -10 || p.alpha <= 0) {
        Object.assign(p, randomParticle(), { x: Math.random() * W, y: H + 10, alpha: 0.4 });
      }
    }
    requestAnimationFrame(draw);
  }

  window.addEventListener('resize', resize);
  init();
  draw();
})();

// ── Navigation ───────────────────────────────────────────────────
$$('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    $$('.nav-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    $$('.view').forEach(v => v.classList.remove('active-view'));
    $(`#view-${btn.dataset.view}`).classList.add('active-view');

    if (btn.dataset.view === 'evaluation') loadEvaluation();
  });
});

// ── Input Validation ─────────────────────────────────────────────
let isRunning = false;

function checkReady() {
  const repo = dom.repoInput.value.trim();
  const bug = dom.bugInput.value.trim();
  dom.btnStart.disabled = !repo || bug.length < 10 || isRunning;
}

dom.repoInput.addEventListener('input', checkReady);
dom.bugInput.addEventListener('input', checkReady);

// ── Health Check ─────────────────────────────────────────────────
async function checkHealth() {
  try {
    const r = await fetch(`${API}/health/`);
    if (r.ok) {
      dom.statusDot.classList.add('online');
      dom.statusDot.classList.remove('error');
      dom.statusLabel.textContent = 'System Ready';
    } else throw new Error('unhealthy');
  } catch {
    dom.statusDot.classList.remove('online');
    dom.statusDot.classList.add('error');
    dom.statusLabel.textContent = 'Offline';
  }
}
checkHealth();
setInterval(checkHealth, 30_000);

// ── Start Debug ──────────────────────────────────────────────────
dom.btnStart.addEventListener('click', startDebug);

let eventSource = null;
let eventLog = [];

async function startDebug() {
  if (isRunning) return;
  const repoUrl = dom.repoInput.value.trim();
  const bugDesc = dom.bugInput.value.trim();

  isRunning = true;
  eventLog = [];

  // UI transition
  dom.inputPanel.classList.add('hidden');
  dom.errorPanel.classList.add('hidden');
  dom.resultsPanel.classList.remove('hidden');

  dom.resultRepo.textContent = repoUrl;
  dom.resultProblem.textContent = `"${bugDesc}"`;

  resetResults();
  dom.btnStart.classList.add('loading');
  dom.btnStart.disabled = true;

  try {
    // 1. Create session
    const sessionRes = await fetch(`${API}/debug/session`, { method: 'POST' });
    if (!sessionRes.ok) throw new Error('Failed to create session');
    const { session_id } = await sessionRes.json();

    // 2. Open SSE
    connectSSE(session_id);

    // 3. Submit debug request
    const debugRes = await fetch(`${API}/debug/?session_id=${session_id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_url: repoUrl, bug_description: bugDesc }),
    });

    const data = await debugRes.json();
    if (!debugRes.ok) {
      showError(data.detail || 'Request failed', `HTTP ${debugRes.status}`);
      return;
    }

    renderResult(data);

  } catch (err) {
    showError(err.message || 'Could not connect to the server.', '');
  } finally {
    isRunning = false;
    dom.btnStart.classList.remove('loading');
    checkReady();
    closeSSE();
  }
}

// ── SSE ───────────────────────────────────────────────────────────
function connectSSE(sessionId) {
  closeSSE();
  eventSource = new EventSource(`${API}/debug/stream/${sessionId}`);

  eventSource.onmessage = (e) => {
    try {
      const evt = JSON.parse(e.data);
      handleEvent(evt);
    } catch { /* ignore malformed */ }
  };

  eventSource.onerror = () => { /* SSE auto-reconnects */ };
}

function closeSSE() {
  if (eventSource) { eventSource.close(); eventSource = null; }
}

// ── Event Handling ────────────────────────────────────────────────
const EVENT_LABELS = {
  debug_request_received: 'Request received',
  debug_service_start:    'Debug service started',
  cloning_repository:     'Cloning repository',
  clone_complete:         'Repository cloned',
  indexing_start:         'Indexing repository',
  indexing_chunks:        'Indexing chunks',
  indexing_complete:      'Indexing complete',
  agent_started:          'Agent started',
  llm_response:           'LLM response',
  token_usage:            'Token usage',
  tool_called:            'Tool called',
  tool_completed:         'Tool completed',
  tool_failed:            'Tool failed',
  agent_completed:        'Agent completed',
  clone_cleanup:          'Cleanup',
  debug_service_success:  'Diagnosis complete',
  debug_service_failed:   'Debug failed',
  debug_error:            'Error',
};

const EVENT_ICONS = {
  cloning_repository:    '📥',
  clone_complete:        '✅',
  indexing_start:        '🗂️',
  indexing_complete:     '✅',
  agent_started:         '🤖',
  tool_called:           '🔧',
  tool_completed:        '✅',
  debug_service_success: '🎉',
  debug_service_failed:  '❌',
  debug_error:           '⚠️',
  token_usage:           '📊',
};

function handleEvent(evt) {
  const label = EVENT_LABELS[evt.event] || evt.event;
  const icon = EVENT_ICONS[evt.event] || '▸';
  const ts = new Date(evt.timestamp * 1000);
  const timeStr = ts.toLocaleTimeString('en-US', { hour12: false });

  // Terminal log
  const termLine = document.createElement('div');
  termLine.className = 'terminal-line';
  termLine.innerHTML =
    `<span class="t-time">${timeStr}</span>` +
    `<span class="t-event">${evt.event}</span>` +
    (evt.message ? `<span class="t-detail">${escapeHtml(evt.message)}</span>` : '');
  dom.terminalLog.appendChild(termLine);
  dom.terminalLog.scrollTop = dom.terminalLog.scrollHeight;

  eventLog.push(evt);
  dom.terminalCount.textContent = `${eventLog.length} events`;

  // Timeline
  const isError    = evt.event.includes('failed') || evt.event.includes('error');
  const isComplete = evt.event.includes('complete') || evt.event.includes('success');

  if (!isError) {
    dom.activityTimeline.querySelectorAll('.timeline-event.active').forEach(el => {
      el.classList.remove('active');
      el.classList.add('completed');
    });
  }

  const node = document.createElement('div');
  const statusClass = isError ? 'error' : (isComplete ? 'completed' : 'active');
  node.className = `timeline-event ${statusClass}`;

  let detailText = '';
  if (evt.data) {
    if (evt.data.tool_name) detailText = evt.data.tool_name;
    if (evt.data.files_processed)
      detailText = `${evt.data.files_processed} files, ${evt.data.chunks_indexed} chunks`;
  }

  node.innerHTML = `
    <span class="timeline-dot"></span>
    <span class="timeline-line"></span>
    <span class="timeline-label">
      <span class="event-name">${icon} ${escapeHtml(label)}</span>
      ${detailText ? `<span class="event-detail">${escapeHtml(detailText)}</span>` : ''}
    </span>
  `;

  dom.activityTimeline.appendChild(node);
  dom.activityTimeline.scrollTop = dom.activityTimeline.scrollHeight;
  dom.eventCount.textContent = dom.activityTimeline.children.length;
}

// ── Render Final Result ───────────────────────────────────────────
function renderResult(data) {
  if (data.status === 'failed' && (!data.diagnosis || data.diagnosis.trim() === '')) {
    showError(data.diagnosis || 'No diagnosis produced.', `Repository: ${data.repository}`);
    return;
  }

  dom.diagPlaceholder.classList.add('hidden');
  dom.diagContent.classList.remove('hidden');

  // Render diagnosis with basic markdown styling
  dom.diagText.innerHTML = renderMarkdown(data.diagnosis || '—');

  // Evidence
  if (data.evidence && data.evidence.length > 0) {
    dom.evidenceSection.classList.remove('hidden');
    dom.evidenceList.innerHTML = '';
    data.evidence.forEach(ev => {
      const item = document.createElement('div');
      item.className = 'evidence-item';
      item.innerHTML = `
        <div class="evidence-header">
          <span>${escapeHtml(ev.file_path)}</span>
          <span>Lines ${ev.start_line}–${ev.end_line}</span>
        </div>
        <pre class="evidence-code">${escapeHtml(ev.code)}</pre>
      `;
      dom.evidenceList.appendChild(item);
    });
  }

  // Files
  if (data.files && data.files.length > 0) {
    dom.fileList.innerHTML = '';
    data.files.forEach(f => {
      const li = document.createElement('li');
      // Show only basename for cleanliness
      const parts = f.replace(/\\/g, '/').split('/');
      const basename = parts[parts.length - 1];
      li.title = f;
      li.textContent = basename;
      dom.fileList.appendChild(li);
    });
  }

  // Metrics
  if (data.metadata) {
    const m = data.metadata;
    dom.metricsBar.classList.remove('hidden');
    dom.mIterations.textContent  = m.iterations ?? '—';
    dom.mToolCalls.textContent   = m.tool_calls  ?? '—';
    dom.mFiles.textContent       = m.files_indexed ?? '—';
    dom.mChunks.textContent      = m.chunks_indexed ?? '—';
    dom.mTokens.textContent      = m.total_tokens?.toLocaleString() ?? '—';
    dom.mCost.textContent        = m.estimated_cost != null ? `$${m.estimated_cost.toFixed(4)}` : '—';
  }
}

// ── Basic Markdown → HTML ─────────────────────────────────────────
function renderMarkdown(text) {
  return escapeHtml(text)
    // **bold**
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // `inline code`
    .replace(/`([^`\n]+)`/g, '<code style="font-family:var(--f-mono);font-size:12px;background:rgba(124,58,237,0.12);padding:1px 5px;border-radius:4px;color:var(--text-accent)">$1</code>')
    // ```block``` (multiline)
    .replace(/```(?:\w+)?\n?([\s\S]*?)```/g, '<pre style="background:var(--bg-elevated);border:1px solid var(--border-subtle);border-radius:8px;padding:12px;margin:8px 0;font-family:var(--f-mono);font-size:12px;overflow-x:auto;color:var(--text-primary)">$1</pre>')
    // - bullet items
    .replace(/^- (.+)$/gm, '• $1')
    // Line breaks
    .replace(/\n/g, '<br>');
}

// ── Error State ───────────────────────────────────────────────────
function showError(message, details) {
  dom.resultsPanel.classList.add('hidden');
  dom.errorPanel.classList.remove('hidden');
  dom.errorMessage.textContent = message;
  if (details) {
    dom.errorDetails.textContent = details;
    dom.errorDetails.classList.remove('hidden');
  } else {
    dom.errorDetails.classList.add('hidden');
  }
}

// ── Reset ─────────────────────────────────────────────────────────
function resetToInput() {
  dom.resultsPanel.classList.add('hidden');
  dom.errorPanel.classList.add('hidden');
  dom.inputPanel.classList.remove('hidden');
  resetResults();
  checkReady();
}

function resetResults() {
  dom.diagPlaceholder.classList.remove('hidden');
  dom.diagContent.classList.add('hidden');
  dom.diagText.innerHTML = '';
  dom.evidenceSection.classList.add('hidden');
  dom.evidenceList.innerHTML = '';
  dom.fileList.innerHTML = '<li class="mono" style="color:var(--text-muted)">—</li>';
  dom.activityTimeline.innerHTML = '';
  dom.eventCount.textContent = '0';
  dom.metricsBar.classList.add('hidden');
  dom.terminalLog.innerHTML = '';
  dom.terminalCount.textContent = '0 events';
}

dom.btnReset.addEventListener('click', resetToInput);
dom.btnRetry.addEventListener('click', resetToInput);

// ── Evaluation ────────────────────────────────────────────────────
let evalLoaded = false;

async function loadEvaluation() {
  if (evalLoaded) return;
  try {
    const r = await fetch(`${API}/evaluation/summary`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();

    dom.evalMeta.textContent = `Dataset: ${data.dataset}  ·  Cases: ${data.total_cases}`;

    dom.evalTbody.innerHTML = '';
    data.metrics.forEach(m => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${escapeHtml(m.label)}</td>
        <td>${m.baseline != null ? m.baseline.toFixed(1) : '—'}</td>
        <td>${m.improved  != null ? m.improved.toFixed(1)  : '—'}</td>
        <td>${escapeHtml(m.unit)}</td>
      `;
      dom.evalTbody.appendChild(row);
    });

    if (data.notes && data.notes.length) {
      dom.evalNotes.innerHTML = data.notes.map(n => `<p>· ${escapeHtml(n)}</p>`).join('');
    }

    dom.evalLoading.classList.add('hidden');
    dom.evalContent.classList.remove('hidden');
    evalLoaded = true;

  } catch (err) {
    dom.evalLoading.classList.add('hidden');
    dom.evalError.classList.remove('hidden');
    dom.evalError.textContent = `Failed to load evaluation data: ${err.message}`;
  }
}

// ── Utilities ─────────────────────────────────────────────────────
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = String(str ?? '');
  return div.innerHTML;
}

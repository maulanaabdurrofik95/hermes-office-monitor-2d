/* ============================================================
   HERMES OFFICE MONITOR 2D — SCRIPT
   Canvas engine: draw rooms + pixel-chibi + live polling
   ============================================================ */

// ---- CONFIG ----
const POLL_MS = 2000;
const OFFICE_W = 800;
const OFFICE_H = 600;

const ROOMS = {
  lobby:      { title: 'Lobby',      x: 120, y: 80,  w: 560, h: 160, color: '#FFD700' },
  dev:        { title: 'Backend',    x: 40,  y: 280, w: 280, h: 280, color: '#4A90D9' },
  frontend:   { title: 'Frontend',   x: 480, y: 280, w: 280, h: 280, color: '#9B59B6' },
  security:   { title: 'Security',   x: 40,  y: 600-320, w: 280, h: 280, color: '#E74C3C' },
  design:     { title: 'Design',     x: 480, y: 600-320, w: 280, h: 280, color: '#F39C12' }
};

const CHARACTERS = {
  hermes:     { room: 'lobby',       px: 320, py: 140, color: '#FFD700', role: 'Orchestrator',  name: 'Hermes',    accessory: 'headset' },
  dev:        { room: 'dev',         px: 180, py: 420, color: '#4A90D9', role: 'Developer',     name: 'Dev',       accessory: 'laptop' },
  frontend:   { room: 'frontend',    px: 620, py: 420, color: '#9B59B6', role: 'Frontend Dev',  name: 'Frontend',  accessory: 'palette' },
  security:   { room: 'security',    px: 180, py: 620-200, color: '#E74C3C', role: 'Security',     name: 'Security',  accessory: 'shield' },
  design:     { room: 'design',      px: 620, py: 620-200, color: '#F39C12', role: 'UI/UX Designer', name: 'Design',   accessory: 'pencil' }
};

const STAGE_ICONS = {
  working: '🔧',
  revisi:  '⚠️',
  queue:   '⏳',
  idle:    '☕',
  done:    '✅'
};

const STATUS_LABELS = {
  working: 'BEKERJA',
  revisi:  'REVISI',
  queue:   'ANTRE',
  idle:    'IDLE',
  done:    'SELESAI'
};

let agentData = {};
let selectedChar = null;
let hoveredChar = null;

// ---- POLL ----
async function pollStatus() {
  try {
    const res = await fetch('/status.json');
    if (!res.ok) throw new Error(`status.json ${res.status}`);
    agentData = await res.json();
    updateFooter();
    render();
  } catch (e) {
    console.warn('[poll] gagal fetch status.json:', e.message);
  }
}

function updateFooter() {
  const now = new Date().toLocaleTimeString('id-ID');
  const el = document.getElementById('last-update');
  if (el) el.textContent = now;

  const online = Object.keys(agentData.characters || {}).filter(k =>
    agentData.characters[k] && agentData.characters[k].stage
  ).length || 0;
  const countEl = document.getElementById('online-count');
  if (countEl) countEl.textContent = `${online}/5 agent online`;
}

// ---- RENDER ----
const canvas = document.getElementById('office');
const ctx = canvas.getContext('2d');

function drawRoom(room) {
  ctx.fillStyle = room.color + '33';
  ctx.fillRect(room.x, room.y, room.w, room.h);
  ctx.strokeStyle = room.color;
  ctx.lineWidth = 2;
  ctx.strokeRect(room.x, room.y, room.w, room.h);
  ctx.fillStyle = room.color;
  ctx.font = 'bold 12px system-ui';
  ctx.textAlign = 'center';
  ctx.fillText(room.title, room.x + room.w / 2, room.y + 18);
}

function drawPixelChibi(x, y, color, stage, name) {
  const bob = Math.sin(Date.now() / 600) * 2;
  const cy = y + bob;

  // Body (small rectangle)
  ctx.fillStyle = color;
  ctx.fillRect(x - 10, cy, 20, 24);
  // Head (big circle)
  ctx.beginPath();
  ctx.arc(x, cy - 14, 12, 0, Math.PI * 2);
  ctx.fillStyle = color;
  ctx.fill();
  // Eyes (white dots)
  ctx.fillStyle = '#fff';
  ctx.beginPath();
  ctx.arc(x - 4, cy - 16, 2.5, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.arc(x + 4, cy - 16, 2.5, 0, Math.PI * 2);
  ctx.fill();
  // Pupil
  ctx.fillStyle = '#111';
  ctx.beginPath();
  ctx.arc(x - 3.5, cy - 15.5, 1, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.arc(x + 4.5, cy - 15.5, 1, 0, Math.PI * 2);
  ctx.fill();
  // Mouth
  ctx.fillStyle = '#111';
  ctx.beginPath();
  ctx.arc(x, cy - 10, 2, 0, Math.PI);
  ctx.fill();
  // Accessory hint (shape)
  ctx.fillStyle = '#fff';
  ctx.font = '9px system-ui';
  ctx.textAlign = 'center';
  ctx.fillText('🎧', x, cy - 24);

  // Stage icon above head
  const icon = STAGE_ICONS[stage] || '☕';
  ctx.font = '12px system-ui';
  ctx.fillText(icon, x, cy - 30);

  // Name
  ctx.fillStyle = '#fff';
  ctx.font = 'bold 10px system-ui';
  ctx.textAlign = 'center';
  ctx.fillText(name, x, cy + 34);
}

function getCharScreenPos(id) {
  const ch = CHARACTERS[id];
  if (!ch) return null;
  const room = ROOMS[ch.room];
  if (!room) return null;
  const scale = OFFICE_W / 800;
  return {
    sx: room.x + (ch.px - room.x) * scale * 0.01,
    sy: room.y + (ch.py - room.y) * scale * 0.01
  };
}

function render() {
  ctx.clearRect(0, 0, OFFICE_W, OFFICE_H);
  ctx.fillStyle = '#161b22';
  ctx.fillRect(0, 0, OFFICE_W, OFFICE_H);

  // Draw floor tiles
  ctx.fillStyle = '#1c2129';
  for (let tx = 0; tx < OFFICE_W; tx += 40) {
    for (let ty = 0; ty < OFFICE_H; ty += 40) {
      ctx.fillRect(tx, ty, 40, 40);
    }
  }

  // Draw rooms
  Object.values(ROOMS).forEach(r => drawRoom(r));

  // Draw characters
  const chars = agentData.characters || {};
  Object.keys(CHARACTERS).forEach(id => {
    const ch = CHARACTERS[id];
    const data = chars[id];
    const stage = data ? data.stage : 'idle';
    const px = ch.px;
    const py = ch.py;
    const pos = getCharScreenPos(id);
    if (!pos) return;
    drawPixelChibi(pos.sx, pos.sy, ch.color, stage, ch.name);

    // Highlight if hovered
    if (hoveredChar === id) {
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);
      ctx.strokeRect(pos.sx - 20, pos.sy - 38, 40, 56);
      ctx.setLineDash([]);
    }
  });
}

// ---- INTERACTION ----
canvas.addEventListener('click', (e) => {
  const rect = canvas.getBoundingClientRect();
  const scaleX = OFFICE_W / rect.width;
  const scaleY = OFFICE_H / rect.height;
  const mx = (e.clientX - rect.left) * scaleX;
  const my = (e.clientY - rect.top) * scaleY;

  let clickedId = null;
  Object.keys(CHARACTERS).forEach(id => {
    const ch = CHARACTERS[id];
    const pos = getCharScreenPos(id);
    if (!pos) return;
    const dx = mx - pos.sx;
    const dy = my - pos.sy;
    if (Math.abs(dx) < 15 && Math.abs(dy) < 30) {
      clickedId = id;
    }
  });

  if (clickedId) {
    selectedChar = clickedId;
    showPanel(clickedId);
  } else {
    selectedChar = null;
    hidePanel();
  }
});

canvas.addEventListener('mousemove', (e) => {
  const rect = canvas.getBoundingClientRect();
  const scaleX = OFFICE_W / rect.width;
  const scaleY = OFFICE_H / rect.height;
  const mx = (e.clientX - rect.left) * scaleX;
  const my = (e.clientY - rect.top) * scaleY;

  let found = null;
  Object.keys(CHARACTERS).forEach(id => {
    const ch = CHARACTERS[id];
    const pos = getCharScreenPos(id);
    if (!pos) return;
    const dx = mx - pos.sx;
    const dy = my - pos.sy;
    if (Math.abs(dx) < 15 && Math.abs(dy) < 30) {
      found = id;
    }
  });

  hoveredChar = found;
  canvas.style.cursor = found ? 'pointer' : 'crosshair';
});

// ---- PANEL ----
function showPanel(id) {
  const ch = CHARACTERS[id];
  const data = agentData.characters ? agentData.characters[id] : null;
  const stage = data ? data.stage : 'idle';
  const tasks = data && data.tasks ? data.tasks : [];
  const note = data ? data.note : '';
  const updatedAt = data ? data.updatedAt : '--';
  const role = ch ? ch.role : '';

  document.getElementById('panel-empty').classList.add('hidden');
  document.getElementById('panel-body').classList.remove('hidden');

  const nameEl = document.getElementById('panel-name');
  if (nameEl) nameEl.textContent = ch ? ch.name : id;
  const roleEl = document.getElementById('panel-role');
  if (roleEl) roleEl.textContent = role;
  const badgeEl = document.getElementById('panel-badge');
  if (badgeEl) {
    badgeEl.textContent = STATUS_LABELS[stage] || stage.toUpperCase();
    badgeEl.className = 'stage-badge ' + stage;
  }
  const roomEl = document.getElementById('panel-room');
  if (roomEl) {
    const roomTitle = ROOMS[ch.room] ? ROOMS[ch.room].title : ch.room;
    roomEl.innerHTML = `Room: <strong>${roomTitle}</strong>`;
  }

  const stageChips = document.getElementById('stage-chips');
  if (stageChips) {
    stageChips.innerHTML = Object.keys(STAGE_ICONS).map(s =>
      `<span class="stage-chip ${s === stage ? 'active' : ''}">${STAGE_ICONS[s]} ${s.toUpperCase()}</span>`
    ).join('');
  }

  const taskList = document.getElementById('task-list');
  if (taskList) {
    taskList.innerHTML = tasks.length
      ? tasks.map(t => `<li>${t}</li>`).join('')
      : '<li class="empty">Belum ada tugas</li>';
  }
  const countEl = document.getElementById('task-count');
  if (countEl) countEl.textContent = tasks.length ? `(${tasks.length})` : '(0)';

  const noteEl = document.getElementById('panel-note');
  if (noteEl) noteEl.textContent = note;

  const metaEl = document.getElementById('panel-meta');
  if (metaEl) metaEl.textContent = `Update: ${updatedAt}`;
}

function hidePanel() {
  document.getElementById('panel-empty').classList.remove('hidden');
  document.getElementById('panel-body').classList.add('hidden');
}

// ---- LOOP ----
function loop() {
  render();
}

// ---- INIT ----
function init() {
  pollStatus();
  setInterval(pollStatus, POLL_MS);
  loop();
  setInterval(loop, 50); // 20fps idle bobbing
}

init();

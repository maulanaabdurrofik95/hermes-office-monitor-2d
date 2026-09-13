/* ============================================================
   HERMES OFFICE MONITOR 2D — RENDER ENGINE (vanilla JS)
   - Canvas 2D rendering, pixel-chibi 48x48 characters
   - Stage status icon above head (🔧⚠️⏳⏳✅ / 😴 idle)
   - 4 room top-down + lobi tengah untuk Hermes
   - Live polling data/<agent>.json tiap 2s
   - Klik karakter → isi panel task
   - Hover → highlight room
   ============================================================ */
(() => {
  "use strict";

  const canvas = document.getElementById("office");
  const ctx = canvas.getContext("2d");
  const PANEL_EMPTY = document.getElementById("panel-empty");
  const PANEL_BODY = document.getElementById("panel-body");
  const LAST_UPDATE  = document.getElementById("last-update");
  const ONLINE_COUNT = document.getElementById("online-count");
  const LIVE_DOT  = document.querySelector(".live-dot");
  const LIVE_TEXT = document.getElementById("live-text");

  const POLL_MS = 2000;
  const AGENT_FILES = ["dev", "frontend", "security", "design", "hermes"];

  /* ---- helpers color ---- */
  function hexToRgb(c) {
    const n = parseInt(c.replace("#", ""), 16);
    return { r: (n >> 16) & 0xff, g: (n >> 8) & 0xff, b: n & 0xff };
  }
  function shade(c, amp) {
    const { r, g, b } = hexToRgb(c);
    const clamp = (v) => Math.max(0, Math.min(255, v | 0));
    return `rgb(${clamp(r + amp)},${clamp(g + amp)},${clamp(b + amp)})`;
  }

  /* ---- office layout ---- */
  // Canvas 800x600. Lobi (Hermes) di tengah, 4 room di pojok.
  const ROOMS = [
    { id: "dev-room",      title: "Backend Room",  color: "#4A90D9", x: 40,  y: 60,  w: 300, h: 220 },
    { id: "frontend-room", title: "Frontend Room", color: "#9B59B6", x: 458, y: 60,  w: 300, h: 220 },
    { id: "security-room", title: "Security Room", color: "#E74C3C", x: 40,  y: 358, w: 300, h: 220 },
    { id: "design-room",   title: "Design Room",   color: "#F39C12", x: 458, y: 358, w: 300, h: 220 },
  ];
  const LOBBY = { id: "lobby", title: "Hermes Lobby", color: "#FFD700", x: 336, y: 248, w: 128, h: 104 };

  // desk positions (center seat per room)
  const DESKS = {
    dev:      { x: 180, y: 200 },
    frontend: { x: 618, y: 200 },
    security: { x: 180, y: 490 },
    design:   { x: 618, y: 490 },
    hermes:   { x: 384, y: 296 }, // tengah lobi
  };

  /* ---- data state ---- */
  const state = { dev:{}, frontend:{}, security:{}, design:{}, hermes:{} };
  let lastOk  = {};
  let errMsg  = "";
  let hoverId = null;
  let selectId = null;
  let t0 = 0;

  /* ---- stage mapping ---- */
  const STAGE_ICON = {
    working: "🔧", revisi: "⚠️", queue: "⏳", idle: "😴", done: "✅",
    revisi2: "⚠️", antre: "⏳", selesai: "✅",
  };
  const STAGE_LABEL = {
    working:"working", revisi:"revisi", queue:"antre", idle:"idle", done:"selesai",
    antre:"antre", selesai:"selesai", revisi2:"revisi",
  };
  const STAGE_COLOR = {
    working: "#FFD93D", revisi: "#FF6B6B", queue: "#8BC3FF",
    idle: "#4CAF50", done: "#2ED573", antre: "#8BC3FF", selesai: "#2ED573", revisi2: "#FF6B6B",
  };
  function stageClass(stage) {
    const m = { working:"working", revisi:"revisi", revisi2:"revisi", queue:"queue", antre:"queue", idle:"idle", done:"done", selesai:"done" };
    return m[stage] || "idle";
  }

  /* ---- avatar builder ---- */
  const ROLE = {
    dev:"Backend Developer", frontend:"Frontend Developer",
    security:"Security Analyst", design:"UI/UX Designer", hermes:"Orchestrator",
  };
  const ACCESSORY = { dev:"laptop", frontend:"palette", security:"shield", design:"pencil", hermes:"monitor" };
  function roomOf(id) {
    return ["dev","frontend","security","design"].includes(id)
      ? ROOMS.find(r => r.title === {dev:"Backend Room",frontend:"Frontend Room",security:"Security Room",design:"Design Room"}[id])
      : LOBBY;
  }
  function avatar(id) {
    const d = state[id] || {};
    const room = roomOf(id);
    return {
      name:      d.agent || id.charAt(0).toUpperCase() + id.slice(1),
      color:     room.color,
      room:      room.title,
      accessory: ACCESSORY[id] || "monitor",
      stage:     d.stage || "idle",
      tasks:     d.tasks || [],
      note:      d.note || "",
      updatedAt: d.updatedAt || "",
      role:      ROLE[id] || id,
      idle:      d.stage === "idle",
    };
  }

  /* === PIXEL-CHIBI 48x48 (drawn via rect grid, pixel look) === */
  function drawChibi(g, cx, cy, scale, av) {
    const s = scale;
    const ox = cx - 24 * s;
    const oy = cy - 24 * s;
    const px = (x, y) => [ox + x * s, oy + y * s];
    const color = av.color;      // outfit
    const skin  = "#F5D4A5";
    const hair  = "#3e2723";
    g.save();
    g.lineJoin = "round";
    g.lineCap = "round";

    // bobbing untuk idle
    const bob = av.idle ? Math.sin(t0 / 500) * 1.6 : 0;
    g.translate(0, bob);

    // === HEAD (24..28 area) ===
    g.fillStyle = skin;
    // round head: 16x16-ish
    g.fillRect(...px(18,10), 8, 8);
    g.fillRect(...px(17,11), 10, 7);

    // hair overlap
    g.fillStyle = hair;
    g.fillRect(...px(17, 9), 10, 3);

    // eyes
    g.fillStyle = "#000";
    g.fillRect(...px(19,13), 1, 1);
    g.fillRect(...px(24,13), 1, 1);

    // mouth (smile bila idle, serius bila kerja)
    if (av.idle) {
      g.fillStyle = "#d32f2f";
      g.fillRect(...px(20,16), 4, 1);
    } else {
      g.fillRect(...px(19,16), 6, 1);
    }

    // === BODY (20..32) ===
    g.fillStyle = color;
    // badan utama
    g.fillRect(...px(15,20), 14, 10);
    // dagu / leher
    g.fillRect(...px(19,20), 6, 1);

    // === AKSESORIS (di tangan / meja) ===
    const acc = av.accessory;
    if (acc === "laptop") {
      g.fillStyle = "#2d2d2d";
      g.fillRect(...px(12,19), 4, 3);   // laptop kiri
      g.fillRect(...px(28,19), 4, 3);  // laptop kanan
      g.strokeStyle = "#fff"; g.lineWidth = Math.max(1,s*0.3);
      g.strokeRect(...px(12,19), 4, 3);
      g.strokeRect(...px(28,19), 4, 3);
    } else if (acc === "palette") {
      g.fillStyle = "#E74C3C"; g.fillRect(...px(16,18), 2, 2);
      g.fillStyle = "#3498db"; g.fillRect(...px(20,18), 2, 2);
      g.fillStyle = "#f1c40f"; g.fillRect(...px(25,18), 2, 2);
      g.fillStyle = "#2ecc71"; g.fillRect(...px(19,21), 2, 2);
      g.fillStyle = "#9b59b6"; g.fillRect(...px(23,21), 2, 2);
    } else if (acc === "shield") {
      g.fillStyle = "#ECF0F1";
      g.beginPath(); g.moveTo(...px(16,18)); g.lineTo(...px(28,18)); g.lineTo(...px(22,23)); g.closePath(); g.fill();
      g.fillStyle = color; g.fillRect(...px(20,16), 4, 2);  // top trim
    } else if (acc === "pencil") {
      g.fillStyle = "#8B4513";
      g.fillRect(...px(24,14), 1, 8);
      g.fillStyle = color;
      g.fillRect(...px(23,22), 3, 1);
    } else if (acc === "monitor") {
      g.fillStyle = "#1F2937";
      g.fillRect(...px(12,18), 16, 7);
      g.strokeStyle = "#fff"; g.lineWidth = Math.max(1,s*0.3);
      g.strokeRect(...px(12,18), 16, 7);
      g.fillStyle = "#374151";
      g.fillRect(...px(17, 0), 10, 2); // stand monitor
      g.fillRect(...px(19,-1), 2, 1);
    }

    // === LEGS (2 gambar) ===
    g.fillStyle = "#2C3E50";
    g.fillRect(...px(16,30), 2, 4);
    g.fillRect(...px(26,30), 2, 4);

    g.restore();
  }

  /* === STATUS ICON di atas kepala === */
  function drawStatusIcon(g, cx, cy, scale, stage) {
    const icon = STAGE_ICON[stage] || "❔";
    const r = 10 * scale + 2;
    const baseY = cy - 28 * scale; // di atas kepala
    g.save();
    g.font = `${Math.round(14 * scale)}px "Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji",serif`;
    g.textAlign = "center";
    g.textBaseline = "middle";
    // glow circle
    g.fillStyle = "rgba(17,20,24,0.94)";
    g.strokeStyle = STAGE_COLOR[stage] || "#fff";
    g.lineWidth = scale;
    g.beginPath(); g.arc(cx, baseY, r, 0, Math.PI * 2);
    g.fill(); g.stroke();
    g.fillText(icon, cx, baseY + scale * 0.5);
    g.restore();
  }

  /* === ROOM RENDER === */
  function drawRooms() {
    for (const room of [...ROOMS, LOBBY]) {
      const hl = hoverId && roomOf(hoverId) && roomOf(hoverId).id === room.id;
      ctx.fillStyle = hl ? shade(room.color, 46) : room.color;
      ctx.fillRect(room.x, room.y, room.w, room.h);
      ctx.strokeStyle = shade(room.color, -55);
      ctx.lineWidth = 2;
      ctx.strokeRect(room.x, room.y, room.w, room.h);
      if (room.id === "lobby") {
        ctx.setLineDash([4, 3]);
        ctx.strokeStyle = "rgba(255,255,255,0.25)";
        ctx.lineWidth = 1;
        ctx.strokeRect(room.x + 1, room.y + 1, room.w - 2, room.h - 2);
        ctx.setLineDash([]);
      }
      // title
      ctx.fillStyle = "#fff";
      ctx.font = "bold 12px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(room.title, room.x + room.w / 2, room.y + 16);
    }
  }

  /* === CHARACTERS RENDER === */
  function drawCharacters() {
    for (const id of AGENT_FILES) {
      const av  = avatar(id);
      const desk = DESKS[id];
      const scale = 1.6;
      drawChibi(ctx, desk.x, desk.y, scale, av);
      drawStatusIcon(ctx, desk.x, desk.y, scale, av.stage);
    }
  }

  /* === MAIN RENDER === */
  function render() {
    t0 = performance.now();
    ctx.fillStyle = "#0a0d12";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    drawRooms();
    drawCharacters();

    // hover label
    if (hoverId) {
      const av = avatar(hoverId);
      ctx.fillStyle = "rgba(255,255,255,0.9)";
      ctx.font = "bold 11px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(av.name, 400, 560);
      ctx.fillStyle = STAGE_COLOR[av.stage] || "#fff";
      ctx.font = "10px Inter, sans-serif";
      ctx.fillText(`Stage: ${STAGE_LABEL[av.stage] || av.stage}`, 400, 576);
    }
  }

  /* === PANEL === */
  function fillPanel(id) {
    const av = avatar(id);
    PANEL_BODY.classList.remove("hidden");
    PANEL_EMPTY.classList.add("hidden");

    document.getElementById("panel-name").textContent  = av.name;
    document.getElementById("panel-role").textContent  = av.role;
    const roomEl = document.getElementById("panel-room");
    roomEl.innerHTML = "";
    const strong = document.createElement("strong");
    strong.textContent = `Room: ${av.room}`;
    roomEl.appendChild(strong);
    document.getElementById("panel-note").textContent  = av.note || "—";
    document.getElementById("task-count").textContent  = `(${av.tasks.length})`;

    const badge = document.getElementById("panel-badge");
    badge.textContent = STAGE_LABEL[av.stage] || av.stage;
    badge.className = "stage-badge " + stageClass(av.stage);

    // task list grouped per stage (format blueprint)
    const list = document.getElementById("task-list");
    list.innerHTML = "";
    if (!av.tasks.length) {
      const li = document.createElement("li");
      li.className = "empty";
      li.textContent = "Tidak ada tugas — " + (av.stage === "idle" ? "santai aja dulu 🛌" : "belum ada tugas");
      list.appendChild(li);
    } else {
      av.tasks.forEach(t => {
        const li = document.createElement("li");
        li.textContent = `• ${t}`;
        list.appendChild(li);
      });
    }

    // stage chips
    const chips = document.getElementById("stage-chips");
    chips.innerHTML = "";
    ["working","revisi","queue","idle","done"].forEach(st => {
      const c = document.createElement("span");
      c.className = "stage-chip";
      const active = (STAGE_LABEL[av.stage] || av.stage) === STAGE_LABEL[st];
      if (active) c.classList.add("active");
      c.textContent = `${STAGE_ICON[st]} ${st}`;
      chips.appendChild(c);
    });
  }
  function resetPanel() {
    PANEL_BODY.classList.add("hidden");
    PANEL_EMPTY.classList.remove("hidden");
    selectId = null;
  }

  /* === POLLING === */
  async function pollAll() {
    const results = await Promise.all(AGENT_FILES.map(async (name) => {
      try {
        const res = await fetch(`data/${name}.json`, { cache: "no-store" });
        if (!res.ok) throw new Error(res.status);
        const json = await res.json();
        state[name] = json;
        lastOk[name] = Date.now();
        return { ok: true, name };
      } catch (e) {
        return { ok: false, name, err: e.message };
      }
    }));
    const failed = results.filter(r => !r.ok);
    errMsg = failed.length ? `${failed.map(r=>r.name).join(",")} ${failed[0].err}` : "";
    render();
    if (selectId) fillPanel(selectId);
    updateMeta();
  }

  function updateMeta() {
    const now = new Date();
    LAST_UPDATE.textContent = now.toLocaleTimeString("id-ID", { hour:"2-digit", minute:"2-digit", second:"2-digit" });
    const online = AGENT_FILES.filter(n => lastOk[n] && (Date.now() - lastOk[n]) < 10000).length;
    ONLINE_COUNT.textContent = `${online}/5`;
    if (errMsg) {
      LIVE_DOT.style.background = "var(--muted)";
      LIVE_TEXT.textContent = "OFFLINE";
    } else {
      LIVE_DOT.style.background = "var(--live)";
      LIVE_TEXT.textContent = "LIVE";
    }
  }

  /* === HIT TEST (scale-aware) === */
  function hitTest(mx, my) {
    for (const id of AGENT_FILES) {
      const desk = DESKS[id];
      if (Math.hypot(mx - desk.x, my - desk.y) < 32) return id;
    }
    return null;
  }
  function mouseToCanvas(e) {
    const rect = canvas.getBoundingClientRect();
    const sx = canvas.width / rect.width;
    const sy = canvas.height / rect.height;
    return {
      x: (e.clientX - rect.left) * sx,
      y: (e.clientY - rect.top)  * sy,
    };
  }

  canvas.addEventListener("mousemove", (e) => {
    const { x, y } = mouseToCanvas(e);
    hoverId = hitTest(x, y);
    render();
  });
  canvas.addEventListener("mouseleave", () => {
    hoverId = null;
    render();
  });
  canvas.addEventListener("click", (e) => {
    const { x, y } = mouseToCanvas(e);
    const hit = hitTest(x, y);
    if (hit) {
      selectId = hit;
      fillPanel(hit);
    }
  });

  /* === INIT === */
  render();
  pollAll();
  setInterval(pollAll, POLL_MS);
})();

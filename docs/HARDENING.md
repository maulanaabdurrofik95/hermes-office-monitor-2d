# 🔐 Hardening Guide — Per-Agent Status Push Mechanism

**Bagian dari security audit. Lihat `../security-report.md` untuk konteks.**

## 1. Bagaimana mekanisme push bekerja (saat ini)

```
Agent (Hermes/Dev/Frontend/Security/Design)
   │  1. tulis data/<agent>.json (stage, tasks, note, updatedAt)
   │  2. git add data/<agent>.json && git commit
   ▼
git push  ──(PAT token)──▶  GitHub repo (maulanaabdurrofik95/hermes-office-monitor-2d)
   │
   ▼
Vercel auto-deploy  ──▶  dashboard fetch data/<agent>.json  ──▶  render di browser
```

**Titik rapuh:** token yang dipakai `git push`. Kalau bocor → siapa pun bisa push apa pun ke repo → (a) Vercel auto-deploy konten jahat, (b) kalau `script.js` naif, itu jadi **stored XSS** untuk semua visitor.

Prinsip utama: **treat token sebagai credential production, bukan sebagai password sekali pakai.**

---

## 2. Aturan Scope Token (WAJIB)

| # | Aturan | Kenapa |
|---|--------|--------|
| 1 | **Finer-grained PAT**, scope hanya **`Contents: Read and write`** pada **1 repo** ini saja | Token hanya bisa push file, tidak bisa ubah branch protection, tidak bisa akses repo lain, tidak bisa baca secret |
| 2 | **JANGAN** pakai classic PAT scope `repo` penuh kalau bisa pakai fine-grained. Fine-grained bisa di-limit per-repo + per-permission | Minimal blast radius |
| 3 | **JANGAN** scope `admin:*`, `workflow`, `actions:write` (kecuali memang perlu CI) | Scope berlebihan = risiko tidak perlu |
| 4 | **1 token per agent** (5 token: hermes, dev, frontend, security, design) | Isolation — 1 token bocor ≠ semua agent bocor |
| 5 | **Expiration**: set expiry **≤ 90 hari** (ideally 30) | Token bocor punya umur terbatas |

### Fine-grained PAT config (rekomendasi)

```
Repository access: Only select repositories → hermes-office-monitor-2d
Permissions:
  - Contents: Read and write        ✅ (butuh ini untuk git push)
  - Metadata: Read-only             ✅ (otomatis, tidak bisa di-disable)
  - Semua permission lain: Access not selected  ❌
Expiration: 30 days
```

> Kalau harus pakai **classic PAT** (misal karena tooling), scope minimum = `repo` saja. Tapi tetap: 1 token/agent + expiry + rotation.

---

## 3. Penyimpanan Token (JANGAN salah tempat)

| Lokasi | Aman? | Catatan |
|--------|-------|---------|
| Env var di mesin agent (`HERMES_GIT_TOKEN`, `DEV_GIT_TOKEN`, ...) | ✅ | Jangan pernah `echo` / log |
| GitHub Actions **secrets** (kalau push via CI) | ✅ | Paling aman kalau push lewat Actions |
| File `.env` di repo | ❌ | `.gitignore` hanya membantu kalau belum pernah di-commit |
| Hardcode di `script.js` / `index.html` | ❌ **LARANG** | Client-side = terbaca semua visitor |
| File config di luar repo yang world-readable | ⚠️ | Set permission 600 (unix) / ACL (windows) |
| Git history / commit message | ❌ | Sekali masuk git = permanen (lihat §6) |

**Aturan emas:** token **hanya** hidup di **memory proses agent** saat push. Tidak ada file, tidak ada log, tidak ada console.

```bash
# ✅ Contoh push yang benar (token dari env, tidak di-echo)
git -c user.name="hermes-agent" -c user.email="hermes@local" \
    -c http.extraHeader="Authorization: Bearer ${HERMES_GIT_TOKEN}" \
    push origin master

# atau remote dengan token di URL (lebih rentan bocor di log/ps) — hindari:
# git push https://<token>@github.com/...   ❌ token muncul di `ps`/history
```

> Hindari `https://<token>@github.com/...` di remote URL — token muncul di `ps aux`, `.git/config`, dan shell history. Pakai `http.extraHeader` atau credential helper.

---

## 4. Token Rotation

| Aspek | Rekomendasi |
|-------|-------------|
| **Jadwal** | Rotasi **setiap 30 hari** (maks 90). Buat script/cron yang reminder. |
| **Cara rotasi** | Buat token baru → test push 1x → **revoke token lama** (GitHub → Settings → Tokens). Jangan biarkan 2 token hidup lama. |
| **Rotation on suspect** | Kalau ada indikasi bocor (commit misterius, akses tak dikenal): **revoke instan**, audit log repo, rotasi. |
| **Dokumentasi** | Catat di tabel: token siapa, dibuat kapan, expiry kapan, revoked kapan. (Jangan catat NILAI token, hanya label + tanggal.) |

Contoh tracking (di luar repo, misal di password manager / notes pribadi):

| Agent | Token label | Dibu | Expiry | Rotasi terakhir | Status |
|-------|-------------|------|--------|-----------------|--------|
| hermes | `hermes-github-2026-09` | 13 Sep 2026 | 13 Okt 2026 | — | aktif |
| dev | `dev-github-2026-09` | 13 Sep 2026 | 13 Okt 2026 | — | aktif |
| ... | | | | | |

---

## 5. Hardening Mekanisme Push (selain token)

### 5.1 Branch Protection (GitHub Settings → Branches)

- Proteksi `master`:
  - ✅ **Require pull request before merging** (kalau volume push kecil) ATAU
  - ✅ **Require status checks** (biar push lewat CI yang validasi JSON)
  - ✅ **Do not allow force pushes**
  - ✅ **Do not allow deletions**
- **Restrict who can push:** kalau bisa, batasi push hanya dari **GitHub Actions** (machine user), bukan dari token langsung. Ini lapisan terkuat.

### 5.2 Validasi JSON sebelum push (CI gate)

Tambahkan **GitHub Action** yang validate `data/*.json` sebelum merge/deploy:

```yaml
# .github/workflows/validate-json.yml
name: Validate agent data
on:
  push:
    paths: ['data/*.json']
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          for f in data/*.json; do
            python3 -c "import json,sys; json.load(open('$f')); print('$f OK')" \
              || { echo "::error::$f invalid JSON"; exit 1; }
          done
```

Bonus: validasi **schema** (field `agent`, `stage`, `tasks`, `updatedAt` harus ada; `stage` harus salah satu dari `idle|working|error`). Ini cegah agent yang buggy push data yang bikin dashboard error.

### 5.3 Rate limit / lockstep

- Tiap agent hanya push file-nya sendiri: `data/hermes.json` hanya boleh di-ubah agent hermes.
- Deteksi anomali: kalau agent `dev` push ke `data/hermes.json` → suspect → alert. (Bisa via Code Scanning / custom check di Actions yang membandingkan `git diff --name-only` dengan identitas pusher.)

### 5.4 Alternatif: GitHub API (Contents endpoint)

Kalau tidak mau `git push`, agent bisa update file via API:

```
PUT /repos/{owner}/{repo}/contents/data/{agent}.json
Authorization: Bearer <fine-grained-token>   (permission: Contents: R/W)
Content-Type: application/vnd.github+json
{ "message": "hermes: status working", "content": "<base64 json>", "sha": "<current-sha>" }
```

- Pro: tidak perlu clone repo, tidak perlu git identity, log commit jelas.
- Kon: 1 request = 1 deploy trigger (sama dengan push). Rate limit: 5.000 req/hr per token (cukup).
- **Token sama rule-nya**: fine-grained, Contents-only, 1/agent, expiry, rotation.

### 5.5 Alternatif paling aman: push via Vercel API

Daripada push ke Git → Vercel, agent bisa deploy file langsung via **Vercel API** (serverless function / service account):

```
POST /v1/deployments  (Vercel API, service token)
```

- Pro: tidak ada repo intermediate, tidak ada git token di sisi agent.
- Kon: perlu Vercel service token (juga credential — sama perlakuannya), lebih kompleks.
- **Rekomendasi untuk v1:** Git + fine-grained PAT sudah cukup. Pindah ke Vercel API hanya kalau butuh lebih tinggi.

---

## 6. Incident Response (kalau token bocor)

1. **Revoke token** di GitHub (Settings → Developer settings → Tokens). Instan.
2. **Audit**: GitHub → repo → **Insights / commit history** — cari commit yang bukan dari agent yang legitimate.
3. **Cek `git log`** untuk commit yang mengubah file di luar scope agent.
4. **Purge dari cache** (kalau perlu) — Vercel auto-deploy akan push ulang commit terakhir, jadi kalau ada commit jahat, **revert** commit-nya (bukan force-push, agar tetap ada jejak).
5. **Rotasi** token pengganti (jangan reuse token lama).
6. **Post-mortem**: bagaimana token bocor? Perbaiki celahnya.

> ⚠️ **Token yang pernah di-commit, tidak bisa di-uncommit.** `git filter-branch` / BFG tidak menghapus dari semua clone/fork. Satu-satunya solusi = **revoke + token baru**.

---

## 7. Checklist Implementasi

- [ ] Buat 5 fine-grained PAT (1 per agent), scope `Contents: R/W` pada repo ini saja
- [ ] Set expiry ≤ 30 hari di tiap token
- [ ] Simpan token di env var / secret manager (bukan file, bukan log)
- [ ] Aktifkan branch protection (no force-push, no delete, require checks)
- [ ] Tambah GitHub Action `validate-json.yml` (validasi JSON + schema)
- [ ] Buat tracking table rotasi token (label + tanggal, tanpa nilai token)
- [ ] Buat cron/reminder rotasi tiap 30 hari
- [ ] Tulis runbook incident response (§6) di tempat yang mudah dicari
- [ ] **Jangan pernah** commit token / jangan pernah log token
- [ ] Pertimbangkan repo **private** (kalau belum)

---

## 8. Ringkasan Prinsip

1. **Least privilege** — token cuma bisa yang benar-benar perlu (Contents: R/W, 1 repo).
2. **Isolation** — 1 token per agent. Bocor 1 ≠ bocor semua.
3. **Expiry** — token punya umur. 30 hari.
4. **Rotation** — rutin (30 hari) + on-suspect (instan).
5. **No secrets in repo** — token tidak pernah masuk git, log, atau file ter-commit.
6. **Defense in depth** — branch protection + CI validation + code review, walau token sudah aman.
7. **Assume breach** — ada runbook. Kalau bocor, tahu persis harus lakukan apa dalam 5 menit.

---

*Hardening guide oleh Security Analyst agent. Bagian dari security audit Hermes Office Monitor 2D.*

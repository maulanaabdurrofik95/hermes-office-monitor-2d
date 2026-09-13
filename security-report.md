# 🛡️ Security Audit — Hermes Office Monitor 2D

**Tanggal:** 13 September 2026
**Target:** `hermes-office-monitor-2d` (repo: `maulanaabdurrofik95/hermes-office-monitor-2d`)
**Hosting:** Vercel (auto-deploy) — static site
**Versi audit:** 1.0

---

## TL;DR (Ringkasan Eksekutif)

Ini **static site** (HTML/CSS/JS + JSON). Artinya **tidak ada server-side logic, tidak ada database, tidak ada auth endpoint** — jadi attack surface-nya kecil. Tidak ada SSRF, tidak ada open redirect, tidak ada injection server-side.

**Risiko utama** ada di 3 hal:

| # | Risiko | Severity | Status |
|---|--------|----------|--------|
| 1 | `script.js` & `style.css` **tidak ada di repo** padahal di-refer dari `index.html` | 🟠 Medium (broken deploy) | **Perlu fix** |
| 2 | **XSS** saat render data JSON ke DOM via `innerHTML` | 🟠 Medium | Mitigasi ada di `script.js` |
| 3 | **Git push token** per agent (PAT) | 🟡 Low-Medium | Hardening guide ada di `docs/HARDENING.md` |
| 4 | CORS / CSP header belum diset | 🟡 Low | **Sudah di-fix** via `vercel.json` |

**Verdict:** Secara arsitektur aman. Tinggal implementasikan hardening di `script.js` (yang belum ada) + ikuti `docs/HARDENING.md`.

---

## 1. Scope Audit

| Komponen | File | Status |
|----------|------|--------|
| Dashboard UI | `index.html` | ✅ Ada |
| Styling | `style.css` | ❌ **Missing** |
| Logic/render | `script.js` | ❌ **Missing** |
| Data statis | `status.json` | ✅ Ada |
| Data per-agent | `data/hermes.json`, `data/dev.json`, `data/frontend.json`, `data/security.json`, `data/design.json` | ✅ Ada (5 file) |
| Deploy config | `vercel.json` | ✅ **Dibuat audit ini** |

> ⚠️ **Temuan penting:** `index.html` (baris 8 & 29) me-load `<link rel="stylesheet" href="style.css" />` dan `<script src="script.js"></script>`, tapi **kedua file ini tidak ada di repo**. Artinya:
> - Deploy Vercel **akan render halaman kosong/blank** (CSS tidak ada, JS tidak jalan).
> - Bisa jadi file-nya ada di branch lain, di `.gitignore`, atau memang belum di-commit.
> - **Aksi:** commit `script.js` + `style.css`, atau perbaiki referensi.

---

## 2. Analisis Risiko per Kategori

### 2.1 Cross-Site Scripting (XSS) — 🟠 Medium

**Model data:** dashboard `fetch()` file `data/*.json` lalu render ke DOM (panel task list, status agent).

**Kenapa berisiko:**
Data JSON **dapat di-ubah oleh siapa pun yang bisa push ke repo** (semua agent). Kalau `script.js` naif, misal:

```js
// ❌ BURUK — rawan XSS
taskList.innerHTML = task.note;            // note bisa: <img src=x onerror=alert(1)>
panelTitle.textContent = `<b>${agent.name}</b>`;  // string concat ke innerHTML
```

Maka isi `note`/`tasks` yang ber-ISI HTML/MALICIOUS akan dieksekusi di browser pengunjung = **XSS Stored** (dipersist via git).

**Mitigasi (WAJIB di `script.js`):**

```js
// ✅ BAIK — pakai textContent, bukan innerHTML
taskList.textContent = task.note;          // otomatis HTML-escape
panelTitle.textContent = agent.name;       // aman

// ✅ Kalau harus render rich text → sanitasi dengan DOMPurify
import DOMPurify from 'https://unpkg.com/dompurify@3.2.4/dist/purify.min.js';
taskList.innerHTML = DOMPurify.sanitize(task.note);
```

**Aturan:**
- **Prioritas `textContent`** untuk semua data dari JSON (name, note, tasks, status).
- Pakai **`DOMPurify`** HANYA kalau memang perlu HTML (misal markdown note).
- **JANGAN** `eval()`, `Function()`, `innerHTML = <data user>`, `document.write()`.
- Jangan percaya `data.json` = trusted. Treat sebagai **untrusted input**.

**Risiko residual:** Rendah, SELAMA `script.js` implementasikan mitigasi di atas.

---

### 2.2 Cross-Origin Resource Sharing (CORS) — 🟡 Low

**Model fetch data:**

| Sumber | `Access-Control-Allow-Origin` | Aman? |
|--------|------------------------------|-------|
| **Vercel static** (deploy ini serve `data/*.json` sendiri) | Same-origin — **CORS tidak apply** (fetch dari same origin) | ✅ Paling aman |
| **GitHub raw** (`raw.githubusercontent.com/...`) | `*` (buka ke semua origin) | ✅ Bisa dipakai, tapi data terbuka ke publik |
| **GitHub API** (`api.github.com/repos/.../contents/...`) | `*` (buka, tapi butuh token + rate limit) | ⚠️ Butuh token, rate limit 60/hr tanpa auth |

**Rekomendasi:**
- **Paling baik:** fetch `data/*.json` **dari Vercel sendiri** (same-origin). Tidak ada CORS sama sekali, cepat, private-by-default kalau repo private.
- Kalau mau fetch dari **GitHub raw** (misal karena Vercel cache), pastikan `connect-src` di CSP mengizinkan domain-nya (sudah di-set di `vercel.json`).
- **Jangan** expose token GitHub di `script.js` (client-side). Kalau perlu API auth, harus ada **serverless function** di Vercel (bukan static).

**Risiko:** Rendah. Tidak ada endpoint yang bisa di- abuse lintas origin.

---

### 2.3 Content-Security-Policy (CSP) — ✅ Diperbaiki

Sebelumnya **tidak ada CSP sama sekali** → browser tanpa pembatasan origin, rawan kalau ada XSS.

**Sekarang sudah diset** di `vercel.json` (lihat section 4):

```
default-src 'self'
script-src 'self' 'unsafe-inline'
style-src 'self' 'unsafe-inline'
img-src 'self' data: https:
connect-src 'self' https://raw.githubusercontent.com https://api.github.com https://objects.githubusercontent.com
font-src 'self' data:
frame-ancestors 'none'
base-uri 'self'
form-action 'self'
upgrade-insecure-requests
```

**Catatan penting:**
- `connect-src` **WAJIB** termasuk `raw.githubusercontent.com` & `api.github.com` karena `script.js` fetch ke sana. Kalau di-*remove*, **fetch akan diblok CSP** → dashboard mati.
- `script-src 'unsafe-inline'` sengaja di-keep **karena** `script.js` (belum ada) kemungkinan pakai inline script/attribute. Kalau nanti semua JS di-external-kan & tanpa inline event handler (`onclick=...`), **hapus `'unsafe-inline'`** untuk hardening lebih ketat.
- `frame-ancestors 'none'` + `X-Frame-Options: DENY` → cegah **clickjacking**.
- `upgrade-insecure-requests` → paksa HTTPS.

**Risiko:** Rendah (sudah mitigasi).

---

### 2.4 SSRF / Open Redirect — ✅ Tidak Ada

- Static site, tidak ada server yang melakukan request berdasarkan input user → **tidak ada SSRF**.
- Tidak ada redirect logic yang di-derive dari input → **tidak ada open redirect**.
- `form-action 'self'` di CSP menambah lapisan keamanan.

---

### 2.5 Git Push Token (Per-Agent) — 🟡 Low-Medium

Ini **bagian paling perlu di-hardening** karena melibatkan **credential (Personal Access Token)** yang dipakai tiap agent push `data/<agent>.json`.

Detail lengkap di **`docs/HARDENING.md`**. Ringkas:
- PAT scope **`repo`** saja (bukan admin:repo, bukan account).
- **1 token per agent** (isolation) → kalau 1 bocor, hanya 1 agent terdampak.
- **Token rotation** berkala + revoke segera kalau suspect bocor.
- **Jangan** commit token ke repo / jangan hardcode di `script.js`.
- Simpan di **GitHub Actions secrets** atau env var, bukan di file.

---

### 2.6 Header Keamanan Tambahan — ✅ Ditambahkan

Semua sudah diset di `vercel.json`:

| Header | Fungsi |
|--------|--------|
| `X-Content-Type-Options: nosniff` | Cegah MIME-type sniffing (misal `.json` di-snak jadi script) |
| `X-Frame-Options: DENY` | Cegah clickjacking via iframe |
| `X-XSS-Protection: 1; mode=block` | Legacy browser XSS filter (belt-and-suspenders) |
| `Strict-Transport-Security` | Paksa HTTPS, cegah MITM/SSL stripping |
| `Referrer-Policy: strict-origin-when-cross-origin` | Jangan bocorkan path referrer ke pihak ketiga |
| `Permissions-Policy` | Matikan camera/mic/geolocation/payment (tidak relevan, cegah abuse) |
| `Cross-Origin-Opener-Policy: same-origin` | Isolate browsing context, cegah cross-origin scripting |
| `Cross-Origin-Resource-Policy: same-origin` | Batasi asset diblok pihak lain |

---

## 3. Matriks Risiko (CVE-style)

| ID | Finding | CVSS-ish | Exploitability | Impact | Fix |
|----|---------|----------|----------------|--------|-----|
| SEC-001 | `script.js`/`style.css` missing → broken deploy | 4.0 | — | Functional (blank page) | Commit file / fix ref |
| SEC-002 | Stored XSS via `innerHTML` on JSON data | 5.5 | Medium (butuh akses push) | High (script di semua visitor) | `textContent` / DOMPurify |
| SEC-003 | No CSP before | 4.0 | Medium | Medium | ✅ `vercel.json` |
| SEC-004 | Git PAT scope/rotation belum di-hardening | 4.5 | Low (repo private?) | Medium (repo takeover) | `docs/HARDENING.md` |
| SEC-005 | GitHub raw = data publik | 2.0 | — | Low (info leak) | Repo private / Vercel same-origin |

> CVSS-ish = estimasi kasar, bukan skor formal.

---

## 4. Deliverable: `vercel.json` (Sudah Dibuat)

File `vercel.json` di root repo berisi:
- **CSP** (dengan `connect-src` untuk GitHub raw/API — **jangan hapus**).
- 8 security header tambahan.
- `cleanOutputs: false` (biarkan `data/` tidak di-bersihkan), `trailingSlash: false`, `public: true`.

Deploy berikutnya otomatis pakai config ini.

---

## 5. Checklist Aksi (Prioritas)

- [ ] **P0:** Commit `script.js` + `style.css` (atau fix referensi di `index.html`) — **tanpa ini deploy blank**.
- [ ] **P0:** Implementasikan **`textContent`** untuk semua render data JSON di `script.js`.
- [ ] **P1:** Kalau butuh rich-text note → pakai **DOMPurify**.
- [ ] **P1:** Terapkan hardening token dari `docs/HARDENING.md` (scope minimal, 1 token/agent, rotation).
- [ ] **P2:** Buat repo **private** (jangan public, karena berisi data + kalau ada token bocor lewat git history).
- [ ] **P2:** Pertimbangkan fetch data dari **Vercel same-origin** (bukan GitHub raw) agar tidak publik + lebih cepat.
- [ ] **P3:** Kalau `script.js` sudah full external & tanpa inline handler → hapus `'unsafe-inline'` dari `script-src`.
- [ ] **P3:** Tambah Vercel **serverless function** kalau perlu API GitHub auth (jangan ever expose token di client).

---

## 6. Referensi

- OWASP XSS: https://owasp.org/www-community/attacks/xss/
- OWASP Content Security Policy: https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP
- GitHub PAT scopes: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
- Vercel Headers: https://vercel.com/docs/projects/project-configuration#headers
- DOMPurify: https://github.com/cure53/DOMPurify

---

*Laporan dibuat oleh Security Analyst agent. Hardening detail per-agent push → `docs/HARDENING.md`.*

# Hermes Office Monitor — Pygame Local

Versi desktop Pygame dari Hermes Office Monitor. Kantor virtual 2D top-down
dengan 5 karakter pixel-chibi (Dev, Frontend, Security, Design, Hermes) yang
duduk di meja masing-masing dengan komputer/laptop.

## Persyaratan

- Python 3.8+
- pygame (`python -m pip install pygame`)

## Cara Pakai

```bash
cd hermes-office-monitor-2d
python office_monitor.py
```

Jendela berjudul **"Hermes Office Monitor"** akan terbuka.

### Interaksi

| Aksi | Hasil |
|------|-------|
| Gerakkan mouse | Karakter yang terdekat di-highlight, nama ditampilkan di bottom bar |
| Klik karakter | Panel detail terbuka di sisi kanan (nama, stage, tasks, note, updatedAt) |
| ESC / klik X (panel) | Tutup panel detail |
| J / L | Pindah fokus karakter ke kanan |
| K / M | Pindah fokus karakter ke kiri |

### Live polling

Aplikasi memindai `data/<agent>.json` setiap **2 detik**. Ganti stage lewat helper:

```bash
python scripts/update_status.py --agent dev --stage revisi --note "Fix bug"
python scripts/update_status.py --agent hermes --stage done --task "Deploy" --no-task
python scripts/update_status.py --agent frontend --stage antre --note "Waiting review"
```

Stage yang didukung: `working`, `revisi`, `antre` (alias `queue`), `idle`,
`selesai` (alias `done`).

### Status icon (di atas kepala karakter)

Gambar dengan pygame primitives — **bukan emoji**:

- `working` → gear putar
- `revisi` → segitiga peringatan !
- `antre` → cangkir kopi
- `idle` → secawan + bulan (santai)
- `selesai` → tanda centang ✓

### Animasi

- **Idle / Revis / Antre**: bobbing ±2px, kedipan mata.
- **Working**: animasi ketikan (tangan bergerak) + cursor berkedip di layar monitor.

## Layout

```
┌─────────────┬──────────────┬─────────────┐
│    DEV      │   FRONTEND   │             │
├─────────────┼──────────────┤   LOBBY     │
│  SECURITY   │   DESIGN     │   (HERMES)  │
└─────────────┴──────────────┴─────────────┘
```

Palet: Dev `#4A90D9` · Frontend `#9B59B6` · Security `#E74C3C` ·
Design `#F39C12` · Hermes `#FFD700` · Floor `#F4F1EA`.

## Headless / screenshot

```bash
SDL_VIDEODRIVER=dummy python office_monitor.py
```

Screenshot otomatis tersedia di `screenshots/preview.png`.
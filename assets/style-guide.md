# Hermes Office Monitor 2D — Style Guide

## 1. Palet Warna per Agent

| Agent | Domain Warna | Room Warna | Hex |
|-------|-------------|------------|-----|
| Dev | Tech biru | Backend Room | `#4A90D9` |
| Frontend | Ungu | Frontend Room | `#9B59B6` |
| Security | Merah | Security Room | `#E74C3C` |
| Design | Orange | Design Room | `#F39C12` |
| Hermes (lobi) | Emas/kuning | Central Lobby | `#FFD700` |

**Floor tile:** off-white `#F4F1EA`, grid polos `#E0D6C2`.

## 2. Sprite Karakter (48×48 px)

Format: pixel chibi, 2-frame idle (bob +2px vertikal).

### Accessor tiap domain:
- **Dev:** laptop kecil + headphones
- **Frontend:** palet warna + kuas
- **Security:** shield/badge + kacamata detektif
- **Design:** pensil + ruler
- **Hermes:** headset + tablet

### Idle animation:
- Frame 0: posisi normal (y offset = 0)
- Frame 1: y offset = +2px (bob up — gambar shift -2px agar kelihatan naik)
- Loop: 800ms per frame, infinite

### Pose idle:
- Duduk, lengan santai (diposisikan di samping tubuh, tidak menempel)

### File naming convention:
```
assets/sprites/{agent}-idle-{frame}.svg
```

| Agent | Frame 0 | Frame 1 |
|-------|---------|---------|
| Dev | `dev-idle-0.svg` | `dev-idle-1.svg` |
| Frontend | `frontend-idle-0.svg` | `frontend-idle-1.svg` |
| Security | `security-idle-0.svg` | `security-idle-1.svg` |
| Design | `design-idle-0.svg` | `design-idle-1.svg` |
| Hermes | `hermes-idle-0.svg` | `hermes-idle-1.svg` |

## 3. Status Icon (16×16 px, di atas kepala)

| Status | Ikon | File |
|--------|------|------|
| Working | Gear 🔧 | `status-working.svg` |
| Revisi | Exclamation ⚠️ | `status-revisi.svg` |
| Antre | Coffee cup + clock ⏳ | `status-antre.svg` |
| Selesai | Checkmark ✅ | `status-selesai.svg` |

**Posisi:** center at `head-center - (0, 4px)` — ikon muncul 4px di atas ujung rambut.

## 4. Room Layout (top-down canvas 800×600)

```
+-----------+ (0,0)           +------------------+ (800,0)
| Dev Room  |                 | Frontend Room    |
| 100,100   | door: (150,90)  | 600,100          | door: (650,90)
|           |                 |                  |
+-----------+  Lobi (tengah)  +------------------+
|           |  375,250        |                  |
| Lobi      |                 |                  |
| Desk      |  monitor wall   |                  |
| x:200,y:250|  (350,230)    |                  |
+-----------+  +-------------+  +------------------+
| Security  |                 | Design Room      |
| Room      |                 |                  |
| 100,400   | door: (150,390) | 600,400          | door: (650,390)
+-----------+                 +------------------+
```

### Room dimensions:
- **Dev:** 150×150 (100,100) wall biru `#4A90D9`
- **Frontend:** 150×150 (600,100) wall ungu `#9B59B6`
- **Security:** 150×150 (100,400) wall merah `#E74C3C`
- **Design:** 150×150 (600,400) wall orange `#F39C12`
- **Lobi:** center lobby, rect (200,150) to (600,450), floor `#F4F1EA`

### Furniture per room:
- **Door:** 8×4px, warna hitam (`#2C3E50`), posisi at top wall of each room
- **Meja:** 40×20px, brow kafe `#8B4513`
- **Kursi:** 6×6px, warna abu `#666666`
- **Wallpaper:** colored wall band (10px strip along top edge of room)

### Lobi furniture:
- **Meja panjang:** 200×30px, brow kafe `#8B4513`, center at (275,265)
- **Monitor besar di dinding:** 120×60px, gradien biru `#3498DB` → `#2980B9`, posisi wall (350,240)

## 5. Asset Source

- Semua aset generate via SVG (open source, no external pack)
- SVG langsung dipakai di canvas sebagai data URI:
  ```js
  const svgData = new XMLSerializer().serializeToString(svgElement);
  const dataUri = 'data:image/svg+xml;base64,' + btoa(svgData);
  ```
- Frontend nanti convert jadi PNG via canvas `drawImage` jika butuh raster

## 6. Usage di Frontend

```
// Sprite rendering
agent.position = {x, y} // from status.json
agent.sprite = 'dev-idle-{frame}.svg' // bob frame 0/1
agent.statusIcon = 'status-{status}.svg'

// Render order (bottom-to-top):
// shadow → legs → body → arms → head → accessory → statusIcon → hair
```

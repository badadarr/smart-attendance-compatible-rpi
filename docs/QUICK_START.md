# 🚀 Quick Start Guide

## Struktur Project Yang Baru

Project ini sekarang sudah diorganisir dengan lebih baik:

```
📁 smart-attendance-compatible-rpi/
├── 🎯 CORE APPLICATIONS (Jalankan ini)
│   ├── add_faces_rpi.py         # Daftar wajah baru
│   ├── take_attendance_rpi.py   # Ambil absensi  
│   ├── app.py                   # Web dashboard
│   └── start.sh                 # Menu utama ⭐ MULAI DARI SINI
│
├── 📝 scripts/ (Script otomatis)
│   ├── installation/            # Script install
│   ├── troubleshooting/         # Script perbaikan
│   ├── maintenance/             # Script perawatan
│   └── testing/                 # Script testing
│
├── 📚 docs/ (Dokumentasi)
├── 🛠️ tools/ (Utilitas)
└── 📊 data/ + templates/ (Data & template)
```

## 🎯 Yang Harus Dijalankan

### 1. Pertama Kali Setup
```bash
# Install sistem
scripts/installation/install_rpi.sh

# ATAU gunakan menu utama
chmod +x start.sh
./start.sh
```

### 2. Penggunaan Sehari-hari  
```bash
# Selalu mulai dari sini
./start.sh

# Pilih opsi:
# 1 = Mulai ambil absensi (UTAMA)
# 2 = Buka web dashboard  
# 3 = Daftar wajah baru
```

### 3. Jika Ada Masalah
```bash
# Troubleshooting otomatis
scripts/troubleshooting/troubleshoot.sh

# Atau dari menu utama
./start.sh
# Pilih opsi 8 = Troubleshoot
```

## 📋 Command Cepat

| Keperluan | Command |
|-----------|---------|
| **Mulai sistem** | `./start.sh` |
| **Install ulang** | `scripts/installation/install_rpi.sh` |
| **Perbaiki masalah** | `scripts/troubleshooting/troubleshoot.sh` |
| **Cek sistem** | `scripts/maintenance/system_check.py` |
| **Tes kamera** | `scripts/testing/test_camera.py` |
| **Backup data** | `scripts/maintenance/backup_restore.sh` |

## 🚨 Error NumPy di Raspberry Pi?

Jalankan script perbaikan khusus:
```bash
scripts/troubleshooting/fix_rpi_installation.sh
```

## 💡 Tips

1. **Selalu mulai dari `./start.sh`** - ini adalah menu utama
2. **Masalah instalasi?** - Gunakan `scripts/troubleshooting/`
3. **Butuh dokumentasi?** - Lihat folder `docs/`
4. **Testing/debugging?** - Gunakan `scripts/testing/`

---
🍓 **Untuk Raspberry Pi OS Debian 12 (bookworm) 64-bit**

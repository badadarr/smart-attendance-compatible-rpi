# Quality Threshold Configuration Guide

## Ringkasan Perubahan

Threshold kualitas minimum untuk deteksi wajah telah **dilonggarkan** dari **0.75 (75%)** menjadi **0.55 (55%)** sebagai pengaturan default.

## Opsi Threshold yang Tersedia

### 1. Preset Configurations

| Preset | Threshold | Deskripsi | Rekomendasi Penggunaan |
|--------|-----------|-----------|------------------------|
| `very_strict` | 0.85 | Kualitas excellent saja | Kamera high-end, lighting bagus |
| `strict` | 0.75 | Kualitas baik diperlukan (default lama) | Lingkungan kantor standar |
| `moderate` | 0.65 | Kualitas dapat diterima | Lighting campuran, kamera rata-rata |
| `relaxed` | 0.55 | Kualitas rendah diterima (default baru) | Lighting buruk, kamera lama, Raspberry Pi |
| `very_relaxed` | 0.45 | Pengecekan kualitas minimal | Kondisi sangat buruk, opsi terakhir |

### 2. Cara Mengubah Threshold

#### Opsi A: Menggunakan File Konfigurasi (Recommended)
1. Edit file `config/quality_config.py`
2. Ubah `ACTIVE_PRESET = "relaxed"` ke preset yang diinginkan
3. Atau set `CUSTOM_THRESHOLD = 0.50` untuk nilai custom

#### Opsi B: Menggunakan Kode Program
```python
# Dalam main function, uncomment salah satu:
system.set_quality_threshold_preset("very_relaxed")  # 0.45
system.set_custom_quality_threshold(0.40)  # Custom value
```

#### Opsi C: Edit Langsung di Kode
Ubah nilai di `__init__` method:
```python
self.min_face_quality = 0.45  # Set ke nilai yang diinginkan
```

## Dampak Perubahan Threshold

### Threshold Lebih Rendah (0.45-0.55):
✅ **Keuntungan:**
- Lebih mudah mendeteksi wajah
- Bekerja dengan lighting buruk
- Kompatibel dengan kamera Raspberry Pi
- Mengurangi "Low Quality" errors

⚠️ **Risiko:**
- Kemungkinan false positive lebih tinggi
- Akurasi pengenalan bisa menurun
- Perlu monitoring lebih ketat

### Threshold Lebih Tinggi (0.75-0.85):
✅ **Keuntungan:**
- Akurasi pengenalan tinggi
- Keamanan lebih baik
- Mengurangi false positive

⚠️ **Kekurangan:**
- Sulit deteksi dalam kondisi buruk
- Banyak "Low Quality" errors
- Butuh kamera dan lighting bagus

## Faktor-faktor yang Mempengaruhi Kualitas

### 1. Area Score (30%)
- Seberapa besar wajah dalam frame
- Minimum: 2% dari total frame

### 2. Sharpness Score (40%)
- Ketajaman/fokus gambar
- Menggunakan Laplacian variance
- Threshold: 500.0 (configurable)

### 3. Brightness Score (20%)
- Kondisi pencahayaan
- Optimal: nilai grayscale sekitar 127

### 4. Symmetry Score (10%)
- Simetri wajah kiri-kanan
- Deteksi posisi miring atau tidak natural

## Rekomendasi Berdasarkan Environment

### Raspberry Pi dengan Kamera Module
```python
ACTIVE_PRESET = "relaxed"  # atau "very_relaxed"
CUSTOM_THRESHOLD = 0.45
```

### Webcam USB Standar
```python
ACTIVE_PRESET = "moderate"
CUSTOM_THRESHOLD = 0.60
```

### Kamera IP/CCTV Bagus
```python
ACTIVE_PRESET = "strict"
CUSTOM_THRESHOLD = 0.70
```

### Lingkungan Lighting Buruk
```python
ACTIVE_PRESET = "very_relaxed"
CUSTOM_THRESHOLD = 0.40
```

## Monitoring dan Testing

1. **Jalankan system dan perhatikan:**
   - Berapa sering muncul "Low Quality" 
   - Akurasi pengenalan nama
   - False positive/negative

2. **Adjust threshold bertahap:**
   - Mulai dari setting rendah (0.45)
   - Naikkan secara bertahap jika terlalu banyak error
   - Turunkan jika terlalu ketat

3. **Log Quality Scores:**
   - System mencatat quality score di CSV
   - Monitor kolom "QUALITY" untuk analisis

## Troubleshooting

### Masalah: Terlalu Banyak "Low Quality"
**Solusi:**
- Turunkan threshold ke 0.45 atau 0.40
- Perbaiki pencahayaan
- Pastikan wajah cukup besar dalam frame

### Masalah: Terlalu Banyak False Recognition
**Solusi:**
- Naikkan threshold ke 0.65 atau 0.70
- Periksa data training
- Tingkatkan confidence threshold

### Masalah: Tidak Ada Deteksi Sama Sekali
**Solusi:**
- Set threshold ke 0.30 untuk testing
- Periksa koneksi kamera
- Pastikan training data tersedia

## Quick Settings untuk Testing

### Ultra Relaxed (Testing Only)
```python
self.min_face_quality = 0.30
```

### Production Recommended
```python
self.min_face_quality = 0.55  # Current default
```

### High Security
```python
self.min_face_quality = 0.80
```

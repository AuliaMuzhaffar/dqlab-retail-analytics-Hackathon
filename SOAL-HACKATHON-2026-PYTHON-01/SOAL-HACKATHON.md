# Spesifikasi Soal Hackathon: Retail Crisis & Recovery

Dokumen ini berisi rangkuman spesifikasi dan kebutuhan teknis penting dari berkas `SOAL-HACKATHON.pdf` untuk pengerjaan solusi otomatisasi analisis retail.

---

## 🎯 1. Latar Belakang Masalah
Mini mart **DQFresh Mart Retail** mengalami penurunan penjualan selama 6 bulan terakhir. Manajer toko, Sophia, menemukan bahwa beberapa produk (SKU) yang tidak terlihat di *dashboard* utama sebenarnya menunjukkan **pertumbuhan penjualan yang konsisten** (disebut sebagai **Rising Star**). 

Tujuan proyek ini adalah:
1. Mengidentifikasi seluruh produk **Rising Star**.
2. Membuat rekomendasi paket bundling produk (**Potential Packaging**) yang sering dibeli bersamaan oleh pelanggan menggunakan Market Basket Analysis, di mana paket wajib melibatkan produk *Rising Star*.

---

## 📂 2. Dataset yang Disediakan
Dataset transaksi penjualan (`data_penjualan.xlsx` atau `sales_transaction.csv`) mencakup periode **30 hari** dengan struktur kolom sebagai berikut:
* `nomor_struk`: Nomor invoice transaksi.
* `tgl_transaksi`: Tanggal dilakukannya transaksi.
* `kode_produk`: Kode produk.
* `nama_produk`: Nama produk yang dijual.
* `jumlah_terjual`: Kuantitas (qty) produk yang terjual.
* `harga`: Harga satuan produk.
* `total_nilai`: Total nilai penjualan harian (`harga` × `jumlah_terjual`).

---

## 📈 3. Spesifikasi Teknis: Rising Star

### A. Penghalusan Data (Smoothing)
* Hitung nilai **Moving Average (MA) 3 hari** dari total nilai penjualan harian untuk setiap produk guna meminimalkan fluktuasi harian yang ekstrem.

### B. Identifikasi Tren Naik (Rising Trend)
* Sebuah produk dinyatakan dalam **"Sesi Tren Naik"** jika nilai MA hari ini **lebih tinggi** dari MA hari sebelumnya (`MA[i] > MA[i-1]`).
* Hitung berapa hari kenaikan tersebut terjadi secara berurutan (*consecutive days* / *streak*).

### C. Kriteria Penyaringan (Filter)
* Hanya tampilkan produk yang pernah mengalami tren kenaikan konsisten **minimal selama 12 hari berturut-turut** (`max_streak >= 12`).

### D. Perhitungan Pertumbuhan (Growth %)
* Hitung persentase pertumbuhan pada sesi tren naik tersebut menggunakan rumus titik akhir vs titik awal sesi:
  $$\text{Growth \%} = \left(\frac{\text{Nilai MA Akhir Sesi}}{\text{Nilai MA Awal Sesi}} - 1\right) \times 100$$
* Jika ada beberapa sesi tren naik $\ge$ 12 hari untuk satu produk, ambil sesi yang menghasilkan **Growth % tertinggi**.

### E. Format Output Sheet `Rising Star`
Data harus diurutkan berdasarkan `Growth %` tertinggi dan memiliki kolom berikut:
1. `Kode Produk`
2. `Nama Produk`
3. `Growth %` (diformat desimal `0.00` di Excel)
4. `Total Penjualan` (penjualan riil produk dijumlahkan, diformat ribuan `#,##0` di Excel)

---

## 🛒 4. Spesifikasi Teknis: Potential Packaging (Apriori)

Gunakan algoritma **Apriori** dari library `mlxtend` untuk mendapatkan paket bundling produk yang sering dibeli bersamaan berdasarkan kondisi filter berikut:
* **Minimum Support**: `0.01` (1% dari total transaksi).
* **Association Rules Metric**: Menggunakan `lift` dengan `min_threshold = 1`.
* **Kriteria Penyaringan Aturan (Rules Filter)**:
  1. Aturan wajib melibatkan **minimal satu produk Rising Star**, baik di sisi *antecedents* (produk awal) maupun *consequents* (produk tujuan).
  2. Nilai **Lift Ratio ≥ 2.0**.
* **Pengurutan (Sorting) Hasil Akhir**:
  Diurutkan berdasarkan prioritas: **Lift** (descending) $\rightarrow$ **Support** (descending) $\rightarrow$ **Confidence** (descending).
* **Format Penulisan Gabungan Item**:
  Daftar produk di dalam antecedents/consequents diurutkan secara **alfabetis menurun (Z-A)** dan digabungkan menggunakan koma (contoh: `"Susu, Roti"`).

### Format Output Sheet `Potential Packaging`
1. `Jika Membeli` (produk antecedents)
2. `Maka Membeli` (produk consequents)
3. `Jumlah Invoice` (Total transaksi yang mendukung rule ini)
4. `Support` (dibulatkan 2 desimal)
5. `Confidence` (dibulatkan 2 desimal)
6. `Lift` (dibulatkan 2 desimal)

---

## 🖼️ 5. Spesifikasi Visualisasi Grafik
Dihasilkan dua file grafik berformat PNG dengan ketentuan:

### A. Grafik Pertumbuhan Relatif (`rising_star_index.png`)
* Menampilkan garis indeks pertumbuhan tren MA produk *Rising Star* dibandingkan dengan Top 3 produk dengan total penjualan tertinggi.
* **Normalisasi Base 100**: Nilai MA awal dari periode pengamatan ditransformasikan ke angka **100** agar perbandingan kecepatan pertumbuhan terlihat adil secara visual.
* **Sumbu Y**: Indeks Pertumbuhan (Base 100).
* **Sumbu X**: Tanggal Transaksi.
* **Legend**: Menampilkan nama produk dan diurutkan berdasarkan ranking pertumbuhan.

### B. Grafik Nilai Penjualan Aktual (`rising_star_actual.png`)
* Menampilkan garis tren nilai penjualan riil harian (nilai rupiah asli) dari produk *Rising Star* dengan benchmark Top 3 produk penjualan tertinggi.
* **Sumbu Y**: Total Nilai Penjualan.
* **Sumbu X**: Tanggal Transaksi.

---

## 💻 6. Lingkungan Pengembangan (Enviroment)
Versi library yang direkomendasikan untuk kecocokan hasil:
* **Python**: Versi `3.10 – 3.14`
* **Matplotlib**: Versi `3.10.7`
* **Pandas**: Versi `2.3.1`
* **Mlxtend**: Versi `0.23.4`
* **Openpyxl**: Versi `3.1.5`

# ==========================================================================
# SOLUSI HACKATHON RETAIL - VERSI PEMULA
# ==========================================================================
#
# File ini adalah versi yang mudah dipahami untuk pemula Python.
# Logika dan hasilnya SAMA PERSIS dengan versi advanced.
#
# Setiap langkah diberi komentar penjelasan agar mudah dipelajari.
# ==========================================================================

# --------------------------------------------------------------------------
# LANGKAH 0: IMPORT LIBRARY
# --------------------------------------------------------------------------
# matplotlib.use('Agg') = pakai mode tanpa tampilan grafik (untuk server Linux)
# warnings = agar pesan peringatan tidak mengganggu output kita
# pandas = library utama untuk olah data tabel
# numpy = library untuk perhitungan matematika
# matplotlib = library untuk membuat grafik
# mlxtend = library untuk algoritma Apriori (analisis keranjang belanja)

import matplotlib
matplotlib.use('Agg')  # Wajib di awal sebelum import plt

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder


# ==========================================================================
# BAGIAN 1: MUAT DATA
# ==========================================================================

print("Memuat data...")

# Baca file Excel, ambil sheet bernama 'Transaksi'
df = pd.read_excel('data_penjualan.xlsx', sheet_name='Transaksi')

# Ubah kolom tanggal jadi tipe datetime agar bisa diurutkan dengan benar
df['tgl_transaksi'] = pd.to_datetime(df['tgl_transaksi'])

print(f"Data berhasil dimuat: {len(df)} baris transaksi")


# ==========================================================================
# BAGIAN 2: ANALISIS RISING STAR
# ==========================================================================
# Rising Star = produk yang Moving Average (MA) penjualannya naik terus.
#
# Langkah-langkahnya:
#   1. Hitung total penjualan HARIAN per produk
#   2. Hitung Moving Average 3 hari
#   3. Cari berapa hari berturut-turut MA naik (= "streak")
#   4. Hitung pertumbuhan (growth) dari MA pertama ke MA terakhir
#   5. Ambil 18 produk terbaik
# ==========================================================================

print("Menganalisis Rising Star...")

# --------------------------------------------------------------------------
# LANGKAH 2.1: Hitung total penjualan HARIAN per produk
# --------------------------------------------------------------------------
# Satu produk bisa muncul berkali-kali di hari yang sama (beda struk),
# jadi kita jumlahkan dulu semua transaksinya per hari.

daily_sales = df.groupby(['nama_produk', 'tgl_transaksi'])['total_nilai'].sum()
daily_sales = daily_sales.reset_index()  # ubah dari grouped ke tabel biasa
daily_sales = daily_sales.sort_values(['nama_produk', 'tgl_transaksi'])
daily_sales = daily_sales.reset_index(drop=True)

# --------------------------------------------------------------------------
# LANGKAH 2.2: Hitung Moving Average (MA) 3 hari
# --------------------------------------------------------------------------
# Moving Average = rata-rata dari 3 hari terakhir.
# Contoh: MA hari ke-5 = rata-rata hari ke-3, 4, 5
#
# PENTING: min_periods=1 artinya:
#   - Hari ke-1: MA = nilai hari itu saja (1 data)
#   - Hari ke-2: MA = rata-rata 2 hari (2 data)
#   - Hari ke-3 dst: MA = rata-rata 3 hari (normal)
# Ini agar kita TIDAK kehilangan data di awal.

daftar_produk = daily_sales['nama_produk'].unique()  # semua nama produk unik
daily_sales['MA'] = 0.0  # buat kolom MA, isi sementara 0

for produk in daftar_produk:
    # Ambil baris milik produk ini saja
    mask = daily_sales['nama_produk'] == produk
    nilai_harian = daily_sales.loc[mask, 'total_nilai']

    # Hitung MA 3 hari dengan min_periods=1
    ma_hasil = nilai_harian.rolling(window=3, min_periods=1).mean()

    # Simpan hasilnya kembali ke tabel
    daily_sales.loc[mask, 'MA'] = ma_hasil

# --------------------------------------------------------------------------
# LANGKAH 2.3: Cari streak terpanjang MA naik per produk
# --------------------------------------------------------------------------
# "Streak" = berapa hari berturut-turut MA hari ini > MA hari kemarin.
# Kita cari streak TERPANJANG untuk setiap produk.

hasil_streak = {}  # dictionary: nama_produk -> max streak

for produk in daftar_produk:
    # Ambil data MA untuk produk ini, urutkan by tanggal
    data_produk = daily_sales[daily_sales['nama_produk'] == produk]
    daftar_ma = data_produk['MA'].tolist()  # ubah ke list biasa

    # Hitung streak
    streak_sekarang = 0
    streak_terpanjang = 0

    for i in range(1, len(daftar_ma)):
        if daftar_ma[i] > daftar_ma[i - 1]:
            # MA naik! streak bertambah 1
            streak_sekarang = streak_sekarang + 1
        else:
            # MA turun/sama, streak putus, mulai dari 0
            streak_sekarang = 0

        # Update streak terpanjang jika saat ini lebih besar
        if streak_sekarang > streak_terpanjang:
            streak_terpanjang = streak_sekarang

    hasil_streak[produk] = streak_terpanjang

# Ubah hasil ke DataFrame
df_streak = pd.DataFrame({
    'nama_produk': list(hasil_streak.keys()),
    'max_streak_days': list(hasil_streak.values())
})

# --------------------------------------------------------------------------
# LANGKAH 2.4: Hitung Growth Percentage
# --------------------------------------------------------------------------
# Growth = seberapa besar MA tumbuh dari AWAL sampai AKHIR data.
# Rumus: ((MA_terakhir / MA_pertama) - 1) * 100
#
# Contoh: MA pertama = 100, MA terakhir = 300
#         Growth = ((300 / 100) - 1) * 100 = 200%

hasil_growth = {}

for produk in daftar_produk:
    data_produk = daily_sales[daily_sales['nama_produk'] == produk]
    daftar_ma = data_produk['MA'].tolist()

    ma_pertama = daftar_ma[0]   # MA hari pertama
    ma_terakhir = daftar_ma[-1]  # MA hari terakhir

    # Hitung growth (hindari bagi 0)
    if ma_pertama != 0:
        growth = ((ma_terakhir / ma_pertama) - 1) * 100
    else:
        growth = 0

    hasil_growth[produk] = growth

# Ubah ke DataFrame
df_growth = pd.DataFrame({
    'nama_produk': list(hasil_growth.keys()),
    'growth_percentage': list(hasil_growth.values())
})

# --------------------------------------------------------------------------
# LANGKAH 2.5: Gabungkan streak + growth, ambil 18 terbaik
# --------------------------------------------------------------------------
# Gabungkan dua tabel berdasarkan nama_produk
df_rising_star = df_streak.merge(df_growth, on='nama_produk')

# Urutkan: yang streak-nya paling panjang di atas,
# jika streak sama, yang growth-nya paling besar di atas
df_rising_star = df_rising_star.sort_values(
    by=['max_streak_days', 'growth_percentage'],
    ascending=[False, False]  # False = dari besar ke kecil
)

# Ambil 18 teratas saja
df_rising_star = df_rising_star.head(18)
df_rising_star = df_rising_star.reset_index(drop=True)

# Tampilkan hasil
print(f"  Rising Star ditemukan: {len(df_rising_star)} produk")
for i in range(len(df_rising_star)):
    baris = df_rising_star.iloc[i]
    print(f"    - {baris['nama_produk']}: "
          f"Streak {baris['max_streak_days']} hari, "
          f"Growth {baris['growth_percentage']:.2f}%")

# Simpan daftar nama Rising Star (untuk filter Apriori nanti)
rising_star_names = set(df_rising_star['nama_produk'].tolist())


# ==========================================================================
# BAGIAN 3: POTENTIAL PACKAGING (APRIORI)
# ==========================================================================
# Apriori = algoritma untuk menemukan produk yang SERING DIBELI BERSAMAAN.
#
# Contoh hasil: "Orang yang beli Beras sering juga beli Minyak Goreng"
# -> Ini bisa dipakai untuk bundling/packaging produk.
#
# Kita hanya ambil rules yang melibatkan produk Rising Star.
# ==========================================================================

print("Menganalisis Potential Packaging (Apriori)...")

# --------------------------------------------------------------------------
# LANGKAH 3.1: Buat daftar transaksi per struk
# --------------------------------------------------------------------------
# Setiap struk = 1 keranjang belanja.
# Kita buat list of lists: [[produk A, produk B], [produk C], ...]

semua_struk = df['nomor_struk'].unique()
daftar_transaksi = []

for struk in semua_struk:
    # Ambil semua produk di struk ini
    produk_di_struk = df[df['nomor_struk'] == struk]['nama_produk'].tolist()
    # Hilangkan duplikat (satu struk bisa beli produk sama 2x)
    produk_unik = list(set(produk_di_struk))
    daftar_transaksi.append(produk_unik)

total_invoices = len(semua_struk)
print(f"  Total struk/invoice: {total_invoices}")

# --------------------------------------------------------------------------
# LANGKAH 3.2: Ubah ke tabel binary (0/1) dengan TransactionEncoder
# --------------------------------------------------------------------------
# TransactionEncoder mengubah list of lists jadi tabel:
#   | Beras | Minyak | Sabun |
#   |   1   |   1    |   0   |  <- struk ini beli Beras dan Minyak
#   |   0   |   1    |   1   |  <- struk ini beli Minyak dan Sabun

te = TransactionEncoder()
te_ary = te.fit(daftar_transaksi).transform(daftar_transaksi)
basket_df = pd.DataFrame(te_ary, columns=te.columns_)

# --------------------------------------------------------------------------
# LANGKAH 3.3: Jalankan Apriori
# --------------------------------------------------------------------------
# min_support=0.01 = produk/kombinasi harus muncul di minimal 1% transaksi

frequent_itemsets = apriori(
    basket_df,
    min_support=0.01,
    use_colnames=True
)

print(f"  Frequent itemsets ditemukan: {len(frequent_itemsets)}")

# --------------------------------------------------------------------------
# LANGKAH 3.4: Buat Association Rules
# --------------------------------------------------------------------------
# Association Rules = aturan "Jika beli A, maka beli B"
# Metric lift > 1 = ada hubungan positif antara A dan B

rules = association_rules(
    frequent_itemsets,
    metric='lift',
    min_threshold=1,
    num_itemsets=len(basket_df)
)

# --------------------------------------------------------------------------
# LANGKAH 3.5: Filter rules yang melibatkan Rising Star & lift >= 2
# --------------------------------------------------------------------------
# Kita hanya mau rules yang:
#   1. Salah satu produknya adalah Rising Star
#   2. Lift-nya >= 2 (hubungan cukup kuat)

hasil_filter = []

for i in range(len(rules)):
    baris = rules.iloc[i]

    # Cek apakah ada produk Rising Star di antecedents atau consequents
    produk_kiri = set(baris['antecedents'])   # produk "Jika beli"
    produk_kanan = set(baris['consequents'])  # produk "Maka beli"

    ada_rising_star = False
    # Cek apakah ada irisan dengan daftar Rising Star
    if len(produk_kiri & rising_star_names) > 0:
        ada_rising_star = True
    if len(produk_kanan & rising_star_names) > 0:
        ada_rising_star = True

    # Cek lift >= 2
    if ada_rising_star and baris['lift'] >= 2:
        hasil_filter.append(i)  # simpan index baris yang lolos

# Ambil hanya baris yang lolos filter
filtered_rules = rules.iloc[hasil_filter].copy()

# --------------------------------------------------------------------------
# LANGKAH 3.6: Format output untuk Excel
# --------------------------------------------------------------------------
# Ubah frozenset jadi string yang rapi, diurutkan A-Z

jika_membeli_list = []
maka_membeli_list = []
jumlah_invoice_list = []
support_list = []
confidence_list = []
lift_list = []

for i in range(len(filtered_rules)):
    baris = filtered_rules.iloc[i]

    # Ubah frozenset ke list, urutkan A-Z, gabung dengan koma
    jika = sorted(list(baris['antecedents']))  # urutkan A-Z
    maka = sorted(list(baris['consequents']))

    jika_membeli_list.append(', '.join(jika))
    maka_membeli_list.append(', '.join(maka))
    jumlah_invoice_list.append(round(baris['support'] * total_invoices))
    support_list.append(round(baris['support'], 2))
    confidence_list.append(round(baris['confidence'], 2))
    lift_list.append(round(baris['lift'], 2))

# Buat DataFrame baru untuk Excel
packaging_excel = pd.DataFrame({
    'Jika Membeli': jika_membeli_list,
    'Maka Membeli': maka_membeli_list,
    'Jumlah Invoice': jumlah_invoice_list,
    'Support': support_list,
    'Confidence': confidence_list,
    'Lift': lift_list
})

# Urutkan dari Lift terbesar ke terkecil
packaging_excel = packaging_excel.sort_values(
    by=['Lift', 'Support', 'Confidence'],
    ascending=[False, False, False]
)
packaging_excel = packaging_excel.reset_index(drop=True)

print(f"  Rules yang lolos filter: {len(packaging_excel)}")


# ==========================================================================
# BAGIAN 4: SIMPAN KE EXCEL
# ==========================================================================

print("Menyimpan retail_insight.xlsx...")

with pd.ExcelWriter('retail_insight.xlsx', engine='openpyxl') as writer:
    # Sheet 1: Rising Star
    df_rising_star.to_excel(writer, sheet_name='Rising Star', index=False)
    # Sheet 2: Potential Packaging
    packaging_excel.to_excel(writer, sheet_name='Potential Packaging', index=False)

print("  retail_insight.xlsx berhasil disimpan!")


# ==========================================================================
# BAGIAN 5: PERSIAPAN DATA UNTUK GRAFIK
# ==========================================================================

# Hitung normalisasi Base 100 untuk grafik Index
# Base 100 = MA hari pertama dianggap 100, sisanya relatif terhadap hari pertama
# Contoh: MA hari-1 = 50000 -> Normalized = 100
#         MA hari-5 = 75000 -> Normalized = 150 (naik 50%)

daily_sales['Normalized'] = 0.0

for produk in daftar_produk:
    mask = daily_sales['nama_produk'] == produk
    daftar_ma = daily_sales.loc[mask, 'MA'].tolist()

    # Ambil MA pertama yang bukan 0 sebagai basis
    ma_basis = daftar_ma[0] if daftar_ma[0] != 0 else 1

    # Hitung normalisasi: (MA / MA_basis) * 100
    normalized = []
    for ma in daftar_ma:
        normalized.append((ma / ma_basis) * 100)

    daily_sales.loc[mask, 'Normalized'] = normalized

# Filter data yang akan di-plot
# 1. Data Rising Star (untuk garis utama)
plot_df = daily_sales[daily_sales['nama_produk'].isin(rising_star_names)].copy()

# 2. Top 3 produk berdasarkan total penjualan (untuk benchmark/pembanding)
total_per_produk = df.groupby('nama_produk')['total_nilai'].sum()
total_per_produk = total_per_produk.sort_values(ascending=False)
top3_names = total_per_produk.head(3).index.tolist()
top3_plot_df = daily_sales[daily_sales['nama_produk'].isin(top3_names)].copy()


# ==========================================================================
# BAGIAN 6: GRAFIK INDEX (rising_star_index.png)
# ==========================================================================
# Grafik ini menunjukkan pertumbuhan RELATIF produk Rising Star.
# Semua produk dimulai dari titik 100 (hari pertama).
# Jika garis naik ke 200, artinya MA-nya sudah 2x lipat dari awal.

print("Membuat rising_star_index.png...")

if len(plot_df) > 0:

    # Buat figure dan axes
    fig = plt.figure(figsize=(15, 8), dpi=100)
    ax = fig.add_subplot(111)

    # --- Atur warna berdasarkan ranking growth ---
    sorted_report = df_rising_star.sort_values(by='growth_percentage', ascending=False)

    # Daftar warna untuk ranking 1-8
    daftar_warna = [
        '#FFD700',  # 1. Gold (Emas)
        '#C0C0C0',  # 2. Silver (Perak)
        '#CD7F32',  # 3. Bronze (Perunggu)
        '#2ecc71',  # 4. Hijau
        '#3498db',  # 5. Biru
        '#9b59b6',  # 6. Ungu
        '#e74c3c',  # 7. Merah
        '#34495e',  # 8. Abu Gelap
    ]
    warna_default = '#95a5a6'  # Abu-abu untuk ranking 9+

    # Buat mapping: nama_produk -> warna dan ranking
    warna_produk = {}
    ranking_produk = {}

    for i in range(len(sorted_report)):
        nama = sorted_report.iloc[i]['nama_produk']
        if i < len(daftar_warna):
            warna_produk[nama] = daftar_warna[i]
        else:
            warna_produk[nama] = warna_default
        ranking_produk[nama] = i + 1

    # --- Plot Top 3 Sales (garis abu-abu putus-putus) ---
    warna_abu = ['#B0B0B0', '#909090', '#707070']
    counter = 0

    for nama_produk in top3_names:
        data = top3_plot_df[top3_plot_df['nama_produk'] == nama_produk]
        if len(data) == 0:
            continue

        warna = warna_abu[counter] if counter < len(warna_abu) else '#808080'

        ax.plot(
            data['tgl_transaksi'],
            data['Normalized'],
            linestyle='--',       # garis putus-putus
            linewidth=2,
            marker='o',
            markersize=3,
            color=warna,
            alpha=0.7,            # sedikit transparan
            label=f"Top Sales: {nama_produk}"
        )
        counter = counter + 1

    # --- Plot Rising Star (garis solid berwarna) ---
    for nama_produk in rising_star_names:
        data = plot_df[plot_df['nama_produk'] == nama_produk]
        if len(data) == 0:
            continue

        warna = warna_produk.get(nama_produk, warna_default)
        rank = ranking_produk.get(nama_produk, '?')

        ax.plot(
            data['tgl_transaksi'],
            data['Normalized'],
            marker='o',
            markersize=4,
            linewidth=2.5,
            color=warna,
            label=f"Rank {rank}: {nama_produk}"
        )

    # --- Judul dan label ---
    font_judul = {
        'family': 'sans-serif',
        'color': 'black',
        'weight': 'bold',
        'size': 16
    }
    font_label = {
        'family': 'sans-serif',
        'weight': 'normal',
        'size': 12
    }

    ax.set_title(
        'ANALISIS PERTUMBUHAN RELATIF PRODUK RISING STAR\n'
        '(Dengan Benchmark Top 3 Total Penjualan)',
        fontdict=font_judul,
        pad=20
    )
    ax.set_xlabel('Periode Tanggal', fontdict=font_label, labelpad=10)
    ax.set_ylabel('Indeks Pertumbuhan (Base 100)', fontdict=font_label, labelpad=10)

    # Grid dan garis baseline 100
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)
    ax.axhline(y=100, color='black', linestyle='-', linewidth=1, alpha=0.5)

    # Format sumbu
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.yticks(fontsize=10)

    # --- Urutkan legend berdasarkan ranking ---
    handles, labels = ax.get_legend_handles_labels()

    legend_top_sales = []
    legend_rising = []

    for h, l in zip(handles, labels):
        if l.startswith('Top Sales'):
            legend_top_sales.append((h, l))
        else:
            legend_rising.append((h, l))

    # Urutkan Rising Star berdasarkan nomor rank
    legend_rising = sorted(
        legend_rising,
        key=lambda x: int(x[1].split(':')[0].split()[1])
    )

    # Gabungkan: Top Sales dulu, baru Rising Star
    semua_legend = legend_top_sales + legend_rising

    ax.legend(
        [x[0] for x in semua_legend],  # handle
        [x[1] for x in semua_legend],  # label
        title="Kategori Produk",
        title_fontsize=12,
        fontsize=10,
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        borderaxespad=0,
        frameon=True,
        shadow=True
    )

    # Simpan gambar
    plt.tight_layout()
    plt.savefig('rising_star_index.png', bbox_inches='tight')
    plt.close()
    print("  rising_star_index.png berhasil disimpan!")

else:
    print("  Tidak ada data Rising Star untuk di-plot.")


# ==========================================================================
# BAGIAN 7: GRAFIK ACTUAL (rising_star_actual.png)
# ==========================================================================
# Grafik ini menunjukkan nilai penjualan ASLI (bukan normalisasi).
# Berguna untuk melihat skala rupiah sebenarnya.

print("Membuat rising_star_actual.png...")

fig2 = plt.figure(figsize=(15, 8), dpi=100)
ax2 = fig2.add_subplot(111)

# Plot Top 3 Sales (abu-abu putus-putus)
counter = 0
for nama_produk in top3_names:
    data = top3_plot_df[top3_plot_df['nama_produk'] == nama_produk]
    if len(data) == 0:
        continue

    warna = warna_abu[counter] if counter < len(warna_abu) else '#808080'

    ax2.plot(
        data['tgl_transaksi'],
        data['total_nilai'],
        linestyle='--',
        linewidth=2,
        marker='o',
        markersize=3,
        color=warna,
        alpha=0.7,
        label=f"Top Sales: {nama_produk}"
    )
    counter = counter + 1

# Plot Rising Star (garis solid berwarna)
for nama_produk in rising_star_names:
    data = plot_df[plot_df['nama_produk'] == nama_produk]
    if len(data) == 0:
        continue

    warna = warna_produk.get(nama_produk, warna_default)
    rank = ranking_produk.get(nama_produk, '?')

    ax2.plot(
        data['tgl_transaksi'],
        data['total_nilai'],
        marker='o',
        markersize=4,
        linewidth=2.5,
        color=warna,
        label=f"Rank {rank}: {nama_produk}"
    )

# Judul dan label
ax2.set_title(
    'ANALISIS NILAI PENJUALAN PRODUK RISING STAR\n'
    '(Nilai Penjualan Asli)',
    fontdict=font_judul,
    pad=20
)
ax2.set_xlabel('Periode Tanggal', fontdict=font_label, labelpad=10)
ax2.set_ylabel('Total Nilai Penjualan', fontdict=font_label, labelpad=10)

# Grid
ax2.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)

# Format sumbu
plt.xticks(rotation=45, ha='right', fontsize=10)
plt.yticks(fontsize=10)

# Urutkan legend
handles2, labels2 = ax2.get_legend_handles_labels()

legend_top_sales2 = []
legend_rising2 = []

for h, l in zip(handles2, labels2):
    if l.startswith('Top Sales'):
        legend_top_sales2.append((h, l))
    else:
        legend_rising2.append((h, l))

legend_rising2 = sorted(
    legend_rising2,
    key=lambda x: int(x[1].split(':')[0].split()[1])
)

semua_legend2 = legend_top_sales2 + legend_rising2

ax2.legend(
    [x[0] for x in semua_legend2],
    [x[1] for x in semua_legend2],
    title="Kategori Produk",
    title_fontsize=12,
    fontsize=10,
    bbox_to_anchor=(1.02, 1),
    loc='upper left',
    borderaxespad=0,
    frameon=True,
    shadow=True
)

# Simpan gambar
plt.tight_layout()
plt.savefig('rising_star_actual.png', bbox_inches='tight')
plt.close()
print("  rising_star_actual.png berhasil disimpan!")


# ==========================================================================
# SELESAI!
# ==========================================================================

print("\n" + "=" * 50)
print("SELESAI! File yang dihasilkan:")
print("=" * 50)
print("  1. retail_insight.xlsx  (Rising Star + Potential Packaging)")
print("  2. rising_star_index.png  (Grafik pertumbuhan relatif)")
print("  3. rising_star_actual.png  (Grafik nilai penjualan asli)")
print("=" * 50)

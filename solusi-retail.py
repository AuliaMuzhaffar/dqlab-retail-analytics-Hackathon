import matplotlib
matplotlib.use('Agg')

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

# ============================================================
# 1. DATA LOADING
# ============================================================

print("Memuat data...")
df = pd.read_excel('data_penjualan.xlsx', sheet_name='Transaksi')
df['tgl_transaksi'] = pd.to_datetime(df['tgl_transaksi'])

# ============================================================
# 2. RISING STAR ANALYSIS
# ============================================================

print("Menganalisis Rising Star...")

# 2a. Agregasi harian per produk (hanya tanggal dengan transaksi)
daily_sales = (
    df.groupby(['kode_produk', 'nama_produk', 'tgl_transaksi'])['total_nilai']
    .sum()
    .reset_index()
)
daily_sales = daily_sales.sort_values(['kode_produk', 'tgl_transaksi']).reset_index(drop=True)

# 2b. Moving Average 3 hari (per produk, hanya hari aktif)
daily_sales['MA'] = (
    daily_sales.groupby('kode_produk')['total_nilai']
    .transform(lambda x: x.rolling(window=3, min_periods=3).mean())
)

# 2c. Identifikasi tren naik berturut-turut
def find_longest_rising(group):
    """Temukan streak terpanjang MA naik berturut-turut."""
    group = group.sort_values('tgl_transaksi').reset_index(drop=True)
    ma = group['MA'].values

    # Cari semua streak
    max_streak = 0
    current_streak = 0
    max_end = -1

    for i in range(1, len(ma)):
        if pd.notna(ma[i]) and pd.notna(ma[i-1]) and ma[i] > ma[i-1]:
            current_streak += 1
            if current_streak > max_streak:
                max_streak = current_streak
                max_end = i
        else:
            current_streak = 0

    if max_streak < 12:
        return None

    # Growth: dari MA hari pertama naik ke MA hari terakhir naik
    # Streak of N means transitions at indices (max_end-N+1) to max_end
    # First rising day = max_end - max_streak + 1
    # Last rising day = max_end
    first_rise_idx = max_end - max_streak
    end_idx = max_end

    ma_start = ma[first_rise_idx]
    ma_end = ma[end_idx]
    growth_pct = ((ma_end - ma_start) / ma_start) * 100

    return {
        'kode_produk': group['kode_produk'].iloc[0],
        'max_consecutive_days': max_streak,
        'growth_pct': round(growth_pct, 2)
    }

rising_results = []
for kode, group in daily_sales.groupby('kode_produk'):
    result = find_longest_rising(group)
    if result is not None:
        rising_results.append(result)

rising_stars_df = pd.DataFrame(rising_results)

# 2d. Gabungkan dengan nama produk & total penjualan
product_totals = (
    df.groupby(['kode_produk', 'nama_produk'])['total_nilai']
    .sum()
    .reset_index()
    .rename(columns={'total_nilai': 'total_penjualan'})
)

final_report = rising_stars_df.merge(product_totals, on='kode_produk', how='left')
final_report = final_report.sort_values('growth_pct', ascending=False).reset_index(drop=True)
final_report.rename(columns={'growth_pct': 'Growth_Pct'}, inplace=True)

print(f"  Rising Star ditemukan: {len(final_report)} produk")
for _, row in final_report.iterrows():
    print(f"    - {row['nama_produk']}: Growth {row['Growth_Pct']}%, Total {row['total_penjualan']:,.0f}")

# Rising Star DataFrame untuk Excel
rising_star_excel = final_report[['kode_produk', 'nama_produk', 'Growth_Pct', 'total_penjualan']].copy()
rising_star_excel['Growth_Pct'] = rising_star_excel['Growth_Pct'].apply(lambda x: int(x) if x == int(x) else x)
rising_star_excel.columns = ['Kode Produk', 'Nama Produk', 'Growth %', 'Total Penjualan']

rising_star_names = set(final_report['nama_produk'].tolist())
rising_star_codes = set(final_report['kode_produk'].tolist())

# ============================================================
# 3. POTENTIAL PACKAGING (APRIORI)
# ============================================================

print("Menganalisis Potential Packaging (Apriori)...")

# 3a. Buat daftar transaksi (set produk per invoice)
transactions = (
    df.groupby('nomor_struk')['nama_produk']
    .apply(lambda x: list(set(x)))
    .tolist()
)

total_invoices = df['nomor_struk'].nunique()

# 3b. TransactionEncoder -> binary matrix
te = TransactionEncoder()
te_ary = te.fit(transactions).transform(transactions)
basket_df = pd.DataFrame(te_ary, columns=te.columns_)

# 3c. Apriori
frequent_itemsets = apriori(
    basket_df,
    min_support=0.01,
    use_colnames=True
)

# 3d. Association Rules
rules = association_rules(
    frequent_itemsets,
    metric='lift',
    min_threshold=1,
    num_itemsets=len(basket_df)
)

# 3e. Filter: harus ada Rising Star & lift >= 2
def has_rising_star(row):
    ant = set(row['antecedents'])
    con = set(row['consequents'])
    return bool(ant & rising_star_names) or bool(con & rising_star_names)

filtered_rules = rules[
    rules.apply(has_rising_star, axis=1) & (rules['lift'] >= 2)
].copy()

# 3f. Format output
packaging_excel = pd.DataFrame({
    'Jika Membeli': filtered_rules['antecedents'].apply(lambda x: ', '.join(sorted(x))),
    'Maka Membeli': filtered_rules['consequents'].apply(lambda x: ', '.join(sorted(x))),
    'Jumlah Invoice': (filtered_rules['support'] * total_invoices).round(0).astype(int),
    'Support': filtered_rules['support'].round(2),
    'Confidence': filtered_rules['confidence'].round(2),
    'Lift': filtered_rules['lift'].round(2)
})

packaging_excel = packaging_excel.sort_values(
    by=['Lift', 'Support', 'Confidence'],
    ascending=[False, False, False]
).reset_index(drop=True)

print(f"  Rules ditemukan: {len(packaging_excel)}")

# ============================================================
# 4. EXCEL OUTPUT
# ============================================================

print("Menyimpan retail_insight.xlsx...")

with pd.ExcelWriter('retail_insight.xlsx', engine='openpyxl') as writer:
    rising_star_excel.to_excel(writer, sheet_name='Rising Star', index=False)
    packaging_excel.to_excel(writer, sheet_name='Potential Packaging', index=False)

print("  retail_insight.xlsx berhasil disimpan.")

# ============================================================
# 5. PERSIAPAN DATA VISUALISASI
# ============================================================

# Gunakan HANYA tanggal dengan transaksi aktual (tanpa zero-fill)
# Ini menghasilkan garis smooth yang sesuai referensi

# Normalisasi Base 100 (berdasarkan MA dari hari aktif)
daily_sales['Normalized'] = daily_sales.groupby('kode_produk')['MA'].transform(
    lambda x: (x / x.dropna().iloc[0]) * 100 if len(x.dropna()) > 0 and x.dropna().iloc[0] != 0 else np.nan
)

# Plot dataframes langsung dari daily_sales agar data 'total_nilai' hari pertama & kedua tidak hilang
plot_df = daily_sales[daily_sales['kode_produk'].isin(rising_star_codes)].copy()

# Top 3 produk berdasarkan total penjualan
top3_sales = (
    df.groupby(['kode_produk', 'nama_produk'])['total_nilai']
    .sum()
    .reset_index()
    .sort_values(by='total_nilai', ascending=False)
    .head(3)
)
top3_codes = top3_sales['kode_produk'].tolist()
top3_plot_df = daily_sales[daily_sales['kode_produk'].isin(top3_codes)].copy()

# ============================================================
# 6. VISUALISASI INDEX (rising_star_index.png)
# ============================================================

print("Membuat rising_star_index.png...")

if len(plot_df) > 0:

    # A. SPESIFIKASI FIGURE
    fig = plt.figure(figsize=(15, 8), dpi=100)
    ax = fig.add_subplot(111)

    # B. PENGATURAN WARNA CUSTOM BERDASARKAN PERINGKAT
    sorted_report = final_report.sort_values(by='Growth_Pct', ascending=False)

    custom_palette = [
        '#FFD700',  # Gold
        '#C0C0C0',  # Silver
        '#CD7F32',  # Bronze
        '#2ecc71',  # Emerald Green
        '#3498db',  # Blue
        '#9b59b6',  # Purple
        '#e74c3c',  # Red
        '#34495e',  # Dark Blue Grey
    ]
    default_color = '#95a5a6'

    color_mapping = {}
    rank_mapping = {}

    for i, row in enumerate(sorted_report.itertuples()):
        kode_produk = row.kode_produk
        color_mapping[kode_produk] = (
            custom_palette[i] if i < len(custom_palette) else default_color
        )
        rank_mapping[kode_produk] = i + 1

    # D. PLOT TOP 3 SALES (ABU-ABU)
    grey_colors = ['#B0B0B0', '#909090', '#707070']

    for idx, (kode_produk, group) in enumerate(
        top3_plot_df.groupby('kode_produk')
    ):
        nama_produk = group['nama_produk'].iloc[0]
        grey_color = grey_colors[idx] if idx < len(grey_colors) else '#808080'

        ax.plot(
            group['tgl_transaksi'],
            group['Normalized'],
            linestyle='--',
            linewidth=2,
            marker='o',
            markersize=3,
            color=grey_color,
            alpha=0.7,
            label=f"Top Sales: {nama_produk}"
        )

    # E. PLOT RISING STAR
    for kode_produk, group in plot_df.groupby('kode_produk'):
        nama_produk = group['nama_produk'].iloc[0]
        line_color = color_mapping.get(kode_produk, default_color)
        rank = rank_mapping.get(kode_produk, '?')
        label_with_rank = f"Rank {rank}: {nama_produk}"

        ax.plot(
            group['tgl_transaksi'],
            group['Normalized'],
            marker='o',
            markersize=4,
            linewidth=2.5,
            color=line_color,
            label=label_with_rank
        )

    # F. TITLE & LABEL
    font_title = {
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
        fontdict=font_title,
        pad=20
    )
    ax.set_xlabel('Periode Tanggal', fontdict=font_label, labelpad=10)
    ax.set_ylabel('Indeks Pertumbuhan (Base 100)', fontdict=font_label, labelpad=10)

    # G. GRID & BASELINE
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)
    ax.axhline(y=100, color='black', linestyle='-', linewidth=1, alpha=0.5)

    # H. FORMAT AXIS
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.yticks(fontsize=10)

    # I. SORT LEGEND BERDASARKAN RANK
    handles, labels = ax.get_legend_handles_labels()

    top_sales_items = []
    rising_items = []

    for h, l in zip(handles, labels):
        if l.startswith('Top Sales'):
            top_sales_items.append((h, l))
        else:
            rising_items.append((h, l))

    rising_items = sorted(
        rising_items,
        key=lambda x: int(x[1].split(':')[0].split()[1])
    )

    final_legend = top_sales_items + rising_items
    final_handles = [x[0] for x in final_legend]
    final_labels = [x[1] for x in final_legend]

    # J. LEGEND
    ax.legend(
        final_handles,
        final_labels,
        title="Kategori Produk",
        title_fontsize=12,
        fontsize=10,
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        borderaxespad=0,
        frameon=True,
        shadow=True
    )

    # K. LAYOUT & SAVE
    plt.tight_layout()
    plt.savefig('rising_star_index.png', bbox_inches='tight')
    plt.close()
    print("  rising_star_index.png berhasil disimpan.")

else:
    print("  Tidak ada data Rising Star untuk di-plot.")

# ============================================================
# 7. VISUALISASI ACTUAL (rising_star_actual.png)
# ============================================================

print("Membuat rising_star_actual.png...")

fig2 = plt.figure(figsize=(15, 8), dpi=100)
ax2 = fig2.add_subplot(111)

# A. PLOT TOP 3 SALES
for idx, (kode_produk, group) in enumerate(
    top3_plot_df.groupby('kode_produk')
):
    nama_produk = group['nama_produk'].iloc[0]
    grey_color = grey_colors[idx] if idx < len(grey_colors) else '#808080'

    ax2.plot(
        group['tgl_transaksi'],
        group['total_nilai'],
        linestyle='--',
        linewidth=2,
        marker='o',
        markersize=3,
        color=grey_color,
        alpha=0.7,
        label=f"Top Sales: {nama_produk}"
    )

# B. PLOT RISING STAR BERDASARKAN NILAI ASLI
for kode_produk, group in plot_df.groupby('kode_produk'):
    nama_produk = group['nama_produk'].iloc[0]
    line_color = color_mapping.get(kode_produk, default_color)
    rank = rank_mapping.get(kode_produk, '?')
    label_with_rank = f"Rank {rank}: {nama_produk}"

    ax2.plot(
        group['tgl_transaksi'],
        group['total_nilai'],
        marker='o',
        markersize=4,
        linewidth=2.5,
        color=line_color,
        label=label_with_rank
    )

# C. TITLE & LABEL
ax2.set_title(
    'ANALISIS NILAI PENJUALAN PRODUK RISING STAR\n'
    '(Nilai Penjualan Asli)',
    fontdict=font_title,
    pad=20
)
ax2.set_xlabel('Periode Tanggal', fontdict=font_label, labelpad=10)
ax2.set_ylabel('Total Nilai Penjualan', fontdict=font_label, labelpad=10)

# D. GRID
ax2.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)

# E. FORMAT AXIS
plt.xticks(rotation=45, ha='right', fontsize=10)
plt.yticks(fontsize=10)

# F. SORT LEGEND
handles2, labels2 = ax2.get_legend_handles_labels()

top_sales_items2 = []
rising_items2 = []

for h, l in zip(handles2, labels2):
    if l.startswith('Top Sales'):
        top_sales_items2.append((h, l))
    else:
        rising_items2.append((h, l))

rising_items2 = sorted(
    rising_items2,
    key=lambda x: int(x[1].split(':')[0].split()[1])
)

final_legend2 = top_sales_items2 + rising_items2
final_handles2 = [x[0] for x in final_legend2]
final_labels2 = [x[1] for x in final_legend2]

# G. LEGEND
ax2.legend(
    final_handles2,
    final_labels2,
    title="Kategori Produk",
    title_fontsize=12,
    fontsize=10,
    bbox_to_anchor=(1.02, 1),
    loc='upper left',
    borderaxespad=0,
    frameon=True,
    shadow=True
)

# H. LAYOUT & SAVE
plt.tight_layout()
plt.savefig('rising_star_actual.png', bbox_inches='tight')
plt.close()
print("  rising_star_actual.png berhasil disimpan.")

# ============================================================
# SELESAI
# ============================================================

print("\nSelesai! File output yang dihasilkan:")
print("  1. retail_insight.xlsx")
print("  2. rising_star_index.png")
print("  3. rising_star_actual.png")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title='Bike Sharing Dashboard', layout='wide')

# =========================
# Load data
# =========================
@st.cache_data
def load_data():
    day_df = pd.read_csv('cleaned_day_df.csv')
    hour_df = pd.read_csv('cleaned_hour_df.csv')

    day_df['date'] = pd.to_datetime(day_df['date'])
    hour_df['date'] = pd.to_datetime(hour_df['date'])

    return day_df, hour_df

day_df, hour_df = load_data()

# Menentukan kolom cuaca untuk dipakai di chart/filter
if 'weather' in hour_df.columns:
    weather_col = 'weather'
elif 'weather_label' in hour_df.columns:
    weather_col = 'weather_label'
else:
    weather_col = None

# =========================
# Filter dalam sidebar
# =========================
st.sidebar.title(':gear: Filters')

# Range tanggal tahun 2011-2012
min_date = day_df['date'].min().date()
max_date = day_df['date'].max().date()

date_range = st.sidebar.date_input(
    ':calendar: Date range',
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)
start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])

year_options = sorted(day_df['year'].unique())
year_selected = st.sidebar.multiselect(':clock1: Tahun', year_options, default=year_options)

season_options = sorted(day_df['season'].unique())
season_selected = st.sidebar.multiselect(':sun_behind_small_cloud: Musim', season_options, default=season_options)

# Filter cuaca
if weather_col:
    weather_options = sorted(hour_df[weather_col].dropna().unique())
    weather_selected = st.sidebar.multiselect(':partly_sunny: Cuaca', weather_options, default=weather_options)
else:
    weather_selected = None
    st.sidebar.info('Kolom weather tidak ditemukan.')


# =========================
# Apply filters ke data
# =========================

# Membuat salinan untuk data yang sudah difilter
day_df_filtered = day_df[
    (day_df['date'].between(start_date, end_date)) &
    (day_df['year'].isin(year_selected)) &
    (day_df['season'].isin(season_selected))
].copy()

hour_df_filtered = hour_df[
    (hour_df['date'].between(start_date, end_date)) &
    (hour_df['year'].isin(year_selected)) &
    (hour_df['season'].isin(season_selected))
].copy()

if weather_col and weather_selected is not None:
    day_df_filtered = day_df_filtered[day_df_filtered[weather_col].isin(weather_selected)].copy()
    if weather_col in hour_df_filtered.columns:
        hour_df_filtered = hour_df_filtered[hour_df_filtered[weather_col].isin(weather_selected)].copy()


# =========================
# Header + KPI
# =========================
st.title(':bike: Bike Sharing Dashboard (2011-2012)')
st.caption('Dashboard interaktif untuk mengeksplorasi tren penyewaan sepeda.')

# Menampilkan KPI
total_penyewaan = int(day_df_filtered['count'].sum())
daily_avg = float(day_df_filtered['count'].mean())
total_casual = int(day_df_filtered['casual'].sum())
total_registered = int(day_df_filtered['registered'].sum())
registered_share = (total_registered / total_penyewaan * 100) if total_penyewaan else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric('Total Penyewaan', f'{total_penyewaan:,}')
k2.metric('Rata-rata Penyewaan Harian', f'{daily_avg:,.0f}')
k3.metric('Pengguna Casual', f'{total_casual:,}')
k4.metric('Pengguna Registered', f'{total_registered:,}')
k5.metric('Registered Share', f'{registered_share:.1f}%')

st.divider()

# =========================
# Visualisasi 1: Analisis Musim dan Cuaca
# =========================
st.subheader(':partly_sunny: Penyewaan sepeda berdasarkan musim dan cuaca')

col1, col2 = st.columns(2)

# Visualisasi musim
with col1:
    season_agg = (day_df_filtered.groupby('season', as_index=False)['count']
                .mean()
                .sort_values('count', ascending=False))

    fig_season = px.bar(
        season_agg, x='season', y='count',
        text_auto='.0f',
        title='Rata-rata Penyewaan Sepeda per Musim',
        color='season'
    )
    fig_season.update_layout(xaxis_title='Musim', yaxis_title='Rata-rata Penyewaan Harian', showlegend=False)
    st.plotly_chart(fig_season, use_container_width=True)

# Visualisasi cuaca
with col2:
    if weather_col:
        weather_agg = (day_df_filtered.groupby(weather_col, as_index=False)['count']
                        .mean()
                        .sort_values('count', ascending=False))

        fig_weather = px.bar(
            weather_agg, x=weather_col, y='count',
            text_auto='.0f',
            title='Rata-rata Penyewaan Sepeda per Cuaca',
            color=weather_col
        )
        fig_weather.update_layout(xaxis_title='Cuaca', yaxis_title='Rata-rata Penyewaan Harian', showlegend=False)
        st.plotly_chart(fig_weather, use_container_width=True)
    else:
        st.info('Weather chart tidak ditampilkan karena kolom cuaca tidak tersedia.')

# Heatmap korelasi musim dan cuaca
if weather_col:
    season_order = ['Spring','Summer','Fall','Winter']
    day_df_filtered['season'] = pd.Categorical(day_df_filtered['season'], categories=season_order, ordered=True)
    pivot_day_df_filtered = day_df_filtered.pivot_table(index='season', columns=weather_col, values='count', aggfunc='mean').fillna(0)
    heatmap_season_weather = px.imshow(
        pivot_day_df_filtered,
        text_auto='.0f',
        aspect='auto',
        color_continuous_scale='YlOrRd',
        title='Korelasi musim dan cuaca terhadap rata-rata penyewaan sepeda',
        labels={'x': 'Cuaca', 'y': 'Musim'}
    )
    st.plotly_chart(heatmap_season_weather, use_container_width=True)

# Insight dari visualisasi
with st.expander(':bulb: Insight'):
    st.markdown('''
    - Rata-rata penyewaan tertinggi terjadi pada musim Fall, diikuti oleh Summer dan Winter, 
                sedangkan Spring cenderung rendah; ini menunjukkan seasonality yang kuat.
    - Demand paling tinggi terjadi pada cuaca Clear, 
                lalu menurun pada cuaca Cloudy, dan turun signifikan pada cuaca Light Rain.
    - Heatmap korelasi musim dan cuaca menunjukkan kombinasi terbaik untuk demand adalah musim 
                hangat + cuaca cerah, sedangkan cuaca hujan menekan penyewaan pada semua musim.
    ''')

st.divider()

# =========================
# Visualisasi 2: Analisis Jam Puncak Penyewaan berdasarkan Jenis Pengguna
# =========================
st.subheader(':clock12: Jam Puncak Penyewaan Sepeda berdasarkan Jenis Pengguna')

agg_mode = st.radio('Aggregation', ['Mean (typical hour)', 'Sum (total volume)'], horizontal=True)

# Menentukan fungsi agregasi (mean atau sum)
agg_function = 'mean' if agg_mode.startswith('Mean') else 'sum'

hourly = (hour_df_filtered.groupby(['year', 'hour'], as_index=False)[['casual', 'registered']]
        .agg(agg_function))

hourly_long = hourly.melt(id_vars=['year', 'hour'], var_name='user_type', value_name='value')

view = st.radio('View', ['Per Tahun', 'Gabungan'], horizontal=True)

# Visualisasi jam puncak pertahun
if view == 'Per Tahun':
    fig_hour = px.line(
        hourly_long,
        x='hour', y='value',
        color='user_type',
        facet_col='year',
        markers=True,
        title='Pola penyewaan per jam berdasarkan jenis pengguna (per tahun)'
    )

    fig_hour.for_each_annotation(lambda a: a.update(text=a.text.split('=')[-1]))
else:
# Visualisasi jam puncak gabungan
    fig_hour = px.line(
        hourly_long,
        x='hour', y='value',
        color='user_type',
        line_dash='year',
        markers=True,
        title='Pola penyewaan per jam berdasarkan jenis pengguna (gabungan)'
    )

fig_hour.update_layout(yaxis_title='Rata-rata Penyewaan', legend_title='Jenis Pengguna')
fig_hour.update_xaxes(title_text='Jam (0-23)', dtick=2)
st.plotly_chart(fig_hour, use_container_width=True)

# Insight dari visualisasi
with st.expander(':bulb: Insight'):
    st.markdown('''
    - Pengguna registered memiliki pola commuting dengan puncak pada sekitar 
                jam 8 dan jam 17.
    - Pengguna casual cenderung memuncak pada jam 12-16, 
                yang mengindikasikan penggunaan untuk aktivitas rekreasi/santai.
    - Pola puncak jam antara tahun 2011 dan 2012 relatif konsisten, 
                namun level penyewaan tahun 2012 lebih tinggi yang menunjukkan pertumbuhan demand.
    ''')

st.divider()

# =========================
# Visualisasi 3: Analisis Rolling Average
# =========================
st.subheader(':chart_with_upwards_trend: Tren Penyewaan Harian (Rolling Average)')

# Memlih rolling window
rolling_window = st.radio('Rolling window (hari)', [7, 30], index=1, horizontal=True)

# Membuat time series untuk rolling average
time_series = (day_df_filtered[['date', 'count']]
                .sort_values('date')
                .set_index('date')
                .asfreq('D'))

time_series['count'] = time_series['count'].interpolate(method='time')
time_series[f'roll_{rolling_window}'] = time_series['count'].rolling(window=rolling_window, min_periods=1).mean()
time_series = time_series.reset_index()

fig_time_series = go.Figure()
fig_time_series.add_trace(go.Scatter(x=time_series['date'], y=time_series['count'], mode='lines',
                            name='Jumlah sewa harian (raw)', line=dict(width=1, color='lightgray')))
fig_time_series.add_trace(go.Scatter(x=time_series['date'], y=time_series[f'roll_{rolling_window}'], mode='lines',
                            name=f'Rolling mean {rolling_window}D', line=dict(width=3, color='#d62728')))

fig_time_series.update_layout(
    title=f'Penyewaan Harian vs Rolling Mean ({rolling_window} Hari)',
    yaxis_title='Penyewaan Harian (count)',
    hovermode='x unified'
)
fig_time_series.update_xaxes(rangeslider_visible=True)

st.plotly_chart(fig_time_series, use_container_width=True)

# Insight dari visualisasi
with st.expander(':bulb: Insight'):
    st.markdown('''
    - Rolling average memperlihatkan tren pertumbuhan dari tahun 2011 ke 2012, 
                dengan level demand pada tahun 2012 relatif lebih tinggi.
    - Terdapat pola musiman, yaitu penyewaan meningkat menuju pertengahan sampai akhir tahun 
                dan menurun kembali di akhir tahun.
    ''')

st.divider()

# =========================
# Visualisasi 4: Analisis Perbandingan Pengguna Casual dan Registered
# =========================
st.subheader(':bar_chart: Perbandingan Penyewaan berdasarkan Pengguna (Casual vs Registered)')

# Memilih view berdasarkan tahun atau bulan
view = st.radio('Bandingkan berdasarkan', ['Tahun', 'Bulan'], horizontal=True)

# Mengurutkan nama bulan
month_order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

# Visualisasi perbandingan casual dan registered per tahun
if view == 'Tahun':
    casual_registered = (day_df_filtered.groupby('year')[['casual','registered']]
            .sum()
            .reset_index())

    casual_registered_long = casual_registered.melt(id_vars='year', var_name='user_type', value_name='total')
    casual_registered_long['user_type'] = casual_registered_long['user_type'].str.title()

    fig_casual_registered = px.bar(
        casual_registered_long, x='year', y='total',
        color='user_type',
        barmode='group',
        text_auto=True,
        title='Total Penyewaan per Tahun: Casual vs Registered'
    )
    fig_casual_registered.update_layout(xaxis_title='Tahun', yaxis_title='Total Penyewaan', legend_title='Jenis Pengguna')
    fig_casual_registered.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
    fig_casual_registered.update_yaxes(tickformat=',')
    ymax = casual_registered_long['total'].max()
    fig_casual_registered.update_yaxes(range=[0, ymax * 1.15])
    st.plotly_chart(fig_casual_registered, use_container_width=True)

else:
# Visualisasi perbandingan casual dan registered per bulan untuk setiap tahun
    select_year = st.selectbox('Pilih tahun', sorted(day_df_filtered['year'].unique()))

    casual_registered = (day_df_filtered[day_df_filtered['year'] == select_year]
            .groupby('month')[['casual','registered']]
            .sum()
            .reset_index())

    casual_registered['month'] = pd.Categorical(casual_registered['month'], categories=month_order, ordered=True)
    casual_registered = casual_registered.sort_values('month')

    casual_registered_long = casual_registered.melt(id_vars='month', var_name='user_type', value_name='total')
    casual_registered_long['user_type'] = casual_registered_long['user_type'].str.title()

    fig_casual_registered = px.bar(
        casual_registered_long,
        x='month', y='total',
        color='user_type',
        barmode='group',
        text_auto=True,
        title=f'Total Penyewaan per Bulan ({select_year}): Casual vs Registered'
    )
    fig_casual_registered.update_layout(xaxis_title='Bulan', yaxis_title='Total Penyewaan', legend_title='Jenis Pengguna')
    st.plotly_chart(fig_casual_registered, use_container_width=True)

# Insight dari visualisasi
with st.expander(':bulb: Insight'):
    st.markdown('''
    - Total penyewaan didominasi oleh pengguna registered pada tahun 2011 maupun 2012, 
                menunjukkan bahwa performa bisnis sangat ditopang oleh pengguna registered.
    - Pada tahun 2012, baik pengguna casual maupun registered meningkat, 
                namun kenaikan terbesar tetap berasal dari pengguna registered.
    ''')

st.divider()

# =========================
# Visualisasi 5: Heatmap Rata-rata Penyewaan berdasarkan Jam dan Hari
# =========================
st.subheader(':date: Heatmap rata-rata penyewaan berdasarkan jam dan hari')

# Mengurutkan nama hari
weekday_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
hour_df_filtered['weekday'] = pd.Categorical(hour_df_filtered['weekday'], categories=weekday_order, ordered=True)

heatmap_weekday_hour = hour_df_filtered.pivot_table(index='weekday', columns='hour', values='count', aggfunc='mean').fillna(0)
fig_hm = px.imshow(
    heatmap_weekday_hour, 
    aspect='auto', 
    text_auto='.0f',
    color_continuous_scale='Blues', 
    title='',
    labels={'x': 'Jam', 'y': 'Hari'}
)
fig_hm.update_xaxes(dtick=1)
st.plotly_chart(fig_hm, use_container_width=True)

# Insight dari visualisasi
with st.expander(':bulb: Insight'):
    st.markdown('''
    - Pada hari kerja, terlihat dua puncak jelas pada pagi hari
                (sekitar jam 7-9) dan sore hari (sekitar jam 16-18), konsisten dengan pola komuter.
    - Pada weekend, aktivitas lebih terkonsentrasi pada siang hingga sore, 
                dan puncaknya tidak setajam hari kerja.
    - Insight ini dapat digunakan untuk membuat keputusan operasional seperti 
                redistribusi sepeda dan penempatan kapasitas pada jam-jam ramai.
    ''')

st.divider()

# =========================
# Preview data yang sudah difilter
# =========================
st.subheader('Preview data yang sudah difilter')

with st.expander('Show filtered data'):
    st.write('Filtered day_df')
    st.dataframe(day_df_filtered, use_container_width=True)
    st.write('Filtered hour_df')
    st.dataframe(hour_df_filtered, use_container_width=True)

st.divider()
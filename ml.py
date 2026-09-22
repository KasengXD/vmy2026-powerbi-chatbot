import warnings
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.preprocessing import MinMaxScaler

warnings.filterwarnings('ignore')

print("=== STARTING MALAYSIA TOURISM ML PIPELINE (2026/2027 EXTENDED) ===")

# =====================================================================
# STEP 1: LOAD DATASETS
# =====================================================================
# State of Entry (SOE) Monthly Arrivals
df_soe = pd.read_csv('arrivals_soe.csv')
df_soe['date'] = pd.to_datetime(df_soe['date'])

# Aggregate monthly arrivals per state
df_monthly = df_soe.groupby(['date', 'soe'])['arrivals'].sum().reset_index()

# Load state infrastructure indicators
df_occ = pd.read_csv('average_occupancy_rates.csv')
latest_year = df_occ['year'].max()
df_occ_latest = df_occ[df_occ['year'] == latest_year][['state', 'average hotel occupancy rate(%)']].rename(
    columns={'average hotel occupancy rate(%)': 'occupancy_rate'}
)

df_guests = pd.read_csv('hotel_guests_2024.csv')[['State', 'Total 2024']].rename(
    columns={'State': 'state', 'Total 2024': 'hotel_guests_2024'}
)

df_home = pd.read_csv('homestay_indicators_2024.csv')[['State', 'No of Rooms', 'Total Income (RM)']].rename(
    columns={'State': 'state', 'No of Rooms': 'homestay_rooms', 'Total Income (RM)': 'homestay_income'}
)

# =====================================================================
# STEP 2: ML TIME-SERIES FORECASTING (2025–2027 HOLT-WINTERS)
# =====================================================================
states = df_monthly['soe'].unique()
forecast_list = []
summary_list = []

# 38 months extends forecast from Nov 2024 through Dec 2027
FORECAST_STEPS = 38 

for state in states:
    state_df = df_monthly[df_monthly['soe'] == state].sort_values('date').set_index('date')['arrivals']
    state_df = state_df.resample('MS').sum()  # Monthly start frequency
    
    # Fit Time-Series Holt-Winters Model per state
    try:
        model = ExponentialSmoothing(
            state_df, 
            trend='add', 
            seasonal='add', 
            seasonal_periods=12, 
            initialization_method="estimated"
        ).fit()
        fut = model.forecast(FORECAST_STEPS)
    except Exception:
        model = ExponentialSmoothing(
            state_df, 
            trend='add', 
            seasonal=None, 
            initialization_method="estimated"
        ).fit()
        fut = model.forecast(FORECAST_STEPS)
        
    # Historical baseline (Last 12 months of actuals, ~2024)
    hist_avg = state_df.tail(12).mean()
    
    # Target period baseline (Average of projected 2026–2027 years)
    fut_avg = fut.tail(24).mean()
    growth_pct = ((fut_avg - hist_avg) / hist_avg) * 100 if hist_avg > 0 else 0
    
    summary_list.append({
        'state': state,
        'Historical_Avg_Monthly_Arrivals': round(hist_avg, 0),
        'Forecasted_Avg_Monthly_Arrivals': round(fut_avg, 0),
        'Forecasted_Growth_Pct': round(growth_pct, 2)
    })
    
    # Export full time-series (Historical Actuals + 2025-2027 Predictions)
    for dt, val in state_df.items():
        forecast_list.append({
            'date': dt.strftime('%Y-%m-%d'),
            'state': state,
            'arrivals': round(max(0, val), 0),
            'type': 'Actual'
        })
    for dt, val in fut.items():
        forecast_list.append({
            'date': dt.strftime('%Y-%m-%d'),
            'state': state,
            'arrivals': round(max(0, val), 0),
            'type': 'Forecast'
        })

df_summary = pd.DataFrame(summary_list)
df_ts = pd.DataFrame(forecast_list)

# =====================================================================
# STEP 3: SUSTAINABLE READINESS INDEXING & QUADRANT MAPPING
# =====================================================================
# Standardize state names for merging
state_map = {'W.P. Labuan': 'Labuan'}
df_summary['state_clean'] = df_summary['state'].replace(state_map)

df_ml = pd.merge(df_summary, df_occ_latest, left_on='state_clean', right_on='state', how='left')
df_ml = pd.merge(df_ml, df_guests, left_on='state_clean', right_on='state', how='left', suffixes=('', '_g'))
df_ml = pd.merge(df_ml, df_home, left_on='state_clean', right_on='state', how='left', suffixes=('', '_h'))

supply_cols = ['occupancy_rate', 'hotel_guests_2024', 'homestay_rooms', 'homestay_income']
df_ml[supply_cols] = df_ml[supply_cols].fillna(df_ml[supply_cols].median())

# Normalize indicators to 0 - 100 scale using MinMaxScaler
scaler = MinMaxScaler()
df_ml[['norm_occ', 'norm_guests', 'norm_rooms', 'norm_inc']] = scaler.fit_transform(df_ml[supply_cols])
df_ml['Readiness_Score'] = (df_ml[['norm_occ', 'norm_guests', 'norm_rooms', 'norm_inc']].mean(axis=1) * 100).round(2)

# Quadrant Logic
growth_median = df_ml['Forecasted_Growth_Pct'].median()
readiness_threshold = 45.0

def assign_quadrant(row):
    high_demand = row['Forecasted_Growth_Pct'] >= growth_median
    high_readiness = row['Readiness_Score'] >= readiness_threshold
    
    if high_demand and not high_readiness:
        return 'Overtourism Risk'
    elif high_demand and high_readiness:
        return 'Balanced Growth'
    elif not high_demand and high_readiness:
        return 'Underutilized Potential'
    else:
        return 'Emerging / Low Priority'

df_ml['Quadrant'] = df_ml.apply(assign_quadrant, axis=1)

# Actionable Policy Tag Mapping
policy_tags = {
    'Overtourism Risk': '⚠️ Dynamic Cap & Infra Upgrade',
    'Balanced Growth': '✅ High-Yield Eco Maintenance',
    'Underutilized Potential': '🌱 Targeted Marketing & Direct Routes',
    'Emerging / Low Priority': '🔄 Foundational Transport Investment'
}
df_ml['Policy_Action'] = df_ml['Quadrant'].map(policy_tags)

# =====================================================================
# STEP 4: CALCULATE DYNAMIC RESOURCE & BUDGET ALLOCATION (%)
# =====================================================================
def calc_budget(row):
    q = row['Quadrant']
    if q == 'Overtourism Risk':
        return pd.Series([70, 10, 20])  # Infra %, Promo %, Sustainability %
    elif q == 'Underutilized Potential':
        return pd.Series([15, 70, 15])
    elif q == 'Balanced Growth':
        return pd.Series([25, 25, 50])
    else:
        return pd.Series([40, 30, 30])

df_ml[['Budget_Infra_Pct', 'Budget_Promo_Pct', 'Budget_Sustain_Pct']] = df_ml.apply(calc_budget, axis=1)

# Clean up final columns for export
df_ml_final = df_ml[[
    'state_clean', 'Historical_Avg_Monthly_Arrivals', 'Forecasted_Avg_Monthly_Arrivals',
    'Forecasted_Growth_Pct', 'Readiness_Score', 'Quadrant', 'Policy_Action',
    'Budget_Infra_Pct', 'Budget_Promo_Pct', 'Budget_Sustain_Pct'
]].rename(columns={'state_clean': 'state'})

# =====================================================================
# STEP 5: EXPORT CSV FILES FOR POWER BI
# =====================================================================
df_ts.to_csv('ml_forecast_arrivals_timeseries.csv', index=False)
df_ml_final.to_csv('ml_recommendations_dataset.csv', index=False)

print("\n=== SUCCESS! ML EXPORTS GENERATED FOR 2026/2027 ===")
print("1. Saved: 'ml_forecast_arrivals_timeseries.csv' (Nov 2024 – Dec 2027)")
print("2. Saved: 'ml_recommendations_dataset.csv' (2026/2027 Quadrants & Budgets)")
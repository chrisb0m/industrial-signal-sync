import pandas as pd
import numpy as np
from scipy.signal import correlate, find_peaks
from dtaidistance import dtw
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# Configuration
DATA_PATH = r'C:\Users\OMISTAJA\Desktop\data\projekti'
ACCEL_FILE = 'Data_processed.csv'
PRESSURE_FILE = 'tana_siistitty_800Hz.csv'
OUTPUT_FILE = 'synchronized_combined_data_improved.csv'

def european_to_float(value):
    """Convert European format (comma decimals) to float"""
    if isinstance(value, str):
        return float(value.replace('.', '').replace(',', '.'))
    return float(value)

def convert_time(time_str):
    """Convert HH:MM:SS,SSSSS to seconds (handles 3-5 digit milliseconds)"""
    if isinstance(time_str, str):
        time_str = time_str.replace('.', ',')
        h, m, s = time_str.split(':')
        if ',' in s:
            s, ms = s.split(',')
            ms = ms.ljust(5, '0')[:5]
            return int(h)*3600 + int(m)*60 + int(s) + int(ms)/100000
        return int(h)*3600 + int(m)*60 + int(s)
    return time_str

def normalize_signal(s):
    """Normalize signal to 0-1 range"""
    return (s - s.min()) / (s.max() - s.min())

# --- STEP 1: Load and Prepare Data ---
print("Loading and preprocessing data...")

# Load acceleration data
accel = pd.read_csv(f"{DATA_PATH}\\{ACCEL_FILE}", sep=';')
for col in ['Acc X', 'Acc Y', 'Acc Z']:
    accel[col] = accel[col].apply(european_to_float)

accel['Time_sec'] = accel['Time'].apply(convert_time)
accel['Acc_Mag'] = np.sqrt(accel['Acc X']**2 + accel['Acc Y']**2 + accel['Acc Z']**2)
accel['Norm_Acc'] = normalize_signal(accel['Acc_Mag'])

# Load pressure data
pressure = pd.read_csv(f"{DATA_PATH}\\{PRESSURE_FILE}", sep=';')
for col in ['Pump1HighPress_values', 'Pump2HighPress_values', 'Machine Speed_values']:
    if col in pressure.columns:
        pressure[col] = pressure[col].apply(european_to_float)

pressure['Time_sec'] = pressure['Machine Speed_time'].apply(convert_time)
pressure['Press_Sum'] = pressure['Pump1HighPress_values'] + pressure['Pump2HighPress_values']
pressure['Norm_Press'] = normalize_signal(pressure['Press_Sum'])

# --- STEP 2: Hybrid Synchronization ---
print("\nPerforming hybrid synchronization...")

# A. Initial coarse alignment using cross-correlation
def cross_corr_align(s1, s2, fs=800, downsample=10):
    """Calculate time offset using cross-correlation"""
    corr = correlate(s1[::downsample], s2[::downsample], mode='full')
    lags = np.arange(-len(s2[::downsample])+1, len(s1[::downsample]))
    lag = lags[np.argmax(corr)] * downsample / fs
    return lag

# Calculate initial offset (coarse)
time_diff = cross_corr_align(accel['Norm_Acc'], pressure['Norm_Press'])
pressure['Time_sec'] += time_diff
print(f"Coarse time adjustment: {time_diff:.3f} seconds")

# B. Fine alignment using DTW on a 10-second window
align_window = min(8000, len(accel), len(pressure))
s1 = accel['Norm_Acc'].values[:align_window]
s2 = pressure['Norm_Press'].values[:align_window]

distance, paths = dtw.warping_paths(s1, s2, window=align_window//4)  # Smaller window for speed
best_path = dtw.best_path(paths)

# Find median time offset
time_diffs = [accel['Time_sec'].iloc[i] - pressure['Time_sec'].iloc[j] for i,j in best_path]
median_offset = np.median(time_diffs)
pressure['Time_sec_aligned'] = pressure['Time_sec'] + median_offset
print(f"Fine time adjustment: {median_offset:.3f} seconds")

# --- STEP 3: Interpolation-Based Merging ---
print("\nPerforming precise interpolation merge...")

# Create interpolation function for pressure data
pressure_interp = interp1d(
    pressure['Time_sec_aligned'],
    pressure[['Pump1HighPress_values', 'Pump2HighPress_values', 'Machine Speed_values']],
    axis=0,
    bounds_error=False,
    fill_value="extrapolate"
)

# Apply interpolation to acceleration timestamps
combined = accel.copy()
combined[['Pump1HighPress_values', 'Pump2HighPress_values', 'Machine Speed_values']] = \
    pressure_interp(accel['Time_sec'])

# --- STEP 4: Visual Verification ---
plt.figure(figsize=(15, 6))

# Plot original signals
plt.subplot(2, 1, 1)
plt.plot(accel['Time_sec'], accel['Norm_Acc'], label='Acceleration')
plt.plot(pressure['Time_sec'], pressure['Norm_Press'], label='Pressure (original)')
plt.title("Before Synchronization")
plt.legend()

# Plot aligned signals
plt.subplot(2, 1, 2)
plt.plot(accel['Time_sec'], accel['Norm_Acc'], label='Acceleration')
plt.plot(pressure['Time_sec_aligned'], pressure['Norm_Press'], 
         label=f'Pressure (aligned by {time_diff+median_offset:.3f}s)')
plt.title("After Synchronization")
plt.legend()

plt.tight_layout()
plt.show()

# --- STEP 5: Save Results ---
keep_cols = [
    'Time', 'Time_sec', 'Sensor ID', 'Acc X', 'Acc Y', 'Acc Z',
    'Machine Speed_values', 'Pump1HighPress_values', 'Pump2HighPress_values'
]
combined = combined[keep_cols]
combined.to_csv(f"{DATA_PATH}\\{OUTPUT_FILE}", sep=';', index=False, float_format='%.6f')

print("\n=== Synchronization Complete ===")
print(f"Total offset applied: {time_diff+median_offset:.6f} seconds")
print(f"Saved to {OUTPUT_FILE}")
print("\nFirst synchronized rows:")
print(combined.head())

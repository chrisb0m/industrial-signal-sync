import pandas as pd
import numpy as np
from datetime import datetime

# File paths
input_path = r'tana_siistitty.csv'
output_path = r'siistitty_800Hz.csv'

# --- STEP 1: Read CSV ---
df = pd.read_csv(
    input_path,
    sep=';',
    skiprows=3,
    header=None,
    names=[
        'Machine Speed_time',
        'Machine Speed_values',
        'Pump1HighPress_values',
        'Pump2HighPress_values'
    ]
)

# --- STEP 2: Convert Time to Seconds (Handles both with/without milliseconds) ---
def time_to_seconds(time_str):
    # Remove leading '0:' if present
    if time_str.startswith('0:'):
        time_str = time_str[2:]
    
    # Replace comma with dot (if European decimal format)
    time_str = time_str.replace(',', '.')
    
    # Check if milliseconds are present
    if '.' in time_str:
        time_obj = datetime.strptime(time_str, "%H:%M:%S.%f")
    else:
        time_obj = datetime.strptime(time_str, "%H:%M:%S")
    
    # Convert to total seconds
    return (time_obj.hour * 3600 + 
            time_obj.minute * 60 + 
            time_obj.second + 
            (time_obj.microsecond / 1e6 if hasattr(time_obj, 'microsecond') else 0))

df['Machine Speed_time'] = df['Machine Speed_time'].apply(time_to_seconds)

# --- STEP 3: Downsample (1kHz → 800Hz) ---
# Keep 4 samples, drop 1 (4:5 ratio)
df_downsampled = df.iloc[[i for i in range(len(df)) if i % 5 != 4]].reset_index(drop=True)

# --- STEP 4: Restore Original Time Format (HH:MM:SS,SSS) ---
def seconds_to_time(total_seconds):
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = total_seconds % 60
    # Format as HH:MM:SS,SSS (European format)
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace('.', ',')

df_downsampled['Machine Speed_time'] = df_downsampled['Machine Speed_time'].apply(seconds_to_time)

# --- STEP 5: Save Result ---
df_downsampled.to_csv(output_path, sep=';', index=False)

# --- Verification ---
print("\n--- First 5 Rows (Downsampled) ---")
print(df_downsampled.head())
print("\n--- Summary ---")
print(f"Original length (1kHz): {len(df)} samples")
print(f"Downsampled length (800Hz): {len(df_downsampled)} samples")
print(f"Saved to: {output_path}")

# industrial-signal-sync
Industrial sensor data resampling and hybrid synchronization (cross-correlation + DTW). Built for real-world deploymen
Industrial Signal Synchronization — Imusys Oy (2024–2025)
Problem
Two industrial measurement systems recorded data at different sampling rates:

Acceleration sensors (Broadsense Gateway): 8 kHz
Pressure/speed sensors (Tana landfill system): 4 kHz / 1 kHz

Before analysis, the data had to be resampled to a common frequency and time-aligned precisely. The signals were recorded independently with no shared trigger, so timestamps had drift and offset between systems.
Solution
A two-stage hybrid synchronization pipeline:
Stage 1 — Resampling (downsample_to_800hz.py)

Converts 1 kHz pressure data to 800 Hz using a 4:5 sample drop method
Handles European timestamp format (HH:MM:SS,SSS with comma decimal separator)
Preserves original time format in output

Stage 2 — Synchronization (synchronize_signals.py)

Coarse alignment using cross-correlation (fast, handles large offsets)
Fine alignment using Dynamic Time Warping / DTW (corrects non-linear drift)
Interpolation-based merging to a unified timeline
Visual before/after verification plots

Results

Combined CSV with acceleration (X/Y/Z), pressure (pump 1 & 2) and machine speed on a single aligned timeline
Synchronization accuracy validated visually and exported for FlexPro analysis
Used in real deployment: Tana landfill compactor planetary gearbox monitoring

Technologies
Python · Pandas · NumPy · SciPy · dtaidistance · Matplotlib
Context
Built as part of a vibration measurement system for industrial applications at Imusys Oy. Measurement sites included Valmet machining (paper cylinder resonance analysis) and Tana landfill (compactor gearbox failure monitoring).

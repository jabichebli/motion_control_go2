import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

# --- Find all monitor logs ---
log_files = glob.glob(os.path.join("logs", "monitor_*.csv.monitor.csv"))

if not log_files:
    print("No monitor files found in ./logs/")
    exit()

# --- Combine all logs ---
dfs = []
for file in log_files:
    try:
        df = pd.read_csv(file, skiprows=1)  # skip gym monitor header line
        df["source"] = os.path.basename(file)
        dfs.append(df)
    except Exception as e:
        print(f"Skipping {file}: {e}")

if not dfs:
    print("No valid log data found.")
    exit()

# --- Merge and sort ---
merged = pd.concat(dfs, ignore_index=True)
merged = merged.sort_index()

# --- Compute timestep and smoothed reward ---
merged["timestep"] = merged["l"].cumsum()       # cumulative episode lengths
merged["rolling_reward"] = merged["r"].rolling(50).mean()  # smooth rewards

# --- Plot ---
plt.figure(figsize=(10, 6))
plt.plot(merged["timestep"], merged["rolling_reward"], label="Rolling Mean (50 episodes)")
plt.title("HalfCheetah Training Performance (merged across all envs)")
plt.xlabel("Timestep")
plt.ylabel("Average Episode Reward")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

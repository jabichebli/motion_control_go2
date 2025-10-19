# plot_training.py
import pandas as pd
import matplotlib.pyplot as plt
import glob

# Find the latest monitor log
log_files = glob.glob("logs/*.csv")
if not log_files:
    print("No log files found in ./logs/")
else:
    df = pd.read_csv(log_files[-1], skiprows=1)  # Skip header comment
    plt.plot(df["r"].rolling(10).mean())
    plt.title("Average Episode Reward (rolling mean)")
    plt.xlabel("Episode")
    plt.ylabel("Reward")
    plt.grid(True)
    plt.show()

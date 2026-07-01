from MCALib import MCA
import time
import numpy as np
import matplotlib.pyplot as plt

# Connect
m = MCA(port='COM10')
if not m.connected:
    print("❌ Connection failed"); exit()

print("✅ Connected!")
print("📡 Source detected near detector - Starting acquisition...")

# Clear any old data first
m.clearHistogram()
m.startHistogram()

# Acquire with live count display
duration = 120  # 2 minutes
print(f"⏱️  Acquiring for {duration} seconds...")
print("─" * 40)

for i in range(duration):
    time.sleep(1)
    m.sync()
    spectrum = np.array(m.getHistogram())
    total_counts = int(spectrum.sum())
    peak_channel = int(spectrum.argmax())
    peak_counts = int(spectrum.max())
    
    # Live progress bar
    progress = int((i+1)/duration * 20)
    bar = "█" * progress + "░" * (20-progress)
    print(f"\r[{bar}] {i+1}s | Total Counts: {total_counts} | "
          f"Peak: Ch{peak_channel}({peak_counts})", end="", flush=True)

print("\n" + "─" * 40)
print("✅ Acquisition complete!")

# Final sync
m.sync()
spectrum = np.array(m.getHistogram())

# ── Plot ──────────────────────────────────
fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# Plot 1: Normal scale
axes[0].plot(spectrum, color='steelblue', linewidth=0.8)
axes[0].fill_between(range(len(spectrum)), spectrum, alpha=0.3, color='steelblue')
axes[0].set_xlabel('Channel Number')
axes[0].set_ylabel('Counts')
axes[0].set_title('Gamma Spectrum (Linear Scale)')
axes[0].grid(True, alpha=0.3)

# Mark highest peak
peak_ch = spectrum.argmax()
axes[0].annotate(f'Peak @ Ch {peak_ch}\n({int(spectrum[peak_ch])} counts)',
                xy=(peak_ch, spectrum[peak_ch]),
                xytext=(peak_ch+50, spectrum[peak_ch]),
                arrowprops=dict(arrowstyle='->', color='red'),
                color='red', fontsize=10)

# Plot 2: Log scale (better for seeing all peaks)
log_spectrum = np.log10(spectrum + 1)  # +1 to avoid log(0)
axes[1].plot(log_spectrum, color='darkorange', linewidth=0.8)
axes[1].fill_between(range(len(log_spectrum)), log_spectrum, alpha=0.3, color='darkorange')
axes[1].set_xlabel('Channel Number')
axes[1].set_ylabel('log(Counts)')
axes[1].set_title('Gamma Spectrum (Log Scale - shows weak peaks better)')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('gamma_with_source.png', dpi=150)
plt.show()

# ── Save CSV ──────────────────────────────
import pandas as pd
df = pd.DataFrame({
    'Channel': range(len(spectrum)),
    'Counts': spectrum.astype(int)
})
df.to_csv('gamma_spectrum.csv', index=False)

print(f"\n📊 Stats:")
print(f"   Total Counts  : {int(spectrum.sum())}")
print(f"   Peak Channel  : {spectrum.argmax()}")
print(f"   Peak Counts   : {int(spectrum.max())}")
print(f"   Active Channels: {int((spectrum>0).sum())}")
print(f"\n💾 Saved: gamma_with_source.png & gamma_spectrum.csv")
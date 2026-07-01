from MCALib import MCA
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.collections import LineCollection
from scipy.signal import find_peaks
import pandas as pd
import threading

# ── Connect ───────────────────────────────
PORT = 'COM10'
m = MCA(port=PORT)
if not m.connected:
    print("Connection failed"); exit()

print("Connected! Co-60 source detected")
m.clearHistogram()
m.startHistogram()

# ── Thread lock — prevents simultaneous sync calls ──
sync_lock   = threading.Lock()
reconnecting = [False]
last_good_spectrum = [np.zeros(1024)]

# Global variable to safely access Radiation Intensity from other threads
current_radiation_intensity = 0

# List to accumulate time-stamped metrics in memory for a clean final export
metrics_history = []

def safe_sync():
    """Sync with lock + auto-reconnect on PermissionError."""
    global m
    if reconnecting[0]:
        return last_good_spectrum[0].copy()

    if not sync_lock.acquire(blocking=False):
        return last_good_spectrum[0].copy()

    try:
        m.sync()
        data = np.array(m.getHistogram(), dtype=float)
        last_good_spectrum[0] = data.copy()
        return data

    except Exception as e:
        print(f"\nSync error: {e}")
        reconnecting[0] = True
        threading.Thread(target=_reconnect, daemon=True).start()
        return last_good_spectrum[0].copy()

    finally:
        sync_lock.release()

def _reconnect():
    """Close port and reconnect cleanly."""
    global m
    print("\nReconnecting...")
    try:
        if m.fd:
            m.fd.close()
    except:
        pass

    time.sleep(2)

    for attempt in range(10):
        try:
            new_m = MCA(port=PORT)
            if new_m.connected:
                m = new_m
                m.startHistogram()
                reconnecting[0] = False
                print("Reconnected!")
                return
        except:
            pass
        print(f"Retry {attempt+1}/10...")
        time.sleep(2)

    print("Could not reconnect after 10 attempts.")
    reconnecting[0] = False

# ── Setup Figure ──────────────────────────
fig, axes = plt.subplots(2, 1, figsize=(14, 10))
fig.patch.set_facecolor('#0d0d0d')

for ax in axes:
    ax.set_facecolor('#0b0f19')  # Sleek deep-tech card background
    ax.tick_params(colors='#94a3b8', labelsize=10)
    ax.xaxis.label.set_color('#94a3b8')
    ax.yaxis.label.set_color('#94a3b8')
    ax.title.set_color('white')
    for spine in ax.spines.values():
        spine.set_edgecolor('#1e293b')

fig.suptitle('LIVE GAMMA SPECTROMETER MONITOR — Co-60 SOURCE',
             color='#00ffcc', fontsize=15, fontweight='bold', y=0.96)

# Initialize Primary Line Plots
line1, = axes[0].plot(np.arange(1024), np.zeros(1024), color='#00ff88', linewidth=1.2, zorder=3)
line2, = axes[1].plot(np.arange(1024), np.zeros(1024), color='#ff6600', linewidth=1.2, zorder=3)

# Global trackers for handling the shading areas cleanly
fill_containers = {"lin": None, "log": None}

# Create dynamic, single collection objects for peak lines
peak_lines1 = LineCollection([], colors='yellow', alpha=0.5, linewidths=1.0, linestyles='--')
peak_lines2 = LineCollection([], colors='yellow', alpha=0.3, linewidths=0.8, linestyles='--')
axes[0].add_collection(peak_lines1)
axes[1].add_collection(peak_lines2)

axes[0].set_xlim(0, 1024); axes[0].set_ylim(0, 10)
axes[0].set_xlabel('Channel Number', fontweight='semibold')
axes[0].set_ylabel('Counts', fontweight='semibold')
axes[0].set_title('Linear Scale Spectrum', color='#00ff88', fontsize=11, pad=10)
axes[0].grid(True, alpha=0.1, color='#efefef', linestyle=':')

axes[1].set_xlim(0, 1024); axes[1].set_ylim(0, 2)
axes[1].set_xlabel('Channel Number', fontweight='semibold')
axes[1].set_ylabel('log10(Counts)', fontweight='semibold')
axes[1].set_title('Logarithmic Scale Viewport (Weak Photopeaks)', color='#ff6600', fontsize=11, pad=10)
axes[1].grid(True, alpha=0.1, color='#efefef', linestyle=':')

# Dashboard Telemetry Boxes
stats_text = axes[0].text(
    0.98, 0.93, '', transform=axes[0].transAxes,
    color='#e2e8f0', fontsize=10, va='top', ha='right', fontfamily='monospace',
    bbox=dict(boxstyle='round,pad=0.6', facecolor='#131a2c', edgecolor='#1e293b', alpha=0.95)
)
status_bar = fig.text(0.015, 0.965, '', color='#64748b', fontsize=9.5, fontfamily='sans-serif')

start_time   = time.time()
frame_count  = [0]
text_annotations = []

# ── Animation Loop ────────────────────────
def animate(i):
    global text_annotations, current_radiation_intensity, metrics_history

    # Fetch data arrays safely from hardware
    spectrum     = safe_sync()
    channels     = np.arange(len(spectrum))
    log_spectrum = np.log10(spectrum + 1)

    # 1. Update Core Trace Lines
    line1.set_data(channels, spectrum)
    line2.set_data(channels, log_spectrum)

    # 2. Re-Render Shading Area Under Curves
    if fill_containers["lin"] is not None:
        fill_containers["lin"].remove()
    if fill_containers["log"] is not None:
        fill_containers["log"].remove()

    fill_containers["lin"] = axes[0].fill_between(channels, spectrum, color='#00ff88', alpha=0.15, zorder=2)
    fill_containers["log"] = axes[1].fill_between(channels, log_spectrum, color='#ff6600', alpha=0.15, zorder=2)

    # 3. Handle Auto-scaling limits dynamically
    axes[0].set_ylim(0, max(spectrum.max(), 5) * 1.2)
    axes[1].set_ylim(0, max(log_spectrum.max(), 0.5) * 1.2)

    # 4. Wipe old frame text labels cleanly
    for txt in text_annotations:
        txt.remove()
    text_annotations.clear()

    # 5. Process Peak Indicators & Vertical Drop lines
    if spectrum.max() > 5:
        peaks, _ = find_peaks(spectrum, height=spectrum.max() * 0.1, distance=20, prominence=2)
        
        segments1 = [((p, 0), (p, spectrum[p])) for p in peaks[:8]]
        segments2 = [((p, 0), (p, log_spectrum[p])) for p in peaks[:8]]
        peak_lines1.set_segments(segments1)
        peak_lines2.set_segments(segments2)

        for p in peaks[:8]:
            txt = axes[0].text(p, spectrum[p] * 1.03, f"Ch {p}\n({int(spectrum[p])})", 
                               color='#facc15', fontsize=8, ha='center', va='bottom',
                               fontweight='bold', fontfamily='monospace')
            text_annotations.append(txt)
    else:
        peak_lines1.set_segments([])
        peak_lines2.set_segments([])

    # 6. Metadata Display Updates & Intensity Evaluation
    elapsed = int(time.time() - start_time)
    total_area = int(spectrum.sum())
    current_radiation_intensity = total_area  
    
    peak_ch = int(spectrum.argmax())
    cps     = total_area / max(elapsed, 1)
    conn    = 'LIVE' if not reconnecting[0] else 'RECONNECTING...'

    stats_text.set_text(
        f'STATUS       : {conn}\n'
        f'RAD INTENSITY: {total_area:,} (Area)\n'
        f'TOTAL COUNTS : {total_area:,}\n'
        f'COUNT RATE   : {cps:.1f} CPS\n'
        f'PEAK CHANNEL : {peak_ch}\n'
        f'MAX COUNTS   : {int(spectrum.max()):,}'
    )
    status_bar.set_text(f'Elapsed Duration: {elapsed}s   |   Rad Intensity (Area): {total_area:,}   |   Device Status: {conn}')
    frame_count[0] += 1

    # 7. Asynchronous Telemetry Recording (Logs metrics trace every second)
    current_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    metrics_history.append({
        'Timestamp': current_timestamp,
        'Elapsed_Sec': elapsed,
        'Rad_Intensity_Area': total_area,
        'Count_Rate_CPS': round(cps, 2)
    })

    return line1, line2, peak_lines1, peak_lines2

# ── Execution Loop ────────────────────────
ani = animation.FuncAnimation(
    fig, animate,
    interval=1000, 
    blit=False,
    cache_frame_data=False
)

plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.show()

# ── Post-Shutdown Clean Save ──────────────
print("\n" + "="*50)
print("EXECUTION STOPPED — EXPORTING FINAL DATA")
print("="*50)

final_spectrum = last_good_spectrum[0]

try:
    # 1. Export raw counts reading data to CSV
    df_spectrum = pd.DataFrame({
        'Channel': range(len(final_spectrum)), 
        'Counts': final_spectrum.astype(int)
    })
    df_spectrum.to_csv('co60_final_spectrum.csv', index=False)

    # 2. Export collected timestamp metrics to a separate downloadable CSV
    df_metrics = pd.DataFrame(metrics_history)
    df_metrics.to_csv('co60_final_metrics.csv', index=False)

    print("SUCCESS: 2 Downloadable CSV files have been automatically created:")
    print("  -> Raw Reading Counts File : co60_final_spectrum.csv")
    print("  -> Timestamp Metrics File   : co60_final_metrics.csv")
except Exception as shutdown_error:
    print(f"❌ Error during file closeout saving blocks: {shutdown_error}")
print("="*50)
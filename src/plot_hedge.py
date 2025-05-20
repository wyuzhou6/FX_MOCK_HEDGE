import matplotlib.pyplot as plt
import os
import pandas as pd

def visualize_hedging(out, result_dir, label='', hedge_ratio=0.5):
    """
    Visualize hedging strategies' P&L, cumulative P&L, and volatility by year.

    Args:
        out (dict): Dictionary containing results and statistics.
        result_dir (str): Output directory for saving plots.
        label (str): Optional label for plot titles and filenames.
        hedge_ratio (float): The hedge ratio used in the strategies.

    Returns:
        str: The file path to the main line chart image.
    """
    results = out['results']
    partial_hedged_std = out['partial_hedged_std']
    partial_hedged_tc_std = out['partial_hedged_tc_std']
    full_hedged_std = out['full_hedged_std']
    full_hedged_tc_std = out['full_hedged_tc_std']
    unhedged_std = out['unhedged_std']

    plt.figure(figsize=(16, 10))
    dates = [d.strftime('%Y-%m') for d in results['Contract_Date']]
    x = range(len(dates))
    step = max(1, len(x) // 12)

    # ---- 1. Main Chart: Periodic P&L of Each Strategy
    ax1 = plt.subplot(2, 1, 1)
    ax1.plot(x, results['Partial_Hedged'], color='purple', marker='^', markersize=4, alpha=0.8, label=f'Partial Hedged ({hedge_ratio*100:.0f}%, No Cost)')
    ax1.plot(x, results['Partial_Hedged_TC'], color='magenta', marker='v', markersize=4, alpha=0.8, label=f'Partial Hedged ({hedge_ratio*100:.0f}%, With Cost)')
    ax1.plot(x, results['Full_Hedged'], color='red', marker='o', markersize=4, alpha=0.8, label='Full Hedged (No Cost)')
    ax1.plot(x, results['Full_Hedged_TC'], color='orange', marker='x', markersize=4, alpha=0.8, label='Full Hedged (With Cost)')
    ax1.plot(x, results['Unhedged'], color='blue', marker='s', markersize=4, alpha=0.8, label='Unhedged')
    title_txt = (
        f"{label} Hedging Performance ({hedge_ratio*100:.0f}% Hedged) | Std: "
        f"Partial={partial_hedged_std:,.0f}, "
        f"Partial_TC={partial_hedged_tc_std:,.0f}, "
        f"Full={full_hedged_std:,.0f}, "
        f"Full_TC={full_hedged_tc_std:,.0f}, "
        f"Unhedged={unhedged_std:,.0f}"
    )
    ax1.set_title(title_txt, fontsize=14)
    ax1.set_ylabel("P&L (CAD)", fontsize=12)
    ax1.axhline(0, color='gray', linestyle=':', alpha=0.5)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    plt.sca(ax1)
    plt.xticks(x[::step], [dates[i] for i in range(0, len(dates), step)], rotation=45)

    # ---- 2. Cumulative P&L Chart
    results['Cum_Partial_Hedged'] = results['Partial_Hedged'].cumsum()
    results['Cum_Partial_Hedged_TC'] = results['Partial_Hedged_TC'].cumsum()
    results['Cum_Full_Hedged'] = results['Full_Hedged'].cumsum()
    results['Cum_Full_Hedged_TC'] = results['Full_Hedged_TC'].cumsum()
    results['Cum_Unhedged'] = results['Unhedged'].cumsum()
    ax2 = plt.subplot(2, 1, 2)
    ax2.plot(x, results['Cum_Partial_Hedged'], color='purple', marker='^', markersize=4, alpha=0.8, label=f'Cumulative Partial Hedged ({hedge_ratio*100:.0f}%, No Cost)')
    ax2.plot(x, results['Cum_Partial_Hedged_TC'], color='magenta', marker='v', markersize=4, alpha=0.8, label=f'Cumulative Partial Hedged ({hedge_ratio*100:.0f}%, With Cost)')
    ax2.plot(x, results['Cum_Full_Hedged'], color='red', marker='o', markersize=4, alpha=0.8, label='Cumulative Full Hedged (No Cost)')
    ax2.plot(x, results['Cum_Full_Hedged_TC'], color='orange', marker='x', markersize=4, alpha=0.8, label='Cumulative Full Hedged (With Cost)')
    ax2.plot(x, results['Cum_Unhedged'], color='blue', marker='s', markersize=4, alpha=0.8, label='Cumulative Unhedged')
    ax2.set_title("Cumulative P&L", fontsize=14)
    ax2.set_ylabel("Cumulative P&L (CAD)", fontsize=12)
    ax2.set_xlabel("Contract Cycle", fontsize=12)
    ax2.axhline(0, color='gray', linestyle=':', alpha=0.5)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left')
    plt.sca(ax2)
    plt.xticks(x[::step], [dates[i] for i in range(0, len(dates), step)], rotation=45)

    plt.tight_layout()
    os.makedirs(result_dir, exist_ok=True)
    output_path = os.path.join(result_dir, f'hedging_line_chart_{label}.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    # ---- 3. Annual Volatility Bar Chart
    results['Year'] = pd.to_datetime(results['Contract_Date']).dt.year
    df_std = results.dropna(subset=['Partial_Hedged', 'Partial_Hedged_TC', 'Full_Hedged', 'Full_Hedged_TC', 'Unhedged'])
    annual_std = df_std.groupby('Year')[['Partial_Hedged', 'Partial_Hedged_TC', 'Full_Hedged', 'Full_Hedged_TC', 'Unhedged']].std().rename(
        columns={
            'Partial_Hedged': f'Partial Hedged Std ({hedge_ratio*100:.0f}%, No Cost)',
            'Partial_Hedged_TC': f'Partial Hedged Std ({hedge_ratio*100:.0f}%, With Cost)',
            'Full_Hedged': 'Full Hedged Std (No Cost)',
            'Full_Hedged_TC': 'Full Hedged Std (With Cost)',
            'Unhedged': 'Unhedged Std'
        }
    )
    bar_width = 0.15
    years = annual_std.index.astype(str)
    x = range(len(years))
    plt.figure(figsize=(16, 6))
    plt.bar([i - 2*bar_width for i in x], annual_std[f'Partial Hedged Std ({hedge_ratio*100:.0f}%, No Cost)'], width=bar_width, color='purple', label=f'Partial Hedged Std ({hedge_ratio*100:.0f}%, No Cost)')
    plt.bar([i - bar_width for i in x], annual_std[f'Partial Hedged Std ({hedge_ratio*100:.0f}%, With Cost)'], width=bar_width, color='magenta', label=f'Partial Hedged Std ({hedge_ratio*100:.0f}%, With Cost)')
    plt.bar(x, annual_std['Full Hedged Std (No Cost)'], width=bar_width, color='red', label='Full Hedged Std (No Cost)')
    plt.bar([i + bar_width for i in x], annual_std['Full Hedged Std (With Cost)'], width=bar_width, color='orange', label='Full Hedged Std (With Cost)')
    plt.bar([i + 2*bar_width for i in x], annual_std['Unhedged Std'], width=bar_width, color='blue', label='Unhedged Std')
    plt.xticks(list(x), years, rotation=45)
    plt.ylabel('Yearly P&L Std (CAD)')
    plt.title(f'Annual P&L Volatility (Std) by Strategy {label} ({hedge_ratio*100:.0f}% Hedged)')
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    output_path_bar = os.path.join(result_dir, f'annual_std_bar_{label}.png')
    plt.savefig(output_path_bar, dpi=300, bbox_inches='tight')
    plt.close()

    # ---- 4. Annual Volatility Trend Line Chart
    plt.figure(figsize=(10, 5))
    plt.plot(annual_std.index, annual_std[f'Partial Hedged Std ({hedge_ratio*100:.0f}%, No Cost)'], marker='^', color='purple', label=f'Partial Hedged ({hedge_ratio*100:.0f}%, No Cost)')
    plt.plot(annual_std.index, annual_std[f'Partial Hedged Std ({hedge_ratio*100:.0f}%, With Cost)'], marker='v', color='magenta', label=f'Partial Hedged ({hedge_ratio*100:.0f}%, With Cost)')
    plt.plot(annual_std.index, annual_std['Full Hedged Std (No Cost)'], marker='o', color='red', label='Full Hedged (No Cost)')
    plt.plot(annual_std.index, annual_std['Full Hedged Std (With Cost)'], marker='x', color='orange', label='Full Hedged (With Cost)')
    plt.plot(annual_std.index, annual_std['Unhedged Std'], marker='s', color='blue', label='Unhedged')
    plt.title(f'Annual P&L Std Trend {label} ({hedge_ratio*100:.0f}% Hedged)')
    plt.xlabel('Year')
    plt.ylabel('Yearly P&L Std (CAD)')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(result_dir, f'annual_std_line_{label}.png'), dpi=300, bbox_inches='tight')
    plt.close()

    return output_path

import matplotlib.pyplot as plt
import os
import pandas as pd

def visualize_hedging(out, result_dir, label=''):
    results = out['results']
    hedged_std = out['hedged_std']
    unhedged_std = out['unhedged_std']
    hedged_tc_std = out.get('hedged_tc_std', None)

    plt.figure(figsize=(16, 8))
    dates = [d.strftime('%Y-%m') for d in results['Contract_Date']]
    x = range(len(dates))
    step = max(1, len(x) // 12)

    # ---- 1. 主图：每期P&L
    ax1 = plt.subplot(2, 1, 1)
    ax1.plot(x, results['Partial_Hedged'], color='red', marker='o', markersize=4, alpha=0.8, label='Hedged P&L (No Cost)')
    ax1.plot(x, results['Hedged_TC'], color='orange', marker='x', markersize=4, alpha=0.8, label='Hedged P&L (With Cost)')
    ax1.plot(x, results['Unhedged'], color='blue', marker='s', markersize=4, alpha=0.8, label='Unhedged P&L')
    title_txt = (
        f"{label} Hedging Performance | Std: "
        f"Hedged={hedged_std:,.0f}, "
        f"Hedged_TC={hedged_tc_std:,.0f}, "
        f"Unhedged={unhedged_std:,.0f}"
    )
    ax1.set_title(title_txt, fontsize=14)
    ax1.set_ylabel("P&L (CAD)", fontsize=12)
    ax1.axhline(0, color='gray', linestyle=':', alpha=0.5)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    plt.sca(ax1)
    plt.xticks(x[::step], [dates[i] for i in range(0, len(dates), step)], rotation=45)

    # ---- 2. 累计盈亏
    ax2 = plt.subplot(2, 1, 2)
    results['Cum_Hedged'] = results['Partial_Hedged'].cumsum()
    results['Cum_Hedged_TC'] = results['Hedged_TC'].cumsum()
    results['Cum_Unhedged'] = results['Unhedged'].cumsum()
    ax2.plot(x, results['Cum_Hedged'], color='red', marker='o', markersize=4, alpha=0.8, label='Cumulative Hedged (No Cost)')
    ax2.plot(x, results['Cum_Hedged_TC'], color='orange', marker='x', markersize=4, alpha=0.8, label='Cumulative Hedged (With Cost)')
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

    # ---- 3. 年度波动率bar图
    # 统计年度波动率
    results['Year'] = pd.to_datetime(results['Contract_Date']).dt.year
    df_std = results.dropna(subset=['Partial_Hedged', 'Hedged_TC', 'Unhedged'])
    annual_std = df_std.groupby('Year')[['Partial_Hedged', 'Hedged_TC', 'Unhedged']].std().rename(
        columns={
            'Partial_Hedged': 'Hedged Std (No Cost)',
            'Hedged_TC': 'Hedged Std (With Cost)',
            'Unhedged': 'Unhedged Std'
        }
    )
    bar_width = 0.25
    years = annual_std.index.astype(str)
    x = range(len(years))
    plt.figure(figsize=(14, 6))
    plt.bar([i - bar_width for i in x], annual_std['Hedged Std (No Cost)'], width=bar_width, color='red', label='Hedged Std (No Cost)')
    plt.bar(x, annual_std['Hedged Std (With Cost)'], width=bar_width, color='orange', label='Hedged Std (With Cost)')
    plt.bar([i + bar_width for i in x], annual_std['Unhedged Std'], width=bar_width, color='blue', label='Unhedged Std')
    plt.xticks(list(x), years, rotation=45)
    plt.ylabel('Yearly P&L Std (CAD)')
    plt.title(f'Annual P&L Volatility (Std) by Strategy {label}')
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    output_path_bar = os.path.join(result_dir, f'annual_std_bar_{label}.png')
    plt.savefig(output_path_bar, dpi=300, bbox_inches='tight')
    plt.close()
    plt.figure(figsize=(10, 5))
    plt.plot(annual_std.index, annual_std['Hedged Std (No Cost)'], marker='o', color='red', label='Hedged (No Cost)')
    plt.plot(annual_std.index, annual_std['Hedged Std (With Cost)'], marker='x', color='orange', label='Hedged (With Cost)')
    plt.plot(annual_std.index, annual_std['Unhedged Std'], marker='s', color='blue', label='Unhedged')
    plt.title(f'Annual P&L Std Trend {label}')
    plt.xlabel('Year')
    plt.ylabel('Yearly P&L Std (CAD)')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(result_dir, f'annual_std_line_{label}.png'), dpi=300, bbox_inches='tight')
    plt.close()


    return output_path

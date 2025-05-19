import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from pandas.tseries.offsets import MonthBegin

# === 1. 初始化设置 ===
current_dir = os.path.dirname(os.path.abspath(__file__))
result_dir = os.path.join(current_dir, 'result')
os.makedirs(result_dir, exist_ok=True)
data_path = os.path.join(current_dir, 'data')

# === 2. 数据加载函数 ===
def load_data():
    """ 加载并合并所有数据文件 """
    # 示例文件路径 - 请根据实际文件调整
    df_position = pd.read_csv(os.path.join(data_path, "mock_positions.csv"), parse_dates=["Date"])
    df_fx = pd.read_csv(os.path.join(data_path, "USDCAD.csv"), parse_dates=["Date"])
    df_fwd = pd.read_csv(os.path.join(data_path, "usdcad_forward_rates_with_stats.csv"), parse_dates=["Date"])
    
    # 合并数据
    df = df_position.merge(df_fx, on="Date", how="inner")
    df = df.merge(df_fwd[['Date', 'Forward_3M']], on="Date", how="inner")
    
    # 数据清洗
    df = df.sort_values("Date").reset_index(drop=True)
    df.fillna(method='ffill', inplace=True)
    return df

from pandas.tseries.offsets import MonthBegin

def quarterly_hedging(df):
    """
    对冲逻辑：每月建仓，三个月后最早一个交易日平仓
    """
    # 1. 提取每月的第一条记录作为建仓日
    monthly_data = df.groupby([df['Date'].dt.year, df['Date'].dt.month]).first().reset_index(drop=True)
    monthly_data['Contract_ID'] = range(1, len(monthly_data) + 1)
    all_dates = df['Date'].sort_values().unique()

    # 2. 定义函数：找到三个月后第一个实际交易日
    def get_3m_after_first_trading_date(current_date):
        current_date = pd.to_datetime(current_date)
        # 获取三个月后的年月
        month = current_date.month - 1 + 3  # 3个月后
        year = current_date.year + month // 12
        month = month % 12 + 1
        # 找三个月后的第一个交易日
        next_dates = [
            date for date in all_dates
            if (date.year == year) and (date.month == month)
        ]
        return next_dates[0] if len(next_dates) > 0 else pd.NaT

    monthly_data['Next_3M_Date'] = monthly_data['Date'].apply(get_3m_after_first_trading_date)

    # 3. 合并 End Spot（平仓价）
    next_3m_spots = df[['Date', 'USDCAD', 'USD_Net_Exposure']].rename(columns={
        'Date': 'Next_3M_Date',
        'USDCAD': 'End_Spot',
        'USD_Net_Exposure': 'Exposure'
    })
    results = monthly_data.merge(next_3m_spots, on='Next_3M_Date', how='left')

    # 4. 标准化列名
    results = results.rename(columns={
        'Date': 'Contract_Date',
        'USDCAD': 'Start_Spot',
        'Forward_3M': 'Contract_Forward'  # 注意这里改为3M
    })

    # 5. 如果没有 Exposure，则添加默认值
    if 'Exposure' not in results.columns:
        results['Exposure'] = 1_000_000

    # 6. 计算盈亏
    results['Partial_Hedged'] = (results['Contract_Forward'] - results['Start_Spot']) * results['Exposure']
    results['Unhedged'] = (results['End_Spot'] - results['Start_Spot']) * results['Exposure']
    results['Spot_Change'] = results['End_Spot'] - results['Start_Spot']
    hedged_std = results['Partial_Hedged'].std()
    unhedged_std = results['Unhedged'].std()
    print('三个月对冲波动率:', hedged_std)
    print('三个月裸敞口波动率:', unhedged_std)

    output_cols = [
        'Contract_ID', 'Contract_Date', 'Next_3M_Date',
        'Start_Spot', 'End_Spot', 'Contract_Forward',
        'Exposure', 'Partial_Hedged', 'Unhedged', 'Spot_Change'
    ]
    return {
        'results': results[output_cols],
        'hedged_std': hedged_std,
        'unhedged_std': unhedged_std
    }




def visualize_hedging(out, result_dir):
    """
    out: dict，包含'results'（DataFrame）、'hedged_std'、'unhedged_std'
    """
    results = out['results']
    hedged_std = out['hedged_std']
    unhedged_std = out['unhedged_std']
    
    import matplotlib.pyplot as plt
    import os
    
    plt.figure(figsize=(16, 8))
    dates = [d.strftime('%Y-%m') for d in results['Contract_Date']]
    x = range(len(dates))

    # 主图：分月盈亏折线图
    ax1 = plt.subplot(2, 1, 1)
    ax1.plot(x, results['Partial_Hedged'], 'r-', marker='o', markersize=8, label='Hedged P&L', linewidth=2)
    ax1.plot(x, results['Unhedged'], 'b-', marker='s', markersize=8, label='Unhedged P&L', linewidth=2)
    for i, (h, u) in enumerate(zip(results['Partial_Hedged'], results['Unhedged'])):
        if abs(h) > 0:
            ax1.text(i, h, f"{h:+,.0f}", ha='center', va='bottom', color='r', fontsize=9)
        if abs(u) > 0:
            ax1.text(i, u, f"{u:+,.0f}", ha='center', va='bottom', color='b', fontsize=9)
    # 主标题加上波动率
    title_txt = (
        f"Monthly Hedging Performance\n"
        f"Hedged Std: {hedged_std:,.0f}   Unhedged Std: {unhedged_std:,.0f}"
    )
    ax1.set_title(title_txt, fontsize=14)
    ax1.set_ylabel("P&L (CAD)", fontsize=12)
    ax1.axhline(0, color='gray', linestyle=':', alpha=0.5)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    plt.sca(ax1)
    plt.xticks(x, dates, rotation=45)

    # 累计盈亏子图
    ax2 = plt.subplot(2, 1, 2)
    results['Cum_Hedged'] = results['Partial_Hedged'].cumsum()
    results['Cum_Unhedged'] = results['Unhedged'].cumsum()
    ax2.plot(x, results['Cum_Hedged'], 'r-', marker='o', label='Cumulative Hedged', linewidth=2)
    ax2.plot(x, results['Cum_Unhedged'], 'b-', marker='s', label='Cumulative Unhedged', linewidth=2)
    final_hedged = results['Cum_Hedged'].iloc[-1]
    final_unhedged = results['Cum_Unhedged'].iloc[-1]
    ax2.text(len(x)-1, final_hedged, f"{final_hedged:+,.0f}", ha='left', va='center', color='r')
    ax2.text(len(x)-1, final_unhedged, f"{final_unhedged:+,.0f}", ha='left', va='center', color='b')
    ax2.set_title("Cumulative P&L", fontsize=14)
    ax2.set_ylabel("Cumulative P&L (CAD)", fontsize=12)
    ax2.set_xlabel("Contract Cycle", fontsize=12)
    ax2.axhline(0, color='gray', linestyle=':', alpha=0.5)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left')
    plt.sca(ax2)
    plt.xticks(x, dates, rotation=45)

    plt.tight_layout()
    output_path = os.path.join(result_dir, 'hedging_line_chart.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    # 年度波动率折线图
    # Step 1: 提取年份
    results['Year'] = pd.to_datetime(results['Contract_Date']).dt.year
    df_std = results.dropna(subset=['Partial_Hedged', 'Unhedged'])
    annual_std = df_std.groupby('Year')[['Partial_Hedged', 'Unhedged']].std().rename(
        columns={'Partial_Hedged': 'Hedged Std', 'Unhedged': 'Unhedged Std'}
    )
    # Step 2: 画图
    plt.figure(figsize=(10, 5))
    plt.plot(annual_std.index, annual_std['Hedged Std'], marker='o', label='Hedged Std')
    plt.plot(annual_std.index, annual_std['Unhedged Std'], marker='s', label='Unhedged Std')
    plt.title('Annual P&L Volatility (Std) by Strategy')
    plt.xlabel('Year')
    plt.ylabel('Yearly P&L Std (CAD)')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    output_path_annual = os.path.join(result_dir, 'annual_std_line.png')
    plt.savefig(output_path_annual, dpi=300, bbox_inches='tight')
    plt.close()

        # 年度波动率条形图
    # （确保 annual_std 已经算好，如前面的 annual_std 变量）

    # Bar settings
    bar_width = 0.35
    years = annual_std.index.astype(str)
    x = range(len(years))
    plt.figure(figsize=(12, 6))
    plt.bar([i - bar_width/2 for i in x], annual_std['Hedged Std'], width=bar_width, label='Hedged Std')
    plt.bar([i + bar_width/2 for i in x], annual_std['Unhedged Std'], width=bar_width, label='Unhedged Std')
    plt.xticks(list(x), years, rotation=45)
    plt.ylabel('Yearly P&L Std (CAD)')
    plt.title('Annual P&L Volatility (Std) by Strategy')
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()

    output_path_bar = os.path.join(result_dir, 'annual_std_bar.png')
    plt.savefig(output_path_bar, dpi=300, bbox_inches='tight')
    plt.close()

    
    return output_path


# === 5. 主执行流程 ===
if __name__ == "__main__":
    # 加载数据
    df = load_data()

    # 计算对冲结果（默认100%对冲）
    out = quarterly_hedging(df)
  # ← 改这里，接收字典

    # 保存结果表
    output_path_results = os.path.join(result_dir, 'results.csv')
    out['results'].to_csv(output_path_results, index=False)  # ← 注意加 index=False

    # 可视化并保存（传递整个字典，已自动显示波动率）
    output_path = visualize_hedging(out, result_dir=result_dir)


    # 打印关键结果
    print("\n=== 对冲策略结果 ===")
    print(out['results'].round(2))  # ← 只打印表部分
    print(f"\n可视化结果已保存至: {output_path}")

    # 波动率也可以单独再打印一遍（虽然前面print过，但汇报可以再强调一次）
    print(f"\n对冲后波动率: {out['hedged_std']:,.2f}")
    print(f"裸敞口波动率: {out['unhedged_std']:,.2f}")
    results = out['results']

    # 找出对冲和裸敞口最大亏损/盈利的月份
    max_loss_hedged = results.loc[results['Partial_Hedged'].idxmin()]
    max_loss_unhedged = results.loc[results['Unhedged'].idxmin()]
    max_gain_hedged = results.loc[results['Partial_Hedged'].idxmax()]
    max_gain_unhedged = results.loc[results['Unhedged'].idxmax()]

    print("\n=== 最大亏损月份（对冲） ===")
    print(max_loss_hedged[['Contract_Date', 'Partial_Hedged', 'Unhedged']])
    print("\n=== 最大亏损月份（裸敞口） ===")
    print(max_loss_unhedged[['Contract_Date', 'Partial_Hedged', 'Unhedged']])

    print("\n=== 最大盈利月份（对冲） ===")
    print(max_gain_hedged[['Contract_Date', 'Partial_Hedged', 'Unhedged']])
    print("\n=== 最大盈利月份（裸敞口） ===")
    print(max_gain_unhedged[['Contract_Date', 'Partial_Hedged', 'Unhedged']])


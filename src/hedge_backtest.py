import pandas as pd

def get_next_trading_date(current_date, all_dates, months_offset=1):
    current_date = pd.to_datetime(current_date)
    month = current_date.month - 1 + months_offset
    year = current_date.year + month // 12
    month = month % 12 + 1
    next_dates = [
        date for date in all_dates
        if (date.year == year) and (date.month == month)
    ]
    return next_dates[0] if len(next_dates) > 0 else pd.NaT

def hedging_backtest(
    df,
    cycle_months=1,
    forward_col='Forward_1M',
    exposure_col='USD_Net_Exposure',
    notional_default=1_000_000,
    transaction_fee_rate=0.0002,  # 0.02% 手续费
    bid_ask_spread=0.0001         # 1 pip 点差
):
    monthly_data = df.groupby([df['Date'].dt.year, df['Date'].dt.month]).first().reset_index(drop=True)
    monthly_data['Contract_ID'] = range(1, len(monthly_data) + 1)
    all_dates = df['Date'].sort_values().unique()
    monthly_data['Close_Date'] = monthly_data['Date'].apply(lambda d: get_next_trading_date(d, all_dates, months_offset=cycle_months))
    next_spots = df[['Date', 'USDCAD', exposure_col]].rename(columns={
        'Date': 'Close_Date',
        'USDCAD': 'End_Spot',
        exposure_col: 'Exposure'
    })
    results = monthly_data.merge(next_spots, on='Close_Date', how='left')
    results = results.rename(columns={
        'Date': 'Contract_Date',
        'USDCAD': 'Start_Spot',
        forward_col: 'Contract_Forward'
    })
    if 'Exposure' not in results.columns:
        results['Exposure'] = notional_default

    # ====== 新增部分：加交易成本 ======
    # 1. 对冲远期价减去点差（模拟真实买入价比理论差一点）
    results['Contract_Forward_TC'] = results['Contract_Forward'] - bid_ask_spread

    # 2. 计算手续费（名义金额 × 手续费率，绝对值保证正数）
    results['Fee'] = abs(results['Exposure']) * transaction_fee_rate

    # 3. 计算含交易成本的对冲盈亏
    results['Hedged_TC'] = (results['Contract_Forward_TC'] - results['Start_Spot']) * results['Exposure'] - results['Fee']

    # 原始对冲和裸敞口盈亏
    results['Partial_Hedged'] = (results['Contract_Forward'] - results['Start_Spot']) * results['Exposure']
    results['Unhedged'] = (results['End_Spot'] - results['Start_Spot']) * results['Exposure']
    results['Spot_Change'] = results['End_Spot'] - results['Start_Spot']

    # 波动率
    hedged_std = results['Partial_Hedged'].std()
    unhedged_std = results['Unhedged'].std()
    hedged_tc_std = results['Hedged_TC'].std()

    # 返回值和输出列（新增了含成本的对冲P&L）
    output_cols = [
        'Contract_ID', 'Contract_Date', 'Close_Date',
        'Start_Spot', 'End_Spot', 'Contract_Forward', 'Contract_Forward_TC',
        'Exposure', 'Fee', 'Partial_Hedged', 'Hedged_TC', 'Unhedged', 'Spot_Change'
    ]
    return {
        'results': results[output_cols],
        'hedged_std': hedged_std,
        'unhedged_std': unhedged_std,
        'hedged_tc_std': hedged_tc_std    # 含交易成本的对冲波动率
    }

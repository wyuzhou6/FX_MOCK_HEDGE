import pandas as pd

def get_next_trading_date(current_date, all_dates, months_offset=1):
    """
    Find the first available trading date in all_dates that is 'months_offset' months after current_date.
    Returns pd.NaT if no such date exists.
    """
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
    transaction_fee_rate=0.0002,  # 0.02% transaction fee
    bid_ask_spread=0.0001,       # 1 pip bid/ask spread
    hedge_ratio=0.5              # Default 50% hedge ratio
):
    """
    Perform FX hedging backtest with different hedge ratios and transaction cost settings.

    Args:
        df (pd.DataFrame): Data containing Date, spot, forward, exposure, etc.
        cycle_months (int): Hedge cycle length in months.
        forward_col (str): Forward rate column name.
        exposure_col (str): Exposure column name.
        notional_default (float): Default notional value if no exposure is provided.
        transaction_fee_rate (float): Transaction fee rate (proportional).
        bid_ask_spread (float): Bid-ask spread applied to forward rate.
        hedge_ratio (float): Hedge ratio (0-1).

    Returns:
        dict: Contains result DataFrame and P&L standard deviations.
    """
    # Validate hedge ratio
    if not 0 <= hedge_ratio <= 1:
        raise ValueError("hedge_ratio must be between 0 and 1")

    # Get first record of each month as contract opening
    monthly_data = df.groupby([df['Date'].dt.year, df['Date'].dt.month]).first().reset_index(drop=True)
    monthly_data['Contract_ID'] = range(1, len(monthly_data) + 1)

    # All unique trading dates
    all_dates = df['Date'].sort_values().unique()
    # Find the next close date for each contract
    monthly_data['Close_Date'] = monthly_data['Date'].apply(
        lambda d: get_next_trading_date(d, all_dates, months_offset=cycle_months)
    )

    # Join closing spot/exposure
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
    # Use default notional if no exposure provided
    if 'Exposure' not in results.columns:
        results['Exposure'] = notional_default

    # ====== Transaction Cost Calculations ======
    # 1. Apply bid/ask spread to the forward rate (simulate real purchase price being slightly worse)
    results['Contract_Forward_TC'] = results['Contract_Forward'] - bid_ask_spread

    # 2. Calculate transaction fee (only for the hedged portion)
    results['Hedged_Exposure'] = results['Exposure'] * hedge_ratio
    results['Fee'] = abs(results['Hedged_Exposure']) * transaction_fee_rate

    # ====== P&L Calculations ======
    # 1. Partial hedge P&L (excluding transaction costs)
    #   - Hedged P&L = (Forward - Start Spot) * Hedged Exposure
    #   - Unhedged P&L = (End Spot - Start Spot) * Unhedged Exposure
    results['Partial_Hedged'] = (
        (results['Contract_Forward'] - results['Start_Spot']) * results['Hedged_Exposure'] +
        (results['End_Spot'] - results['Start_Spot']) * results['Exposure'] * (1 - hedge_ratio)
    )

    # 2. Partial hedge P&L (including transaction costs)
    results['Partial_Hedged_TC'] = (
        (results['Contract_Forward_TC'] - results['Start_Spot']) * results['Hedged_Exposure'] +
        (results['End_Spot'] - results['Start_Spot']) * results['Exposure'] * (1 - hedge_ratio) -
        results['Fee']
    )

    # 3. Full hedge P&L (original Partial_Hedged is now named Full_Hedged)
    results['Full_Hedged'] = (results['Contract_Forward'] - results['Start_Spot']) * results['Exposure']
    results['Full_Hedged_TC'] = (
        (results['Contract_Forward_TC'] - results['Start_Spot']) * results['Exposure'] -
        abs(results['Exposure']) * transaction_fee_rate
    )

    # 4. Unhedged P&L
    results['Unhedged'] = (results['End_Spot'] - results['Start_Spot']) * results['Exposure']
    results['Spot_Change'] = results['End_Spot'] - results['Start_Spot']

    # ====== Standard Deviation (Volatility) Calculation ======
    partial_hedged_std = results['Partial_Hedged'].std()
    partial_hedged_tc_std = results['Partial_Hedged_TC'].std()
    full_hedged_std = results['Full_Hedged'].std()
    full_hedged_tc_std = results['Full_Hedged_TC'].std()
    unhedged_std = results['Unhedged'].std()

    # ====== Output Columns ======
    output_cols = [
        'Contract_ID', 'Contract_Date', 'Close_Date',
        'Start_Spot', 'End_Spot', 'Contract_Forward', 'Contract_Forward_TC',
        'Exposure', 'Hedged_Exposure', 'Fee',
        'Partial_Hedged', 'Partial_Hedged_TC',
        'Full_Hedged', 'Full_Hedged_TC', 'Unhedged', 'Spot_Change'
    ]
    return {
        'results': results[output_cols],
        'partial_hedged_std': partial_hedged_std,
        'partial_hedged_tc_std': partial_hedged_tc_std,
        'full_hedged_std': full_hedged_std,
        'full_hedged_tc_std': full_hedged_tc_std,
        'unhedged_std': unhedged_std
    }

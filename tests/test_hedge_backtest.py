import pytest
from src.data_loader import load_data
from src.hedge_backtest import hedging_backtest

def test_hedging_backtest_basic():
    df = load_data(forward_col='Forward_1M')
    out = hedging_backtest(df, cycle_months=1, forward_col='Forward_1M')

    # Check output structure and type
    assert 'results' in out
    res = out['results']
    assert not res.empty

    # Check key columns exist and are numeric
    for col in ['Partial_Hedged', 'Partial_Hedged_TC', 'Full_Hedged', 'Full_Hedged_TC', 'Unhedged']:
        assert col in res.columns


    # Check volatilities are non-negative
    assert out['partial_hedged_std'] >= 0
    assert out['partial_hedged_tc_std'] >= 0
    assert out['unhedged_std'] >= 0

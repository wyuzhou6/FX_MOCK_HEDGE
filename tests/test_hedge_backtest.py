import pytest
from src.data_loader import load_data
from src.hedge_backtest import hedging_backtest

def test_hedging_backtest_basic():
    df = load_data(forward_col='Forward_1M')
    out = hedging_backtest(df, cycle_months=1, forward_col='Forward_1M')
    # 检查输出结构和类型
    assert 'results' in out
    res = out['results']
    assert not res.empty
    # 检查关键列
    for col in ['Partial_Hedged', 'Hedged_TC', 'Unhedged']:
        assert col in res.columns
        assert res[col].dtype.kind in 'fi'  # float/int
    # 检查波动率为非负数
    assert out['hedged_std'] >= 0
    assert out['hedged_tc_std'] >= 0
    assert out['unhedged_std'] >= 0

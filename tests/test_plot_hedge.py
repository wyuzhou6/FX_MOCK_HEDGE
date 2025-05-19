import pytest
from src.data_loader import load_data
from src.hedge_backtest import hedging_backtest
from src.plot_hedge import visualize_hedging
import os

def test_visualize_hedging_runs(tmp_path):
    df = load_data(forward_col='Forward_1M')
    out = hedging_backtest(df, cycle_months=1, forward_col='Forward_1M')
    output_path = visualize_hedging(out, result_dir=tmp_path, label='1M_TEST')
    assert os.path.exists(output_path)
    assert output_path.endswith('.png')

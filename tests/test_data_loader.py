import pytest
from src.data_loader import load_data

def test_load_data_basic():
    df = load_data(forward_col='Forward_1M')
    assert not df.empty
    assert 'Date' in df.columns
    assert df.isnull().sum().sum() == 0   # 没有NaN

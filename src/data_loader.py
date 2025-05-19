import os
import pandas as pd

def get_project_root():
    # 获取 FX_MOCK_HEDGE 这个文件夹的绝对路径
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_data(forward_col='Forward_1M'):
    root = get_project_root()
    data_dir = os.path.join(root, 'data')
    df_position = pd.read_csv(os.path.join(data_dir, "mock_positions.csv"), parse_dates=["Date"])
    df_fx = pd.read_csv(os.path.join(data_dir, "USDCAD.csv"), parse_dates=["Date"])
    df_fwd = pd.read_csv(os.path.join(data_dir, "usdcad_forward_rates_with_stats.csv"), parse_dates=["Date"])
    df = df_position.merge(df_fx, on="Date", how="inner")
    df = df.merge(df_fwd[['Date', forward_col]], on="Date", how="inner")
    df = df.sort_values("Date").reset_index(drop=True)
    df.ffill(inplace=True)  # 新写法
    return df

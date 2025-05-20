import os
import pandas as pd

def get_project_root():
    # Get the absolute path to the FX_MOCK_HEDGE project folder
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_data(forward_col='Forward_1M'):
    """
    Load and merge mock position, FX spot, and forward rate data.
    Args:
        forward_col (str): The column name for the desired forward rate.
    Returns:
        pd.DataFrame: Merged and sorted DataFrame with all relevant columns.
    """
    root = get_project_root()
    data_dir = os.path.join(root, 'data')
    # Load mock position data
    df_position = pd.read_csv(os.path.join(data_dir, "mock_positions.csv"), parse_dates=["Date"])
    # Load FX spot rate data
    df_fx = pd.read_csv(os.path.join(data_dir, "USDCAD.csv"), parse_dates=["Date"])
    # Load forward rate data
    df_fwd = pd.read_csv(os.path.join(data_dir, "usdcad_forward_rates_with_stats.csv"), parse_dates=["Date"])
    # Merge all data on "Date"
    df = df_position.merge(df_fx, on="Date", how="inner")
    df = df.merge(df_fwd[['Date', forward_col]], on="Date", how="inner")
    # Sort by date and reset index
    df = df.sort_values("Date").reset_index(drop=True)
    # Forward-fill any missing values
    df.ffill(inplace=True)
    return df

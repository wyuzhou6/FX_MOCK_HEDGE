from data_loader import load_data
from hedge_backtest import hedging_backtest
from plot_hedge import visualize_hedging
import os

def get_project_root():
    # Get the absolute path to the project root directory
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    project_root = get_project_root()
    result_dir = os.path.join(project_root, 'result')

    # Define the backtest cycles and corresponding forward rate columns
    strategies = [
        {'label': '1M', 'cycle': 1, 'forward_col': 'Forward_1M'},
        {'label': '3M', 'cycle': 3, 'forward_col': 'Forward_3M'},
        # {'label': '6M', 'cycle': 6, 'forward_col': 'Forward_6M'},  
      
    ]

    for strat in strategies:
        print(f"Backtesting {strat['label']} hedging strategy...")
        df = load_data(forward_col=strat['forward_col'])
        out = hedging_backtest(df, cycle_months=strat['cycle'], forward_col=strat['forward_col'])
        out_path = visualize_hedging(out, result_dir=result_dir, label=strat['label'])
        print(f"{strat['label']} hedging complete. Chart saved to {out_path}")
        # Save the complete results table as CSV
        csv_path = os.path.join(result_dir, f'hedge_backtest_{strat['label']}_full.csv')
        out['results'].to_csv(csv_path, index=False)
        print(f"{strat['label']} detailed results table saved to {csv_path}")

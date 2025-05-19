from data_loader import load_data
from hedge_backtest import hedging_backtest
from plot_hedge import visualize_hedging
import os

def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    project_root = get_project_root()
    result_dir = os.path.join(project_root, 'result')

    # 定义你要跑的周期和forward列
    strategies = [
        {'label': '1M', 'cycle': 1, 'forward_col': 'Forward_1M'},
        {'label': '3M', 'cycle': 3, 'forward_col': 'Forward_3M'},
        #{'label': '6M', 'cycle': 6, 'forward_col': 'Forward_6M'},  # 假设你有6M远期数据
        # 以后可以扩展更多周期...
    ]

    for strat in strategies:
        print(f"回测{strat['label']}对冲策略...")
        df = load_data(forward_col=strat['forward_col'])
        out = hedging_backtest(df, cycle_months=strat['cycle'], forward_col=strat['forward_col'])
        out_path = visualize_hedging(out, result_dir=result_dir, label=strat['label'])
        print(f"{strat['label']}对冲完成，图表已保存至 {out_path}")
        # 输出完整大表
        csv_path = os.path.join(result_dir, f'hedge_backtest_{strat["label"]}_full.csv')
        out['results'].to_csv(csv_path, index=False)
        print(f"{strat['label']}详细结果表已保存至 {csv_path}")

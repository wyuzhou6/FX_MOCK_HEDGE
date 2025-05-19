#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
高级对冲策略模块：实现更复杂的FX对冲策略
"""

import numpy as np
import pandas as pd

def calculate_mixed_hedge_strategy(df, exposure_column, forward_ratio=0.6, option_ratio=0.2,
                                  initial_forward=None, option_strike=None, option_premium_pct=0.01):
    """
    计算混合工具对冲策略（远期+期权+不对冲）
    
    Args:
        df: 数据框
        exposure_column: 敞口列名
        forward_ratio: 远期合约对冲比例 (0-1)
        option_ratio: 期权对冲比例 (0-1)
        initial_forward: 初始远期汇率
        option_strike: 期权执行价，若为None则使用initial_forward
        option_premium_pct: 期权费率（按名义金额的百分比）
    
    Returns:
        DataFrame: 添加了混合工具对冲策略计算结果的数据框
    """
    if initial_forward is None:
        initial_forward = df['Forward_3M'].iloc[0]
    
    if option_strike is None:
        option_strike = initial_forward
    
    # 计算未对冲比例
    unhedged_ratio = 1 - forward_ratio - option_ratio
    
    # 计算期权成本
    option_premium = df[exposure_column] * option_ratio * option_premium_pct
    
    # 计算混合策略价值
    # 远期部分 + 期权部分（使用看跌期权保护） + 未对冲部分 - 期权费
    df['Mixed_Strategy_Value'] = (
        # 远期部分锁定汇率
        df[exposure_column] * forward_ratio * initial_forward +
        # 期权部分：取最大值(执行价格, 实际汇率)
        df[exposure_column] * option_ratio * np.maximum(option_strike, df['CADUSD']) -
        # 期权费用
        option_premium.iloc[0] +
        # 未对冲部分
        df[exposure_column] * unhedged_ratio * df['CADUSD']
    )
    
    df['Mixed_Strategy_Daily_PnL'] = df['Mixed_Strategy_Value'].diff()
    df['Mixed_Strategy_Cumulative_PnL'] = df['Mixed_Strategy_Daily_PnL'].fillna(0).cumsum()
    
    return df

def calculate_adaptive_hedge_strategy(df, exposure_column, vol_window=20, threshold_high=0.1, 
                                     threshold_low=0.05, max_ratio=0.9, min_ratio=0.3):
    """
    计算自适应对冲策略，根据波动率趋势调整
    
    Args:
        df: 数据框
        exposure_column: 敞口列名
        vol_window: 波动率计算窗口
        threshold_high: 高波动率阈值
        threshold_low: 低波动率阈值
        max_ratio: 最大对冲比例
        min_ratio: 最小对冲比例
    
    Returns:
        DataFrame: 添加了自适应对冲策略计算结果的数据框
    """
    # 计算滚动波动率
    df['Rolling_Volatility'] = df['CADUSD'].pct_change().rolling(window=vol_window).std() * np.sqrt(252)
    
    # 计算波动率变化趋势
    df['Vol_Change'] = df['Rolling_Volatility'].diff(5)
    
    # 根据波动率水平和趋势设置对冲比例
    df['Adaptive_Hedge_Ratio'] = 0.5  # 基准对冲比例
    
    # 高波动率环境 - 增加对冲
    df.loc[df['Rolling_Volatility'] > threshold_high, 'Adaptive_Hedge_Ratio'] = 0.7
    
    # 低波动率环境 - 减少对冲
    df.loc[df['Rolling_Volatility'] < threshold_low, 'Adaptive_Hedge_Ratio'] = 0.4
    
    # 波动率上升趋势 - 进一步增加对冲
    df.loc[(df['Vol_Change'] > 0.01) & (df['Rolling_Volatility'] > threshold_low), 
           'Adaptive_Hedge_Ratio'] = 0.8
    
    # 波动率下降趋势 - 进一步减少对冲
    df.loc[(df['Vol_Change'] < -0.01) & (df['Rolling_Volatility'] < threshold_high),
           'Adaptive_Hedge_Ratio'] = 0.3
    
    # 确保对冲比例在设定范围内
    df['Adaptive_Hedge_Ratio'] = df['Adaptive_Hedge_Ratio'].clip(min_ratio, max_ratio)
    
    # 创建策略价值计算
    rebalance_condition = (df['Adaptive_Hedge_Ratio'].diff().abs() >= 0.1) | (df.index == 0)
    df['adaptive_rebalance_group'] = rebalance_condition.cumsum()
    
    # 对每个再平衡区间，使用该区间的第一个远期汇率
    df['adaptive_hedge_rate'] = df.groupby('adaptive_rebalance_group')['Forward_3M'].transform('first')
    
    # 计算对冲和非对冲部分
    df['Adaptive_Hedged_Value'] = (
        df[exposure_column] * df['Adaptive_Hedge_Ratio'] * df['adaptive_hedge_rate'] +
        df[exposure_column] * (1 - df['Adaptive_Hedge_Ratio']) * df['CADUSD']
    )
    
    df['Adaptive_Hedged_Daily_PnL'] = df['Adaptive_Hedged_Value'].diff()
    df['Adaptive_Hedged_Cumulative_PnL'] = df['Adaptive_Hedged_Daily_PnL'].fillna(0).cumsum()
    
    return df

def calculate_tactical_hedge_strategy(df, exposure_column, ma_fast=5, ma_slow=20):
    """
    计算策略性对冲策略，根据汇率趋势信号调整
    
    Args:
        df: 数据框
        exposure_column: 敞口列名
        ma_fast: 快速移动均线窗口
        ma_slow: 慢速移动均线窗口
    
    Returns:
        DataFrame: 添加了策略性对冲策略计算结果的数据框
    """
    # 计算移动均线
    df['MA_Fast'] = df['CADUSD'].rolling(window=ma_fast).mean()
    df['MA_Slow'] = df['CADUSD'].rolling(window=ma_slow).mean()
    
    # 计算趋势信号
    df['Trend_Signal'] = np.where(df['MA_Fast'] > df['MA_Slow'], 1, -1)  # 1=上升趋势，-1=下降趋势
    
    # 基于趋势设置对冲比例
    df['Tactical_Hedge_Ratio'] = 0.5  # 默认对冲比例
    
    # 上升趋势（对国内货币不利）- 增加对冲
    df.loc[df['Trend_Signal'] == 1, 'Tactical_Hedge_Ratio'] = 0.8
    
    # 下降趋势（对国内货币有利）- 减少对冲
    df.loc[df['Trend_Signal'] == -1, 'Tactical_Hedge_Ratio'] = 0.3
    
    # 创建策略价值计算
    rebalance_condition = (df['Tactical_Hedge_Ratio'].diff() != 0) | (df.index == 0)
    df['tactical_rebalance_group'] = rebalance_condition.cumsum()
    
    # 对每个再平衡区间，使用该区间的第一个远期汇率
    df['tactical_hedge_rate'] = df.groupby('tactical_rebalance_group')['Forward_3M'].transform('first')
    
    # 计算对冲和非对冲部分
    df['Tactical_Hedged_Value'] = (
        df[exposure_column] * df['Tactical_Hedge_Ratio'] * df['tactical_hedge_rate'] +
        df[exposure_column] * (1 - df['Tactical_Hedge_Ratio']) * df['CADUSD']
    )
    
    df['Tactical_Hedged_Daily_PnL'] = df['Tactical_Hedged_Value'].diff()
    df['Tactical_Hedged_Cumulative_PnL'] = df['Tactical_Hedged_Daily_PnL'].fillna(0).cumsum()
    
    return df
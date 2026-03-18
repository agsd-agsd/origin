import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

class ModelEvaluator:
    def __init__(self, experiment_name: str, hub_id: int):
        """
        初始化模型评估器
        Args:
            experiment_name: 实验名称，用于创建日志目录
            hub_id: BrokerHub的ID
        """
        self.experiment_name = experiment_name
        self.hub_id = hub_id
        self.base_path = Path(f"result/logs/{experiment_name}/hub_{hub_id}")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # 为每种模型创建单独的日志文件
        self.log_files = {
            "b2e_model": self.base_path / "b2e_model_eval.jsonl",
            "investment_pred": self.base_path / "investment_pred_eval.jsonl",
            "rate_opt": self.base_path / "rate_optimization_eval.jsonl",
            "market_cycle": self.base_path / "market_cycle_eval.jsonl",
            "competitive_pressure": self.base_path / "competitive_pressure_eval.jsonl"
        }
        
        # 初始化每个日志文件
        for file_path in self.log_files.values():
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    pass

    def _append_to_log(self, model_type: str, log_entry: Dict) -> None:
        """将评估结果追加到对应的日志文件"""
        log_entry["hub_id"] = self.hub_id
        with open(self.log_files[model_type], 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def log_b2e_evaluation(self, 
                          iteration: int,
                          predicted_transactions: List[Dict],
                          actual_transactions: List[Tuple[int, int, str, str]]) -> None:
        """记录B2E模型的评估结果"""
        actual_dict = [{"fee": tx[0], "amount": tx[1]} for tx in actual_transactions]
        
        pred_fees = np.array([tx['fee'] for tx in predicted_transactions])
        actual_fees = np.array([tx['fee'] for tx in actual_dict])
        pred_amounts = np.array([tx['amount'] for tx in predicted_transactions])
        actual_amounts = np.array([tx['amount'] for tx in actual_dict])
        
        metrics = {
            "fee_mse": float(mean_squared_error(actual_fees, pred_fees)),
            "fee_mae": float(mean_absolute_error(actual_fees, pred_fees)),
            "fee_r2": float(r2_score(actual_fees, pred_fees)),
            "amount_mse": float(mean_squared_error(actual_amounts, pred_amounts)),
            "amount_mae": float(mean_absolute_error(actual_amounts, pred_amounts)),
            "amount_r2": float(r2_score(actual_amounts, pred_amounts))
        }
        
        log_entry = {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "predictions": [dict(tx) for tx in predicted_transactions],
            "actuals": [{"fee": tx[0], "amount": tx[1]} for tx in actual_transactions],
            "metrics": metrics
        }
        
        self._append_to_log("b2e_model", log_entry)

    def log_investment_prediction(self,
                                iteration: int,
                                predicted_investment: float,
                                actual_investment: float,
                                fee_rate: float) -> None:
        """记录投资预测模型的评估结果"""
        prediction_error = predicted_investment - actual_investment
        relative_error = prediction_error / (actual_investment + 1e-7)
        
        log_entry = {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "predicted_investment": float(predicted_investment),
            "actual_investment": float(actual_investment),
            "fee_rate": float(fee_rate),
            "absolute_error": float(prediction_error),
            "relative_error": float(relative_error)
        }
        
        self._append_to_log("investment_pred", log_entry)

    def log_rate_optimization(self,
                            iteration: int,
                            theoretical_optimal_rate: float,
                            market_optimal_rate: float,
                            final_rate: float,
                            actual_revenue: float) -> None:
        """记录费率优化模型的评估结果"""
        log_entry = {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "theoretical_optimal_rate": float(theoretical_optimal_rate),
            "market_optimal_rate": float(market_optimal_rate),
            "final_rate": float(final_rate),
            "actual_revenue": float(actual_revenue)
        }
        
        self._append_to_log("rate_opt", log_entry)

    def log_market_cycle(self,
                        iteration: int,
                        phase: str,
                        trend: str,
                        momentum: float,
                        revenue_change: float) -> None:
        """记录市场周期分析的评估结果"""
        log_entry = {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "trend": trend,
            "momentum": float(momentum),
            "revenue_change": float(revenue_change)
        }
        
        self._append_to_log("market_cycle", log_entry)

    def log_competitive_pressure(self,
                               iteration: int,
                               pressure_value: float,
                               market_share: float,
                               rate_difference: float,
                               position_factor: float) -> None:
        """记录竞争压力评估的结果"""
        log_entry = {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "pressure_value": float(pressure_value),
            "market_share": float(market_share),
            "rate_difference": float(rate_difference),
            "position_factor": float(position_factor)
        }
        
        self._append_to_log("competitive_pressure", log_entry)

    def visualize_b2e_evaluation(self) -> None:
        """可视化B2E模型的评估结果"""
        logs = []
        with open(self.log_files["b2e_model"], 'r') as f:
            for line in f:
                logs.append(json.loads(line))
        
        if not logs:
            print(f"No B2E evaluation data available for hub {self.hub_id}")
            return
        
        plots_dir = self.base_path / "plots" / "b2e_model"
        plots_dir.mkdir(parents=True, exist_ok=True)
        
        # 误差随时间变化图
        self._plot_b2e_errors_over_time(logs, plots_dir)
        
        # 预测vs实际值散点图
        self._plot_b2e_predictions_vs_actuals(logs, plots_dir)
        
        # R²分数随时间变化图
        self._plot_b2e_r2_scores(logs, plots_dir)

    def visualize_investment_prediction(self) -> None:
        """可视化投资预测模型的评估结果"""
        logs = []
        with open(self.log_files["investment_pred"], 'r') as f:
            for line in f:
                logs.append(json.loads(line))
        
        if not logs:
            print(f"No investment prediction data available for hub {self.hub_id}")
            return
        
        plots_dir = self.base_path / "plots" / "investment_pred"
        plots_dir.mkdir(parents=True, exist_ok=True)
        
        # 预测vs实际投资额时间序列图
        plt.figure(figsize=(12, 6))
        iterations = [log['iteration'] for log in logs]
        pred_inv = [log['predicted_investment'] for log in logs]
        actual_inv = [log['actual_investment'] for log in logs]
        
        plt.plot(iterations, pred_inv, label='Predicted', marker='o')
        plt.plot(iterations, actual_inv, label='Actual', marker='s')
        plt.xlabel('Iteration')
        plt.ylabel('Investment Amount')
        plt.title(f'Investment Predictions Over Time (Hub {self.hub_id})')
        plt.legend()
        plt.grid(True)
        plt.savefig(plots_dir / 'investment_over_time.png')
        plt.close()
        
        # 费率-投资额关系图
        plt.figure(figsize=(10, 6))
        fee_rates = [log['fee_rate'] for log in logs]
        plt.scatter(fee_rates, actual_inv, alpha=0.5, label='Actual')
        plt.scatter(fee_rates, pred_inv, alpha=0.5, label='Predicted')
        plt.xlabel('Fee Rate')
        plt.ylabel('Investment Amount')
        plt.title(f'Fee Rate vs Investment (Hub {self.hub_id})')
        plt.legend()
        plt.grid(True)
        plt.savefig(plots_dir / 'fee_rate_vs_investment.png')
        plt.close()

    def visualize_rate_optimization(self) -> None:
        """可视化费率优化模型的评估结果"""
        logs = []
        with open(self.log_files["rate_opt"], 'r') as f:
            for line in f:
                logs.append(json.loads(line))
        
        if not logs:
            print(f"No rate optimization data available for hub {self.hub_id}")
            return
        
        plots_dir = self.base_path / "plots" / "rate_opt"
        plots_dir.mkdir(parents=True, exist_ok=True)
        
        # 不同费率策略对比图
        plt.figure(figsize=(12, 6))
        iterations = [log['iteration'] for log in logs]
        theoretical_rates = [log['theoretical_optimal_rate'] for log in logs]
        market_rates = [log['market_optimal_rate'] for log in logs]
        final_rates = [log['final_rate'] for log in logs]
        
        plt.plot(iterations, theoretical_rates, label='Theoretical Optimal', marker='o')
        plt.plot(iterations, market_rates, label='Market Optimal', marker='s')
        plt.plot(iterations, final_rates, label='Final Rate', marker='^')
        plt.xlabel('Iteration')
        plt.ylabel('Fee Rate')
        plt.title(f'Fee Rate Strategies Comparison (Hub {self.hub_id})')
        plt.legend()
        plt.grid(True)
        plt.savefig(plots_dir / 'rate_strategies.png')
        plt.close()
        
        # 费率与收益关系图
        plt.figure(figsize=(10, 6))
        revenues = [log['actual_revenue'] for log in logs]
        plt.scatter(final_rates, revenues, alpha=0.5)
        plt.xlabel('Final Fee Rate')
        plt.ylabel('Actual Revenue')
        plt.title(f'Fee Rate vs Revenue (Hub {self.hub_id})')
        plt.grid(True)
        plt.savefig(plots_dir / 'rate_vs_revenue.png')
        plt.close()

    def visualize_market_cycle(self) -> None:
        """可视化市场周期分析的评估结果"""
        logs = []
        with open(self.log_files["market_cycle"], 'r') as f:
            for line in f:
                logs.append(json.loads(line))
        
        if not logs:
            print(f"No market cycle data available for hub {self.hub_id}")
            return
        
        plots_dir = self.base_path / "plots" / "market_cycle"
        plots_dir.mkdir(parents=True, exist_ok=True)
        
        # 市场周期和趋势图
        plt.figure(figsize=(15, 8))
        iterations = [log['iteration'] for log in logs]
        phases = [log['phase'] for log in logs]
        momentum = [log['momentum'] for log in logs]
        revenue_changes = [log['revenue_change'] for log in logs]
        
        # 上半部分显示市场阶段
        plt.subplot(2, 1, 1)
        # 修改这里的相关代码
        phase_map = {'growth': 2, 'stable': 1, 'decline': 0, 'initial': 1}  # 添加 'initial' 映射
        try:
            phase_values = [phase_map[p] for p in phases]
            plt.plot(iterations, phase_values, marker='o')
            plt.yticks([0, 1, 2], ['Decline', 'Stable/Initial', 'Growth'])
        except KeyError as e:
            print(f"Unexpected phase value found: {e}")
            # 如果出现了未知的阶段，我们可以用一个默认值
            phase_values = [phase_map.get(p, 1) for p in phases]  # 使用 get 方法，对未知阶段返回默认值 1
            plt.plot(iterations, phase_values, marker='o')
            plt.yticks([0, 1, 2], ['Decline', 'Stable/Initial', 'Growth'])

# 续接之前的代码，完成 visualize_competitive_pressure 方法以及其他辅助方法

    def visualize_competitive_pressure(self) -> None:
        """可视化竞争压力评估的结果"""
        logs = []
        with open(self.log_files["competitive_pressure"], 'r') as f:
            for line in f:
                logs.append(json.loads(line))
        
        if not logs:
            print(f"No competitive pressure data available for hub {self.hub_id}")
            return
        
        plots_dir = self.base_path / "plots" / "competitive_pressure"
        plots_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. 竞争压力和市场份额的时间序列图
        plt.figure(figsize=(12, 6))
        iterations = [log['iteration'] for log in logs]
        pressure = [log['pressure_value'] for log in logs]
        market_share = [log['market_share'] for log in logs]
        
        plt.plot(iterations, pressure, label='Competitive Pressure', marker='o')
        plt.plot(iterations, market_share, label='Market Share', marker='s')
        plt.xlabel('Iteration')
        plt.ylabel('Value')
        plt.title(f'Competitive Pressure and Market Share Over Time (Hub {self.hub_id})')
        plt.legend()
        plt.grid(True)
        plt.savefig(plots_dir / 'pressure_and_share.png')
        plt.close()
        
        # 2. 费率差异和竞争压力的散点图
        plt.figure(figsize=(10, 6))
        rate_differences = [log['rate_difference'] for log in logs]
        
        plt.scatter(rate_differences, pressure, alpha=0.5)
        plt.xlabel('Rate Difference')
        plt.ylabel('Competitive Pressure')
        plt.title(f'Rate Difference vs Competitive Pressure (Hub {self.hub_id})')
        plt.grid(True)
        plt.savefig(plots_dir / 'rate_diff_vs_pressure.png')
        plt.close()
        
        # 3. 市场地位因子的影响图
        plt.figure(figsize=(12, 6))
        position_factors = [log['position_factor'] for log in logs]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 左图：市场地位因子随时间的变化
        ax1.plot(iterations, position_factors, marker='o')
        ax1.set_xlabel('Iteration')
        ax1.set_ylabel('Position Factor')
        ax1.set_title('Market Position Factor Over Time')
        ax1.grid(True)
        
        # 右图：市场地位因子与压力的关系
        ax2.scatter(position_factors, pressure, alpha=0.5)
        ax2.set_xlabel('Position Factor')
        ax2.set_ylabel('Competitive Pressure')
        ax2.set_title('Position Factor vs Pressure')
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig(plots_dir / 'position_factor_analysis.png')
        plt.close()
        
        # 4. 综合热力图
        plt.figure(figsize=(10, 8))
        
        # 创建网格数据
        rate_diff_bins = np.linspace(min(rate_differences), max(rate_differences), 20)
        position_bins = np.linspace(min(position_factors), max(position_factors), 20)
        pressure_grid = np.zeros((19, 19))
        count_grid = np.zeros((19, 19))
        
        for rd, pf, pr in zip(rate_differences, position_factors, pressure):
            i = np.digitize(rd, rate_diff_bins) - 1
            j = np.digitize(pf, position_bins) - 1
            if 0 <= i < 19 and 0 <= j < 19:
                pressure_grid[i, j] += pr
                count_grid[i, j] += 1
        
        # 避免除以零
        mask = count_grid > 0
        pressure_grid[mask] = pressure_grid[mask] / count_grid[mask]
        
        sns.heatmap(pressure_grid.T, 
                   xticklabels=np.round(rate_diff_bins[:-1], 3),
                   yticklabels=np.round(position_bins[:-1], 3),
                   cmap='YlOrRd')
        plt.xlabel('Rate Difference')
        plt.ylabel('Position Factor')
        plt.title(f'Competitive Pressure Heat Map (Hub {self.hub_id})')
        plt.tight_layout()
        plt.savefig(plots_dir / 'pressure_heatmap.png')
        plt.close()

    def _plot_b2e_errors_over_time(self, logs: List[Dict], plots_dir: Path) -> None:
        """辅助方法：绘制B2E模型误差随时间的变化"""
        plt.figure(figsize=(12, 6))
        iterations = [log['iteration'] for log in logs]
        fee_mse = [log['metrics']['fee_mse'] for log in logs]
        amount_mse = [log['metrics']['amount_mse'] for log in logs]
        
        plt.plot(iterations, fee_mse, label='Fee MSE', marker='o')
        plt.plot(iterations, amount_mse, label='Amount MSE', marker='s')
        plt.xlabel('Iteration')
        plt.ylabel('Mean Squared Error')
        plt.title(f'B2E Model Prediction Error Over Time (Hub {self.hub_id})')
        plt.legend()
        plt.grid(True)
        plt.savefig(plots_dir / 'error_over_time.png')
        plt.close()

    def _plot_b2e_predictions_vs_actuals(self, logs: List[Dict], plots_dir: Path) -> None:
        """辅助方法：绘制B2E模型预测值与实际值的对比图"""
        plt.figure(figsize=(15, 6))
        actual_fees = []
        predicted_fees = []
        actual_amounts = []
        predicted_amounts = []

        for log in logs:
            for pred, act in zip(log['predictions'], log['actuals']):
                predicted_fees.append(pred['fee'])
                actual_fees.append(act['fee'])
                predicted_amounts.append(pred['amount'])
                actual_amounts.append(act['amount'])

        # 费用预测散点图
        plt.subplot(1, 2, 1)
        plt.scatter(actual_fees, predicted_fees, alpha=0.5)
        max_fee = max(max(actual_fees), max(predicted_fees))
        min_fee = min(min(actual_fees), min(predicted_fees))
        plt.plot([min_fee, max_fee], [min_fee, max_fee], 'r--', label='Perfect Prediction')
        plt.xlabel('Actual Fee')
        plt.ylabel('Predicted Fee')
        plt.title(f'Fee Predictions vs Actuals (Hub {self.hub_id})')
        plt.legend()

        # 金额预测散点图
        plt.subplot(1, 2, 2)
        plt.scatter(actual_amounts, predicted_amounts, alpha=0.5)
        max_amount = max(max(actual_amounts), max(predicted_amounts))
        min_amount = min(min(actual_amounts), min(predicted_amounts))
        plt.plot([min_amount, max_amount], [min_amount, max_amount], 'r--', label='Perfect Prediction')
        plt.xlabel('Actual Amount')
        plt.ylabel('Predicted Amount')
        plt.title(f'Amount Predictions vs Actuals (Hub {self.hub_id})')
        plt.legend()

        plt.tight_layout()
        plt.savefig(plots_dir / 'predictions_vs_actuals.png')
        plt.close()

    def _plot_b2e_r2_scores(self, logs: List[Dict], plots_dir: Path) -> None:
        """辅助方法：绘制B2E模型R²分数随时间的变化"""
        plt.figure(figsize=(12, 6))
        iterations = [log['iteration'] for log in logs]
        fee_r2 = [log['metrics']['fee_r2'] for log in logs]
        amount_r2 = [log['metrics']['amount_r2'] for log in logs]
        
        plt.plot(iterations, fee_r2, label='Fee R²', marker='o')
        plt.plot(iterations, amount_r2, label='Amount R²', marker='s')
        plt.xlabel('Iteration')
        plt.ylabel('R² Score')
        plt.title(f'B2E Model R² Scores Over Time (Hub {self.hub_id})')
        plt.legend()
        plt.grid(True)
        plt.savefig(plots_dir / 'r2_scores.png')
        plt.close()

    def generate_summary_report(self) -> None:
        """生成评估总结报告"""
        report_path = self.base_path / "evaluation_summary.txt"
        
        with open(report_path, 'w') as f:
            f.write(f"Evaluation Summary for Hub {self.hub_id}\n")
            f.write("=" * 50 + "\n\n")
            
            # B2E模型性能总结
            f.write("B2E Model Performance\n")
            f.write("-" * 20 + "\n")
            try:
                with open(self.log_files["b2e_model"], 'r') as b2e_f:
                    logs = [json.loads(line) for line in b2e_f]
                    if logs:
                        recent_logs = logs[-10:]  # 最近10次迭代
                        avg_fee_mse = np.mean([log['metrics']['fee_mse'] for log in recent_logs])
                        avg_amount_mse = np.mean([log['metrics']['amount_mse'] for log in recent_logs])
                        f.write(f"Average Fee MSE (last 10 iterations): {avg_fee_mse:.4f}\n")
                        f.write(f"Average Amount MSE (last 10 iterations): {avg_amount_mse:.4f}\n")
            except Exception as e:
                f.write(f"Error processing B2E data: {str(e)}\n")
            
            f.write("\n")
            
            # 投资预测性能总结
            f.write("Investment Prediction Performance\n")
            f.write("-" * 20 + "\n")
            try:
                with open(self.log_files["investment_pred"], 'r') as inv_f:
                    logs = [json.loads(line) for line in inv_f]
                    if logs:
                        recent_logs = logs[-10:]
                        avg_rel_error = np.mean([abs(log['relative_error']) for log in recent_logs])
                        f.write(f"Average Relative Error (last 10 iterations): {avg_rel_error:.4f}\n")
            except Exception as e:
                f.write(f"Error processing investment prediction data: {str(e)}\n")
            
            f.write("\n")
            
            # 费率优化性能总结
            f.write("Rate Optimization Performance\n")
            f.write("-" * 20 + "\n")
            try:
                with open(self.log_files["rate_opt"], 'r') as rate_f:
                    logs = [json.loads(line) for line in rate_f]
                    if logs:
                        recent_logs = logs[-10:]
                        avg_revenue = np.mean([log['actual_revenue'] for log in recent_logs])
                        f.write(f"Average Revenue (last 10 iterations): {avg_revenue:.4f}\n")
            except Exception as e:
                f.write(f"Error processing rate optimization data: {str(e)}\n")
            
            f.write("\n")
            
            # 市场周期分析总结
            f.write("Market Cycle Analysis\n")
            f.write("-" * 20 + "\n")
            try:
                with open(self.log_files["market_cycle"], 'r') as cycle_f:
                    logs = [json.loads(line) for line in cycle_f]
                    if logs:
                        recent_logs = logs[-10:]
                        phase_counts = {}
                        for log in recent_logs:
                            phase = log['phase']
                            phase_counts[phase] = phase_counts.get(phase, 0) + 1
                        f.write("Market Phase Distribution (last 10 iterations):\n")
                        for phase, count in phase_counts.items():
                            f.write(f"  {phase}: {count/len(recent_logs)*100:.1f}%\n")
            except Exception as e:
                f.write(f"Error processing market cycle data: {str(e)}\n")
            
            f.write("\n")
            
            # 竞争压力分析总结
            f.write("Competitive Pressure Analysis\n")
            f.write("-" * 20 + "\n")
            try:
                with open(self.log_files["competitive_pressure"], 'r') as pressure_f:
                    logs = [json.loads(line) for line in pressure_f]
                    if logs:
                        recent_logs = logs[-10:]
                        avg_pressure = np.mean([log['pressure_value'] for log in recent_logs])
                        avg_market_share = np.mean([log['market_share'] for log in recent_logs])
                        f.write(f"Average Competitive Pressure (last 10 iterations): {avg_pressure:.4f}\n")
                        f.write(f"Average Market Share (last 10 iterations): {avg_market_share:.4f}\n")
            except Exception as e:
                f.write(f"Error processing competitive pressure data: {str(e)}\n")
import numpy as np
from typing import List, Dict, Tuple
from scipy.optimize import minimize_scalar
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from scipy.optimize import nnls
from src.utils.logger import Logger
import random
import math

class ManagementFeeOptimizer:
    def __init__(self, config: Dict):
        # 基本参数
        self.id = config["params"]["id"]
        self.initial_funds = config["params"]["initial_funds"]
        self.min_fee_rate = config["params"]["min_tax_rate"]
        self.max_fee_rate = config["params"]["max_tax_rate"]
        self.learning_rate = config["params"]["learning_rate"]
        self.logger = Logger.get_logger()
        
        # 当前状态
        self.current_fee_rate = config["params"]["initial_tax_rate"]
        self.current_market_share = 0.0
        
        # 历史数据记录
        self.fee_rate_history = [self.current_fee_rate]
        self.revenue_history = []
        self.market_share_history = []
        self.participation_history = []
        self.fee_investment_pairs = []
        
        # 模型相关
        self.b2e_model = {
            'fee': LinearRegression(),
            'amount': LinearRegression(),
            'scaler': StandardScaler()
        }
        self.scaler = StandardScaler()
        self.history_transaction_data = []
        self.b2e_model_fee = LinearRegression()
        self.b2e_model_amount = LinearRegression()

    def analyze_market_cycle(self) -> Dict:
        """分析市场周期和趋势"""
        if len(self.revenue_history) < 10:
            return {'phase': 'initial', 'trend': 'neutral', 'momentum': 1.0}
        
        recent_revenue = self.revenue_history[-5:]
        long_term_avg = np.mean(self.revenue_history)
        short_term_avg = np.mean(recent_revenue)
        trend = short_term_avg / long_term_avg
        
        # 计算动量
        revenue_changes = np.diff(recent_revenue)
        momentum = np.mean(revenue_changes) / (abs(long_term_avg) + 1e-7)
        
        if trend > 1.1:
            phase = 'growth'
            trend_type = 'positive'
        elif trend < 0.9:
            phase = 'decline'
            trend_type = 'negative'
        else:
            phase = 'stable'
            trend_type = 'neutral'
            
        return {
            'phase': phase,
            'trend': trend_type,
            'momentum': momentum
        }

    def evaluate_market_position(self, participation_rate: float) -> Dict:
        """评估市场地位"""
        self.current_market_share = participation_rate
        self.market_share_history.append(participation_rate)
        
        if len(self.market_share_history) < 5:
            return {'position': 'neutral', 'strength': 0.5}
            
        avg_share = np.mean(self.market_share_history[-5:])
        share_trend = (participation_rate - self.market_share_history[-5]) / 0.5  # 归一化趋势
        
        if avg_share > 0.6:
            position = 'dominant'
            strength = min(1.0, avg_share + 0.2)
        elif avg_share < 0.3:
            position = 'challenger'
            strength = max(0.0, avg_share - 0.1)
        else:
            position = 'neutral'
            strength = 0.5
            
        return {
            'position': position,
            'strength': strength,
            'trend': share_trend
        }

    def calculate_competitive_pressure(self, market_data: Dict) -> float:
        """计算竞争压力"""
        if not market_data or 'avg_market_rate' not in market_data:
            return 0.5
            
        rate_difference = abs(self.current_fee_rate - market_data['avg_market_rate'])
        market_position = self.evaluate_market_position(market_data.get('participation_rate', 0.5))
        
        # 基础压力
        base_pressure = 0.5
        
        # 费率差异导致的压力
        rate_pressure = rate_difference * 2  # 费率差异越大，压力越大
        
        # 市场地位影响
        position_factor = 1.5 if market_position['position'] == 'challenger' else 0.8
        
        return min(1.0, base_pressure + rate_pressure * position_factor)

    def update_b2e_model(self, transaction_data: List[Tuple[int, int, str, str]]) -> List[dict]:
        """更新和预测B2E模型"""
        self.history_transaction_data.append(transaction_data)
        if len(self.history_transaction_data) > 10:
            self.history_transaction_data.pop(0)
        
        X = []
        y_fee = []
        y_amount = []
        
        for epoch_transactions in self.history_transaction_data:
            for fee, amount, sender, receiver in epoch_transactions:
                X.append([fee, amount])
                y_fee.append(fee)
                y_amount.append(amount)
                
        if not X:
            return []
            
        X = np.array(X)
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        
        self.b2e_model_fee.fit(X_scaled, y_fee)
        self.b2e_model_amount.fit(X_scaled, y_amount)
        
        predicted_transactions = []
        for fee, amount, sender, receiver in transaction_data:
            feature = self.scaler.transform([[fee, amount]])
            predicted_fee = self.b2e_model_fee.predict(feature)[0]
            predicted_amount = self.b2e_model_amount.predict(feature)[0]
            
            predicted_transactions.append({
                'fee': max(0, predicted_fee),
                'amount': max(0, predicted_amount),
                'sender': sender,
                'receiver': receiver
            })
        
        return predicted_transactions

    def predict_investment(self, fee_rate: float, market_data: Dict) -> float:
        # 跳过第一轮的随机分配数据
        filtered_pairs = self.fee_investment_pairs[1:] if len(self.fee_investment_pairs) > 1 else []
        # filtered_pairs = self.fee_investment_pairs
        
        if len(filtered_pairs) >= 2:
            X = np.array([f for f, _ in filtered_pairs]).reshape(-1, 1)
            y = np.array([i for _, i in filtered_pairs])
            poly_features = np.column_stack([X, X**2, np.ones_like(X)])
            coeffs, _ = nnls(poly_features, y)
            base_prediction = max(0, coeffs[0] * fee_rate + coeffs[1] * fee_rate**2 + coeffs[2])
        else:
            base_prediction = self.initial_funds

        # 其他因素保持不变
        rate_factor = (1 - fee_rate) ** 3
        competitive_factor = math.exp(-5 * (fee_rate - market_data.get('avg_market_rate', fee_rate)))
        cycle_factor = 1.2 if self.analyze_market_cycle()['phase'] == 'growth' else 0.8 if self.analyze_market_cycle()['phase'] == 'decline' else 1.0

        # return max(base_prediction * rate_factor * competitive_factor * cycle_factor, 0.1 * self.initial_funds)
        return base_prediction * rate_factor * competitive_factor * cycle_factor
    def predict_b2e_earnings(self, transactions: List[dict], predicted_investments: float, market_data: Dict) -> float:
        """
        预测B2E收益，考虑资金排序的优先级
        
        Args:
            transactions: 预测的交易列表
            predicted_investments: 预测的投资金额
            market_data: 市场数据，包含其他投资者/BrokerHub的资金信息
        """
        if not transactions or not isinstance(transactions[0], dict):
            return 0.0
        
        try:
            # 获取所有投资者的资金信息并排序
            all_investments = []
            for id, funds in market_data['current_funds'].items():
                if id != self.id:  # 排除自己
                    all_investments.append((id, funds))
            
            # 加入自己的预测投资额
            all_investments.append((self.id, predicted_investments))
            
            # 按资金量从大到小排序
            all_investments.sort(key=lambda x: x[1], reverse=True)
            
            # 找到自己在排序中的位置
            my_rank = next(i for i, (id, _) in enumerate(all_investments) if id == self.id)
            
            # 计算优先级更高的投资者的总资金
            higher_priority_funds = sum(funds for id, funds in all_investments[:my_rank])
            
            # 按照收益率排序交易
            sorted_txs = sorted(transactions,
                              key=lambda x: x['fee'] / (x['amount'] + 1e-7),
                              reverse=True)
            
            total_earnings = 0.0
            remaining_investment = predicted_investments
            
            # 模拟交易处理
            for tx in sorted_txs:
                # 如果优先级更高的投资者的资金足够处理此交易，跳过
                if tx['amount'] <= higher_priority_funds:
                    higher_priority_funds -= tx['amount']
                    continue
                    
                # 检查自己的资金是否足够处理剩余交易
                if tx['amount'] <= remaining_investment:
                    total_earnings += tx['fee']
                    remaining_investment -= tx['amount']
                    if remaining_investment <= 0:
                        break
            
            return total_earnings
            
        except Exception as e:
            self.logger.info(f"Error in predict_b2e_earnings: {e}")
            return 0.0

    def update_investment_model(self, fee_rate: float, investment: float):
        """更新投资模型"""
        self.fee_investment_pairs.append((fee_rate, investment))
        if len(self.fee_investment_pairs) > 100:
            self.fee_investment_pairs.pop(0)

    def calculate_optimal_rate(self, market_data: Dict) -> float:
        """
        计算最优管理费率
        考虑因素：市场地位、竞争压力、历史表现、当前参与率
        """
        # 获取当前市场状态
        participation_rate = market_data.get('participation_rate', 0.5)
        avg_market_rate = market_data.get('avg_market_rate', self.current_fee_rate)
        total_investment = market_data.get('total_investment', 0)
        
        # 分析市场周期和位置
        market_cycle = self.analyze_market_cycle()
        market_position = self.evaluate_market_position(participation_rate)
        
        # 基础费率范围设置
        if participation_rate < 0.2:  # 弱势地位
            base_max_rate = min(0.25, avg_market_rate * 0.9)
            base_min_rate = max(0.05, avg_market_rate * 0.5)
            position_factor = 0.8  # 降低费率以提升竞争力
        elif participation_rate > 0.6:  # 强势地位
            base_max_rate = min(0.45, avg_market_rate * 1.3)
            base_min_rate = max(0.15, avg_market_rate * 0.8)
            position_factor = 1.2  # 可以维持较高费率
        else:  # 中等地位
            base_max_rate = min(0.35, avg_market_rate * 1.1)
            base_min_rate = max(0.1, avg_market_rate * 0.7)
            position_factor = 1.0
        
        # 市场周期调整
        if market_cycle['phase'] == 'growth':
            cycle_factor = 1.1  # 增长期可以稍微提高费率
        elif market_cycle['phase'] == 'decline':
            cycle_factor = 0.9  # 衰退期需要降低费率
        else:
            cycle_factor = 1.0
            
        # 收益趋势调整
        if len(self.revenue_history) >= 5:
            recent_revenue_trend = (self.revenue_history[-1] / (np.mean(self.revenue_history[-5:]) + 1e-7)) - 1
            if recent_revenue_trend > 0.1:
                trend_factor = 1.1  # 收益上升趋势，可以维持或适度提高费率
            elif recent_revenue_trend < -0.1:
                trend_factor = 0.9  # 收益下降趋势，需要降低费率
            else:
                trend_factor = 1.0
        else:
            trend_factor = 1.0
        
        # 竞争压力调整
        competitive_pressure = self.calculate_competitive_pressure(market_data)
        pressure_factor = 1 - (competitive_pressure * 0.2)  # 竞争压力大时降低费率
        
        # 计算目标费率范围
        min_rate = base_min_rate * cycle_factor * pressure_factor
        max_rate = base_max_rate * cycle_factor * pressure_factor
        
        # 计算目标费率
        target_rate = self.current_fee_rate * position_factor * trend_factor
        
        # 确保费率在全局允许范围内
        target_rate = np.clip(target_rate, self.min_fee_rate, self.max_fee_rate)
        
        # 确保费率在当前市场条件下的合理范围内
        target_rate = np.clip(target_rate, min_rate, max_rate)
        
        # 添加随机扰动以避免局部最优
        if random.random() < 0.1:  # 10%的概率添加随机扰动
            noise = random.uniform(-0.02, 0.02)
            target_rate = np.clip(target_rate + noise, min_rate, max_rate)
        
        self.logger.info(f"""
            Calculate optimal rate:
            - Participation Rate: {participation_rate:.2f}
            - Market Position Factor: {position_factor:.2f}
            - Cycle Factor: {cycle_factor:.2f}
            - Trend Factor: {trend_factor:.2f}
            - Pressure Factor: {pressure_factor:.2f}
            - Target Rate: {target_rate:.4f}
            - Rate Range: [{min_rate:.4f}, {max_rate:.4f}]
        """)
        
        return target_rate

    def optimize(self, iteration: int, last_b2e_rates: List[float], 
                last_b2e_earnings: List[float], participation_rate1: float,
                total_investment: float, current_funds: Dict[int, float],
                current_earn: float, transaction_data: List[Tuple[int, int, str, str]]) -> float:
        """优化函数"""
        self.logger.info(f"Starting optimization for iteration {iteration}")
        
        # 更新历史数据
        self.revenue_history.append(current_earn)
        self.update_investment_model(self.current_fee_rate, current_funds[self.id])
        self.participation_history.append(participation_rate1)
        
        # 构建市场数据
        market_data = {
            'avg_market_rate': np.mean(last_b2e_rates) if last_b2e_rates else self.current_fee_rate,
            'participation_rate': participation_rate1,
            'total_investment': total_investment,
            'current_funds': current_funds,
            'competitor_rate': next((rate for i, rate in enumerate(last_b2e_rates) 
                                   if i != self.id), self.current_fee_rate)
        }
        
        # 更新预测模型
        predicted_transactions = self.update_b2e_model(transaction_data)
        def objective(fee_rate: float) -> float:
            predicted_investment = self.predict_investment(fee_rate, market_data)
            predicted_earnings = self.predict_b2e_earnings(
                predicted_transactions, 
                predicted_investment,
                market_data
            )
            # 计算B2E收益率
            b2e_yield = predicted_earnings / (predicted_investment + 1e-7)
            
            self.logger.info(f"fee_rate: {fee_rate}")
            self.logger.info(f"predicted_investment: {predicted_investment}")
            self.logger.info(f"predicted_earnings: {predicted_earnings}")
            self.logger.info(f"b2e_yield: {b2e_yield}")
            self.logger.info(f"participation_rate1: {participation_rate1}")
            
            if predicted_earnings < 1e-7:
                return fee_rate * 1e10  # 费率越高，返回值越大，优化器会倾向于选择更小的费率

            
            # 动态费率上限 = B2E收益率 * 调节系数(0.4)
            optimal_rate = b2e_yield * 0.4
            
            # 费率偏离惩罚
            rate_penalty = (fee_rate - optimal_rate) ** 2
            
            # 收益计算
            net_revenue = predicted_earnings * fee_rate * participation_rate1
                        
            return -(net_revenue * (1 - rate_penalty))
            
        def calculate_optimal_rate(self, market_data: Dict) -> float:
            max_rate = min(0.4, market_data.get('avg_market_rate', 0.3) * 1.2)
            min_rate = max(0.1, market_data.get('avg_market_rate', 0.3) * 0.8)
            return np.clip(self.current_fee_rate, min_rate, max_rate)
        
        # 优化费率
        result = minimize_scalar(
            objective,
            bounds=(self.min_fee_rate, self.max_fee_rate),
            method='bounded'
        )
        
        # 获取理论最优费率
        theoretical_optimal = result.x
        
        # 获取基于市场分析的最优费率
        market_optimal = self.calculate_optimal_rate(market_data)
        
        # 结合两种方法
        combined_rate = 0.6 * theoretical_optimal + 0.4 * market_optimal
        
        self.logger.info(f"{self.id}, theoretical_optimal: {theoretical_optimal}, market_optimal: {market_optimal}")
        
        # 使用动态学习率
        cycle_data = self.analyze_market_cycle()
        base_learning_rate = self.learning_rate * (1.2 if cycle_data['momentum'] > 0 else 0.8)
        
        # 更新费率
        new_fee_rate = self.current_fee_rate + base_learning_rate * (combined_rate - self.current_fee_rate)
        
        # 确保在范围内
        self.current_fee_rate = np.clip(new_fee_rate, self.min_fee_rate, self.max_fee_rate)
        
        predicted_investment = self.predict_investment(self.current_fee_rate, market_data)
        predicted_earnings = self.predict_b2e_earnings(
            predicted_transactions, 
            predicted_investment,
            market_data
        )

        # 如果最优解的收益接近于0，直接返回最小费率
        if predicted_earnings < 1e-7:
            self.current_fee_rate =self.current_fee_rate * 0.8
        
        
        self.fee_rate_history.append(self.current_fee_rate)
        
        self.logger.info(f"New fee rate: {self.current_fee_rate:.4f}, Learning rate: {self.learning_rate:.4f}")
        
        return self.current_fee_rate
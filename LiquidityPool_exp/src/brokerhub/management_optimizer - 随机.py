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
    def init(self, config: Dict):
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
        self.revenue_rate_history = []

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
    def optimize(self, iteration: int, last_b2e_rates: List[float], 
                last_b2e_earnings: List[float], participation_rate1: float,
                total_investment: float, current_funds: Dict[int, float],
                current_earn: float, transaction_data: List[Tuple[int, int, str, str]]) -> float:
        """优化函数"""
        self.logger.info(f"Starting optimization for iteration {iteration}")
        # 更新历史数据
        self.revenue_history.append(current_earn)
        self.participation_history.append(participation_rate1)

        # history_length =  if len(self.revenue_history) >= 5 else len(self.revenue_history)

        if(iteration <= 1):
            self.current_fee_rate = self.current_fee_rate * 1.2
            self.fee_rate_history.append(self.current_fee_rate)
            self.revenue_rate_history.append(0)
            return self.current_fee_rate

        user_funds = current_funds[self.id] - self.initial_funds
        revenue_rate = self.revenue_history[-1] * (user_funds / current_funds[self.id])

        sign = 1 if(revenue_rate > self.revenue_rate_history[-1]) else -1
        self.current_fee_rate = self.current_fee_rate * (1.0 + sign * random.uniform(0, 1.0) / iteration)
        if(self.current_fee_rate > self.max_fee_rate):
            self.current_fee_rate = self.max_fee_rate        
        if(self.current_fee_rate < self.min_fee_rate):
            self.current_fee_rate = self.min_fee_rate
        self.fee_rate_history.append(self.current_fee_rate)
        self.revenue_rate_history.append(revenue_rate)

        self.logger.info(f"New fee rate: {self.current_fee_rate:.4f}, Learning rate: {self.learning_rate:.4f}")

        return self.current_fee_rate
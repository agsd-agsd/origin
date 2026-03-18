import numpy as np
from typing import List, Dict
from scipy.optimize import minimize_scalar,nnls
from typing import List, Tuple
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler

class ImprovedTaxRateOptimizer:
    def __init__(self, config: Dict):
    # def __init__(self, initial_delta: float, learning_rate: float = 0.01, memory_size: int = 5):
        self.id = config["params"]["id"]
        self.initial_funds = config["params"]["initial_funds"]
        self.delta = config["params"]["initial_tax_rate"]
        self.learning_rate = config["params"]["learning_rate"]
        self.memory_size = config["params"]["memory_size"]
        self.revenue_history: List[float] = []
        self.participation_history: List[float] = []
        self.delta_history: List[float] = [config["params"]["initial_tax_rate"]]
        self.last_participation_rate = 0
        
        self.earnings_history: List[float] = []
        self.earnings_model = make_pipeline(PolynomialFeatures(degree=2), LinearRegression())
        self.min_data_points = config["params"]["min_data_points"]  # 建立模型所需的最小数据点数量
        
        # 新增: b2e投资-收益模型
        self.b2e_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.b2e_data_X = []
        self.b2e_data_y = []
        
        # 新增: delta-brokerHub投资模型
        self.max_delta = config["params"]["max_tax_rate"]
        self.min_delta = config["params"]["min_tax_rate"]
        self.delta_investment_model = None
        self.delta_data = []
        self.investment_data = []
        self.history_transaction_data=[]

        # 初始化 fee 和 amount 的回归模型
        self.scaler = StandardScaler()
        self.b2e_model_fee = LinearRegression()
        self.b2e_model_amount = LinearRegression()
                        

    # # 删除：改成利用回归模型预测出当前轮的跨分片交易信息，并根据这个预测信息估算当前轮的收益
    # def update_b2e_model(self, investments: List[float], earnings: List[float], transaction_data: List[Tuple[int, int, str, str]]):
    #     # print(f"======================b2e_model==========================")
    #     # print(investments)
    #     # print(earnings)
    #     # print(f"======================b2e_model==========================")
        
    #     if len(self.b2e_data_X) > 1000:  # 限制数据点数量
    #         self.b2e_data_X = self.b2e_data_X[-1000:]
    #         self.b2e_data_y = self.b2e_data_y[-1000:]
        
    #     if len(self.b2e_data_X) > 1:  # 确保有足够的数据来训练模型
    #         self.b2e_model.fit(np.array(self.b2e_data_X).reshape(-1, 1), self.b2e_data_y)
    #     else:
    #         print("Not enough data to train B2E model")   

    # def predict_b2e_earnings(self, investment: float) -> float:
    #     if len(self.b2e_data_X) < 10:  # 如果数据不足，返回一个基于简单比例的估计
    #         return investment * (sum(self.b2e_data_y) / sum(self.b2e_data_X)) if sum(self.b2e_data_X) > 0 else investment
    #     return self.b2e_model.predict([[investment]])[0]


    ## 修改：回归出当前epoch的交易信息
    def update_b2e_model(self, transaction_data: List[Tuple[int, int, str, str]]) -> List[Tuple[int, int, str, str]]:
        """
        根据每轮交易数据更新模型，并预测当前轮的所有交易数据。
        transaction_data: 当前轮的交易数据，包含每笔交易的 (fee, amount, sender, receiver)
        """

        # 更新历史交易数据，确保最多保留 10 轮数据
        self.history_transaction_data.append(transaction_data)
        if len(self.history_transaction_data) > 10:
            self.history_transaction_data.pop(0)  # 移除最旧的一轮交易数据

        # 获取当前使用的数据轮次
        history_data_len = len(self.history_transaction_data)
        #print(f"Using {history_data_len} rounds of data for training.")

        # 构造用于训练的数据
        X = []  # 特征数据
        y_fee = []  # fee 标签
        y_amount = []  # amount 标签

        # 使用最近的数据进行训练
        for epoch_transactions in self.history_transaction_data:
            for fee, amount, sender, receiver in epoch_transactions:
                # 提取特征：我们可以根据实际需要加入更多的特征
                X.append([fee, amount])  # 特征：这里只用 fee 和 amount
                y_fee.append(fee)
                y_amount.append(amount)

        # 调试输出：查看训练数据
        # print(f"Training data (X): {X}")
        # print(f"Training data (y_fee): {y_fee}")
        # print(f"Training data (y_amount): {y_amount}")

        # 标准化输入特征
        X_scaled = self.scaler.fit_transform(X)  # 将所有历史数据的特征标准化

        # 训练模型
        self.b2e_model_fee.fit(X_scaled, y_fee)  # 训练 fee 预测模型
        self.b2e_model_amount.fit(X_scaled, y_amount)  # 训练 amount 预测模型

        # print("Model updated with historical data.")

        # 使用模型预测当前轮次的所有交易数据
        predicted_transaction_data = []
        total_transaction = 0

        for epoch_transactions in self.history_transaction_data:
            # 对每笔交易进行预测
            for fee, amount, sender, receiver in epoch_transactions:
                # 对当前交易数据进行预测
                feature = self.scaler.transform([[fee, amount]])  # 标准化当前数据
                predicted_fee = self.b2e_model_fee.predict(feature)[0]  # 预测 fee
                predicted_amount = self.b2e_model_amount.predict(feature)[0]  # 预测 amount
                predicted_transaction_data.append({
                    'predicted_fee': predicted_fee,
                    'predicted_amount': predicted_amount,
                    'sender': sender,
                    'receiver': receiver
                })
                total_transaction += predicted_amount

        # 调试输出：查看预测的交易数据
        # print(f"预测总跨分片交易额度: {total_transaction}")

        return predicted_transaction_data  # 返回预测的交易数据
    
    ## 贪心算法预测收益
    def predict_b2e_earnings(self, predicted_transaction_data: List[dict], predicted_investments: float) -> float:
        """
        使用贪心算法根据预测的交易数据和投资额计算预测收益。
        - 按照交易的收益率（predicted_fee / predicted_amount）从大到小排序，逐一执行
        - 确保每笔跨分片交易的金额小于对应的投资额。

        Args:
            predicted_transaction_data (List[dict]): 预测的交易数据，每笔交易包含 'predicted_fee' 和 'predicted_amount'。
            predicted_investments (float): 总投资额。

        Returns:
            predicted_earnings (float): 计算后的总预测收益。
        """
        # 对交易数据按 predicted_fee / predicted_amount 从大到小排序
        predicted_transaction_data_sorted = sorted(predicted_transaction_data, 
                                                key=lambda x: x['predicted_fee'] / x['predicted_amount'], 
                                                reverse=True)

        total_earnings = 0.0
        for i in range(len(predicted_transaction_data_sorted)):
            transaction = predicted_transaction_data_sorted[i]

            predicted_fee = transaction['predicted_fee']
            predicted_amount = transaction['predicted_amount']
            
            # 确保每笔交易的金额小于对应的投资额
            if predicted_amount <= predicted_investments:
                predicted_transaction_earnings = predicted_fee + predicted_amount
                total_earnings += predicted_transaction_earnings
                predicted_investments -= predicted_amount  # 更新剩余投资额
            # else:
            #     print(f"Transaction {i+1} exceeds investment limit, skipping it.")

        return total_earnings

    # def update_delta_investment_model(self, delta: float, total_investment: float):
    #     self.delta_data.append(delta)
    #     self.investment_data.append(total_investment)
    #     nums = 50
    #     if len(self.delta_data) > nums:  # 限制数据点数量
    #         self.delta_data = self.delta_data[-nums:]
    #         self.investment_data = self.investment_data[-nums:]
        
    #     if len(self.delta_data) > 2:  # 确保有足够的数据点进行拟合
    #         X = np.array(self.delta_data).reshape(-1, 1)
    #         y = np.array(self.investment_data)
            
    #         # 数据归一化
    #         scaler_X = StandardScaler()
    #         scaler_y = StandardScaler()
    #         X_scaled = scaler_X.fit_transform(X)
    #         y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).ravel()

    #         # 定义步进函数和多项式回归
    #         def step_function(x, a, b, c):
    #             return a * np.heaviside(x - b, 1) + c

    #         best_model = None
    #         best_score = -np.inf

    #         # 尝试步进函数
    #         try:
    #             popt, _ = curve_fit(step_function, X_scaled.ravel(), y_scaled)
    #             score = r2_score(y_scaled, step_function(X_scaled.ravel(), *popt))
    #             best_model = ("步进函数", lambda x: step_function(x, *popt), score)
    #             best_score = score
    #         except RuntimeError:
    #             print("")
    #             # print("无法拟合步进函数")

    #         # 尝试多项式回归（2次和3次）
    #         for degree in [2, 3]:
    #             poly = PolynomialFeatures(degree=degree)
    #             X_poly = poly.fit_transform(X_scaled)
    #             poly_reg = LinearRegression()
    #             poly_reg.fit(X_poly, y_scaled)
    #             score = r2_score(y_scaled, poly_reg.predict(X_poly))
    #             if score > best_score:
    #                 best_score = score
    #                 best_model = (f"{degree}次多项式回归", 
    #                               lambda x: poly_reg.predict(poly.transform(x.reshape(-1, 1))), 
    #                               score)

    #         if best_model:
    #             name, func, score = best_model
    #             # print(f"最佳模型: {name}, R² 分数: {score:.4f}")
    #             self.delta_investment_model = lambda x: scaler_y.inverse_transform(
    #                 func(scaler_X.transform([[x]])).reshape(-1, 1)
    #             ).ravel()[0]
    #         else:
    #             # print("所有模型拟合失败，使用简单线性回归")
    #             reg = LinearRegression().fit(X, y)
    #             self.delta_investment_model = lambda x: reg.predict([[x]])[0]
    #     else:
    #         # print("数据点不足，使用平均值")
    #         self.delta_investment_model = lambda x: np.mean(self.investment_data)
        
    def update_delta_investment_model(self, delta: float, total_investment: float):
        self.delta_data.append(delta)
        self.investment_data.append(total_investment)
        nums = 50  # 限制数据点数量
        if len(self.delta_data) > nums:
            self.delta_data = self.delta_data[-nums:]
            self.investment_data = self.investment_data[-nums:]
        
        # 数据点数量
        data_length = len(self.delta_data)
        
        if data_length >= 2:
            # 检查并过滤非数值数据
            valid_data = [
                (d, i) for d, i in zip(self.delta_data, self.investment_data)
                if isinstance(d, (int, float)) and isinstance(i, (int, float))
            ]
            
            if not valid_data:
                # 如果没有有效的数据点，使用平均投资额进行预测
                avg_investment = max(0, np.mean([
                    i for i in self.investment_data if isinstance(i, (int, float))
                ]))
                self.delta_investment_model = lambda x: avg_investment
                # print(f"BrokerHub {self.id}: 无有效数据，使用平均投资额 {avg_investment:.4f} 进行预测")
                return
            
            # 提取有效的 delta 和 investment 数据
            X = np.array([d for d, _ in valid_data], dtype=float).reshape(-1, 1)
            y = np.array([i for _, i in valid_data], dtype=float)
            
            # 构建设计矩阵，添加常数项
            X_design = np.hstack([X, np.ones_like(X)])
            
            # 使用非负最小二乘法进行线性拟合
            coeffs_nnls, _ = nnls(X_design, y)
            y_pred_nnls = X_design @ coeffs_nnls
            score_nnls = r2_score(y, y_pred_nnls)
            best_model = ("非负线性回归", lambda x: max(0, coeffs_nnls[0]*x + coeffs_nnls[1]), score_nnls)
            best_score = score_nnls
            
            # 当数据量足够时，尝试多项式回归模型
            if data_length >= 10:
                for degree in [2, 3]:
                    poly = PolynomialFeatures(degree=degree)
                    X_poly = poly.fit_transform(X)
                    model = LinearRegression()
                    model.fit(X_poly, y)
                    y_pred = model.predict(X_poly)
                    score = r2_score(y, y_pred)
                    
                    # 如果新的模型得分更高，更新最佳模型
                    if score > best_score:
                        best_model = (
                            f"{degree}次多项式回归",
                            lambda x: max(0, model.predict(poly.transform([[x]]))[0]),
                            score
                        )
                        best_score = score
            
            # 选择最佳模型
            model_name, model_func, model_score = best_model
            self.delta_investment_model = model_func
            # print(f"BrokerHub {self.id}: 使用模型 '{model_name}' 进行拟合，R²得分为 {model_score:.4f}")
        else:
            # 数据点不足，使用平均值
            avg_investment = max(0, np.mean(self.investment_data))
            self.delta_investment_model = lambda x: avg_investment
            # print(f"BrokerHub {self.id}: 数据不足，使用平均投资额 {avg_investment:.4f} 进行预测")


    def predict_investment(self, delta: float) -> float:
        if self.delta_investment_model is None:
            return max(0, np.mean(self.investment_data)) if self.investment_data else 0 # 确保非负
        predicted_investment = self.delta_investment_model(delta)
        # print(f"BrokerHub {self.id}：对于税率 {delta}，预测的投资值为：{predicted_investment}")
        return predicted_investment

    def optimize(self, iteration: int, last_b2e_rates: List[float], last_b2e_earnings: List[float], participation_rate1: float, total_investment: float, current_funds: List[float], current_earn: float, transaction_data: List[Tuple[int, int, str, str]]) -> float:
        
        # print(f"BrokerHub {self.id}: 收益： {current_earn}，上一轮参与率为：{participation_rate1}，投入的总资金为 {total_investment}，其中{self.id} 占 {current_funds[self.id]}")
        # 添加收益阈值检测
        if iteration > 1 and participation_rate1 < 0.1:
            # 如果参与率过小，主动降低税率
            self.delta = max(self.min_delta, self.delta * 0.9)  # 税率降低至90%，并确保不低于最小值
            self.delta_history.append(self.delta)
            # print(f"BrokerHub {self.id}: 由于参与率过低，降低税率至 {self.delta}")
            return self.delta
        # 更新模型
        # self.update_b2e_model(current_funds, last_b2e_earnings)
        self.update_delta_investment_model(self.delta, current_funds[self.id])
        
        # 更新收益历史
        current_revenue = current_earn
        self.revenue_history.append(current_revenue + 1e-5)
        
        # 更新参与率历史
        self.participation_history.append(participation_rate1)
    
        # 计算短期收益趋势
        short_term_trend = self.calculate_short_term_trend()

        ## 新增：预测当前epoch交易信息
        predicted_transaction_data = self.update_b2e_model(transaction_data)

        def objective(delta: float) -> float:
            # 预测investments    
            predicted_investment = self.predict_investment(delta)
            predicted_earnings = self.predict_b2e_earnings(predicted_transaction_data, predicted_investment)
            
            # 去掉唯一一个用户的收益
            predicted_earnings = (predicted_earnings - self.initial_funds) * 1.0 / (predicted_earnings + 1e-7) * delta 
            
            # print(f"当前税率：{delta}，预期收益为：{predicted_earnings}")

            brokerhub_rate = (1 - delta) * predicted_earnings / predicted_investment if predicted_investment > 0 else 0
            participation_rate = participation_rate1
            expected_revenue = delta * predicted_earnings * 1e-11  

            return expected_revenue
            
            # 添加历史趋势因子
            trend_factor = self.calculate_trend_factor()
            
            # 添加波动性惩罚
            volatility_penalty = self.calculate_volatility_penalty(delta)
            
            # 长期稳定性奖励
            stability_reward = self.calculate_stability_reward(delta, participation_rate)
            
            participation_factor = (self.last_participation_rate - participation_rate) * 1e4  # 添加参与率因子

            self.last_participation_rate = participation_rate
                        
            # 根据短期趋势调整目标函数
            trend_adjustment = 1 + short_term_trend * 3  # 增加短期趋势的影响
            # 添加收益下降惩罚
            revenue_decline_penalty = 0
            if len(self.revenue_history) > 1 and self.revenue_history[-1] < self.revenue_history[-2]:
                revenue_decline_penalty = (self.revenue_history[-2] - self.revenue_history[-1]) / self.revenue_history[-2] * 1e5
            # 计算收益波动性
            if len(self.revenue_history) >= 5:
                revenue_volatility = np.std(self.revenue_history[-5:]) / np.mean(self.revenue_history[-5:])
            else:
                revenue_volatility = 0
            
            revenue_volatility_penalty = revenue_volatility * 1e5  # 增加对收益波动的惩罚
            
            return -(expected_revenue * trend_adjustment + 
                     participation_rate * expected_revenue * 2 + 
                     stability_reward - 
                     volatility_penalty * 1.5 - 
                     revenue_decline_penalty - 
                     revenue_volatility_penalty)
            # 稳定代码
            # trend_adjustment = 1 + short_term_trend

            # return -(expected_revenue * trend_adjustment + 
                     # participation_rate * expected_revenue * 0.5 + 
                     # stability_reward * 10 -  # 增加稳定性奖励的权重
                     # volatility_penalty * 0.1)  # 减小波动性惩罚的影响


        result = minimize_scalar(objective, bounds=(self.min_delta, self.max_delta), method='bounded')
        new_delta = result.x
        
        # 动态调整学习率
        revenue_volatility = np.std(self.revenue_history[-5:]) / np.mean(self.revenue_history[-5:]) if len(self.revenue_history) >= 5 else 0
        adaptive_learning_rate = self.learning_rate * (1 + revenue_volatility * 2 )  # 根据收益波动增加学习率

        # 应用自适应学习率
        self.delta = max(min(self.delta + adaptive_learning_rate * (new_delta - self.delta), self.max_delta), self.min_delta)
        # 更新 delta 历史
        
        # if self.detect_stagnation():
        #     # 如果检测到停滞，强制进行一次较大的调整
        #     self.delta = max(min(self.delta * (1 + np.random.uniform(-0.2, 0.2)), self.max_delta), self.min_delta)
    
        self.delta = max(min(self.delta, self.max_delta), self.min_delta)
        
        self.delta_history.append(self.delta)
        
        return self.delta
    
    def detect_stagnation(self) -> bool:
        if len(self.delta_history) < 20:
            return False
        recent_changes = np.diff(self.delta_history[-20:])
        return np.all(np.abs(recent_changes) < 1e-5)  # 如果最近20次迭代税率变化都很小，则认为陷入停滞

    def calculate_short_term_trend(self) -> float:
        if len(self.revenue_history) < 5:
            return 0
        recent_trend = (self.revenue_history[-1] - np.mean(self.revenue_history[-5:-1])) / np.mean(self.revenue_history[-5:-1])
        return np.clip(recent_trend * 5, -1, 1)  # 放大趋势影响并限制在 [-1, 1] 范围内
        # return np.clip(recent_trend, -0.1, 0.1)  # 稳定代码        
   
    def calculate_trend_factor(self) -> float:
        if len(self.revenue_history) < 2:
            return 0
        recent_trend = (self.revenue_history[-1] - self.revenue_history[-2]) / max(self.revenue_history[-2], 1)
        return recent_trend * 500  # 放大趋势影响

    def calculate_volatility_penalty(self, proposed_delta: float) -> float:
        if len(self.delta_history) < 2:
            return 0
        recent_volatility = abs(proposed_delta - self.delta_history[-1])
        return recent_volatility * 2000  # 放大波动性惩罚

    def calculate_stability_reward(self, proposed_delta: float, participation_rate: float) -> float:
        if len(self.participation_history) < self.memory_size:
            return 0
        avg_participation = np.mean(self.participation_history[-self.memory_size:])
        stability_score = 1 - abs(participation_rate - avg_participation)
        return stability_score * 10  # 放大稳定性奖励
        # 稳定代码
        # delta_stability = 1 - abs(proposed_delta - self.delta) / self.delta
        # return (stability_score * 100 + delta_stability * 1000)  # 大幅增加稳定性奖励

    def get_statistics(self) -> Tuple[List[float], List[float], List[float]]:
        return self.delta_history, self.revenue_history, self.participation_history
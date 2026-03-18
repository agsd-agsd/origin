import numpy as np
from typing import List, Dict
from src.brokerhub.management_optimizer import ManagementFeeOptimizer
from src.utils.logger import Logger

class BrokerHub:
    def __init__(self, config: Dict):
        self.id = config['id']
        
        self.logger = Logger.get_logger()
        self.initial_funds = config['initial_funds']
        self.current_funds = self.initial_funds
        self.tax_rate = config["optimizer"]["params"]['initial_tax_rate']
        self.optimizer_type = config["optimizer"]["type"]
        if(self.optimizer_type == "manage"):
            self.tax_optimizer = ManagementFeeOptimizer(
                {**config["optimizer"], 'experiment_name': config['experiment_name']})
        self.users = set()
        
        # 直接从 b2e 获得的收益
        self.b2e_revenue_history = []
        self.b2e_rate_history = []
        
        # 未去掉唯一一个 volunteer 的收益
        self.revenue_history = []
        
        # 去掉唯一一个 volunteer 的收益
        self.net_revenue_history = []
        self.tax_rate_history = []
        self.current_funds_history = []
        self.total_user_funds = 0
        self.iteration=0
        # self.historical_max_successful_rate_history = []  
        
    def get_earnings_rank(self, b2e_result: Dict) -> int:
        # 获取所有的收益数据
        earnings = b2e_result["earnings"]

        # 获取当前id的收益
        current_earnings = earnings[self.id]

        # 排序收益数据，按从高到低的顺序排序，得到一个排序后的列表
        sorted_earnings = sorted(earnings.items(), key=lambda x: x[1], reverse=True)

        # # 遍历排序后的列表，找到当前id的排名
        # for id_, earnings_value in sorted_earnings:
        #     self.logger.info(f"id: {id_}, 收益: {earnings_value}")


        for rank, (id_, earnings_value) in enumerate(sorted_earnings, 1):
            if id_ == self.id:
                return rank

        # 如果没有找到（理论上不可能发生），返回-1
        return -1


    def update_market(self, b2e_result: Dict):
    
        self.current_funds = b2e_result["current_funds"][self.id]
        self.logger.info(f"{self.id} 's current fund is: {self.current_funds}")
        self.logger.info(f"{self.id} 's b2e earning is {b2e_result['earnings'][self.id]}")
        self.current_funds_history.append(self.current_funds)
        
        self.b2e_revenue_history.append(b2e_result["earnings"][self.id])
        self.b2e_rate_history.append(b2e_result["earnings"][self.id] * 1.0 / self.current_funds)
        
        self.revenue_history.append(self.b2e_revenue_history[-1] * self.tax_rate)
        
        # # 去掉不会退出的唯一一个 volunteer 的收益
        net_revenue_rate = (self.current_funds - self.initial_funds) * 1.0 / self.current_funds * self.tax_rate
        
        # self.logger.info(f"{self.id} : {net_revenue_rate},{self.current_funds - self.initial_funds}/{self.current_funds}")
        net_revenue = self.b2e_revenue_history[-1] * net_revenue_rate
        
        self.net_revenue_history.append(net_revenue)
        
        self.tax_rate_history.append(self.tax_rate)
        
        
        self.logger.info(f"{self.id} 's principal earning is {b2e_result['earnings'][self.id] * (self.current_funds - self.initial_funds) * 1.0 / self.current_funds}")
        self.logger.info(f"{self.id} 's MER earning is {net_revenue}")
        self.logger.info(f"{self.id} earn rank is {self.get_earnings_rank(b2e_result)}")
        

   
    def make_decision(self, market_data: Dict) -> Dict:
        """
        根据市场数据做出决策，主要是优化税率
        """
        self.iteration=self.iteration+1

        b2e_rates = list(market_data['b2e_rates'].values())
        b2e_earnings = list(market_data['b2e_earnings'].values())
        num_users = market_data['num_users']
        total_investment = market_data['total_investment']
        current_funds = market_data['current_funds']
        transaction_data = market_data['transaction_data']
        # self.logger.info(transaction_data)
        
        # self.logger.info(f"======================{self.id}==========================")
        # self.logger.info(b2e_rates)
        # self.logger.info(b2e_earnings)
        # self.logger.info(num_users)
        # self.logger.info(total_investment)
        # self.logger.info(current_funds)
        # self.logger.info(f"======================{self.id}==========================")
        
        if(self.optimizer_type == "manage"):
            self.new_tax_rate = self.tax_optimizer.optimize(
                iteration=len(self.tax_rate_history),
                last_b2e_rates=market_data['b2e_rates'],
                last_b2e_earnings=market_data['b2e_earnings'],
                participation_rate1= len(self.users)/len(current_funds),
                total_investment=total_investment,
                current_funds=current_funds,
                current_earn = self.net_revenue_history[-1],
                transaction_data = transaction_data
            )
        elif(self.optimizer_type == "sym"):
            self.new_tax_rate = self.tax_rate
        self.tax_rate = self.new_tax_rate

        # self.logger.info(f"{self.id} net_revenue is {self.net_revenue_history[-1]}")
        self.logger.info(f"{self.id} tax_rate is {self.tax_rate}")
        return {
            'tax_rate': self.tax_rate
        }
        
    def update_decision(self, acc: Dict):
        
        self.current_funds = self.initial_funds + self.total_user_funds
        
        # 是否将收益累加
        if(acc["acc"]):
            self.initial_funds += self.revenue_history[-1]
            self.current_funds += self.revenue_history[-1]
        
        
    def add_user(self, user_id: int, user_funds: float):
        self.users.add(user_id)
        self.total_user_funds += user_funds

    def remove_user(self, user_id: int, user_funds: float):
        self.users.remove(user_id)
        self.total_user_funds -= user_funds
    
    def get_state(self) -> Dict:
        """
        返回 BrokerHub 的当前状态
        """
        return {
            'id': self.id,
            'current_funds': self.current_funds,
            'b2e_revenue': self.b2e_revenue_history[-1],
            'revenue': self.revenue_history[-1],
            'net_revenue': self.net_revenue_history[-1],
            'tax_rate': self.tax_rate,
            # 'historical_max_successful_rate': self.historical_max_successful_rate_history[-1],
            'users': list(self.users),
            'total_user_funds': self.total_user_funds
        }
    def calculate_user_share(self, total_earnings: float, user_funds: float) -> float:
        user_share = total_earnings * (1 - self.tax_rate) * (user_funds / self.total_user_funds)
        return user_share
    
    def calculate_expected_revenue(self, total_earnings: float) -> float:
        """
        计算 brokerHub 预期收益
        """
        return self.tax_rate * total_earnings

    def get_user_earnings_rate(self) -> float:
        """
        计算用户在该 BrokerHub 中的预期收益率
        """
        return (1 - self.tax_rate)  * self.b2e_rate_history[-1]
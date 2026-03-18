import random
from typing import List, Dict
from src.utils.logger import Logger

class Volunteer:
    def __init__(self, id: int, initial_balance: int, risk_tolerance: float = 0.5, acc: bool = False):
        self.id = id
        self.logger = Logger.get_logger()
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.risk_tolerance = risk_tolerance
        self.current_brokerhub = None
        self.earnings_history = []
        self.earnings_rate_history = []
        self.b2e_rate_history = [] # 添加这个属性来存储上一次的 B2E 收益率
        self.b2e_revenue_history = [] # 添加这个属性来存储上一次的 B2E 收益率
        self.acc = acc

        # 设置当前经过了多少轮
        self.iteration = 0

        # 上一次离开brokerhub是什么时候
        self.last_leave_iteration = -100

        self.stay_intervals = [3,6]

        # 加入brokerhub后必须经过多少轮才可以离开，随机设置一个3到6的整数
        self.leave_interval = random.randint(self.stay_intervals[0], self.stay_intervals[1])
    
    def make_decision(self, market_data: Dict, brokerhubs: List[Dict]) -> Dict:
        """
        根据市场数据和所有BrokerHub的信息做出决策
        """
        # 每次自增1
        self.iteration = self.iteration + 1
        # 计算直接参与B2E的预期收益率
        b2e_rate = self.b2e_rate_history[-1]
        # self.logger.info(f"volunteer {self.id} b2e : {b2e_rate}")
        best_bh_list = []
        best_bh_rate = 0

        self.logger.info(f"volunteer {self.id} b2e_rate : {b2e_rate}")
        for bh in brokerhubs:
            # 增加一个随机波动，防止brokerhub1和2几乎一样时volunteer一股脑加入一个
            current_bh_rate = bh.get_user_earnings_rate() * random.uniform(0.95,1.05)
            # if self.id % 10 ==0:
            # self.logger.info(f"volunteer {self.id} {bh.id} : {current_bh_rate}")
            # self.logger.info(f"b2e rate is:{b2e_rate}")
            self.logger.info(f"volunteer {self.id} {bh.id} : {current_bh_rate}")
            
            if current_bh_rate > best_bh_rate:
                best_bh_rate = current_bh_rate
                best_bh_list = [bh]

            # elif abs(current_bh_rate-best_bh_rate) / current_bh_rate < 0.01:
            #     best_bh_list.append(bh)
        
        best_bh = None
        if best_bh_list:
            best_bh = random.choice(best_bh_list)
        
        if best_bh_rate > b2e_rate:

            if(not self.current_brokerhub):
                # 从 b2e 加入 brokerhub，更新 self.last_leave_iteration
                self.last_leave_iteration = self.iteration
                return {'action': 'join', 'brokerhub_id': best_bh.id, "leave_id": -1}
          
            if best_bh.id != self.current_brokerhub.id:
                # 如果停留时间过短则强制留下
                if self.iteration - self.last_leave_iteration < self.leave_interval:
                    return {'action': 'stay'}
                
                # 加入另一个brokerhub，更新self.last_leave_iteration
                self.last_leave_iteration = self.iteration
                self.leave_interval = random.randint(self.stay_intervals[0], self.stay_intervals[1])
                return {'action': 'join', 'brokerhub_id': best_bh.id, "leave_id": self.current_brokerhub.id}
                
            elif best_bh.id == self.current_brokerhub.id:
                return {'action': 'stay'}
        else:
            if(not self.current_brokerhub):
                return {'action': 'leave',"brokerhub_id":-1, "leave_id":-1}
            return {'action': 'leave', 'brokerhub_id': -1, "leave_id": self.current_brokerhub.id}

    def update_market(self, b2e_result: Dict, brokerhubs: List[Dict]): 
        if(self.current_brokerhub != None):
            self.earnings_rate_history.append(self.current_brokerhub.get_user_earnings_rate())
            self.earnings_history.append(self.earnings_rate_history[-1] * self.balance)
        elif(self.current_brokerhub == None):
            self.earnings_history = [b2e_result["earnings"][self.id]]
            self.earnings_rate_history = [b2e_result["earnings"][self.id] / self.balance]
            self.b2e_rate_history = [b2e_result["rates"][self.id]]
            self.b2e_revenue_history = [b2e_result["earnings"][self.id]]
        
    def update_decision(self, des: List[Dict], brokerhubs: List[Dict]):
        """
        更新Volunteer的状态
        """
        
        if(des["action"] == "leave"):
            if(des["leave_id"] != -1):
                self.current_brokerhub.remove_user(self.id, self.balance)
                self.current_brokerhub = None
            return self.current_brokerhub
        
        
        
        if(des["action"] == "join"):
            current_bh = next(bh for bh in brokerhubs if bh.id == des["brokerhub_id"])
            self.current_brokerhub = current_bh
            if(des["leave_id"] == -1):
                current_bh.add_user(self.id, self.balance)
            else:
                leave_bh = next(bh for bh in brokerhubs if bh.id == des["leave_id"])
                leave_bh.remove_user(self.id, self.balance)  
                if self.acc:
                    self.balance += self.earnings_history[-1]
                current_bh.add_user(self.id, self.balance)  
                
        return self.current_brokerhub

    def get_state(self) -> Dict:
        """
        返回Volunteer的当前状态
        """
        return {
            'id': self.id,
            'balance': self.balance,
            'current_brokerhub': self.current_brokerhub.id if self.current_brokerhub != None else None,
            'total_earnings': sum(self.earnings_history),
            'last_b2e_rate': self.b2e_rate_history[-1],
            'revenue_rate': self.earnings_rate_history[-1]
        }
import os
import json
from typing import List, Dict, Type, Tuple
from src.brokerhub.brokerhub import BrokerHub
from src.volunteer.volunteer_manager import VolunteerManager
from decimal import Decimal
from src.utils.logger import Logger

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, int):
            return str(obj)  # Convert all integers to strings to avoid scientific notation
        return super(DecimalEncoder, self).default(obj)

class MarketSimulator:
    def __init__(self, config: Dict, B2ERoundingClass: Type, wait_for_write_tasks: Type, experiment_name: str):
        self.config = config
        self.logger = Logger.get_logger()
        self.B2ERoundingClass = B2ERoundingClass
        self.wait_for_write_tasks = wait_for_write_tasks
        
        self.brokerhubs = [BrokerHub({**bh_config, 'experiment_name': config['experiment_name']}) for bh_config in config['brokerhubs']]
        self.brokerhub_dict = {bh.id: bh for bh in self.brokerhubs}  # 创建一个字典用于快速查找
        self.volunteer_manager = VolunteerManager(config)
        self.current_epoch = 0
        self.market_history = []
        self.experiment_name = experiment_name
        
        self.current_items = None
        self.current_capacities = None
        self.current_txs_number = None
        self.sorted_indices = None  # 新增：用于存储排序后的索引
        self.original_capacities = None  # 新增：用于存储原始顺序的capacities
        self.initial_investments = {}  # 新增：用于跟踪初始投资金额
        self.b2e_rates = {}  # 新增：用于跟踪 b2e 投资收益

        self.transaction_data = []; # 新增：用于存储交易数据

    def run_simulation(self, num_epochs: int):
        for epoch in range(num_epochs):
            self.logger.info("---------------------------------------------------------")
            self.logger.info(f"epoch:{epoch}")
            self.current_epoch = epoch
            self.prepare_b2e_data(epoch)
            b2e_result = self.run_b2e()
            
            self.update_brokerHub_volunter_revenue(b2e_result)
            
            self.record_market_state()
            
            bh_decisions = self.make_brokerhub_decisions(b2e_result, self.current_items)
            vol_decisions = self.make_volunteer_decisions(b2e_result, bh_decisions)
            self.update_market_state(b2e_result, bh_decisions, vol_decisions)
        # self.record_market_state()

        self.wait_for_write_tasks()
        self.export_simulation_results()
    
    def prepare_b2e_data(self, epoch: int):
        data_path = os.path.join(self.config['processed_data_path'], self.experiment_name, f'item{epoch}', 'data1.txt')
        with open(data_path, "r") as f:
            allData = f.readlines()
            slice = allData[1].strip().split(" : ")[1].split(",")
            self.current_txs_number = int(slice[1]) - int(slice[0])
            data = allData[3:]
            self.current_items = []

            fee_amount = 0
            transaction_amount = 0
            for item in data[0].strip().split(" "):
                item = item[1:-1].split(",")
                transaction_amount += int(item[0])
                fee_amount += int(item[1])
                self.current_items.append((int(item[0]), int(item[1]), item[2], item[3]))
            # 打印跨分片交易信息
            # self.logger.info(f"Number of items in current_items: {len(self.current_items)}")
            # self.logger.info(f"总跨分片交易金额为: {fee_amount}; 总手续费为 {transaction_amount}")

        # 创建一个列表来存储每个volunteer的资金状态和ID
        self.broker_funds = []
        for v in self.volunteer_manager.volunteers:
            initial_investment = self.initial_investments.get(v.id, v.balance)
            if not v.current_brokerhub:
                self.broker_funds.append((initial_investment, False, v))
            else:
                self.broker_funds.append((initial_investment, True, v))
        
        # 添加BrokerHub的资金和ID
        for bh in self.brokerhubs:
            initial_investment = self.initial_investments.get(bh.id, bh.current_funds)
            self.broker_funds.append((initial_investment, False, bh))
        
        
        self.broker_funds_join = [item for item in self.broker_funds if item[1] == False]
        # 排序直接参与B2E的资金
        sorted_direct_b2e = sorted(self.broker_funds_join, key=lambda x: x[0], reverse=True)

        
        self.current_capacities = [fund for fund,join,v in sorted_direct_b2e]
        
        
        
        self.sorted_ids = [broker[2].id for broker in sorted_direct_b2e]
        
        self.original_capacities = {v.id : fund for fund, _, v in sorted_direct_b2e}
        # self.logger.info(self.sorted_indices)
        # self.logger.info(self.original_capacities)
        

    def load_epoch_data(self, epoch: int) -> Dict:
        data_path = os.path.join(self.config['processed_data_path'], self.experiment_name, f'item{epoch}', 'data1.txt')
        with open(data_path, 'r') as f:
            lines = f.readlines()
        capacities = list(map(int, lines[-1].strip().split(', ')))
        ctxs = [list(map(int, ctx.strip('()').split(','))) for ctx in lines[-2].strip().split(') ') if ctx]
        return {'capacities': capacities, 'ctxs': ctxs}


    def run_b2e(self) -> Dict:
        data_path = os.path.join(self.config['processed_data_path'], self.experiment_name, f'item{self.current_epoch}')
        using_time, value, sorted_funds = self.B2ERoundingClass(
            dataEpoch = [self.current_items,
            self.current_capacities,
            self.current_txs_number],
            var_type = self.config['b2e']['varType'],
            resultPath = data_path,
            iter_num = self.config['b2e']['iterNum'],
            alpha = self.config['b2e']['alpha'],
            feeRatio = self.config['b2e']['feeRatio'],
            sorted_ids = self.sorted_ids  # 传递排序后的ID
        )
        
        # 将 id 和获取收益的结果进行对应
        id_earning_dict = {}
        for i, idx in enumerate(self.sorted_ids):
            id_earning_dict[idx] = sorted_funds[i]
        
        rates = {k: v / self.original_capacities[k] if self.original_capacities[k] != 0 else 0 for k, v in id_earning_dict.items()}
        
        
        self.b2e_rates.update(rates)
        
        return {'earnings': id_earning_dict, 'rates': rates, "current_funds": self.original_capacities}

    def update_brokerHub_volunter_revenue(self, b2e_result: Dict):
        for bh in self.brokerhubs:
            bh.update_market(b2e_result)
            
        self.volunteer_manager.update_market(b2e_result, self.brokerhubs)

    def make_brokerhub_decisions(self, b2e_result: Dict, current_items: List[Tuple[int, int, str, str]]) -> List[Dict]:
        # 构建 market_data 字典，包含 b2e 数据和当前跨分片交易信息的特征
        market_data = {
            'b2e_rates': b2e_result['rates'],
            'b2e_earnings': b2e_result['earnings'],
            'num_users': len(self.volunteer_manager.volunteers),
            'total_investment': sum(b2e_result["current_funds"].values()),
            'current_funds': b2e_result["current_funds"],
            'transaction_data': current_items  # 新增：添加跨分片交易数据
        }

        # 对每个 BrokerHub 调用 make_decision，并传入构建好的 market_data
        return [bh.make_decision(market_data) for bh in self.brokerhubs]
    
    def make_volunteer_decisions(self, b2e_result: Dict, bh_decisions: List[Dict]) -> List[Dict]:
        market_data = {
            'b2e_rates': self.b2e_rates
        }

        return self.volunteer_manager.make_decisions(market_data, self.brokerhubs)

    
    def update_market_state(self, b2e_result: Dict, bh_decisions: List[Dict], vol_decisions: List[Dict]):
        # 更新志愿者状态
        
        # 加入到对应的 BrokerHub，状态以及资金
        self.volunteer_manager.update_decisions(vol_decisions, self.brokerhubs)
        
        
        # 更新 BrokerHub 状态
        for bh, decision in zip(self.brokerhubs, bh_decisions):
            bh.update_decision({"acc":self.config["Balance_accumulation"]})
            
    def record_market_state(self):
        state = {
            'epoch': self.current_epoch,
            'brokerhubs': [bh.get_state() for bh in self.brokerhubs],
            'volunteers': self.volunteer_manager.get_states()
        }
        self.market_history.append(state)

    def export_simulation_results(self):
        output_path = os.path.join(self.config['output']['outputPath'], f'simulation_results_{self.experiment_name}.json')
        
        processed_history = [self.process_state_for_export(state) for state in self.market_history]
        
        # self.logger.info(processed_history)
        
        with open(output_path, 'w') as f:
            json.dump(processed_history, f, indent=2, cls=DecimalEncoder)

    def process_state_for_export(self, state):
        def process_value(value):
            if isinstance(value, (int, float, Decimal)):
                return str(value)
            elif isinstance(value, dict):
                return {k: process_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [process_value(item) for item in value]
            return value

        return process_value(state)
        
    def get_market_state(self) -> Dict:
        return self.market_history[-1] if self.market_history else None
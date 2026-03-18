import json
import os
import numpy as np

def load_2hubs_data(base_path):
    """加载所有2hubs实验数据"""
    all_experiments = []
    
    # 加载hub1系列（1-10）
    for i in range(1, 11):
        filename = f"simulation_results_2hubs_hub1_20w_300_diff_final_balance{i}.json"
        filepath = os.path.join(base_path, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    all_experiments.append({
                        'name': f'hub1_{i}',
                        'data': data
                    })
            except Exception as e:
                print(f"加载文件 {filepath} 时出错: {e}")
    
    # 加载hub2系列（1-10）
    for i in range(1, 11):
        filename = f"simulation_results_2hubs_hub2_20w_300_diff_final_balance{i}.json"
        filepath = os.path.join(base_path, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    all_experiments.append({
                        'name': f'hub2_{i}',
                        'data': data
                    })
            except Exception as e:
                print(f"加载文件 {filepath} 时出错: {e}")
    
    return all_experiments

def calculate_hub_ranking_epoch0(epoch_data):
    """计算epoch 0时各hub的排名"""
    # 计算总市场
    total_market = 0
    
    # 未加入hub的volunteer余额
    for volunteer in epoch_data['volunteers']:
        if volunteer['current_brokerhub'] is None:
            total_market += float(volunteer['balance'])
    
    # 所有hub的资金
    hub_funds = []
    for hub in epoch_data['brokerhubs']:
        funds = float(hub['current_funds'])
        total_market += funds
        hub_funds.append({
            'id': hub['id'],
            'funds': funds,
            'share': funds / total_market * 100 if total_market > 0 else 0
        })
    
    # 按资金排序，资金多的排名靠前
    hub_funds.sort(key=lambda x: x['funds'], reverse=True)
    
    # 分配排名
    for rank, hub in enumerate(hub_funds):
        hub['ranking'] = rank + 1
    
    return hub_funds

def calculate_hub_revenue_rate_epoch0(epoch_data):
    """计算epoch 0时各hub的收益率"""
    hub_revenue_rates = []
    
    for hub in epoch_data['brokerhubs']:
        funds = float(hub['current_funds'])
        revenue = float(hub['b2e_revenue'])
        
        # 收益率 = 收益 / 资金
        revenue_rate = revenue / funds if funds > 0 else 0
        
        hub_revenue_rates.append({
            'id': hub['id'],
            'funds': funds,
            'revenue': revenue,
            'revenue_rate': revenue_rate
        })
    
    # 按收益率排序
    hub_revenue_rates.sort(key=lambda x: x['revenue_rate'], reverse=True)
    
    return hub_revenue_rates

def identify_monopolist_with_share(epoch_data):
    """识别垄断者和市场份额"""
    total_market = 0
    
    # 未加入hub的volunteer余额
    for volunteer in epoch_data['volunteers']:
        if volunteer['current_brokerhub'] is None:
            total_market += float(volunteer['balance'])
    
    # 所有hub的资金
    for hub in epoch_data['brokerhubs']:
        total_market += float(hub['current_funds'])
    
    if total_market == 0:
        return None
    
    # 找到市场份额最大的hub
    max_share = 0
    monopolist_id = None
    
    for hub in epoch_data['brokerhubs']:
        hub_share = float(hub['current_funds']) / total_market * 100
        if hub_share > max_share:
            max_share = hub_share
            monopolist_id = hub['id']
    
    return {
        'id': monopolist_id,
        'share': max_share
    }

def find_first_monopoly_time(data, convergence_threshold=90):
    """找到第一次垄断的时间和垄断者"""
    for epoch_idx, epoch_data in enumerate(data):
        monopolist = identify_monopolist_with_share(epoch_data)
        if monopolist and monopolist['share'] >= convergence_threshold:
            return epoch_idx, monopolist['id']
    return -1, None

def find_convergence_time(data, convergence_threshold=90):
    """找到收敛时间：从最后往前推，找到最后一次开始垄断的时间"""
    if not data:
        return -1, None
    
    # 首先确认最终状态是否为垄断状态
    final_state = data[-1]
    final_monopolist = identify_monopolist_with_share(final_state)
    
    if not final_monopolist or final_monopolist['share'] < convergence_threshold:
        return -1, None  # 最终状态不是垄断，无收敛
    
    final_monopolist_id = final_monopolist['id']
    
    # 从最后往前推，找到这个monopolist最后一次开始连续垄断的时间点
    convergence_epoch = len(data) - 1  # 从最后一个epoch开始
    
    for epoch_idx in range(len(data) - 2, -1, -1):  # 从倒数第二个epoch往前
        epoch_data = data[epoch_idx]
        current_monopolist = identify_monopolist_with_share(epoch_data)
        
        # 检查当前epoch是否仍然是同一个monopolist且达到垄断阈值
        if (current_monopolist and 
            current_monopolist['id'] == final_monopolist_id and 
            current_monopolist['share'] >= convergence_threshold):
            convergence_epoch = epoch_idx
        else:
            # 找到了垄断开始的地方，停止搜索
            break
    
    return convergence_epoch, final_monopolist_id

def analyze_2hubs_experiments():
    """分析2hubs实验的垄断情况"""
    # 数据路径
    base_path = os.path.join(os.path.dirname(__file__), "../result/output")
    
    print("开始加载2hubs实验数据...")
    all_experiments = load_2hubs_data(base_path)
    print(f"成功加载 {len(all_experiments)} 个实验")
    
    # 分析结果
    ranking_analysis = {
        'BrokerHub1_advantage': [],  # Hub1在epoch0排名更前
        'BrokerHub2_advantage': []   # Hub2在epoch0排名更前
    }
    
    revenue_rate_analysis = {
        'BrokerHub1_advantage': [],  # Hub1在epoch0收益率更高
        'BrokerHub2_advantage': []   # Hub2在epoch0收益率更高
    }
    
    print("\n" + "="*80)
    print("开始分析每个实验...")
    print("="*80)
    
    for exp in all_experiments:
        exp_name = exp['name']
        data = exp['data']
        
        print(f"\n分析实验: {exp_name}")
        print("-" * 40)
        
        if len(data) == 0:
            print("  数据为空，跳过")
            continue
        
        # Epoch 0 分析
        epoch0_data = data[0]
        
        # 1. 按排名分析
        hub_rankings = calculate_hub_ranking_epoch0(epoch0_data)
        print("  Epoch 0 Hub排名:")
        for hub in hub_rankings:
            print(f"    {hub['id']}: 排名{hub['ranking']}, 资金{hub['funds']/1e18:.2f}ETH, 份额{hub['share']:.2f}%")
        
        # 2. 按收益率分析
        hub_revenue_rates = calculate_hub_revenue_rate_epoch0(epoch0_data)
        print("  Epoch 0 Hub收益率:")
        for hub in hub_revenue_rates:
            print(f"    {hub['id']}: 收益率{hub['revenue_rate']*100:.4f}%, 收益{hub['revenue']/1e18:.2f}ETH")
        
        # 3. 找到垄断时间
        first_monopoly_time, first_monopolist = find_first_monopoly_time(data)
        final_monopoly_time, final_monopolist = find_convergence_time(data)
        
        print(f"  第一次垄断: epoch {first_monopoly_time}, 垄断者: {first_monopolist}")
        print(f"  最终垄断开始: epoch {final_monopoly_time}, 垄断者: {final_monopolist}")
        
        # 4. 按排名分类
        if len(hub_rankings) >= 2:
            if hub_rankings[0]['id'] == 'BrokerHub1':
                # Hub1排名更前
                ranking_analysis['BrokerHub1_advantage'].append({
                    'exp_name': exp_name,
                    'first_monopoly': (first_monopoly_time, first_monopolist),
                    'final_monopoly': (final_monopoly_time, final_monopolist),
                    'hub1_ranking': hub_rankings[0]['ranking'],
                    'hub2_ranking': hub_rankings[1]['ranking']
                })
            else:
                # Hub2排名更前
                ranking_analysis['BrokerHub2_advantage'].append({
                    'exp_name': exp_name,
                    'first_monopoly': (first_monopoly_time, first_monopolist),
                    'final_monopoly': (final_monopoly_time, final_monopolist),
                    'hub1_ranking': next(h['ranking'] for h in hub_rankings if h['id'] == 'BrokerHub1'),
                    'hub2_ranking': next(h['ranking'] for h in hub_rankings if h['id'] == 'BrokerHub2')
                })
        
        # 5. 按收益率分类
        if len(hub_revenue_rates) >= 2:
            if hub_revenue_rates[0]['id'] == 'BrokerHub1':
                # Hub1收益率更高
                revenue_rate_analysis['BrokerHub1_advantage'].append({
                    'exp_name': exp_name,
                    'first_monopoly': (first_monopoly_time, first_monopolist),
                    'final_monopoly': (final_monopoly_time, final_monopolist),
                    'hub1_rate': hub_revenue_rates[0]['revenue_rate'],
                    'hub2_rate': hub_revenue_rates[1]['revenue_rate']
                })
            else:
                # Hub2收益率更高
                revenue_rate_analysis['BrokerHub2_advantage'].append({
                    'exp_name': exp_name,
                    'first_monopoly': (first_monopoly_time, first_monopolist),
                    'final_monopoly': (final_monopoly_time, final_monopolist),
                    'hub1_rate': next(h['revenue_rate'] for h in hub_revenue_rates if h['id'] == 'BrokerHub1'),
                    'hub2_rate': next(h['revenue_rate'] for h in hub_revenue_rates if h['id'] == 'BrokerHub2')
                })
    
    # 打印汇总结果
    print_summary_results(ranking_analysis, revenue_rate_analysis)

import json
import os
import numpy as np

def load_2hubs_data(base_path):
    """加载所有2hubs实验数据"""
    all_experiments = []
    
    # 加载hub1系列（1-10）
    for i in range(1, 11):
        filename = f"simulation_results_2hubs_hub1_20w_300_diff_final_balance{i}.json"
        filepath = os.path.join(base_path, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    all_experiments.append({
                        'name': f'hub1_{i}',
                        'data': data
                    })
            except Exception as e:
                print(f"加载文件 {filepath} 时出错: {e}")
    
    # 加载hub2系列（1-10）
    for i in range(1, 11):
        filename = f"simulation_results_2hubs_hub2_20w_300_diff_final_balance{i}.json"
        filepath = os.path.join(base_path, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    all_experiments.append({
                        'name': f'hub2_{i}',
                        'data': data
                    })
            except Exception as e:
                print(f"加载文件 {filepath} 时出错: {e}")
    
    return all_experiments

def calculate_hub_ranking_epoch0(epoch_data):
    """计算epoch 0时各hub的排名"""
    # 计算总市场
    total_market = 0
    
    # 未加入hub的volunteer余额
    for volunteer in epoch_data['volunteers']:
        if volunteer['current_brokerhub'] is None:
            total_market += float(volunteer['balance'])
    
    # 所有hub的资金
    hub_funds = []
    for hub in epoch_data['brokerhubs']:
        funds = float(hub['current_funds'])
        total_market += funds
        hub_funds.append({
            'id': hub['id'],
            'funds': funds,
            'share': funds / total_market * 100 if total_market > 0 else 0
        })
    
    # 按资金排序，资金多的排名靠前
    hub_funds.sort(key=lambda x: x['funds'], reverse=True)
    
    # 分配排名
    for rank, hub in enumerate(hub_funds):
        hub['ranking'] = rank + 1
    
    return hub_funds

def calculate_hub_revenue_rate_epoch0(epoch_data):
    """计算epoch 0时各hub的收益率"""
    hub_revenue_rates = []
    
    for hub in epoch_data['brokerhubs']:
        funds = float(hub['current_funds'])
        revenue = float(hub['b2e_revenue'])
        
        # 收益率 = 收益 / 资金
        revenue_rate = revenue / funds if funds > 0 else 0
        
        hub_revenue_rates.append({
            'id': hub['id'],
            'funds': funds,
            'revenue': revenue,
            'revenue_rate': revenue_rate
        })
    
    # 按收益率排序
    hub_revenue_rates.sort(key=lambda x: x['revenue_rate'], reverse=True)
    
    return hub_revenue_rates

def identify_monopolist_with_share(epoch_data):
    """识别垄断者和市场份额"""
    total_market = 0
    
    # 未加入hub的volunteer余额
    for volunteer in epoch_data['volunteers']:
        if volunteer['current_brokerhub'] is None:
            total_market += float(volunteer['balance'])
    
    # 所有hub的资金
    for hub in epoch_data['brokerhubs']:
        total_market += float(hub['current_funds'])
    
    if total_market == 0:
        return None
    
    # 找到市场份额最大的hub
    max_share = 0
    monopolist_id = None
    
    for hub in epoch_data['brokerhubs']:
        hub_share = float(hub['current_funds']) / total_market * 100
        if hub_share > max_share:
            max_share = hub_share
            monopolist_id = hub['id']
    
    return {
        'id': monopolist_id,
        'share': max_share
    }

def find_first_monopoly_time(data, convergence_threshold=90):
    """找到第一次垄断的时间和垄断者"""
    for epoch_idx, epoch_data in enumerate(data):
        monopolist = identify_monopolist_with_share(epoch_data)
        if monopolist and monopolist['share'] >= convergence_threshold:
            return epoch_idx, monopolist['id']
    return -1, None

def find_convergence_time(data, convergence_threshold=90):
    """找到收敛时间：从最后往前推，找到最后一次开始垄断的时间"""
    if not data:
        return -1, None
    
    # 首先确认最终状态是否为垄断状态
    final_state = data[-1]
    final_monopolist = identify_monopolist_with_share(final_state)
    
    if not final_monopolist or final_monopolist['share'] < convergence_threshold:
        return -1, None  # 最终状态不是垄断，无收敛
    
    final_monopolist_id = final_monopolist['id']
    
    # 从最后往前推，找到这个monopolist最后一次开始连续垄断的时间点
    convergence_epoch = len(data) - 1  # 从最后一个epoch开始
    
    for epoch_idx in range(len(data) - 2, -1, -1):  # 从倒数第二个epoch往前
        epoch_data = data[epoch_idx]
        current_monopolist = identify_monopolist_with_share(epoch_data)
        
        # 检查当前epoch是否仍然是同一个monopolist且达到垄断阈值
        if (current_monopolist and 
            current_monopolist['id'] == final_monopolist_id and 
            current_monopolist['share'] >= convergence_threshold):
            convergence_epoch = epoch_idx
        else:
            # 找到了垄断开始的地方，停止搜索
            break
    
    return convergence_epoch, final_monopolist_id

def analyze_2hubs_experiments():
    """分析2hubs实验的垄断情况"""
    # 数据路径
    base_path = os.path.join(os.path.dirname(__file__), "../result/output")
    
    print("开始加载2hubs实验数据...")
    all_experiments = load_2hubs_data(base_path)
    print(f"成功加载 {len(all_experiments)} 个实验")
    
    # 分析结果
    ranking_analysis = {
        'BrokerHub1_advantage': [],  # Hub1在epoch0排名更前
        'BrokerHub2_advantage': []   # Hub2在epoch0排名更前
    }
    
    revenue_rate_analysis = {
        'BrokerHub1_advantage': [],  # Hub1在epoch0收益率更高
        'BrokerHub2_advantage': []   # Hub2在epoch0收益率更高
    }
    
    print("\n" + "="*80)
    print("开始分析每个实验...")
    print("="*80)
    
    for exp in all_experiments:
        exp_name = exp['name']
        data = exp['data']
        
        print(f"\n分析实验: {exp_name}")
        print("-" * 40)
        
        if len(data) == 0:
            print("  数据为空，跳过")
            continue
        
        # Epoch 0 分析
        epoch0_data = data[0]
        
        # 1. 按排名分析
        hub_rankings = calculate_hub_ranking_epoch0(epoch0_data)
        print("  Epoch 0 Hub排名:")
        for hub in hub_rankings:
            print(f"    {hub['id']}: 排名{hub['ranking']}, 资金{hub['funds']/1e18:.2f}ETH, 份额{hub['share']:.2f}%")
        
        # 2. 按收益率分析
        hub_revenue_rates = calculate_hub_revenue_rate_epoch0(epoch0_data)
        print("  Epoch 0 Hub收益率:")
        for hub in hub_revenue_rates:
            print(f"    {hub['id']}: 收益率{hub['revenue_rate']*100:.4f}%, 收益{hub['revenue']/1e18:.2f}ETH")
        
        # 3. 找到垄断时间
        first_monopoly_time, first_monopolist = find_first_monopoly_time(data)
        final_monopoly_time, final_monopolist = find_convergence_time(data)
        
        print(f"  第一次垄断: epoch {first_monopoly_time}, 垄断者: {first_monopolist}")
        print(f"  最终垄断开始: epoch {final_monopoly_time}, 垄断者: {final_monopolist}")
        
        # 4. 按排名分类
        if len(hub_rankings) >= 2:
            if hub_rankings[0]['id'] == 'BrokerHub1':
                # Hub1排名更前
                ranking_analysis['BrokerHub1_advantage'].append({
                    'exp_name': exp_name,
                    'first_monopoly': (first_monopoly_time, first_monopolist),
                    'final_monopoly': (final_monopoly_time, final_monopolist),
                    'hub1_ranking': hub_rankings[0]['ranking'],
                    'hub2_ranking': hub_rankings[1]['ranking']
                })
            else:
                # Hub2排名更前
                ranking_analysis['BrokerHub2_advantage'].append({
                    'exp_name': exp_name,
                    'first_monopoly': (first_monopoly_time, first_monopolist),
                    'final_monopoly': (final_monopoly_time, final_monopolist),
                    'hub1_ranking': next(h['ranking'] for h in hub_rankings if h['id'] == 'BrokerHub1'),
                    'hub2_ranking': next(h['ranking'] for h in hub_rankings if h['id'] == 'BrokerHub2')
                })
        
        # 5. 按收益率分类
        if len(hub_revenue_rates) >= 2:
            if hub_revenue_rates[0]['id'] == 'BrokerHub1':
                # Hub1收益率更高
                revenue_rate_analysis['BrokerHub1_advantage'].append({
                    'exp_name': exp_name,
                    'first_monopoly': (first_monopoly_time, first_monopolist),
                    'final_monopoly': (final_monopoly_time, final_monopolist),
                    'hub1_rate': hub_revenue_rates[0]['revenue_rate'],
                    'hub2_rate': hub_revenue_rates[1]['revenue_rate']
                })
            else:
                # Hub2收益率更高
                revenue_rate_analysis['BrokerHub2_advantage'].append({
                    'exp_name': exp_name,
                    'first_monopoly': (first_monopoly_time, first_monopolist),
                    'final_monopoly': (final_monopoly_time, final_monopolist),
                    'hub1_rate': next(h['revenue_rate'] for h in hub_revenue_rates if h['id'] == 'BrokerHub1'),
                    'hub2_rate': next(h['revenue_rate'] for h in hub_revenue_rates if h['id'] == 'BrokerHub2')
                })
    
    # 打印汇总结果
    print_summary_results(ranking_analysis, revenue_rate_analysis)

def print_summary_results(ranking_analysis, revenue_rate_analysis):
    """打印汇总结果"""
    print("\n" + "="*80)
    print("汇总统计结果")
    print("="*80)
    
    # 1. 按排名分析的汇总
    print("\n1. 按Epoch 0排名分析:")
    print("-" * 50)
    
    print(f"\nHub1排名优势组 ({len(ranking_analysis['BrokerHub1_advantage'])} 个实验):")
    hub1_first_times = []
    hub1_final_times = []
    hub1_first_winners = []
    hub1_final_winners = []
    
    for exp in ranking_analysis['BrokerHub1_advantage']:
        print(f"  {exp['exp_name']}: 第一次垄断 epoch {exp['first_monopoly'][0]} by {exp['first_monopoly'][1]}, "
              f"最终垄断 epoch {exp['final_monopoly'][0]} by {exp['final_monopoly'][1]}")
        
        if exp['first_monopoly'][0] >= 0:
            hub1_first_times.append(exp['first_monopoly'][0])
            hub1_first_winners.append(exp['first_monopoly'][1])
        if exp['final_monopoly'][0] >= 0:
            hub1_final_times.append(exp['final_monopoly'][0])
            hub1_final_winners.append(exp['final_monopoly'][1])
    
    print(f"\nHub2排名优势组 ({len(ranking_analysis['BrokerHub2_advantage'])} 个实验):")
    hub2_first_times = []
    hub2_final_times = []
    hub2_first_winners = []
    hub2_final_winners = []
    
    for exp in ranking_analysis['BrokerHub2_advantage']:
        print(f"  {exp['exp_name']}: 第一次垄断 epoch {exp['first_monopoly'][0]} by {exp['first_monopoly'][1]}, "
              f"最终垄断 epoch {exp['final_monopoly'][0]} by {exp['final_monopoly'][1]}")
        
        if exp['first_monopoly'][0] >= 0:
            hub2_first_times.append(exp['first_monopoly'][0])
            hub2_first_winners.append(exp['first_monopoly'][1])
        if exp['final_monopoly'][0] >= 0:
            hub2_final_times.append(exp['final_monopoly'][0])
            hub2_final_winners.append(exp['final_monopoly'][1])
    
    # 2. 按收益率分析的汇总
    print("\n2. 按Epoch 0收益率分析:")
    print("-" * 50)
    
    print(f"\nHub1收益率优势组 ({len(revenue_rate_analysis['BrokerHub1_advantage'])} 个实验):")
    for exp in revenue_rate_analysis['BrokerHub1_advantage']:
        print(f"  {exp['exp_name']}: 第一次垄断 epoch {exp['first_monopoly'][0]} by {exp['first_monopoly'][1]}, "
              f"最终垄断 epoch {exp['final_monopoly'][0]} by {exp['final_monopoly'][1]}")
    
    print(f"\nHub2收益率优势组 ({len(revenue_rate_analysis['BrokerHub2_advantage'])} 个实验):")
    for exp in revenue_rate_analysis['BrokerHub2_advantage']:
        print(f"  {exp['exp_name']}: 第一次垄断 epoch {exp['first_monopoly'][0]} by {exp['first_monopoly'][1]}, "
              f"最终垄断 epoch {exp['final_monopoly'][0]} by {exp['final_monopoly'][1]}")
    
    # 3. 统计分析
    print("\n3. 统计分析:")
    print("-" * 50)
    
    if hub1_first_times:
        print(f"Hub1排名优势组 - 第一次垄断时间: 平均 {np.mean(hub1_first_times):.1f} ± {np.std(hub1_first_times):.1f}")
        print(f"Hub1排名优势组 - 第一次垄断者: {dict([(x, hub1_first_winners.count(x)) for x in set(hub1_first_winners)])}")
    
    if hub1_final_times:
        print(f"Hub1排名优势组 - 最终垄断时间: 平均 {np.mean(hub1_final_times):.1f} ± {np.std(hub1_final_times):.1f}")
        print(f"Hub1排名优势组 - 最终垄断者: {dict([(x, hub1_final_winners.count(x)) for x in set(hub1_final_winners)])}")
    
    if hub2_first_times:
        print(f"Hub2排名优势组 - 第一次垄断时间: 平均 {np.mean(hub2_first_times):.1f} ± {np.std(hub2_first_times):.1f}")
        print(f"Hub2排名优势组 - 第一次垄断者: {dict([(x, hub2_first_winners.count(x)) for x in set(hub2_first_winners)])}")
    
    if hub2_final_times:
        print(f"Hub2排名优势组 - 最终垄断时间: 平均 {np.mean(hub2_final_times):.1f} ± {np.std(hub2_final_times):.1f}")
        print(f"Hub2排名优势组 - 最终垄断者: {dict([(x, hub2_final_winners.count(x)) for x in set(hub2_final_winners)])}")

if __name__ == "__main__":
    analyze_2hubs_experiments()

if __name__ == "__main__":
    analyze_2hubs_experiments()
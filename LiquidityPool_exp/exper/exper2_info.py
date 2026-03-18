import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys

def convert_label_name(bh_id):
    """
    将BrokerHub标识符转换为LiquidityPool标识符
    例如: BrokerHub1 -> LiquidityPool1
    """
    return bh_id.replace('BrokerHub', 'LiquidityPool')

def output_all_data(results_path, epoch_limit=90):
    """
    输出指定epoch范围内的所有数据
    """
    print(f"\n=== 完整数据输出 (Epoch 0-{epoch_limit}) ===")
    
    # 加载JSON数据
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    # 获取所有BrokerHub的ID
    brokerhub_ids = list(set(bh['id'] for state in results for bh in state['brokerhubs']))
    brokerhub_ids.sort()
    
    # 用于存储分析数据
    analysis_data = {}
    
    # 为每个BrokerHub收集数据
    for bh_id in brokerhub_ids[:2]:  # 只处理前两个BrokerHub
        pool_name = convert_label_name(bh_id)
        analysis_data[pool_name] = {
            'epochs': [],
            'mfr': [],
            'rank': [],
            'participation': [],
            'revenue_ratio': [],
            'funds': [],
            'net_revenue': [],
            'stakeholder_revenue': []
        }
        
        # 收集数据
        for state in results[:epoch_limit+1]:  # +1 确保包含epoch_limit
            bh = next((bh for bh in state['brokerhubs'] if bh['id'] == bh_id), None)
            if bh:
                epoch = int(state['epoch'])
                
                # 管理费率 (MFR)
                mfr = float(bh['tax_rate']) * 100
                
                # BrokerHub排名 - 计算在所有broker和hub中的总排名
                all_balances = []
                all_ids = []
                
                # 收集所有已加入hub的volunteer ID
                joined_volunteer_ids = set()
                for hub in state['brokerhubs']:
                    joined_volunteer_ids.update(hub['users'])
                
                # 只收集还未加入任何hub的volunteers的余额
                for volunteer in state['volunteers']:
                    if volunteer['id'] not in joined_volunteer_ids:
                        all_balances.append(float(volunteer['balance']))
                        all_ids.append(f"volunteer_{volunteer['id']}")
                
                # 收集所有hubs的余额
                for hub in state['brokerhubs']:
                    all_balances.append(float(hub['current_funds']))
                    all_ids.append(f"hub_{hub['id']}")
                
                # 按余额降序排序
                sorted_indices = np.argsort(all_balances)[::-1]
                
                # 找到当前hub在总排名中的位置
                hub_index = all_ids.index(f"hub_{bh_id}")
                rank = np.where(sorted_indices == hub_index)[0][0] + 1
                
                # 参与率
                total_volunteers = len(state['volunteers'])
                participation_rate = (len(bh['users']) + 1) / (total_volunteers + 1) * 100
                
                # 收益率比例
                current_funds = float(bh['current_funds'])
                revenue_ratio = float(bh['b2e_revenue']) / current_funds * 100 if current_funds > 0 else 0
                
                # 投资者资金
                total_user_funds = float(bh['total_user_funds'])
                funds_eth = total_user_funds / 1e18
                
                # 净收益比例
                if total_user_funds > 0:
                    net_revenue_ratio = float(bh['net_revenue']) / total_user_funds * 100
                else:
                    net_revenue_ratio = 0
                
                # 投资者收益率
                if total_user_funds > 0:
                    investor_revenue_ratio = (float(bh['b2e_revenue']) * (1 - float(bh['tax_rate']))) / total_user_funds * 100
                else:
                    investor_revenue_ratio = 0
                
                # 存储到分析数据
                analysis_data[pool_name]['epochs'].append(epoch)
                analysis_data[pool_name]['mfr'].append(mfr)
                analysis_data[pool_name]['rank'].append(rank)
                analysis_data[pool_name]['participation'].append(participation_rate)
                analysis_data[pool_name]['revenue_ratio'].append(revenue_ratio)
                analysis_data[pool_name]['funds'].append(funds_eth)
                analysis_data[pool_name]['net_revenue'].append(net_revenue_ratio)
                analysis_data[pool_name]['stakeholder_revenue'].append(investor_revenue_ratio)
    
    # 输出所有数据
    for pool_name in analysis_data.keys():
        data = analysis_data[pool_name]
        
        print(f"\n" + "="*120)
        print(f"{pool_name} - 完整数据 (Epoch 0-{epoch_limit})")
        print(f"="*120)
        
        # 表头
        print(f"{'Epoch':<6} {'MFR(%)':<8} {'Rank':<6} {'Participation(%)':<15} {'Pool Revenue(%)':<15} {'Stakeholder Revenue(%)':<20} {'Pool Net Revenue(%)':<18} {'Total Funds(ETH)':<16}")
        print(f"-" * 120)
        
        # 打印数据 - 分段显示，每20行一组
        for i in range(0, len(data['epochs']), 20):
            if i > 0:
                print(f"\n{pool_name} (续) - Epoch {data['epochs'][i]} to {data['epochs'][min(i+19, len(data['epochs'])-1)]}")
                print(f"-" * 120)
                print(f"{'Epoch':<6} {'MFR(%)':<8} {'Rank':<6} {'Participation(%)':<15} {'Pool Revenue(%)':<15} {'Stakeholder Revenue(%)':<20} {'Pool Net Revenue(%)':<18} {'Total Funds(ETH)':<16}")
                print(f"-" * 120)
            
            end_idx = min(i + 20, len(data['epochs']))
            
            for idx in range(i, end_idx):
                epoch = data['epochs'][idx]
                mfr = data['mfr'][idx]
                rank = data['rank'][idx]
                participation = data['participation'][idx]
                pool_revenue = data['revenue_ratio'][idx]
                stakeholder_revenue = data['stakeholder_revenue'][idx]
                net_revenue = data['net_revenue'][idx]
                funds = data['funds'][idx]
                
                # 标记一些特殊点
                marker = ""
                if participation > 90:
                    marker = " >>>90%"
                elif participation > 80:
                    marker = " >>80%"
                elif participation > 70:
                    marker = " >70%"
                
                print(f"{epoch:<6} {mfr:<8.2f} {rank:<6} {participation:<15.2f} {pool_revenue:<15.3f} {stakeholder_revenue:<20.3f} {net_revenue:<18.3f} {funds:<16.2f}{marker}")
            
            print(f"-" * 120)
        
        # 为每个pool输出一些统计信息
        print(f"\n{pool_name} 统计摘要:")
        print(f"  平均MFR: {np.mean(data['mfr']):.2f}%")
        print(f"  平均排名: {np.mean(data['rank']):.1f}")
        print(f"  平均参与率: {np.mean(data['participation']):.2f}%")
        print(f"  最高参与率: {np.max(data['participation']):.2f}% (Epoch {data['epochs'][np.argmax(data['participation'])]})")
        print(f"  平均资金: {np.mean(data['funds']):.2f} ETH")
        print(f"  最高资金: {np.max(data['funds']):.2f} ETH (Epoch {data['epochs'][np.argmax(data['funds'])]})")
        
        # 找出高参与率的epochs
        high_participation_epochs = [(data['epochs'][i], data['participation'][i]) 
                                   for i in range(len(data['participation'])) 
                                   if data['participation'][i] > 90]
        
        if high_participation_epochs:
            print(f"  高参与率时期 (>90%): {len(high_participation_epochs)} 个epoch")
            for epoch, rate in high_participation_epochs:
                print(f"    Epoch {epoch}: {rate:.2f}%")
        else:
            print(f"  高参与率时期 (>90%): 无")

def export_to_csv(analysis_data, epoch_limit):
    """
    将数据导出为CSV文件，方便进一步分析
    """
    import csv
    
    for pool_name in analysis_data.keys():
        data = analysis_data[pool_name]
        
        filename = f"{pool_name}_data_epoch_0_{epoch_limit}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # 写入表头
            writer.writerow(['Epoch', 'MFR(%)', 'Rank', 'Participation(%)', 
                           'Pool_Revenue(%)', 'Stakeholder_Revenue(%)', 
                           'Pool_Net_Revenue(%)', 'Total_Funds(ETH)'])
            
            # 写入数据
            for i in range(len(data['epochs'])):
                writer.writerow([
                    data['epochs'][i],
                    round(data['mfr'][i], 2),
                    data['rank'][i],
                    round(data['participation'][i], 2),
                    round(data['revenue_ratio'][i], 3),
                    round(data['stakeholder_revenue'][i], 3),
                    round(data['net_revenue'][i], 3),
                    round(data['funds'][i], 2)
                ])
        
        print(f"数据已导出到: {filename}")

if __name__ == "__main__":
    # =========================== 参数设置 ===========================
    experiment_name = "trump_20w_300_diff_final_balance2"  # 实验名称
    epoch_limit = 90  # 输出epoch范围
    
    # 文件路径参数
    results_filename = f"simulation_results_{experiment_name}.json"
    input_folder = "../result/output"
    
    # =================================================================
    
    # 构建完整路径
    results_path = os.path.join(os.path.dirname(__file__), input_folder, results_filename)
    
    # 检查输入文件是否存在
    if not os.path.exists(results_path):
        print(f"错误：找不到输入文件 {results_path}")
        print(f"请确保文件存在并检查路径设置")
        sys.exit(1)
    
    # 输出所有数据
    print(f"开始输出完整数据...")
    print(f"输入文件: {results_path}")
    print(f"输出范围: Epoch 0-{epoch_limit}")
    
    analysis_data = output_all_data(results_path, epoch_limit)
    
    # 询问是否导出CSV
    export_csv = input(f"\n是否导出为CSV文件？(y/n): ").lower().strip()
    if export_csv == 'y' or export_csv == 'yes':
        export_to_csv(analysis_data, epoch_limit)
    
    print(f"\n数据输出完成！")
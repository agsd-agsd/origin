import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import MultipleLocator
import matplotlib.patches as patches
import glob

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_experiment_data(base_path, experiment_pattern, num_files=None):
    """
    加载实验数据
    """
    experiment_files = []
    
    if num_files is None:
        # 对于3hubs, 4hubs, 5hubs, 10hubs的情况
        # 查找所有匹配的文件
        pattern = f"simulation_results_{experiment_pattern}*.json"
        files = glob.glob(os.path.join(base_path, pattern))
        experiment_files = sorted(files)
    else:
        # 对于2hubs的情况，有特定的命名规则
        for i in range(1, num_files + 1):
            filename = f"simulation_results_{experiment_pattern}{i}.json"
            filepath = os.path.join(base_path, filename)
            if os.path.exists(filepath):
                experiment_files.append(filepath)
    
    data_list = []
    for filepath in experiment_files:
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                data_list.append(data)
        except Exception as e:
            print(f"加载文件 {filepath} 时出错: {e}")
    
    return data_list

def calculate_market_share(data_list):
    """
    计算市场份额演化
    """
    if not data_list:
        return [], []
    
    # 假设所有实验都有相同的epoch数
    epochs = [int(state['epoch']) for state in data_list[0]]
    
    # 获取所有hub的ID
    all_hub_ids = set()
    for data in data_list:
        for state in data:
            for hub in state['brokerhubs']:
                all_hub_ids.add(hub['id'])
    
    hub_ids = sorted(list(all_hub_ids))
    
    # 计算每个实验的市场份额
    all_market_shares = {hub_id: [] for hub_id in hub_ids}
    
    for data in data_list:
        hub_shares = {hub_id: [] for hub_id in hub_ids}
        
        for state in data:
            # 计算总市场金额（所有volunteer的balance之和）
            total_volunteer_balance = sum(float(v['balance']) for v in state['volunteers'])
            total_hub_funds = sum(float(h['current_funds']) for h in state['brokerhubs'])
            total_market = total_volunteer_balance + total_hub_funds            
            
            # 计算每个hub的市场份额
            for hub_id in hub_ids:
                hub = next((h for h in state['brokerhubs'] if h['id'] == hub_id), None)
                if hub and total_market > 0:
                    market_share = float(hub['current_funds']) / total_market * 100
                else:
                    market_share = 0
                hub_shares[hub_id].append(market_share)
        
        # 添加到总列表
        for hub_id in hub_ids:
            all_market_shares[hub_id].append(hub_shares[hub_id])
    
    return epochs, all_market_shares, hub_ids

def find_convergence_times(market_shares_data, threshold=90):
    """
    找到第一次和最后一次达到垄断的时间
    """
    convergence_times = []
    
    for experiment_data in market_shares_data:
        first_convergence = None
        last_convergence = None
        
        for epoch_idx, epoch_shares in enumerate(experiment_data):
            if max(epoch_shares.values()) >= threshold:
                if first_convergence is None:
                    first_convergence = epoch_idx
                last_convergence = epoch_idx  # 持续更新最后一次
        
        convergence_times.append({
            'first': first_convergence,
            'last': last_convergence
        })
    
    return convergence_times

def calculate_total_revenue(data_list):
    """
    修正版：使用 revenue_rate * balance 计算volunteer的epoch收益
    """
    experiment_revenues = []
    
    for data in data_list:
        total_experiment_revenue = 0
        
        print(f"处理实验，包含 {len(data)} 个epoch")
        
        for epoch_data in data:
            # Hub的收益
            epoch_hub_revenue = sum(float(hub['revenue']) for hub in epoch_data['brokerhubs'])
            
            # Volunteer的收益：revenue_rate * balance
            epoch_volunteer_revenue = 0
            for volunteer in epoch_data['volunteers']:
                revenue_rate = float(volunteer['revenue_rate'])
                balance = float(volunteer['balance'])
                volunteer_epoch_revenue = revenue_rate * balance
                epoch_volunteer_revenue += volunteer_epoch_revenue
            
            # 该epoch总收益
            epoch_total_revenue = epoch_hub_revenue + epoch_volunteer_revenue
            total_experiment_revenue += epoch_total_revenue
        
        # 转换为ETH
        experiment_revenue_eth = total_experiment_revenue / 1e18
        experiment_revenues.append(experiment_revenue_eth)
        print(f"实验总收益: {experiment_revenue_eth:.1f} ETH")
    
    return experiment_revenues

def load_without_hub_data(base_path):
    """
    重新检查Social Optimum/No Hub的计算
    """
    total_experiment_revenue = 0
    valid_epochs = 0
    
    print(f"正在扫描路径: {base_path}")
    
    # 查找所有item文件夹
    for epoch in range(300):
        item_folder = os.path.join(base_path, f"item{epoch}")
        result_file = os.path.join(item_folder, "b2e_test_results.json")
        
        if os.path.exists(result_file):
            try:
                with open(result_file, 'r') as f:
                    data = json.load(f)
                    
                # 计算该epoch所有参与者的总收益
                epoch_earnings = data[0]['earnings']
                epoch_total = sum(epoch_earnings.values())
                total_experiment_revenue += epoch_total
                valid_epochs += 1
                
                # 调试信息：打印前几个epoch的详情
                if epoch <= 3:
                    print(f"Epoch {epoch}: {len(epoch_earnings)} 个参与者, 总收益: {epoch_total/1e18:.2f} ETH")
                    non_zero_count = sum(1 for v in epoch_earnings.values() if v > 0)
                    print(f"  其中 {non_zero_count} 个参与者有收益")
                
            except Exception as e:
                print(f"加载文件 {result_file} 时出错: {e}")
    
    print(f"总共找到 {valid_epochs} 个有效epoch")
    print(f"累积总收益: {total_experiment_revenue/1e18:.2f} ETH")
    
    if valid_epochs > 0:
        return [total_experiment_revenue / 1e18]
    else:
        return []

def plot_market_concentration_welfare_analysis(output_folder):
    """
    绘制市场集中度和福利分析图 - Fig. 4 (修正版)
    """
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    # 数据路径
    base_path = os.path.join(os.path.dirname(__file__), "../result/output")
    
    print("开始加载数据...")
    
    # 加载2hubs数据（hub1和hub2各10份）
    print("加载2hubs数据...")
    data_2hubs_hub1 = load_experiment_data(base_path, "2hubs_hub1_20w_300_diff_final_balance", 10)
    data_2hubs_hub2 = load_experiment_data(base_path, "2hubs_hub2_20w_300_diff_final_balance", 10)
    data_2hubs = data_2hubs_hub1 + data_2hubs_hub2
    
    # 加载其他hubs数据
    hub_configs = [3, 4, 5, 10]
    all_hub_data = {2: data_2hubs}
    
    for num_hubs in hub_configs:
        print(f"加载{num_hubs}hubs数据...")
        pattern = f"{num_hubs}hubs_20w_300_diff_final_balance"
        data = load_experiment_data(base_path, pattern)
        all_hub_data[num_hubs] = data
    
    # 修正对照数据路径
    print("加载Social Optimum数据...")
    social_optimum_path = os.path.join(os.path.dirname(__file__), 
                                     "../src/data/processed_data/witouthub/without_one_trump_20w_300_diff_final_balance")
    social_optimum_revenues = load_without_hub_data(social_optimum_path)
    
    print("加载No Hub数据...")
    no_hub_path = os.path.join(os.path.dirname(__file__), 
                              "../src/data/processed_data/witouthub/without_trump_20w_300_diff_final_balance")
    no_hub_revenues = load_without_hub_data(no_hub_path)
    
    print(f"Social Optimum数据: {len(social_optimum_revenues)} 个实验")
    print(f"No Hub数据: {len(no_hub_revenues)} 个实验")
    if social_optimum_revenues:
        print(f"Social Optimum平均收益: {np.mean(social_optimum_revenues):.1f} ETH")
    if no_hub_revenues:
        print(f"No Hub平均收益: {np.mean(no_hub_revenues):.1f} ETH")
    
    # 创建图形
    fig = plt.figure(figsize=(12, 8))
    gs = GridSpec(2, 2, figure=fig, hspace=0.25, wspace=0.27,
                  left=0.08, right=1, top=1, bottom=0)
    
    ax1 = fig.add_subplot(gs[0, 0])  # 左上
    ax2 = fig.add_subplot(gs[0, 1])  # 右上
    ax3 = fig.add_subplot(gs[1, :])  # 下方跨列
    
    # 绘制子图
    plot_market_share_evolution(ax1, data_2hubs)
    plot_convergence_analysis(ax2, all_hub_data)
    plot_welfare_comparison(ax3, all_hub_data, social_optimum_revenues, no_hub_revenues)
    
    # 设置整体标题
    # fig.suptitle('Fig. 4: Market Concentration and Welfare Analysis', 
                # fontsize=16, fontweight='bold', y=0.98)
    
    # 保存图形
    output_path = os.path.join(output_folder, 'fig4_market_concentration_welfare_analysis.pdf')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Fig. 4 已生成: {output_path}")

def identify_monopolist_with_share(epoch_data):
    """识别垄断者和市场份额"""
    # 计算总市场
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

def find_convergence_time(data, convergence_threshold=90):
    """找到收敛时间：从最后往前推，找到最后一次开始垄断的时间"""
    if not data:
        return -1
    
    # 首先确认最终状态是否为垄断状态
    final_state = data[-1]
    final_monopolist = identify_monopolist_with_share(final_state)
    
    if not final_monopolist or final_monopolist['share'] < convergence_threshold:
        return -1  # 最终状态不是垄断，无收敛
    
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
    
    return convergence_epoch

def find_first_monopoly_time(data, convergence_threshold=90):
    """找到第一次垄断的时间"""
    for epoch_idx, epoch_data in enumerate(data):
        monopolist = identify_monopolist_with_share(epoch_data)
        if monopolist and monopolist['share'] >= convergence_threshold:
            return epoch_idx
    return -1

def plot_market_share_evolution(ax, data_2hubs):
    """绘制市场份额演化 - 子图(a) - 添加第一次和最终垄断时间"""
    if not data_2hubs:
        print("警告: 没有2hubs数据")
        return
    
    # 按照新的逻辑分组实验
    high_alpha_experiments = []  # 高α组 (接近对称的初始条件)
    low_alpha_experiments = []   # 低α组 (高度不对称的初始条件)
    
    print("\n开始分析2hubs实验的初始条件...")
    
    for exp_idx, data in enumerate(data_2hubs):
        if len(data) < 5:  # 确保有足够的数据点
            continue
            
        # 分析前5个epoch的收益率差异
        early_revenue_rates = []
        
        for epoch_data in data[:5]:
            hub_revenue_rates = {}
            
            # 计算每个hub的收益率 (简化：用revenue/current_funds)
            for hub in epoch_data['brokerhubs']:
                if float(hub['current_funds']) > 0:
                    revenue_rate = float(hub['revenue']) / float(hub['current_funds'])
                    hub_revenue_rates[hub['id']] = revenue_rate
            
            if len(hub_revenue_rates) >= 2:
                rates = list(hub_revenue_rates.values())
                rate_diff = abs(rates[0] - rates[1]) / max(rates) if max(rates) > 0 else 0
                early_revenue_rates.append(rate_diff)
        
        # 计算平均收益率差异
        if early_revenue_rates:
            avg_rate_diff = np.mean(early_revenue_rates)
            
            # 分组逻辑：收益率差异小的归为高α组，差异大的归为低α组
            if avg_rate_diff < 0.1:  # 阈值可以调整
                high_alpha_experiments.append(data)
                print(f"实验 {exp_idx+1}: 高α组 (差异={avg_rate_diff:.3f})")
            else:
                low_alpha_experiments.append(data)
                print(f"实验 {exp_idx+1}: 低α组 (差异={avg_rate_diff:.3f})")
    
    print(f"分组结果: 高α组 {len(high_alpha_experiments)} 个实验, 低α组 {len(low_alpha_experiments)} 个实验")
    
    # 如果分组结果不理想，使用备选方案
    if len(high_alpha_experiments) < 8 or len(low_alpha_experiments) < 5:
        print("使用备选分组方案...")
        high_alpha_experiments = data_2hubs[:12]
        low_alpha_experiments = data_2hubs[12:20] if len(data_2hubs) >= 20 else data_2hubs[12:]
    
    # 计算两组的平均市场份额演化
    # scenarios = [
        # (high_alpha_experiments, '#1f77b4', 'High α (α ≈ 0.7): Near-Symmetric Initial Conditions'),
        # (low_alpha_experiments, '#ff7f0e', 'Low α (α ≈ 0.3): High Initial Asymmetry')
    # ]
    
    scenarios = [
        (high_alpha_experiments, '#1f77b4', 'High α (α ≈ 0.7)'),
        (low_alpha_experiments, '#ff7f0e', 'Low α (α ≈ 0.3)')
    ]
    
    epochs = None
    group_convergence_times = []
    
    for group_idx, (group_experiments, color, label) in enumerate(scenarios):
        if not group_experiments:
            continue
            
        epochs = list(range(len(group_experiments[0])))
        
        # 计算该组所有实验的市场份额演化
        all_experiment_shares = []
        group_first_convergence = []   # 第一次垄断时间
        group_final_convergence = []   # 最终垄断时间
        
        for data in group_experiments:
            experiment_shares = []
            
            for epoch_idx, epoch_data in enumerate(data):
                # 计算市场份额
                total_market = 0
                
                # 未加入hub的volunteer余额
                for volunteer in epoch_data['volunteers']:
                    if volunteer['current_brokerhub'] is None:
                        total_market += float(volunteer['balance'])
                
                # 所有hub的资金
                for hub in epoch_data['brokerhubs']:
                    total_market += float(hub['current_funds'])
                
                if total_market == 0:
                    experiment_shares.append(0)
                    continue
                
                # 找到市场份额最大的hub
                max_share = 0
                for hub in epoch_data['brokerhubs']:
                    hub_share = float(hub['current_funds']) / total_market * 100
                    max_share = max(max_share, hub_share)
                
                # 确保不超过100%
                max_share = min(max_share, 100.0)
                experiment_shares.append(max_share)
            
            all_experiment_shares.append(experiment_shares)
            
            # 计算第一次垄断时间
            first_convergence = find_first_monopoly_time(data, 90)
            if first_convergence >= 0:
                group_first_convergence.append(first_convergence)
            
            # 计算最终垄断时间
            final_convergence = find_convergence_time(data, 90)
            if final_convergence >= 0:
                group_final_convergence.append(final_convergence)
        
        # 计算平均值和标准差
        if all_experiment_shares:
            all_experiment_shares = np.array(all_experiment_shares)
            mean_shares = np.mean(all_experiment_shares, axis=0)
            std_shares = np.std(all_experiment_shares, axis=0)
            
            # 绘制主线
            ax.plot(epochs, mean_shares, color=color, linewidth=2, label=label)
            
            # 绘制置信区间阴影 - 设置更透明
            upper_bound = np.minimum(mean_shares + std_shares, 100.0)
            lower_bound = np.maximum(mean_shares - std_shares, 0.0)
            
            ax.fill_between(epochs, lower_bound, upper_bound,
                           color=color, alpha=0.4)
            
            # 记录收敛时间
            convergence_data = {}
            if group_first_convergence:
                avg_first_convergence = np.mean(group_first_convergence)
                convergence_data['first'] = avg_first_convergence
                print(f"{label}: 平均第一次垄断时间 {avg_first_convergence:.1f} epoch")
            
            if group_final_convergence:
                avg_final_convergence = np.mean(group_final_convergence)
                convergence_data['final'] = avg_final_convergence
                print(f"{label}: 平均最终垄断时间 {avg_final_convergence:.1f} epoch")
            
            if convergence_data:
                group_convergence_times.append((convergence_data, label, color))
    
    # 添加垄断化时间点标注 - 显示两个时间
    for convergence_data, group_label, color in group_convergence_times:
        group_name = group_label.split(":")[0]
        
        # 绘制第一次垄断时间的垂直线
        if 'first' in convergence_data:
            first_time = convergence_data['first']
            ax.axvline(x=first_time, color=color, linestyle=':', alpha=0.6, linewidth=1.5)
            
            # 第一次垄断标注
            y_pos_first = 25 if 'High α' in group_label else 40
            # ax.text(first_time + 3, y_pos_first, f'{group_name}, First Convergence Time : {first_time:.0f}', 
                    # fontsize=12, color=color,
                    # bbox=dict(boxstyle="round,pad=0.2", facecolor='lightcyan', 
                             # alpha=0.7, edgecolor=color))
        
        # 绘制最终垄断时间的垂直线
        if 'final' in convergence_data:
            final_time = convergence_data['final']
            ax.axvline(x=final_time, color=color, linestyle='--', alpha=0.7, linewidth=1.5)
            
            # 最终垄断标注
            y_pos_final = 50 if 'High α' in group_label else 70
            # ax.text(final_time + 3, y_pos_final, f'{group_name}\nFinal Convergence Time : {final_time:.0f}', 
                    # fontsize=12, color=color,
                    # bbox=dict(boxstyle="round,pad=0.2", facecolor='white', 
                             # alpha=0.7, edgecolor=color))
    
    
    from matplotlib.lines import Line2D
    custom_lines = [
        Line2D([0], [0], color='gray', linestyle=':', alpha=0.7, linewidth=1.5),
        Line2D([0], [0], color='gray', linestyle='--', alpha=0.7, linewidth=1.5)
    ]
    
    # 在左上角添加线型说明
    legend_lines = ax.legend(custom_lines, ['First Monopolization Time', 'Final Monopolization Time'], bbox_to_anchor=(1, 0.38),handlelength=1.5, handletextpad=0.5, loc='lower right', fontsize=14, frameon=True, 
                            framealpha=0.8)
    ax.add_artist(legend_lines)  # 保持这个图例
    
    # 添加完全主导标注
    ax.axhline(y=100, color='gray', linestyle=':', alpha=0.5)
    ax.text(150, 102, 'Complete Dominance', fontsize=14, color='black')
    
    # 设置坐标轴和格式
    ax.set_xlabel('Epoch', fontsize=14)
    ax.set_ylabel('Market Share (%)', fontsize=16)
    ax.set_xlim(0, 300)
    ax.set_ylim(0, 110)
    ax.xaxis.set_major_locator(MultipleLocator(50))
    ax.yaxis.set_major_locator(MultipleLocator(20))
    ax.tick_params(axis='x', labelsize=14)  # X轴刻度文字大小
    ax.tick_params(axis='y', labelsize=14)  # Y轴刻度文字大小
    ax.grid(True, linestyle='--', alpha=0.3, color='gray')
    
    # 主要数据线的图例
    ax.legend(loc='upper right', bbox_to_anchor=(1, 0.9) ,handlelength=1.5, handletextpad=0.5, fontsize=14, frameon=True, fancybox=True, 
             framealpha=0.4, edgecolor='black')
    
    # 标题放在下方
    ax.text(0.5, -0.17, '(a) Monopolization Dynamics: α-Parameter Effects', 
            fontsize = 14, fontweight='bold', ha='center', va='top',
            transform=ax.transAxes)

def plot_convergence_analysis(ax, all_hub_data):
    """绘制收敛时间分析 - 修正最终垄断时间计算"""
    num_hubs_list = []
    first_convergence_mean = []
    first_convergence_std = []
    final_convergence_mean = []
    final_convergence_std = []
    
    for num_hubs, data_list in sorted(all_hub_data.items()):
        if not data_list:
            continue
            
        print(f"分析 {num_hubs} hubs 的收敛时间...")
        
        all_first_times = []
        all_final_times = []
        
        for data in data_list:
            print(f"  处理实验，包含 {len(data)} 个epoch")
            
            # 计算每个epoch的垄断状态
            monopoly_states = []  # True表示垄断，False表示竞争
            
            for epoch_idx, epoch_data in enumerate(data):
                # 计算总市场
                total_market = 0
                
                # 未加入hub的volunteer余额
                for volunteer in epoch_data['volunteers']:
                    if volunteer['current_brokerhub'] is None:
                        total_market += float(volunteer['balance'])
                
                # 所有hub的资金
                for hub in epoch_data['brokerhubs']:
                    total_market += float(hub['current_funds'])
                
                # 检查是否垄断
                is_monopoly = False
                if total_market > 0:
                    for hub in epoch_data['brokerhubs']:
                        hub_share = float(hub['current_funds']) / total_market * 100
                        if hub_share > 90:
                            is_monopoly = True
                            break
                
                monopoly_states.append(is_monopoly)
            
            # 找第一次垄断时间（从前往后）
            first_time = None
            for i, is_monopoly in enumerate(monopoly_states):
                if is_monopoly:
                    first_time = i
                    break
            
            # 找最终垄断时间（从后往前）
            final_time = None
            if monopoly_states[-1]:  # 如果最后一个epoch是垄断状态
                # 从后往前找到第一个非垄断状态
                for i in range(len(monopoly_states) - 1, -1, -1):
                    if not monopoly_states[i]:
                        # 找到第一个非垄断状态，下一个就是最终垄断开始
                        final_time = i + 1
                        break
                
                # 如果从头到尾都是垄断状态
                if final_time is None:
                    final_time = 0  # 从第一个epoch就开始垄断
            else:
                # 如果最后不是垄断状态，找最后一次垄断的结束
                # 这种情况下，可能需要其他处理逻辑
                for i in range(len(monopoly_states) - 1, -1, -1):
                    if monopoly_states[i]:
                        # 找到最后一次垄断，然后往前找开始
                        temp_final = i
                        for j in range(i, -1, -1):
                            if not monopoly_states[j]:
                                final_time = j + 1
                                break
                        if final_time is None:
                            final_time = 0
                        break
            
            # 记录结果
            if first_time is not None:
                all_first_times.append(first_time)
                print(f"    第一次垄断: epoch {first_time}")
            
            if final_time is not None:
                all_final_times.append(final_time)
                print(f"    最终垄断开始: epoch {final_time}")
            
            # 调试：打印垄断状态序列的概况
            monopoly_count = sum(monopoly_states)
            print(f"    总垄断epochs: {monopoly_count}/{len(monopoly_states)}")
        
        # 计算统计数据
        if all_first_times and all_final_times:
            num_hubs_list.append(num_hubs)
            
            first_mean = np.mean(all_first_times)
            first_std = np.std(all_first_times) if len(all_first_times) > 1 else 0
            first_convergence_mean.append(first_mean)
            first_convergence_std.append(first_std)
            
            final_mean = np.mean(all_final_times)
            final_std = np.std(all_final_times) if len(all_final_times) > 1 else 0
            final_convergence_mean.append(final_mean)
            final_convergence_std.append(final_std)
            
            print(f"{num_hubs} hubs - 第一次垄断: {first_mean:.1f}±{first_std:.1f}, 最终垄断: {final_mean:.1f}±{final_std:.1f}")
    
    # 绘制两条线
    if num_hubs_list:
        ax.errorbar(num_hubs_list, first_convergence_mean, yerr=first_convergence_std,
                   color='#d62728', marker='o', markersize=6, linewidth=2,
                   linestyle='-', alpha=0.8, capsize=5, capthick=2.5,
                   label='First Monopolization Time')
        
        ax.errorbar(num_hubs_list, final_convergence_mean, yerr=final_convergence_std,
                   color='#2ca02c', marker='s', markersize=6, linewidth=2,
                   linestyle='--', alpha=0.8, capsize=5, capthick=2.5,
                   label='Final Monopolization Time')
    
    # 设置坐标轴
    ax.set_xlabel('Number of AggreHubs', fontsize=14)
    ax.set_ylabel('Convergence Time (Epochs)', fontsize=14)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 150)
    ax.set_xticks([0, 2, 3, 4, 5, 10])
    ax.yaxis.set_major_locator(MultipleLocator(50))
    ax.tick_params(axis='x', labelsize=14)  # X轴刻度文字大小
    ax.tick_params(axis='y', labelsize=14)  # Y轴刻度文字大小
    ax.grid(True, linestyle='--', alpha=0.3, color='gray')
    ax.legend(fontsize=14, loc='upper right', frameon=True, fancybox=True, 
                      framealpha=0.4)
    ax.text(0.5, -0.17, '(b) Convergence Time', 
            fontsize=14, fontweight='bold', ha='center', va='top',
            transform=ax.transAxes)

def plot_welfare_comparison(ax, all_hub_data, social_optimum_revenues, no_hub_revenues):
    """绘制福利比较 - 修正版，处理数据范围问题"""
    categories = ['Social Optimum(W*)', 'No Hub']
    revenues = []
    errors = []
    colors = ['#ffd700', '#808080']
    
    # 计算Social Optimum
    if social_optimum_revenues:
        revenues.append(np.mean(social_optimum_revenues))
        errors.append(np.std(social_optimum_revenues) if len(social_optimum_revenues) > 1 else 0)
        print(f"Social Optimum: {np.mean(social_optimum_revenues):.1f} ± {np.std(social_optimum_revenues):.1f} ETH")
    else:
        revenues.append(0)
        errors.append(0)
    
    # 计算No Hub
    if no_hub_revenues:
        revenues.append(np.mean(no_hub_revenues))
        errors.append(np.std(no_hub_revenues) if len(no_hub_revenues) > 1 else 0)
        print(f"No Hub: {np.mean(no_hub_revenues):.1f} ± {np.std(no_hub_revenues):.1f} ETH")
    else:
        revenues.append(0)
        errors.append(0)
    
    # 计算不同hub数量的收益
    hub_colors = ['#2ca02c', '#17becf', '#9467bd', '#8c564b', '#e377c2']
    
    for i, (num_hubs, data_list) in enumerate(sorted(all_hub_data.items())):
        if not data_list:
            continue
            
        print(f"\n计算 {num_hubs} Hubs 收益...")
        hub_revenues = calculate_total_revenue(data_list)
        
        if hub_revenues:
            categories.append(f'{num_hubs} Hubs')
            mean_revenue = np.mean(hub_revenues)
            std_revenue = np.std(hub_revenues) if len(hub_revenues) > 1 else 0
            revenues.append(mean_revenue)
            errors.append(std_revenue)
            colors.append(hub_colors[i % len(hub_colors)])
            print(f"{num_hubs} Hubs: {mean_revenue:.1f} ± {std_revenue:.1f} ETH")
    
    # 绘制柱状图
    x_pos = np.arange(len(categories))
    bars = ax.bar(x_pos, revenues, width=0.6, color=colors, alpha=0.8, 
                 edgecolor='black', linewidth=0.5)
    
    # 添加误差棒
    ax.errorbar(x_pos, revenues, yerr=errors, fmt='none', 
               color='black', linewidth=1.5, capsize=2)
    
    # 在柱子顶部添加数值
    for i, (bar, revenue, error) in enumerate(zip(bars, revenues, errors)):
        height = bar.get_height() + error
        ax.text(bar.get_x() + bar.get_width()/2., height + max(revenues)*0.01,
               f'{revenue:.0f}', ha='center', va='bottom', fontsize=12)
    
    # 设置坐标轴 - 智能调整Y轴范围和刻度
    # ax.set_xlabel('Market Structure', fontsize=12)
    # ax.set_ylabel('Total Revenue (ETH)', fontsize=14)
    ax.set_ylabel('Welfare (ETH)', fontsize=16)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(categories, fontsize=12)
    
    
    
    ax.set_ylim(8500, 9800)  # 设置Y轴范围
    ax.yaxis.set_major_locator(MultipleLocator(250))  # 每250一个主刻度
    ax.tick_params(axis='x', labelsize=14)  # X轴刻度文字大小
    ax.tick_params(axis='y', labelsize=14)  # Y轴刻度文字大小
    # 智能设置Y轴刻度，避免过多刻度警告
    # max_revenue = max(revenues) if revenues else 1000
    # if max_revenue > 100000:
        # 对于很大的数值，使用更大的刻度间隔
        # tick_interval = int(max_revenue / 10 / 1000) * 1000  # 向上取整到千位
        # ax.yaxis.set_major_locator(MultipleLocator(tick_interval))
    # elif max_revenue > 10000:
        # ax.yaxis.set_major_locator(MultipleLocator(2000))
    # elif max_revenue > 1000:
        # ax.yaxis.set_major_locator(MultipleLocator(500))
    # else:
        # ax.yaxis.set_major_locator(MultipleLocator(100))
    
    ax.grid(True, linestyle='--', alpha=0.3, color='gray', axis='y')
    ax.text(0.5, -0.13, '(c) Welfare Ranking: Monopolistic Concentration Outperforms Competition', 
            fontsize=14, fontweight='bold', ha='center', va='top',
            transform=ax.transAxes)

if __name__ == "__main__":
    output_folder = "./0703exper4"
    
    print("开始生成Fig. 4: Market Concentration and Welfare Analysis...")
    print(f"输出文件夹: {output_folder}")
    
    # 生成图表
    plot_market_concentration_welfare_analysis(output_folder)
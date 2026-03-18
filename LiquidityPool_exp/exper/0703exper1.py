import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys

# 设置matplotlib样式
plt.rcParams['font.size'] = 10
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['xtick.labelsize'] = 12
plt.rcParams['ytick.labelsize'] = 12

def load_experiment_data(base_path, experiment_prefix, num_runs=10):
    """
    加载实验数据
    """
    data = []
    
    for i in range(1, num_runs + 1):
        if experiment_prefix == "2hubs_hub2_20w_300_diff_final_balance":
            if i == 1 or i == 3:
                continue
        
        filename = f"simulation_results_{experiment_prefix}{i}.json"
        filepath = os.path.join(base_path, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                result = json.load(f)
                data.append(result)
            print(f"已加载: {filename}")
        else:
            print(f"警告: 找不到文件 {filename}")
    
    return data

def get_hub_info(epoch_data):
    """
    获取两个hub的详细信息
    """
    hub1_info = None
    hub2_info = None
    
    for hub in epoch_data['brokerhubs']:
        if hub['id'] == 'BrokerHub1':
            hub1_info = {
                'funds': float(hub['current_funds']),
                'revenue': float(hub['b2e_revenue']),
                'users': len(hub['users']),
                'total_user_funds': float(hub['total_user_funds'])
            }
        elif hub['id'] == 'BrokerHub2':
            hub2_info = {
                'funds': float(hub['current_funds']),
                'revenue': float(hub['b2e_revenue']),
                'users': len(hub['users']),
                'total_user_funds': float(hub['total_user_funds'])
            }
    
    return hub1_info, hub2_info

def calculate_revenue_rate(hub_info):
    """
    计算收益率 (revenue / funds)
    """
    if hub_info['funds'] > 0:
        return hub_info['revenue'] / hub_info['funds']
    else:
        return 0

def calculate_market_share_trajectory(experiment_data, max_epochs=300):
    """
    计算市场份额轨迹
    """
    hub1_trajectory = []
    hub2_trajectory = []
    
    total_epochs = min(len(experiment_data), max_epochs)
    
    for epoch_idx in range(total_epochs):
        epoch_data = experiment_data[epoch_idx]
        hub1_info, hub2_info = get_hub_info(epoch_data)
        
        # 计算市场份额
        total_funds = hub1_info['funds'] + hub2_info['funds']
        if total_funds > 0:
            hub1_share = (hub1_info['funds'] / total_funds) * 100
            hub2_share = (hub2_info['funds'] / total_funds) * 100
        else:
            hub1_share = 50.0
            hub2_share = 50.0
        
        hub1_trajectory.append(hub1_share)
        hub2_trajectory.append(hub2_share)
    
    return hub1_trajectory, hub2_trajectory

def find_convergence_time(hub1_trajectory, hub2_trajectory, threshold=95):
    """
    找到收敛时间（一方达到threshold%市场份额的时间）
    """
    for epoch_idx in range(len(hub1_trajectory)):
        if hub1_trajectory[epoch_idx] >= threshold or hub2_trajectory[epoch_idx] >= threshold:
            return epoch_idx
    
    # 如果没有达到threshold，返回最后一个epoch
    return len(hub1_trajectory) - 1

def determine_initial_leader(experiment_data):
    """
    根据epoch 0的收益率确定初始领先者
    """
    epoch_0_data = experiment_data[0]
    hub1_info, hub2_info = get_hub_info(epoch_0_data)
    
    hub1_rate = calculate_revenue_rate(hub1_info)
    hub2_rate = calculate_revenue_rate(hub2_info)
    
    if hub1_rate > hub2_rate:
        return 'Hub1', hub1_rate, hub2_rate
    elif hub2_rate > hub1_rate:
        return 'Hub2', hub1_rate, hub2_rate
    else:
        return 'Tie', hub1_rate, hub2_rate

def determine_final_winner(experiment_data):
    """
    确定最终胜利者
    """
    last_epoch_data = experiment_data[-1]
    hub1_info, hub2_info = get_hub_info(last_epoch_data)
    
    if hub1_info['funds'] > hub2_info['funds']:
        return 'Hub1'
    elif hub2_info['funds'] > hub1_info['funds']:
        return 'Hub2'
    else:
        return 'Tie'

def plot_path_dependence_mixed_trajectories(input_folder, output_folder, experiments_per_scenario=5):
    """
    绘制路径依赖性混合轨迹-箱线图
    """
    try:
        # 创建输出文件夹
        os.makedirs(output_folder, exist_ok=True)
        
        # 加载所有数据
        print("正在加载所有实验数据...")
        scenario_a_data = load_experiment_data(input_folder, "2hubs_hub1_20w_300_diff_final_balance")
        scenario_b_data = load_experiment_data(input_folder, "2hubs_hub2_20w_300_diff_final_balance")
        
        all_experiments = scenario_a_data + scenario_b_data
        
        if not all_experiments:
            print("错误: 无法加载实验数据")
            return None
        
        print(f"总共加载了 {len(all_experiments)} 个实验")
        
        # 分析所有实验的初始领先者
        print("\n分析所有实验的初始收益率...")
        experiment_analysis = []
        
        for i, experiment in enumerate(all_experiments):
            initial_leader, hub1_rate, hub2_rate = determine_initial_leader(experiment)
            final_winner = determine_final_winner(experiment)
            
            if(hub1_rate == hub2_rate):
                continue
            
            experiment_analysis.append({
                'index': i,
                'initial_leader': initial_leader,
                'final_winner': final_winner,
                'hub1_initial_rate': hub1_rate,
                'hub2_initial_rate': hub2_rate,
                'data': experiment
            })  
            
            print(f"实验 {i+1}: 初始领先者={initial_leader} (Hub1率={hub1_rate:.8f}, Hub2率={hub2_rate:.8f}), 最终胜利者={final_winner}")
        
        # 按初始领先者分组并选择样本
        hub1_lead_experiments = [exp for exp in experiment_analysis if exp['initial_leader'] == 'Hub1']
        hub2_lead_experiments = [exp for exp in experiment_analysis if exp['initial_leader'] == 'Hub2']
        
        print(f"\nHub1初始领先: {len(hub1_lead_experiments)} 个实验")
        print(f"Hub2初始领先: {len(hub2_lead_experiments)} 个实验")
        
        # 选择前N个实验
        selected_hub1_experiments = hub1_lead_experiments[:experiments_per_scenario]
        selected_hub2_experiments = hub2_lead_experiments[:experiments_per_scenario]
        
        print(f"选择Hub1领先实验: {len(selected_hub1_experiments)} 个")
        print(f"选择Hub2领先实验: {len(selected_hub2_experiments)} 个")
        
        if len(selected_hub1_experiments) < experiments_per_scenario or len(selected_hub2_experiments) < experiments_per_scenario:
            print(f"警告: 数据不足，实际使用 Hub1:{len(selected_hub1_experiments)} 个, Hub2:{len(selected_hub2_experiments)} 个")
        
        # 计算轨迹数据
        print("\n计算轨迹数据...")
        
        # Hub1领先场景
        hub1_scenario_trajectories = {'hub1': [], 'hub2': [], 'convergence_times': [], 'final_winners': []}
        for exp in selected_hub1_experiments:
            hub1_traj, hub2_traj = calculate_market_share_trajectory(exp['data'])
            convergence_time = find_convergence_time(hub1_traj, hub2_traj)
            
            hub1_scenario_trajectories['hub1'].append(hub1_traj)
            hub1_scenario_trajectories['hub2'].append(hub2_traj)
            hub1_scenario_trajectories['convergence_times'].append(convergence_time)
            hub1_scenario_trajectories['final_winners'].append(exp['final_winner'])
        
        # Hub2领先场景
        hub2_scenario_trajectories = {'hub1': [], 'hub2': [], 'convergence_times': [], 'final_winners': []}
        for exp in selected_hub2_experiments:
            hub1_traj, hub2_traj = calculate_market_share_trajectory(exp['data'])
            convergence_time = find_convergence_time(hub1_traj, hub2_traj)
            
            hub2_scenario_trajectories['hub1'].append(hub1_traj)
            hub2_scenario_trajectories['hub2'].append(hub2_traj)
            hub2_scenario_trajectories['convergence_times'].append(convergence_time)
            hub2_scenario_trajectories['final_winners'].append(exp['final_winner'])
        
        # 创建图形
        print("开始绘图...")
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
        
        # 子图A: Hub1初始领先场景轨迹图
        print("绘制子图A...")
        if hub1_scenario_trajectories['hub1']:
            # 确保所有轨迹长度一致
            min_length = min(len(traj) for traj in hub1_scenario_trajectories['hub1'])
            epochs = list(range(min_length))
            
            # 截取轨迹
            hub1_trajs = [traj[:min_length] for traj in hub1_scenario_trajectories['hub1']]
            hub2_trajs = [traj[:min_length] for traj in hub1_scenario_trajectories['hub2']]
            
            # 绘制半透明轨迹线
            for i in range(len(hub1_trajs)):
                ax1.plot(epochs, hub1_trajs[i], 'b-', alpha=0.3, linewidth=1)
                ax1.plot(epochs, hub2_trajs[i], 'r-', alpha=0.3, linewidth=1)
            
            # 计算统计数据
            hub1_median = np.median(hub1_trajs, axis=0)
            hub2_median = np.median(hub2_trajs, axis=0)
            hub1_p25 = np.percentile(hub1_trajs, 25, axis=0)
            hub1_p75 = np.percentile(hub1_trajs, 75, axis=0)
            hub2_p25 = np.percentile(hub2_trajs, 25, axis=0)
            hub2_p75 = np.percentile(hub2_trajs, 75, axis=0)
            
            # 绘制置信区间
            ax1.fill_between(epochs, hub1_p25, hub1_p75, color='blue', alpha=0.2)
            ax1.fill_between(epochs, hub2_p25, hub2_p75, color='red', alpha=0.2)
            
            # 绘制中位数轨迹
            ax1.plot(epochs, hub1_median, 'b-', linewidth=3, label='Hub1')
            ax1.plot(epochs, hub2_median, 'r-', linewidth=3, label='Hub2')
            
            # 统计最终胜利者
            hub1_wins = hub1_scenario_trajectories['final_winners'].count('Hub1')
            hub2_wins = hub1_scenario_trajectories['final_winners'].count('Hub2')
            
            # 添加标注
            ax1.text(0.98, 0.98, f'Hub1: {hub1_wins}/{len(selected_hub1_experiments)}\nHub2: {hub2_wins}/{len(selected_hub1_experiments)}',
                    transform=ax1.transAxes, ha='right', va='top',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.8),
                    fontsize=10, fontweight='bold')
        
        ax1.set_title('Scenario A: Hub1 Initially Leads', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Epoch', fontsize=12)
        ax1.set_ylabel('Market Share (%)', fontsize=12)
        ax1.set_xlim(0, 300)
        ax1.set_ylim(0, 100)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # 子图B: Hub2初始领先场景轨迹图
        print("绘制子图B...")
        if hub2_scenario_trajectories['hub1']:
            # 确保所有轨迹长度一致
            min_length = min(len(traj) for traj in hub2_scenario_trajectories['hub1'])
            epochs = list(range(min_length))
            
            # 截取轨迹
            hub1_trajs = [traj[:min_length] for traj in hub2_scenario_trajectories['hub1']]
            hub2_trajs = [traj[:min_length] for traj in hub2_scenario_trajectories['hub2']]
            
            # 绘制半透明轨迹线
            for i in range(len(hub1_trajs)):
                ax2.plot(epochs, hub1_trajs[i], 'b-', alpha=0.3, linewidth=1)
                ax2.plot(epochs, hub2_trajs[i], 'r-', alpha=0.3, linewidth=1)
            
            # 计算统计数据
            hub1_median = np.median(hub1_trajs, axis=0)
            hub2_median = np.median(hub2_trajs, axis=0)
            hub1_p25 = np.percentile(hub1_trajs, 25, axis=0)
            hub1_p75 = np.percentile(hub1_trajs, 75, axis=0)
            hub2_p25 = np.percentile(hub2_trajs, 25, axis=0)
            hub2_p75 = np.percentile(hub2_trajs, 75, axis=0)
            
            # 绘制置信区间
            ax2.fill_between(epochs, hub1_p25, hub1_p75, color='blue', alpha=0.2)
            ax2.fill_between(epochs, hub2_p25, hub2_p75, color='red', alpha=0.2)
            
            # 绘制中位数轨迹
            ax2.plot(epochs, hub1_median, 'b-', linewidth=3)
            ax2.plot(epochs, hub2_median, 'r-', linewidth=3)
            
            # 统计最终胜利者
            hub1_wins = hub2_scenario_trajectories['final_winners'].count('Hub1')
            hub2_wins = hub2_scenario_trajectories['final_winners'].count('Hub2')
            
            # 添加标注
            ax2.text(0.98, 0.98, f'Hub1: {hub1_wins}/{len(selected_hub2_experiments)}\nHub2: {hub2_wins}/{len(selected_hub2_experiments)}',
                    transform=ax2.transAxes, ha='right', va='top',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral", alpha=0.8),
                    fontsize=10, fontweight='bold')
        
        ax2.set_title('Scenario B: Hub2 Initially Leads', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Epoch', fontsize=12)
        ax2.set_xlim(0, 300)
        ax2.set_ylim(0, 100)
        ax2.grid(True, alpha=0.3)
        
        # 子图C: 收敛时间箱线图
        print("绘制子图C...")
        convergence_data = [
            hub1_scenario_trajectories['convergence_times'],
            hub2_scenario_trajectories['convergence_times']
        ]
        
        box_plot = ax3.boxplot(convergence_data, labels=['Hub1 Initially Leads', 'Hub2 Initially Leads'],
                              patch_artist=True)
        
        # 设置箱线图颜色
        colors = ['lightblue', 'lightcoral']
        for patch, color in zip(box_plot['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        # 添加散点显示原始数据
        for i, data in enumerate(convergence_data):
            x = [i + 1] * len(data)
            ax3.scatter(x, data, alpha=0.6, s=30, color=['blue', 'red'][i])
        
        ax3.set_title('Convergence Time Distribution', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Convergence Time (Epochs)', fontsize=12)
        ax3.grid(True, alpha=0.3)
        
        # 调整子图间距
        plt.subplots_adjust(wspace=0.3)
        plt.tight_layout()
        
        # 保存图形
        output_path = os.path.join(output_folder, 'path_dependence_mixed_trajectories.png')
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        
        output_path_pdf = os.path.join(output_folder, 'path_dependence_mixed_trajectories.pdf')
        plt.savefig(output_path_pdf, dpi=200, bbox_inches='tight', facecolor='white')
        
        plt.close()
        
        print("图片保存成功!")
        
        # 打印统计总结
        print("\n" + "="*80)
        print("路径依赖性混合轨迹分析总结")
        print("="*80)
        
        print(f"\n场景A (Hub1初始收益率领先) - {len(selected_hub1_experiments)}个实验:")
        hub1_scenario_hub1_wins = hub1_scenario_trajectories['final_winners'].count('Hub1')
        hub1_scenario_hub2_wins = hub1_scenario_trajectories['final_winners'].count('Hub2')
        print(f"  最终胜利者: Hub1={hub1_scenario_hub1_wins}, Hub2={hub1_scenario_hub2_wins}")
        print(f"  平均收敛时间: {np.mean(hub1_scenario_trajectories['convergence_times']):.1f} epochs")
        print(f"  收敛时间范围: {min(hub1_scenario_trajectories['convergence_times'])}-{max(hub1_scenario_trajectories['convergence_times'])} epochs")
        
        print(f"\n场景B (Hub2初始收益率领先) - {len(selected_hub2_experiments)}个实验:")
        hub2_scenario_hub1_wins = hub2_scenario_trajectories['final_winners'].count('Hub1')
        hub2_scenario_hub2_wins = hub2_scenario_trajectories['final_winners'].count('Hub2')
        print(f"  最终胜利者: Hub1={hub2_scenario_hub1_wins}, Hub2={hub2_scenario_hub2_wins}")
        print(f"  平均收敛时间: {np.mean(hub2_scenario_trajectories['convergence_times']):.1f} epochs")
        print(f"  收敛时间范围: {min(hub2_scenario_trajectories['convergence_times'])}-{max(hub2_scenario_trajectories['convergence_times'])} epochs")
        
        # 路径依赖验证
        scenario_a_path_dependence = hub1_scenario_hub1_wins / len(selected_hub1_experiments) * 100
        scenario_b_path_dependence = hub2_scenario_hub2_wins / len(selected_hub2_experiments) * 100
        
        print(f"\n路径依赖验证:")
        print(f"  场景A路径依赖率: {scenario_a_path_dependence:.1f}% (初始领先者获胜)")
        print(f"  场景B路径依赖率: {scenario_b_path_dependence:.1f}% (初始领先者获胜)")
        
        overall_path_dependence = (hub1_scenario_hub1_wins + hub2_scenario_hub2_wins) / (len(selected_hub1_experiments) + len(selected_hub2_experiments)) * 100
        print(f"  总体路径依赖率: {overall_path_dependence:.1f}%")
        
        print(f"\n图表已保存到:")
        print(f"PNG: {output_path}")
        print(f"PDF: {output_path_pdf}")
        
        return {
            'scenario_a': {
                'hub1_wins': hub1_scenario_hub1_wins,
                'hub2_wins': hub1_scenario_hub2_wins,
                'convergence_times': hub1_scenario_trajectories['convergence_times']
            },
            'scenario_b': {
                'hub1_wins': hub2_scenario_hub1_wins,
                'hub2_wins': hub2_scenario_hub2_wins,
                'convergence_times': hub2_scenario_trajectories['convergence_times']
            },
            'path_dependence_rates': {
                'scenario_a': scenario_a_path_dependence,
                'scenario_b': scenario_b_path_dependence,
                'overall': overall_path_dependence
            }
        }
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # =========================== 参数设置 ===========================
    input_folder = "../result/output"  # 输入文件夹路径
    output_folder = "./0703path_dependence"  # 输出文件夹路径
    experiments_per_scenario = 5  # 每个场景使用的实验数量，可调整为10
    
    # =================================================================
    
    # 构建完整路径
    input_path = os.path.join(os.path.dirname(__file__), input_folder)
    
    # 检查输入文件夹是否存在
    if not os.path.exists(input_path):
        print(f"错误：找不到输入文件夹 {input_path}")
        print(f"请确保文件夹存在并检查路径设置")
        sys.exit(1)
    
    print(f"开始分析路径依赖性混合轨迹...")
    print(f"输入文件夹: {input_path}")
    print(f"输出文件夹: {output_folder}")
    print(f"每个场景实验数量: {experiments_per_scenario}")
    
    result = plot_path_dependence_mixed_trajectories(input_path, output_folder, experiments_per_scenario)
    
    if result is None:
        print("分析失败，请检查错误信息")
    else:
        print("\n🎉 路径依赖性混合轨迹分析完成!")
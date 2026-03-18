import matplotlib.pyplot as plt
import numpy as np
import json
import os
import glob
from scipy import stats

def load_experiment_data(base_path, experiment_pattern, num_files=None):
    """加载实验数据"""
    experiment_files = []
    
    if num_files is None:
        pattern = f"simulation_results_{experiment_pattern}*.json"
        files = glob.glob(os.path.join(base_path, pattern))
        experiment_files = sorted(files)
    else:
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

def calculate_alpha_parameter_corrected(epoch_0_data, epoch_t_data):
    """
    修正版α参数计算：去除LiquidityPool初始资金，只考虑用户投资
    """
    # 1. 获取epoch 0时各LiquidityPool的初始资金
    initial_funds_map = {}
    for hub_0 in epoch_0_data['brokerhubs']:
        hub_id = hub_0['id']
        initial_funds = float(hub_0['current_funds'])
        initial_funds_map[hub_id] = initial_funds
    
    # 2. 计算各LiquidityPool获得的纯用户投资
    pool_user_investments = []
    pool_ids = []
    
    for hub_t in epoch_t_data['brokerhubs']:
        hub_id = hub_t['id']
        current_funds = float(hub_t['current_funds'])
        
        # 获取该pool的初始资金
        initial_funds = initial_funds_map.get(hub_id, 0)
        
        # 纯用户投资 = 当前资金 - 初始资金
        user_investment = current_funds - initial_funds
        user_investment = max(0, user_investment)  # 确保非负
        
        pool_user_investments.append(user_investment)
        pool_ids.append(hub_id)
    
    if len(pool_user_investments) < 2:
        return None, None, None, None
    
    # 3. 计算总用户投资和平均投资
    total_user_investment = sum(pool_user_investments)
    num_pools = len(pool_user_investments)
    
    if total_user_investment == 0:
        # 如果没有用户投资，认为是完全对称
        return 1.0, [0] * num_pools, pool_user_investments, 0
    
    avg_investment = total_user_investment / num_pools
    
    # 4. 计算每个pool的标准化偏差 ε_b
    epsilons = []
    for investment in pool_user_investments:
        epsilon_b = (investment - avg_investment) / avg_investment
        epsilons.append(epsilon_b)
    
    # 5. 验证 ∑ε_b = 0 (应该接近0)
    epsilon_sum = sum(epsilons)
    
    # 6. 计算最大绝对偏差
    max_epsilon = max(abs(eps) for eps in epsilons)
    
    # 7. 根据公式计算α: max|ε_b| ≤ (1-α)/α，因此 α = 1/(1 + max|ε_b|)
    if max_epsilon == 0:
        alpha = 1.0  # 完全对称
    else:
        alpha = 1.0 / (1.0 + max_epsilon)
    
    return alpha, epsilons, pool_user_investments, max_epsilon

def calculate_max_market_share(epoch_data):
    """计算某个epoch的最大市场份额"""
    total_market = 0
    
    for volunteer in epoch_data['volunteers']:
        if volunteer['current_brokerhub'] is None:
            total_market += float(volunteer['balance'])
    
    for hub in epoch_data['brokerhubs']:
        total_market += float(hub['current_funds'])
    
    if total_market == 0:
        return 0, None
    
    max_share = 0
    dominant_hub_id = None
    
    for hub in epoch_data['brokerhubs']:
        hub_share = float(hub['current_funds']) / total_market * 100
        if hub_share > max_share:
            max_share = hub_share
            dominant_hub_id = hub['id']
    
    return max_share, dominant_hub_id

def analyze_multiple_convergences(data, convergence_threshold=90):
    """分析一个实验中的多轮收敛"""
    convergences = []
    current_state = "competing"
    monopoly_start = None
    
    for epoch_idx, epoch_data in enumerate(data):
        max_share, dominant_hub = calculate_max_market_share(epoch_data)
        
        if max_share >= convergence_threshold:
            if current_state == "competing":
                monopoly_start = epoch_idx
                current_state = "monopolized"
                convergences.append({
                    'convergence_time': epoch_idx,
                    'monopolist': dominant_hub
                })
        else:
            if current_state == "monopolized":
                current_state = "competing"
                monopoly_start = None
    
    return convergences

def process_experiments_by_config(data_list, config_name):
    """处理单个配置的实验数据，计算α参数但不分组"""
    experiments_with_alpha = []
    
    print(f"\n开始处理{config_name}配置的实验...")
    
    for exp_idx, data in enumerate(data_list):
        if len(data) < 10:  # 确保有足够数据
            continue
        
        print(f"\n{config_name} 实验 {exp_idx+1}:")
        
        # 使用epoch 0作为初始状态，epoch 5-10的平均状态作为稳定后的投资状态
        epoch_0_data = data[0]
        
        # 选择一个较早但稳定的epoch来计算α（避免太早期的波动）
        target_epochs = [5, 6, 7, 8, 9]  # 使用多个epoch的平均值
        alpha_values = []
        
        for epoch_idx in target_epochs:
            if epoch_idx < len(data):
                epoch_t_data = data[epoch_idx]
                alpha, epsilons, investments, max_eps = calculate_alpha_parameter_corrected(
                    epoch_0_data, epoch_t_data)
                
                if alpha is not None:
                    alpha_values.append(alpha)
                    print(f"      Epoch {epoch_idx}: α = {alpha:.4f}")
        
        if alpha_values:
            # 使用多个epoch的平均α值
            avg_alpha = np.mean(alpha_values)
            std_alpha = np.std(alpha_values)
            
            print(f"    平均α值: {avg_alpha:.4f} ± {std_alpha:.4f}")
            
            experiments_with_alpha.append({
                'data': data,
                'exp_idx': exp_idx,
                'alpha': avg_alpha,
                'alpha_std': std_alpha,
                'alpha_values': alpha_values,
                'config': config_name
            })
        else:
            print(f"    无法计算α参数")
    
    print(f"\n{config_name}配置实验的α值分布:")
    for exp in experiments_with_alpha:
        print(f"实验 {exp['exp_idx']+1}: α = {exp['alpha']:.4f} ± {exp['alpha_std']:.4f}")
    
    return experiments_with_alpha

def plot_alpha_convergence_analysis_corrected(output_folder):
    """绘制基于修正α参数的收敛分析图"""
    
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    # 数据路径
    base_path = os.path.join(os.path.dirname(__file__), "../result/output")
    
    # 加载三种配置的数据
    print("加载三种配置的2hubs数据...")
    
    # 1. 极端不均衡配置
    # data_severe_hub1 = load_experiment_data(base_path, "2hubs_hub1_20w_300_diff_final_balance", 10)
    data_severe_hub2 = load_experiment_data(base_path, "2hubs_hub2_20w_300_diff_final_balance", 10)
    # data_severe_all = data_severe_hub1 + data_severe_hub2
    data_severe_all =  data_severe_hub2
    
    # 2. 中等均衡配置
    data_medium = load_experiment_data(base_path, "2hubs_20w_300_diff_final_balance_medium", 5)
    
    # 3. 完全均衡配置
    data_fully = load_experiment_data(base_path, "2hubs_20w_300_diff_final_balance_fully", 5)
    
    print(f"极端不均衡: {len(data_severe_all)} 个实验")
    print(f"中等均衡: {len(data_medium)} 个实验")
    print(f"完全均衡: {len(data_fully)} 个实验")
    
    # 处理每种配置的实验数据
    configs_experiments = {}
    
    configs_experiments['severe'] = process_experiments_by_config(data_severe_all, "极端不均衡")
    configs_experiments['medium'] = process_experiments_by_config(data_medium, "中等均衡")
    configs_experiments['fully'] = process_experiments_by_config(data_fully, "完全均衡")
    
    # 分析每个实验的多轮收敛
    print("\n=== 分析多轮收敛信息 ===")
    for config_name, experiments in configs_experiments.items():
        print(f"\n{config_name}配置:")
        for exp in experiments:
            convergences = analyze_multiple_convergences(exp['data'], 90)
            exp['convergences'] = convergences
            exp['convergence_count'] = len(convergences)
            
            if convergences:
                print(f"  实验 {exp['exp_idx']+1} (α={exp['alpha']:.4f}): 收敛{len(convergences)}次, 时间点{[c['convergence_time'] for c in convergences]}")
            else:
                print(f"  实验 {exp['exp_idx']+1} (α={exp['alpha']:.4f}): 未收敛")
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(7, 5))
    
    # 绘制散点图
    plot_alpha_scatter_corrected(ax, configs_experiments)
    
    # 保存图形
    plt.tight_layout()
    output_path = os.path.join(output_folder, 'alpha_parameter_analysis_by_config.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    output_path_pdf = os.path.join(output_folder, 'alpha_parameter_analysis_by_config.pdf')
    plt.savefig(output_path_pdf, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n修正α参数收敛分析图已生成:")
    print(f"PNG: {output_path}")
    print(f"PDF: {output_path_pdf}")

def plot_alpha_scatter_corrected(ax, configs_experiments):
    """绘制基于修正α参数的收敛散点图 - 三种配置分别显示"""
    
    # 三种配置的颜色和形状
    config_styles = {
        'severe': {'color': 'g', 'marker': 's', 'name': 'Whale-dominated'},           # 绿色方形
        'medium': {'color': 'tab:blue', 'marker': 'o', 'name': 'Mixed participant'},   # 蓝色圆形
        'fully': {'color': 'darkorange', 'marker': '^', 'name': 'Equal distribution'}       # 橙色三角形
    }
    
    # 统一的散点大小
    uniform_size = 160
    
    all_alphas = []
    all_convergence_times = []
    
    # 遍历三种配置
    for config_key, experiments in configs_experiments.items():
        if not experiments:
            continue
            
        style = config_styles[config_key]
        config_color = style['color']
        marker = style['marker']
        config_name = style['name']
        
        print(f"\n绘制{config_name}配置: {len(experiments)}个实验")
        
        # 收集当前配置的数据用于趋势线
        config_x = []
        config_y = []
        
        for exp in experiments:
            alpha_val = exp['alpha']
            convergences = exp.get('convergences', [])
            
            if not convergences:
                continue
            
            # 计算X轴偏移，避免同一α值的多个散点重叠
            x_offsets = []
            if len(convergences) == 1:
                x_offsets = [0]
            else:
                offset_range = 0.002  # 偏移范围
                x_offsets = np.linspace(-offset_range, offset_range, len(convergences))
            
            # 绘制该实验的所有收敛点
            exp_x = []
            exp_y = []
            
            for i, (conv, x_offset) in enumerate(zip(convergences, x_offsets)):
                point_x = alpha_val + x_offset
                point_y = conv['convergence_time']
                
                # 绘制散点
                ax.scatter(point_x, point_y, s=uniform_size, c=config_color, marker=marker, 
                          alpha=0.8, edgecolors='black', linewidth=1, zorder=4)
                
                exp_x.append(point_x)
                exp_y.append(point_y)
                config_x.append(point_x)
                config_y.append(point_y)
                
                # 记录全局数据
                all_alphas.append(point_x)
                all_convergence_times.append(point_y)
            
            # 如果有多个收敛点，用线连接同一实验的所有点
            if len(exp_x) > 1:
                sorted_points = sorted(zip(exp_x, exp_y), key=lambda p: p[1])
                sorted_x, sorted_y = zip(*sorted_points)
                
                ax.plot(sorted_x, sorted_y, color=config_color, alpha=0.4, 
                       linewidth=2, linestyle='-', zorder=2)
        
        # 绘制当前配置的趋势线和相关系数标注
        if len(config_x) > 1:
            z = np.polyfit(config_x, config_y, 1)
            p = np.poly1d(z)
            x_trend = np.linspace(min(config_x), max(config_x), 100)
            
            # 可选：绘制趋势线
            # ax.plot(x_trend, p(x_trend), color=config_color, linewidth=3, 
                   # alpha=0.8, linestyle='--', zorder=3)
            
            # 相关系数
            r, p_val = stats.pearsonr(config_x, config_y)
            print(f"  {config_name}: r={r:.3f}, p={p_val:.5f}")
            
            # 自定义每个配置的text位置
            text_positions = {
                'severe': (0.535, 122),    # 极端不均衡
                'medium': (0.59, 122),     # 中等均衡  
                'fully': (0.65, 130)       # 完全均衡
            }
            
            text_x, text_y = text_positions.get(config_key, (0.5, 50))
            if(p_val > 0.1):
                ax.text(text_x, text_y, f'r={r:.3f}\np={p_val:.3f}', 
                       fontsize=20, ha='center', va='center', color=config_color,
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='white', 
                               alpha=0.8, edgecolor=config_color),
                       fontweight='bold')
            else:
                ax.text(text_x, text_y, f'r={r:.3f}\np<0.001', 
                       fontsize=20, ha='center', va='center', color=config_color,
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='white', 
                               alpha=0.8, edgecolor=config_color),
                       fontweight='bold')
    
    # 全局趋势线（可选）
    if len(all_alphas) > 2:
        z_global = np.polyfit(all_alphas, all_convergence_times, 1)
        p_global = np.poly1d(z_global)
        x_global = np.linspace(min(all_alphas), max(all_alphas), 100)
        
        # 绘制全局趋势线
        # ax.plot(x_global, p_global(x_global), color='black', linewidth=2, 
               # alpha=0.6, linestyle=':', zorder=1)
        
        r_global, p_val_global = stats.pearsonr(all_alphas, all_convergence_times)
        print(f"\n全局相关性: r={r_global:.3f}, p={p_val_global:.5f}")
        
        # 全局相关系数标注
        # ax.text(0.02, 0.98, f'Overall: r={r_global:.3f}, p={p_val_global:.5f}', 
               # transform=ax.transAxes, fontsize=16, ha='left', va='top',
               # bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', 
                       # alpha=0.9, edgecolor='black'),
               # fontweight='bold')
    
    # 设置坐标轴和格式
    ax.set_xlabel('α Parameter', fontsize=25)
    ax.set_ylabel('Convergence epoch', fontsize=25)
    
    from matplotlib.ticker import MultipleLocator

    # 设置坐标轴范围
    # if all_alphas:
        # ax.set_xlim(min(all_alphas) - 0.01, min(1.0, max(all_alphas) + 0.01))
    ax.set_xlim(0.49, 0.68)
    ax.xaxis.set_major_locator(MultipleLocator(0.05))
    ax.set_ylim(0, 220)
    
    # 网格
    ax.grid(True, linestyle='--', alpha=0.3)
    
    # 创建图例 - 3种配置
    legend_elements = []
    for config_key, style in config_styles.items():
        if config_key in configs_experiments and configs_experiments[config_key]:
            legend_elements.append(plt.scatter([], [], s=uniform_size, 
                                             c=style['color'], marker=style['marker'], 
                                             edgecolors='black', linewidth=1, 
                                             label=style['name'], alpha=0.8))
    
    # 添加全局趋势线到图例
    # if len(all_alphas) > 2:
        # legend_elements.append(plt.plot([], [], color='black', alpha=0.6, linewidth=2,
                                       # linestyle=':', label='Overall trend')[0])
    
    ax.legend(handles=legend_elements, loc='upper right', fontsize=20,
             bbox_to_anchor=(0.6, 1.03), handlelength=0.7, handletextpad=0.4, markerscale=1,
             frameon=True, fancybox=True, framealpha=0.9, borderpad=0.4)
    
    # 设置字体大小
    ax.tick_params(axis='both', labelsize=25)
    
    print("\n修正α参数收敛分析图绘制完成！")

if __name__ == "__main__":
    output_folder = "./0801exper4"
    
    print("开始生成基于配置类型的α参数收敛分析图...")
    print(f"输出文件夹: {output_folder}")
    
    # 生成图表
    plot_alpha_convergence_analysis_corrected(output_folder)
    
    print("\n配置类型α参数收敛分析图生成完成！")
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

def classify_experiments_by_alpha_corrected(data_list, config_name):
    """根据修正的α参数对单个配置进行分组"""
    experiments_with_alpha = []
    
    print(f"\n开始计算{config_name}的修正α参数...")
    
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
    
    # 按α值排序
    experiments_with_alpha.sort(key=lambda x: x['alpha'])
    
    print(f"\n{config_name}实验的α值分布:")
    for exp in experiments_with_alpha:
        print(f"实验 {exp['exp_idx']+1}: α = {exp['alpha']:.4f} ± {exp['alpha_std']:.4f}")
    
    # 分组：简单二分法
    if len(experiments_with_alpha) >= 2:
        mid_point = len(experiments_with_alpha) // 2
        lower_alpha_experiments = experiments_with_alpha[:mid_point]
        higher_alpha_experiments = experiments_with_alpha[mid_point:]
        
        print(f"\n{config_name}按α值分组:")
        print(f"Lower α组: {len(lower_alpha_experiments)} 个实验")
        print(f"Higher α组: {len(higher_alpha_experiments)} 个实验")
    else:
        lower_alpha_experiments = experiments_with_alpha
        higher_alpha_experiments = []
    
    return lower_alpha_experiments, higher_alpha_experiments

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
    data_severe_all = data_severe_hub2
    
    # 2. 中等均衡配置
    data_medium = load_experiment_data(base_path, "2hubs_20w_300_diff_final_balance_medium", 5)
    
    # 3. 完全均衡配置
    data_fully = load_experiment_data(base_path, "2hubs_20w_300_diff_final_balance_fully", 5)
    
    print(f"极端不均衡: {len(data_severe_all)} 个实验")
    print(f"中等均衡: {len(data_medium)} 个实验")
    print(f"完全均衡: {len(data_fully)} 个实验")
    
    # 对每种配置分别进行α值分组
    configs_grouped = {}
    
    # 分组每种配置
    severe_lower, severe_higher = classify_experiments_by_alpha_corrected(data_severe_all, "极端不均衡")
    medium_lower, medium_higher = classify_experiments_by_alpha_corrected(data_medium, "中等均衡")
    fully_lower, fully_higher = classify_experiments_by_alpha_corrected(data_fully, "完全均衡")
    
    # 存储分组结果
    configs_grouped = {
        'severe': {'lower': severe_lower, 'higher': severe_higher},
        'medium': {'lower': medium_lower, 'higher': medium_higher},
        'fully': {'lower': fully_lower, 'higher': fully_higher}
    }
    
    # 分析每个实验的多轮收敛
    print("\n=== 分析多轮收敛信息 ===")
    for config_name, groups in configs_grouped.items():
        print(f"\n{config_name}配置:")
        for group_name, experiments in groups.items():
            print(f"  {group_name} α组:")
            for exp in experiments:
                convergences = analyze_multiple_convergences(exp['data'], 90)
                exp['convergences'] = convergences
                exp['convergence_count'] = len(convergences)
                
                if convergences:
                    print(f"    实验 {exp['exp_idx']+1} (α={exp['alpha']:.4f}): 收敛{len(convergences)}次, 时间点{[c['convergence_time'] for c in convergences]}")
                else:
                    print(f"    实验 {exp['exp_idx']+1} (α={exp['alpha']:.4f}): 未收敛")
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # 绘制散点图
    plot_alpha_scatter_corrected(ax, configs_grouped)
    
    # 保存图形
    plt.tight_layout()
    output_path = os.path.join(output_folder, 'subfig3_corrected_alpha_parameter_analysis.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    output_path_pdf = os.path.join(output_folder, 'subfig3_corrected_alpha_parameter_analysis.pdf')
    plt.savefig(output_path_pdf, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n修正α参数收敛分析图已生成:")
    print(f"PNG: {output_path}")
    print(f"PDF: {output_path_pdf}")

def plot_alpha_scatter_corrected(ax, configs_grouped):
    """绘制基于修正α参数的收敛散点图 - 支持三种配置"""
    
    # 三种配置的颜色
    config_colors = {
        'severe': 'g',           # 绿色 - 极端不均衡
        'medium': 'tab:blue',    # 蓝色 - 中等均衡  
        'fully': 'darkorange'    # 橙色 - 完全均衡
    }
    
    config_names = {
        'severe': 'Severe Imbalance',
        'medium': 'Moderate Balance',
        'fully': 'Full Balance'
    }
    
    # α值分组的形状
    alpha_markers = {
        'lower': 's',    # 方形 - Lower α
        'higher': 'o'    # 圆形 - Higher α
    }
    
    alpha_names = {
        'lower': 'Lower α',
        'higher': 'Higher α'
    }
    
    # 统一的散点大小
    uniform_size = 160
    
    all_alphas = []
    all_convergence_times = []
    
    # 遍历三种配置
    for config_key, groups in configs_grouped.items():
        config_color = config_colors[config_key]
        config_name = config_names[config_key]
        
        print(f"\n绘制{config_name}配置:")
        
        # 遍历Lower α和Higher α组
        for alpha_group_key, experiments in groups.items():
            marker = alpha_markers[alpha_group_key]
            alpha_group_name = alpha_names[alpha_group_key]
            
            print(f"  {alpha_group_name}组: {len(experiments)}个实验")
            
            # 收集当前组的数据用于趋势线
            group_x = []
            group_y = []
            
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
                              alpha=0.7, edgecolors='black', linewidth=1, zorder=4)
                    
                    exp_x.append(point_x)
                    exp_y.append(point_y)
                    group_x.append(point_x)
                    group_y.append(point_y)
                    
                    # 记录全局数据
                    all_alphas.append(point_x)
                    all_convergence_times.append(point_y)
                
                # 如果有多个收敛点，用线连接同一实验的所有点
                if len(exp_x) > 1:
                    sorted_points = sorted(zip(exp_x, exp_y), key=lambda p: p[1])
                    sorted_x, sorted_y = zip(*sorted_points)
                    
                    ax.plot(sorted_x, sorted_y, color=config_color, alpha=0.4, 
                           linewidth=2, linestyle='-', zorder=2)
            
            # 绘制每个组的趋势线和相关系数标注
            if len(group_x) > 1:
                z = np.polyfit(group_x, group_y, 1)
                p = np.poly1d(z)
                x_trend = np.linspace(min(group_x), max(group_x), 100)
                
                # 相关系数
                r, p_val = stats.pearsonr(group_x, group_y)
                print(f"    {alpha_group_name}: r={r:.3f}, p={p_val:.5f}")
                
                # 自定义每个组合的text位置
                text_positions = {
                    ('severe', 'lower'): (0.555, 110),
                    ('severe', 'higher'): (0.555, 50),
                    ('medium', 'lower'): (0.555, 90),
                    ('medium', 'higher'): (0.555, 70),
                    ('fully', 'lower'): (0.555, 80),
                    ('fully', 'higher'): (0.555, 40)
                }
                
                text_x, text_y = text_positions.get((config_key, alpha_group_key), (0.5, 50))
                
                ax.text(text_x, text_y, f'r={r:.3f}\np={p_val:.5f}', 
                       fontsize=16, ha='center', va='center', color=config_color,
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='white', 
                               alpha=0.9, edgecolor=config_color),
                       fontweight='bold')
    
    # 设置坐标轴和格式
    ax.set_xlabel('α Parameter', fontsize=25)
    ax.set_ylabel('Convergence epoch', fontsize=25)
    
    # 设置坐标轴范围
    if all_alphas:
        ax.set_xlim(min(all_alphas) - 0.01, min(1.0, max(all_alphas) + 0.01))
    ax.set_ylim(0, 125)
    
    # 网格
    ax.grid(True, linestyle='--', alpha=0.3)
    
    # 创建图例 - 6种组合
    legend_elements = []
    for config_key, config_color in config_colors.items():
        config_name = config_names[config_key]
        for alpha_key, marker in alpha_markers.items():
            alpha_name = alpha_names[alpha_key]
            label = f'{config_name} {alpha_name}'
            
            legend_elements.append(plt.scatter([], [], s=uniform_size, c=config_color, marker=marker, 
                                             edgecolors='black', linewidth=1, 
                                             label=label, alpha=0.7))
    
    ax.legend(handles=legend_elements, loc='upper right', fontsize=16,
             bbox_to_anchor=(1.0, 1.0), handlelength=0.7, handletextpad=0.1, markerscale=1,
             frameon=True, fancybox=True, framealpha=0.9, borderpad=0.3)
    
    # 设置字体大小
    ax.tick_params(axis='both', labelsize=25)
    
    print("\n修正α参数收敛分析图绘制完成！")

if __name__ == "__main__":
    output_folder = "./0801exper3"
    
    print("开始生成基于修正α参数的收敛分析图...")
    print(f"输出文件夹: {output_folder}")
    
    # 生成图表
    plot_alpha_convergence_analysis_corrected(output_folder)
    
    print("\n修正α参数收敛分析图生成完成！")
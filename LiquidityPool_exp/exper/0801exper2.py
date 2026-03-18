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
    
    print(f"    初始资金: {[initial_funds_map.get(pid, 0) for pid in pool_ids]}")
    print(f"    当前资金: {[hub['current_funds'] for hub in epoch_t_data['brokerhubs']]}")
    print(f"    用户投资: {pool_user_investments}")
    print(f"    总用户投资: {total_user_investment:.2f}")
    print(f"    平均投资: {avg_investment:.2f}")
    print(f"    ε_b值: {[f'{eps:.4f}' for eps in epsilons]}")
    print(f"    ε_b和: {epsilon_sum:.6f}")
    print(f"    max|ε_b|: {max_epsilon:.4f}")
    print(f"    计算得α: {alpha:.4f}")
    
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

def classify_experiments_by_alpha_corrected(data_2hubs):
    """根据修正的α参数进行分组"""
    experiments_with_alpha = []
    
    print("\n开始计算每个实验的修正α参数...")
    
    for exp_idx, data in enumerate(data_2hubs):
        if len(data) < 10:  # 确保有足够数据
            continue
        
        print(f"\n实验 {exp_idx+1}:")
        
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
                'alpha_values': alpha_values
            })
        else:
            print(f"    无法计算α参数")
    
    # 按α值排序
    experiments_with_alpha.sort(key=lambda x: x['alpha'])
    
    print(f"\n所有实验的α值分布:")
    for exp in experiments_with_alpha:
        print(f"实验 {exp['exp_idx']+1}: α = {exp['alpha']:.4f} ± {exp['alpha_std']:.4f}")
    
    # 计算整体α值统计
    all_alphas = [exp['alpha'] for exp in experiments_with_alpha]
    if all_alphas:
        alpha_median = np.median(all_alphas)
        print(f"\nα值统计: 中位数 = {alpha_median:.4f}")
        print(f"α值范围: [{min(all_alphas):.4f}, {max(all_alphas):.4f}]")
    
    # 分组：以中位数为界，或者使用更明确的阈值
    if len(experiments_with_alpha) >= 6:
        # 如果样本足够，按三分位数分组，取两端
        sorted_exps = sorted(experiments_with_alpha, key=lambda x: x['alpha'])
        n = len(sorted_exps)
        
        # 取α值最低的1/3和最高的1/3
        lower_third = n // 3
        upper_third = 2 * n // 3
        
        lower_alpha_experiments = sorted_exps[:lower_third]
        higher_alpha_experiments = sorted_exps[upper_third:]
        
        print(f"\n按α值分组 (三分位法):")
        print(f"Lower α组 (α值最低1/3，更不对称): {len(lower_alpha_experiments)} 个实验")
        for exp in lower_alpha_experiments:
            print(f"  实验 {exp['exp_idx']+1}: α = {exp['alpha']:.4f}")
        
        print(f"Higher α组 (α值最高1/3，更对称): {len(higher_alpha_experiments)} 个实验")
        for exp in higher_alpha_experiments:
            print(f"  实验 {exp['exp_idx']+1}: α = {exp['alpha']:.4f}")
    
    else:
        # 样本较少时，简单二分
        mid_point = len(experiments_with_alpha) // 2
        lower_alpha_experiments = experiments_with_alpha[:mid_point]
        higher_alpha_experiments = experiments_with_alpha[mid_point:]
        
        print(f"\n按α值分组 (二分法):")
        print(f"Lower α组: {len(lower_alpha_experiments)} 个实验")
        print(f"Higher α组: {len(higher_alpha_experiments)} 个实验")
    
    return lower_alpha_experiments, higher_alpha_experiments

def plot_alpha_convergence_analysis_corrected(output_folder):
    """绘制基于修正α参数的收敛分析图"""
    
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    # 数据路径
    base_path = os.path.join(os.path.dirname(__file__), "../result/output")
    
    print("加载2hubs数据...")
    # 加载所有2hubs数据
    data_2hubs_hub1 = load_experiment_data(base_path, "2hubs_hub1_20w_300_diff_final_balance", 10)
    data_2hubs_hub2 = load_experiment_data(base_path, "2hubs_hub2_20w_300_diff_final_balance", 10)
    data_2hubs_all = data_2hubs_hub1 + data_2hubs_hub2
    
    print(f"总共加载了 {len(data_2hubs_all)} 个2hubs实验")
    
    # 根据修正的α参数分组
    lower_alpha_experiments, higher_alpha_experiments = classify_experiments_by_alpha_corrected(data_2hubs_all)
    
    # 分析每个实验的多轮收敛
    print("\n=== 分析多轮收敛信息 ===")
    for group_name, experiments in [("Lower α组", lower_alpha_experiments), ("Higher α组", higher_alpha_experiments)]:
        print(f"\n{group_name}:")
        for exp in experiments:
            print(f"实验 {exp['exp_idx']+1} (α={exp['alpha']:.4f}):")
            convergences = analyze_multiple_convergences(exp['data'], 90)
            exp['convergences'] = convergences
            exp['convergence_count'] = len(convergences)
            
            if convergences:
                print(f"  收敛次数: {len(convergences)}")
                print(f"  收敛时间点: {[c['convergence_time'] for c in convergences]}")
            else:
                print(f"  未发生收敛")
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(7, 5))
    
    # 绘制散点图
    plot_alpha_scatter_corrected(ax, lower_alpha_experiments, higher_alpha_experiments)
    
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

def plot_alpha_scatter_corrected(ax, lower_alpha_experiments, higher_alpha_experiments):
    """绘制基于修正α参数的收敛散点图"""
    
    colors = ['#ff7f0e', '#1f77b4']  # 橙色(Lower α)、蓝色(Higher α)
    markers = ['s', 'o']  # 方块、圆圈
    labels = ['Lower α', 'Higher α']
    
    # 统一的散点大小
    uniform_size = 160
    
    all_alphas = []
    all_convergence_times = []
    
    for group_idx, (experiments, color, marker, label) in enumerate(zip(
        [lower_alpha_experiments, higher_alpha_experiments], colors, markers, labels
    )):
        
        # 收集所有散点数据用于趋势线
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
                ax.scatter(point_x, point_y, s=uniform_size, c=color, marker=marker, 
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
                
                ax.plot(sorted_x, sorted_y, color=color, alpha=0.4, 
                       linewidth=2, linestyle='-', zorder=2)
        
        # 绘制分组趋势线
        if len(group_x) > 1:
            z = np.polyfit(group_x, group_y, 1)
            p = np.poly1d(z)
            x_trend = np.linspace(min(group_x), max(group_x), 100)
            # ax.plot(x_trend, p(x_trend), color=color, linewidth=3, 
                   # alpha=0.8, linestyle='--', zorder=3)
            
            # 相关系数
            r, p_val = stats.pearsonr(group_x, group_y)
            mid_x = np.mean(x_trend)
            mid_y = p(mid_x)
            
            # 自定义每个组的text位置
            if group_idx == 0:  # Lower α组
                text_x = 0.555   # 直接指定x坐标
                text_y = 110     # 直接指定y坐标
            else:  # Higher α组 
                text_x = 0.635   # 直接指定x坐标
                text_y = 50     # 直接指定y坐标
            print(r, p_val)
            ax.text(text_x, text_y, f'r={r:.3f}\np={p_val:.5f}', 
                   fontsize=20, ha='center', va='center', color=color,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', 
                           alpha=0.9, edgecolor=color),
                   fontweight='bold')
    
    # 全局趋势线
    if len(all_alphas) > 2:
        z_global = np.polyfit(all_alphas, all_convergence_times, 1)
        p_global = np.poly1d(z_global)
        x_global = np.linspace(min(all_alphas), max(all_alphas), 100)
        # ax.plot(x_global, p_global(x_global), color='black', linewidth=2, 
               # alpha=0.6, linestyle=':', zorder=1, label='Overall Trend')
        
        r_global, p_val_global = stats.pearsonr(all_alphas, all_convergence_times)
        print(f"\n全局相关性: r={r_global:.3f}, p={p_val_global:.3f}")
    
    # 计算α值的统计信息
    if all_alphas:
        alpha_mean = np.mean(all_alphas)
        alpha_std = np.std(all_alphas)
        alpha_min = min(all_alphas)
        alpha_max = max(all_alphas)
        
        # 添加α值分布信息
        stats_text = (f"α Parameter Statistics:\n"
                     f"Range: [{alpha_min:.3f}, {alpha_max:.3f}]\n"
                     f"Mean: {alpha_mean:.3f} ± {alpha_std:.3f}\n"
                     f"Based on User Investment Only")
        # ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
               # fontsize=10, va='top', ha='left',
               # bbox=dict(boxstyle="round,pad=0.4", facecolor='lightcyan', 
                       # alpha=0.9, edgecolor='blue'))
    
    # 设置坐标轴和格式
    ax.set_xlabel('α Parameter', fontsize=25)
    ax.set_ylabel('Convergence epoch', fontsize=25)
    # ax.set_title('(c) Corrected α-Parameter Effects on Convergence Patterns\n'
                # 'Based on User Investment Distribution (Excluding Initial LiquidityPool Funds)', 
                # fontsize=16, fontweight='bold', pad=20)
    
    # 设置坐标轴范围
    if all_alphas:
        ax.set_xlim(min(all_alphas) - 0.01, min(1.0, max(all_alphas) + 0.01))
    ax.set_ylim(0, 125)
    # ax.set_yticks(np.arange(0, 301, 50))
    
    # 添加理论关键点标注
    # if all_alphas and max(all_alphas) < 0.95:
        # ax.axvline(x=1.0, color='red', linestyle=':', alpha=0.7, linewidth=2)
        # ax.text(1.0, 280, 'Perfect Symmetry\n(α = 1)', fontsize=10, ha='center', va='top',
               # color='red', fontweight='bold',
               # bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
    
    # 网格
    ax.grid(True, linestyle='--', alpha=0.3)
    
    # 图例
    legend_elements = []
    for color, marker, label in zip(colors, markers, labels):
        legend_elements.append(plt.scatter([], [], s=uniform_size, c=color, marker=marker, 
                                         edgecolors='black', linewidth=1, 
                                         label=label, alpha=0.7))
    
    # legend_elements.append(plt.plot([], [], color='gray', alpha=0.4, linewidth=2,
                                   # label='Multi-convergence connection')[0])
    # legend_elements.append(plt.plot([], [], color='black', alpha=0.6, linewidth=2,
                                   # linestyle=':', label='Overall trend')[0])
    
    ax.legend(handles=legend_elements, loc='upper right', fontsize=25,
             bbox_to_anchor=(0.95, 1.02), handlelength=0.7, handletextpad = 0.1, markerscale = 1,
             frameon=True, fancybox=True, framealpha=0.9, borderpad=0.1)
    
    # 添加说明文字
    # explanation_text = (
        # "• α calculated from user investment distribution: α = 1/(1 + max|εᵦ|)\n"
        # "• εᵦ based on (user_investment - avg_investment) / avg_investment\n"
        # "• LiquidityPool initial funds excluded from calculation\n"
        # "• Each dot represents one convergence event at its actual epoch time"
    # )
    # ax.text(0.02, 0.02, explanation_text, transform=ax.transAxes, 
           # fontsize=10, va='bottom', ha='left',
           # bbox=dict(boxstyle="round,pad=0.4", facecolor='lightyellow', 
                   # alpha=0.9, edgecolor='orange'))
    
    # 设置字体大小
    ax.tick_params(axis='both', labelsize=25)
    
    print("\n修正α参数收敛分析图绘制完成！")

if __name__ == "__main__":
    output_folder = "./0801exper2"
    
    print("开始生成基于修正α参数的收敛分析图...")
    print(f"输出文件夹: {output_folder}")
    
    # 生成图表
    plot_alpha_convergence_analysis_corrected(output_folder)
    
    print("\n修正α参数收敛分析图生成完成！")
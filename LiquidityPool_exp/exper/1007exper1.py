import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys
from matplotlib.ticker import MultipleLocator
import glob
from scipy.stats import gaussian_kde

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_experiment_data_by_pattern(base_path, pattern):
    """根据模式加载实验数据"""
    search_pattern = f"simulation_results_{pattern}*.json"
    files = glob.glob(os.path.join(base_path, search_pattern))
    
    data_list = []
    for filepath in sorted(files):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                data_list.append(data)
        except Exception as e:
            print(f"加载文件 {filepath} 时出错: {e}")
    
    return data_list

def get_configuration_data(base_path):
    """获取三种配置的数据"""
    configs = {}
    
    # 严重不均衡配置 (α=0.3) - 普通的 diff_final_balance
    severe_patterns = [
        "2hubs_hub1_20w_300_diff_final_balance",
        "2hubs_hub2_20w_300_diff_final_balance", 
        "3hubs_20w_300_diff_final_balance",
        "4hubs_20w_300_diff_final_balance",
        "5hubs_20w_300_diff_final_balance",
        "10hubs_20w_300_diff_final_balance"
    ]
    
    severe_data = []
    for pattern in severe_patterns:
        data_list = load_experiment_data_by_pattern(base_path, pattern)
        severe_data.extend(data_list)
        print(f"加载 {pattern}: {len(data_list)} 个实验")
    
    configs['severe'] = severe_data
    
    # 中等均衡配置 (α=0.6) - medium
    medium_data = load_experiment_data_by_pattern(base_path, "2hubs_20w_300_diff_final_balance_medium")
    configs['medium'] = medium_data
    print(f"加载 medium: {len(medium_data)} 个实验")
    
    # 完全均衡配置 (α=0.8) - fully
    fully_data = load_experiment_data_by_pattern(base_path, "2hubs_20w_300_diff_final_balance_fully")
    configs['fully'] = fully_data
    print(f"加载 fully: {len(fully_data)} 个实验")
    
    return configs

def plot_user_distribution_pdf(ax):
    """绘制用户配置分布PDF图 - 概率密度函数"""
    base_path = os.path.join(os.path.dirname(__file__), "../result/output")
    
    # 获取三种配置的数据
    configs = get_configuration_data(base_path)
    
    def get_representative_experiment_wealth(data_list, config_name):
        if not data_list:
            print(f"警告: {config_name} 没有数据")
            return np.array([])
        
        # 只取第一个实验
        data = data_list[0]
        first_epoch = data[0]
        
        # 提取1000个用户的balance
        balances = [float(v['balance']) / 1e18 for v in first_epoch['volunteers']]
        balances = np.array(balances)
        
        print(f"{config_name}: 实验有 {len(balances)} 个用户, 余额范围 {np.min(balances):.4f} - {np.max(balances):.2f} ETH")
        return balances
    
    # 获取三种配置的代表性实验数据
    wealth_severe = get_representative_experiment_wealth(configs['severe'], "Whale-dominated")
    wealth_medium = get_representative_experiment_wealth(configs['medium'], "Mixed participant")
    wealth_fully = get_representative_experiment_wealth(configs['fully'], "Equal distribution")
    
    if len(wealth_severe) == 0 or len(wealth_medium) == 0 or len(wealth_fully) == 0:
        print("警告: 某些配置没有找到有效数据")
        return
    
    # 配置数据：颜色、线型、线宽、标签
    # 线宽从 1.8, 1.8, 2.5 放大到 3.6, 3.6, 5.0
    configs_data = [
        (wealth_severe, '#1f77b4', '-', 3.6, 'Whale-dominated'),
        (wealth_medium, '#ff7f0e', '--', 3.6, 'Mixed participant'), 
        (wealth_fully, '#1a7a1a', ':', 5.0, 'Equal distribution')
    ]
    
    # 确定x轴范围：10^-2 到 10^2
    all_wealth = np.concatenate([wealth_severe, wealth_medium, wealth_fully])
    x_min, x_max = np.min(all_wealth), np.max(all_wealth)
    x_range = np.linspace(x_min, x_max, 1000)  # 线性均匀采样
    
    # 绘制每种配置的PDF
    for wealth_data, color, linestyle, linewidth, label in configs_data:
        if len(wealth_data) > 1:
            try:
                kde = gaussian_kde(wealth_data)
                pdf_values = kde(x_range)
                
                # 只绘制线条，不填充
                ax.plot(x_range, pdf_values, color=color, linestyle=linestyle, 
                       linewidth=linewidth, label=label)
                
            except Exception as e:
                print(f"计算 {label} 的KDE时出错: {e}")
    
    # 设置坐标轴 - 字体从 13 放大到 26
    ax.set_xlabel('Stakeholder Balance (ETH)', fontsize=26)
    ax.set_ylabel('PDF', fontsize=26)
    
    # X轴对数尺度，范围 10^-2 到 10^2
    ax.set_xscale('log')
    ax.set_xlim(1e-2, 1e2)
    
    # Y轴线性尺度，范围 -0.05 到 0.85
    ax.set_ylim(-0.1, 0.9)
    ax.yaxis.set_major_locator(MultipleLocator(0.2))

    
    # 设置刻度字体大小 - 从 11 放大到 22
    ax.tick_params(axis='both', labelsize=22)
    
    # 网格和图例 - 字体从 10 放大到 20，handlelength 从 1.8 调整到 3.6
    ax.grid(True, alpha=0.3, which='major')
    ax.legend(loc='center right', fontsize=20, handlelength=1.8, framealpha=0.8)


def create_all_figures():
    """创建所有四个子图"""
    output_folder = "./1007exper1"
    os.makedirs(output_folder, exist_ok=True)
    
    # 设置全局字体参数 - 全部放大2倍
    plt.rcParams.update({
        'font.size': 22,           # 从 11 → 22
        'axes.labelsize': 26,      # 从 13 → 26
        'xtick.labelsize': 22,     # 从 11 → 22
        'ytick.labelsize': 22,     # 从 11 → 22
        'legend.fontsize': 20      # 从 10 → 20
    })
    
    # 子图1: 用户配置分布PDF图
    # 图片尺寸从 3.5×2.5 改为 7×5 英寸
    fig1, ax1 = plt.subplots(1, 1, figsize=(7, 5))
    plot_user_distribution_pdf(ax1)
    plt.tight_layout()
    
    # 保存图片，DPI=300
    fig1.savefig(os.path.join(output_folder, '1007exper1_user_distribution_pdf.png'), 
                dpi=300, bbox_inches='tight')
    fig1.savefig(os.path.join(output_folder, '1007exper1_user_distribution_pdf.pdf'), 
                dpi=300, bbox_inches='tight')
    plt.close(fig1)
    
    print("图片已保存到:", output_folder)

if __name__ == "__main__":
    create_all_figures()
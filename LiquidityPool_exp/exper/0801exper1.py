import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys
from matplotlib.ticker import MultipleLocator
import glob

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_experiment_data_by_pattern(base_path, pattern):
    """
    根据模式加载实验数据
    """
    # 构建搜索模式
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
    """
    获取三种配置的数据
    """
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
    
# 正确：每个实验都是独立的1000个用户
def analyze_single_experiment_wealth(data_list, config_name):
    """
    从单个实验中提取1000个用户的财富分布
    """
    if not data_list:
        return np.array([])
    
    # 只取第一个实验作为代表
    data = data_list[0]
    first_epoch = data[0]
    
    # 提取这1000个用户的balance
    balances = [float(v['balance']) / 1e18 for v in first_epoch['volunteers']]
    
    print(f"{config_name} 配置: 使用第一个实验，{len(balances)} 个用户")
    return np.sort(balances)  # 从小到大排序
    
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gaussian_kde

def plot_user_distribution_pdf(ax):
    """绘制用户配置分布PDF图 - 概率密度函数"""
    base_path = os.path.join(os.path.dirname(__file__), "../result/output")
    
    # 获取三种配置的数据
    configs = get_configuration_data(base_path)
    
    # 每种配置只取一个代表性实验的1000个用户
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
    wealth_severe = get_representative_experiment_wealth(configs['severe'], "严重不均衡")
    wealth_medium = get_representative_experiment_wealth(configs['medium'], "中等均衡")
    wealth_fully = get_representative_experiment_wealth(configs['fully'], "完全均衡")
    
    if len(wealth_severe) == 0 or len(wealth_medium) == 0 or len(wealth_fully) == 0:
        print("警告: 某些配置没有找到有效数据")
        return
    
    # 配置数据和颜色
    # configs_data = [
        # (wealth_severe, 'g', 'Severe Imbalance'),
        # (wealth_medium, 'tab:blue', 'Moderate Balance'), 
        # (wealth_fully, 'darkorange', 'Full Balance')
    # ]
    configs_data = [
        (wealth_severe, 'g', 'Whale-dominated'),
        (wealth_medium, 'tab:blue', 'Mixed participant'), 
        (wealth_fully, 'darkorange', 'Equal distribution')
    ]
    
    # 确定共同的x轴范围
    all_wealth = np.concatenate([wealth_severe, wealth_medium, wealth_fully])
    x_min, x_max = np.min(all_wealth), np.max(all_wealth)
    
    # 创建用于PDF计算的x轴点
    x_range = np.linspace(x_min, x_max, 1000)
    
    # 绘制每种配置的PDF
    for wealth_data, color, label in configs_data:
        # 方法1: 使用直方图估计PDF
        # n, bins, patches = ax.hist(wealth_data, bins=50, alpha=0.5, color=color, 
        #                           density=True, label=label)
        
        # 方法2: 使用核密度估计 (KDE) 获得更平滑的PDF
        if len(wealth_data) > 1:  # 确保有足够的数据点
            try:
                kde = gaussian_kde(wealth_data)
                pdf_values = kde(x_range)
                
                # 填充区域图显示PDF
                ax.fill_between(x_range, 0, pdf_values, alpha=0.5, color=color, label=label)
                
                # 也可以添加边界线
                ax.plot(x_range, pdf_values, color=color, linewidth=2, alpha=0.8)
                
            except Exception as e:
                print(f"计算 {label} 的KDE时出错: {e}")
                # 降级到直方图方法
                ax.hist(wealth_data, bins=50, alpha=0.5, color=color, 
                       density=True, label=label)
    
    # 设置坐标轴
    ax.set_xlabel('Stakeholder Balance (ETH)', fontsize=25)
    ax.set_ylabel('PDF', fontsize=25)
    
    # 设置x轴为对数尺度（如果数据跨度很大）
    if x_max / x_min > 100:  # 如果数据跨度超过100倍，使用对数尺度
        ax.set_xscale('log')
    
    ax.set_xlim(x_min * 0.9, x_max * 1.1)
    
    # 网格和图例
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right', fontsize=25, bbox_to_anchor=(1, 0.95))
    
    # ax.set_title('User Balance Distribution PDF', fontsize=14, fontweight='bold')


def create_all_figures():
    """创建所有四个子图"""
    output_folder = "./0801exper1"
    os.makedirs(output_folder, exist_ok=True)
    
    # 设置字体大小
    plt.rcParams.update({
        'font.size': 10,
        'axes.titlesize': 14,
        'axes.labelsize': 12,
        'xtick.labelsize': 25,
        'ytick.labelsize': 25,
        'legend.fontsize': 25
    })
    
    # 子图1: 用户配置分布图
    # fig1, ax1 = plt.subplots(1, 1, figsize=(6, 4))
    # plot_user_distribution(ax1)
    # plt.tight_layout()
    
    
    
    
    # 保存图1
    # fig1.savefig(os.path.join(output_folder, '0801exper1_user_distribution.png'), 
                # dpi=300, bbox_inches='tight')
    # fig1.savefig(os.path.join(output_folder, '0801exper1_user_distribution.pdf'), 
                # dpi=300, bbox_inches='tight')
    # plt.close(fig1)
    
    # 子图1: 用户配置分布图
    fig1, ax1 = plt.subplots(1, 1, figsize=(7, 5))
    plot_user_distribution_pdf(ax1)
    plt.tight_layout()
    
    
    
    
    # 保存图1
    fig1.savefig(os.path.join(output_folder, '0801exper1_user_distribution_pdf.png'), 
                dpi=300, bbox_inches='tight')
    fig1.savefig(os.path.join(output_folder, '0801exper1_user_distribution_pdf.pdf'), 
                dpi=300, bbox_inches='tight')
    plt.close(fig1)
    

if __name__ == "__main__":
    create_all_figures()
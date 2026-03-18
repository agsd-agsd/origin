import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys
from scipy import stats

# 添加项目根目录到Python路径，以便导入其他模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def plot_participation_pdf(results, output_path, epoch_limit):
    """
    绘制参与率的概率密度分布图
    
    Args:
        results: 完整的结果数据
        output_path: 输出路径
        epoch_limit: epoch限制数量
    """
    # 获取所有BrokerHub的ID
    brokerhub_ids = list(set(bh['id'] for state in results for bh in state['brokerhubs']))
    brokerhub_ids.sort()
    
    # 为每个BrokerHub收集参与率数据
    participation_rates_dict = {}
    
    for bh_id in brokerhub_ids:
        participation_rates = []
        for state in results[:epoch_limit]:
            total_volunteers = len(state['volunteers'])
            bh = next((bh for bh in state['brokerhubs'] if bh['id'] == bh_id), None)
            if bh:
                participation_rate = (len(bh['users']) + 1) / (total_volunteers + 1)
                participation_rates.append(participation_rate)
        participation_rates_dict[bh_id] = participation_rates
    
    # 设置图形
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 设置颜色
    colors = ['#2E8B57', '#4682B4', '#FFA500']  # 绿色、蓝色、橙色
    
    # 为每个BrokerHub绘制概率密度分布
    for idx, (bh_id, rates) in enumerate(participation_rates_dict.items()):
        if rates:  # 确保有数据
            # 创建核密度估计
            density = stats.gaussian_kde(rates)
            
            # 创建x轴的点
            x_range = np.linspace(0, 1, 200)
            y_values = density(x_range)
            
            # 绘制填充区域
            ax.fill_between(x_range, y_values, alpha=0.6, 
                           color=colors[idx % len(colors)], 
                           label=f'{bh_id}')
            
            # 绘制线条
            ax.plot(x_range, y_values, color=colors[idx % len(colors)], linewidth=2)
    
    # 设置图形属性
    ax.set_xlabel('Participation Rate', fontsize=12)
    ax.set_ylabel('Probability Density', fontsize=12)
    ax.set_title('Distribution of Participation Rates', fontsize=14)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, None)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    
    # 保存图形
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def plot_all_graphs(results_path, output_folder, epoch_limit):
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    # 加载JSON数据
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    # 绘制参与率分布图
    plot_participation_pdf(results, 
                          os.path.join(output_folder, 'participation_rate_distribution.png'), 
                          epoch_limit)
    
    print("参与率分布图已生成！")

if __name__ == "__main__":
    # =========================== 参数设置 ===========================
    # 实验参数
    experiment_name = "trump_20w_300_diff_motivation_balance"  # 实验名称，用于文件命名
    num_epochs = 300  # 总的epoch数量，决定绘图的x轴长度
    
    # 文件路径参数
    results_filename = f"simulation_results_{experiment_name}.json"  # 结果文件名
    input_folder = "../result/output"  # 输入文件夹（相对于当前脚本的路径）
    output_folder_base = "./exper3"  # 输出文件夹基础路径（相对于当前脚本的路径）
    
    # =================================================================
    
    # 构建完整路径
    results_path = os.path.join(os.path.dirname(__file__), input_folder, results_filename)
    output_folder = output_folder_base
    
    plot_all_graphs(results_path, output_folder, epoch_limit=num_epochs)
import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import MultipleLocator

# 添加项目根目录到Python路径，以便导入其他模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def plot_multiple_brokerhubs_mer_participation(results_path, output_folder, epoch_limit, num_hubs):
    """
    为多个BrokerHub创建管理费率和参与率的对比图
    """
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    # 加载JSON数据
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    # 获取所有BrokerHub的ID并排序
    brokerhub_ids = list(set(bh['id'] for state in results for bh in state['brokerhubs']))
    brokerhub_ids.sort()
    
    # 确保只处理指定数量的hubs
    brokerhub_ids = brokerhub_ids[:num_hubs]
    
    # 创建图形 - 1行2列的布局
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
    
    # 提取数据
    epochs = [int(state['epoch']) for state in results][:epoch_limit]
    
    # 定义颜色映射
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    # 为每个BrokerHub收集和绘制数据
    for idx, bh_id in enumerate(brokerhub_ids):
        color = colors[idx % len(colors)]
        
        # 初始化数据列表
        mer_values = []
        participation_rates = []
        
        # 收集数据
        for state in results[:epoch_limit]:
            bh = next((bh for bh in state['brokerhubs'] if bh['id'] == bh_id), None)
            if bh:
                # 管理费率 (MER)
                mer_values.append(float(bh['tax_rate']) * 100)
                
                # 参与率计算
                total_volunteers = len(state['volunteers'])
                participation_rate = (len(bh['users'])) / total_volunteers * 100
                participation_rates.append(participation_rate)
            else:
                # 如果某个epoch中该hub不存在，填充0
                mer_values.append(0)
                participation_rates.append(0)
        
        # 绘制管理费率 (子图1)
        ax1.plot(epochs, mer_values, '-', color=color, 
                label=f'{bh_id}', linewidth=2.5, 
                marker='o', markevery=10, markersize=6)
        
        # 绘制参与率 (子图2)
        ax2.plot(epochs, participation_rates, '-', color=color, 
                label=f'{bh_id}', linewidth=2.5, 
                marker='s', markevery=10, markersize=6)
    
    # 设置子图1 - 管理费率
    ax1.set_xlabel('Epoch', fontsize=20)
    ax1.set_ylabel('Management Fee Ratio (%)', fontsize=20)
    ax1.set_title('(a) Management Fee Ratio Evolution', fontsize=22, pad=20)
    
    # 设置Y轴百分比格式
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
    ax1.set_ylim(0, 105)
    
    # 设置刻度
    ax1.xaxis.set_major_locator(MultipleLocator(50))
    ax1.yaxis.set_major_locator(MultipleLocator(20))
    ax1.tick_params(axis='both', labelsize=18)
    
    # 网格和图例
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper right', fontsize=18, frameon=True, 
              fancybox=True, shadow=True)
    
    # 设置子图2 - 参与率
    ax2.set_xlabel('Epoch', fontsize=20)
    ax2.set_ylabel('Participation Rate (%)', fontsize=20)
    ax2.set_title('(b) Investor Participation Rate', fontsize=22, pad=20)
    
    # 设置Y轴百分比格式
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
    ax2.set_ylim(0, 105)
    
    # 设置刻度
    ax2.xaxis.set_major_locator(MultipleLocator(50))
    ax2.yaxis.set_major_locator(MultipleLocator(20))
    ax2.tick_params(axis='both', labelsize=18)
    
    # 网格和图例
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper right', fontsize=18, frameon=True, 
              fancybox=True, shadow=True)
    
    # 调整子图间距
    plt.tight_layout()
    
    # 保存图形
    output_filename = f'{num_hubs}hubs_mer_participation_comparison.pdf'
    output_path = os.path.join(output_folder, output_filename)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"{num_hubs}个BrokerHub的MER和参与率对比图已生成: {output_path}")

def plot_multiple_experiments():
    """
    批量处理多个实验的绘图
    """
    # 实验配置列表
    experiments = [
        {"num_hubs": 3, "experiment_name": "3hubs_20w_300_diff_final_balance"},
        {"num_hubs": 4, "experiment_name": "4hubs_20w_300_diff_final_balance"},
        {"num_hubs": 5, "experiment_name": "5hubs_20w_300_diff_final_balance"},
        {"num_hubs": 10, "experiment_name": "10hubs_20w_300_diff_final_balance"},
    ]
    
    # 通用参数
    num_epochs = 300
    input_folder = "../result/output"
    output_folder_base = "./exper_multiple_hubs"
    
    for exp in experiments:
        print(f"\n处理实验: {exp['experiment_name']}")
        
        # 构建文件路径
        results_filename = f"simulation_results_{exp['experiment_name']}.json"
        results_path = os.path.join(os.path.dirname(__file__), input_folder, results_filename)
        output_folder = output_folder_base
        
        # 检查输入文件是否存在
        if not os.path.exists(results_path):
            print(f"警告：找不到输入文件 {results_path}，跳过此实验")
            continue
        
        # 绘制图表
        print(f"输入文件: {results_path}")
        print(f"BrokerHub数量: {exp['num_hubs']}")
        
        try:
            plot_multiple_brokerhubs_mer_participation(
                results_path, output_folder, num_epochs, exp['num_hubs']
            )
        except Exception as e:
            print(f"绘制 {exp['experiment_name']} 时出错: {e}")

if __name__ == "__main__":
    # 你可以选择以下两种运行方式之一：
    
    # 方式1: 单独处理一个实验
    # =========================== 单个实验参数设置 ===========================
    single_experiment = True  # 设置为True来运行单个实验，False来批量处理
    
    if single_experiment:
        # 单个实验的参数
        num_hubs = 10  # BrokerHub数量
        experiment_name = "10hubs_20w_300_diff_final_balance"  # 实验名称
        num_epochs = 300  # epoch数量
        
        # 文件路径参数
        results_filename = f"simulation_results_{experiment_name}.json"
        input_folder = "../result/output"
        output_folder_base = "./exper6"
        
        # 构建完整路径
        results_path = os.path.join(os.path.dirname(__file__), input_folder, results_filename)
        output_folder = output_folder_base
        
        # 检查输入文件是否存在
        if not os.path.exists(results_path):
            print(f"错误：找不到输入文件 {results_path}")
            print(f"请确保文件存在并检查路径设置")
            sys.exit(1)
        
        # 绘制图表
        print(f"开始绘制图表...")
        print(f"输入文件: {results_path}")
        print(f"输出文件夹: {output_folder}")
        print(f"BrokerHub数量: {num_hubs}")
        print(f"Epoch限制: {num_epochs}")
        
        plot_multiple_brokerhubs_mer_participation(results_path, output_folder, num_epochs, num_hubs)
    
    # 方式2: 批量处理多个实验
    else:
        print("开始批量处理多个实验...")
        plot_multiple_experiments()
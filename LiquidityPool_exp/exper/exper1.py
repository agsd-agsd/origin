import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys

# 添加项目根目录到Python路径，以便导入其他模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def plot_broker_distribution(results_path, output_folder, epoch_number=1):
    """
    绘制单个epoch的broker余额分布和收益率，特别标注hub
    """
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    # 加载JSON数据
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    # 找到指定epoch的数据
    epoch_data = None
    for state in results:
        if int(state['epoch']) == epoch_number:
            epoch_data = state
            break
    
    if epoch_data is None:
        print(f"未找到 epoch {epoch_number} 的数据")
        return
    
    # 收集数据
    balances = []
    revenue_ratios = []
    broker_ids = []
    broker_types = []  # 记录是volunteer还是hub
    hub_names = []     # 记录hub的名称
    
    # 首先添加 volunteers (brokers) 的数据
    for volunteer in epoch_data['volunteers']:
        broker_id = int(volunteer['id'])
        balance = float(volunteer['balance']) / 1e18  # 转换为 Wei
        revenue_rate = float(volunteer['revenue_rate'])
        
        balances.append(balance)
        revenue_ratios.append(revenue_rate * 100)  # 转换为百分比
        broker_ids.append(broker_id)
        broker_types.append('volunteer')
        hub_names.append(None)
    
    # 然后添加 hubs 的数据
    start_id = len(broker_ids)
    for i, hub in enumerate(epoch_data['brokerhubs']):
        hub_id = start_id + i
        balance = float(hub['current_funds']) / 1e18  # 转换为 Wei
        b2e_revenue = float(hub['b2e_revenue'])
        current_funds = float(hub['current_funds'])
        revenue_ratio = b2e_revenue / current_funds if current_funds > 0 else 0
        
        balances.append(balance)
        revenue_ratios.append(revenue_ratio * 100)  # 转换为百分比
        broker_ids.append(hub_id)
        broker_types.append('hub')
        hub_names.append(hub['id'])  # 保存hub的名称
    
    # 按余额降序排序
    sorted_indices = np.argsort(balances)[::-1]
    balances = np.array(balances)[sorted_indices]
    revenue_ratios = np.array(revenue_ratios)[sorted_indices]
    broker_ids = np.array(broker_ids)[sorted_indices]
    broker_types = np.array(broker_types)[sorted_indices]
    hub_names = np.array(hub_names)[sorted_indices]
    
    # 定义颜色
    colors = []
    hub_colors = {'BrokerHub1': '#ff3333', 'BrokerHub2': '#00cc44'}  # 亮红色和亮绿色
    
    for i, broker_type in enumerate(broker_types):
        if broker_type == 'volunteer':
            colors.append('steelblue')
        else:
            # 根据hub名称分配颜色
            hub_name = hub_names[i]
            colors.append(hub_colors.get(hub_name, 'purple'))
    
    # 创建图形
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 左图：Balance分布
    
    x_positions = np.arange(len(balances))
    x_positions = x_positions + 0.5  # 所有柱子都向右移动0.5个单位

    bars1 = ax1.bar(x_positions, balances, width=0.8, color=colors)
    ax1.set_xlabel('BrokerID', fontsize=14)
    ax1.set_ylabel('Balance of broker (Wei)', fontsize=14)
    ax1.set_title('(a) Distribution of broker balances', fontsize=14, pad=20, y=-0.2)  # 子标题放在图片下面
    ax1.set_xlim(-0.5, len(balances))
    ax1.set_ylim(0, max(balances) * 1.1)
    
    # 设置刻度
    ax1.xaxis.set_major_locator(plt.MultipleLocator(10))
    ax1.tick_params(axis='both', labelsize=12)
    
    # 右图：Revenue Ratio分布
    revenue_positions = np.arange(len(revenue_ratios))
    revenue_positions = revenue_positions + 0.5  # 所有柱子都向右移动0.5个单位
    bars2 = ax2.bar(revenue_positions, revenue_ratios, width=0.8, color=colors)
    ax2.set_xlabel('BrokerID', fontsize=14)
    ax2.set_ylabel('Revenue Ratio (%)', fontsize=14)
    ax2.set_title('(b) Revenue Distribution from Broker2Earn', fontsize=14, pad=20, y=-0.2)  # 子标题放在图片下面
    ax2.set_xlim(-0.5, len(revenue_ratios))
    ax2.set_ylim(0, max(revenue_ratios) * 1.1)
    
    # 设置刻度和格式
    ax2.xaxis.set_major_locator(plt.MultipleLocator(10))
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0f}%'))
    ax2.tick_params(axis='both', labelsize=12)
    
    # 创建图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='steelblue', label='Other Brokers'),  # 改为 Other Brokers
        Patch(facecolor= hub_colors['BrokerHub1'], label='BrokerHub1'),
        Patch(facecolor= hub_colors['BrokerHub2'], label='BrokerHub2')
    ]
    
    # 在右图添加图例（放在两图的中间位置）
    ax2.legend(handles=legend_elements, loc='upper right', fontsize=12)
    
    # 调整子图间距
    plt.tight_layout()
    
    # 保存图形
    output_path = os.path.join(output_folder, f'broker_distribution_epoch_{epoch_number}.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Epoch {epoch_number} 的分布图已生成！")
    
    # 输出一些统计信息
    print(f"Epoch {epoch_number} 统计信息：")
    print(f"- 总broker数（包括volunteers和hubs）: {len(balances)}")
    print(f"- Other Brokers数量: {sum(broker_types == 'volunteer')}")
    print(f"- Hubs数量: {sum(broker_types == 'hub')}")
    print(f"- 最大余额: {max(balances):.2f} Wei")
    print(f"- 最小余额: {min(balances):.2f} Wei")
    print(f"- 最大收益率: {max(revenue_ratios):.2f}%")
    print(f"- 最小收益率: {min(revenue_ratios):.2f}%")
    
    # 输出hub的具体信息
    for i, broker_type in enumerate(broker_types):
        if broker_type == 'hub':
            print(f"- {hub_names[i]}: 余额={balances[i]:.2f} Wei, 收益率={revenue_ratios[i]:.2f}%")

if __name__ == "__main__":
    # =========================== 参数设置 ===========================
    # 实验参数
    experiment_name = "trump_20w_300_diff_motivation_balance"  # 实验名称，用于文件命名
    epoch_number = 1  # 要绘制的epoch编号
    
    # 文件路径参数
    results_filename = f"simulation_results_{experiment_name}.json"  # 结果文件名
    input_folder = "../result/output"  # 输入文件夹（相对于当前脚本的路径）
    output_folder_base = "./exper1"  # 输出文件夹改为 exper1
    
    # =================================================================
    
    # 构建完整路径
    results_path = os.path.join(os.path.dirname(__file__), input_folder, results_filename)
    output_folder = output_folder_base
    
    # 检查输入文件是否存在
    if not os.path.exists(results_path):
        print(f"错误：找不到输入文件 {results_path}")
        print(f"请确保文件存在并检查路径设置")
        sys.exit(1)
    
    # 绘制图表
    print(f"开始绘制 Epoch {epoch_number} 的分布图...")
    print(f"输入文件: {results_path}")
    print(f"输出文件夹: {output_folder}")
    
    plot_broker_distribution(results_path, output_folder, epoch_number)
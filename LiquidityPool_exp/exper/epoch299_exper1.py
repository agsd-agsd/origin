import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys
from matplotlib.transforms import Bbox

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
        balance = float(volunteer['balance']) / 1e18  # 转换为 ETH
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
        balance = float(hub['current_funds']) / 1e18  # 转换为 ETH
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
    hub_colors = {'BrokerHub1': '#00cc44', 'BrokerHub2': '#ff3333'}  # 互换颜色：亮绿色和亮红色
    
    for i, broker_type in enumerate(broker_types):
        if broker_type == 'volunteer':
            colors.append('steelblue')
        else:
            # 根据hub名称分配颜色
            hub_name = hub_names[i]
            colors.append(hub_colors.get(hub_name, 'purple'))
    
    # 创建具有断轴效果的左图
    fig = plt.figure(figsize=(15, 6))
    
    # 创建两个子图，一个用于高值部分，一个用于低值部分
    # 调整高度比例可以改变断轴部分的宽度：[1, 3] 表示上部分高度是下部分的1/3
    # 增大第一个数字会增加上部分高度，减小断轴的宽度
    # 例如：[1, 4]会使断轴更宽，[2, 3]会使断轴更窄
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 3], hspace=0.1, width_ratios=[1, 1])
    ax1_top = fig.add_subplot(gs[0, 0])  # 上部分（高值）
    ax1_bottom = fig.add_subplot(gs[1, 0])  # 下部分（低值）
    ax2 = fig.add_subplot(gs[:, 1])  # 右图占据整个右侧
    
    # 设置断轴的范围
    # 这里您可以调整这四个值来控制断轴的位置
    y_top_min = 70  # 上部分的最小值 - 断轴下方的上限
    y_top_max = max(balances) * 1.1  # 上部分的最大值 - 上图的上限
    y_bottom_max = 6.5  # 下部分的最大值 - 断轴上方的下限
    y_bottom_min = 0  # 下部分的最小值 - 下图的下限
    
    # 注意：为了断轴效果正确，必须确保 y_bottom_max < y_top_min

    # 绘制柱状图
    x_positions = np.arange(len(balances))
    x_positions = x_positions + 0.5  # 所有柱子都向右移动0.5个单位
    
    # 在上下两个子图上绘制柱状图
    bars1_top = ax1_top.bar(x_positions, balances, width=0.8, color=colors)
    bars1_bottom = ax1_bottom.bar(x_positions, balances, width=0.8, color=colors)
    
    # 设置上下子图的y轴范围
    ax1_top.set_ylim(y_top_min, y_top_max)
    ax1_bottom.set_ylim(y_bottom_min, y_bottom_max)
    
    # 隐藏上图的x轴刻度和标签
    ax1_top.set_xticks([])
    ax1_top.spines['bottom'].set_visible(False)
    ax1_bottom.spines['top'].set_visible(False)
    
    # 定义断轴标记参数
    d = 0.02  # 断轴标记的大小

    # 考虑高度比例 (假设比例为1:3)
    height_ratio = 1/3  # 根据您的height_ratios=[1, 3]设置

    # 为上图底部绘制斜线
    kwargs = dict(transform=ax1_top.transAxes, color='k', clip_on=False)

    # 上图中的斜线 - 左侧
    ax1_top.plot((-d, +d), (-d, +d), **kwargs)         # 左下斜线 (45度)

    # 上图中的斜线 - 右侧
    ax1_top.plot((1-d, 1+d), (-d, +d), **kwargs)       # 右下斜线 (45度)

    # 为下图顶部绘制斜线 - 角度需要调整以保持视觉上的平行
    kwargs.update(transform=ax1_bottom.transAxes)

    # 下图中的斜线 - 左侧 (调整斜率以与上图斜线平行)
    ax1_bottom.plot((-d, +d), (1-d*height_ratio, 1+d*height_ratio), **kwargs)  # 左上斜线

    # 下图中的斜线 - 右侧 (调整斜率以与上图斜线平行)
    ax1_bottom.plot((1-d, 1+d), (1-d*height_ratio, 1+d*height_ratio), **kwargs)  # 右上斜线
    
    # 设置x轴范围和刻度
    ax1_bottom.set_xlim(-0.5, len(balances) + 0.5)
    ax1_top.set_xlim(-0.5, len(balances) + 0.5)
    ax1_bottom.xaxis.set_major_locator(plt.MultipleLocator(10))
    
    # 添加标签和标题
    ax1_bottom.set_xlabel('BrokerID', fontsize=14)
    ax1_bottom.set_ylabel('Balance (ETH)', fontsize=14, y = 0.7)

    # 修改标题位置 - 将标题放在图表上方而不是内部
    # fig.text(0.25, 0.95, '(a) Distribution of broker balances', fontsize=14, ha='center')
    ax1_bottom.set_title('(a) Distribution of broker balances', fontsize=14, pad=20, y=-0.3)  # 子标题放在图片下面



    # 创建图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='steelblue', label='Other Brokers'),
        Patch(facecolor=hub_colors['BrokerHub1'], label='BrokerHub1'),
        Patch(facecolor=hub_colors['BrokerHub2'], label='BrokerHub2')
    ]
    
    # 设置刻度大小    
    ax1_top.legend(handles=legend_elements, loc='upper right', fontsize=14)

    ax1_top.tick_params(axis='both', labelsize=14)
    ax1_bottom.tick_params(axis='both', labelsize=14)
    
    # 右图：Revenue Ratio分布
    revenue_positions = np.arange(len(revenue_ratios))
    revenue_positions = revenue_positions + 0.5  # 所有柱子都向右移动0.5个单位
    bars2 = ax2.bar(revenue_positions, revenue_ratios, width=0.8, color=colors)
    ax2.set_xlabel('BrokerID', fontsize=14)
    ax2.set_ylabel('Revenue Ratio (%)', fontsize=14)
    
    # 修改标题位置 - 将标题放在图表下方与 (a) 图一致的风格
    # fig.text(0.75, 0.05, '(b) Revenue Distribution from Broker2Earn', fontsize=14, ha='center')
    ax2.set_title('(b) Revenue Distribution from Broker2Earn', fontsize=14, pad=20, y=-0.22)  # 子标题放在图片下面

    ax2.set_xlim(-0.5, len(revenue_ratios) + 0.5)
    ax2.set_ylim(0, 40)  # 设置固定的y轴上限为40%
    
    # 设置刻度和格式
    ax2.xaxis.set_major_locator(plt.MultipleLocator(10))
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0f}%'))
    ax2.tick_params(axis='both', labelsize=14)
    
    
    # 在右图添加图例
    ax2.legend(handles=legend_elements, loc='upper right', fontsize=14)
    
    # 调整整体布局，但保持断轴部分的间距设置
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
    print(f"- 最大余额: {max(balances):.2f} ETH")  # 修正单位为ETH
    print(f"- 最小余额: {min(balances):.2f} ETH")  # 修正单位为ETH
    print(f"- 最大收益率: {max(revenue_ratios):.2f}%")
    print(f"- 最小收益率: {min(revenue_ratios):.2f}%")
    
    # 输出hub的具体信息
    for i, broker_type in enumerate(broker_types):
        if broker_type == 'hub':
            print(f"- {hub_names[i]}: 余额={balances[i]:.2f} ETH, 收益率={revenue_ratios[i]:.2f}%")  # 修正单位为ETH

if __name__ == "__main__":
    # =========================== 参数设置 ===========================
    # 实验参数
    experiment_name = "trump_20w_300_diff_motivation_balance"  # 实验名称，用于文件命名
    epoch_number = 299  # 要绘制的epoch编号
    
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
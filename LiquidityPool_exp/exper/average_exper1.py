import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys
from matplotlib.transforms import Bbox

# 添加项目根目录到Python路径，以便导入其他模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def plot_average_broker_distribution(results_path, output_folder, start_epoch=0, end_epoch=299):
    """
    绘制多个epoch的平均broker余额分布和收益率，特别标注hub
    在b图中，根据broker在不同hub状态下的收益比例堆叠不同颜色
    """
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    # 加载JSON数据
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    # 过滤出指定范围内的epoch数据
    epoch_data_list = []
    for state in results:
        epoch = int(state['epoch'])
        if start_epoch <= epoch <= end_epoch:
            epoch_data_list.append(state)
    
    if not epoch_data_list:
        print(f"未找到 epoch {start_epoch} 到 {end_epoch} 的数据")
        return
    
    print(f"找到 {len(epoch_data_list)} 个epoch的数据进行平均")
    
    # 初始化数据存储
    broker_balances = {}  # 按broker_id存储每个epoch的balance
    broker_revenues = {}  # 按broker_id存储每个epoch的revenue_rate
    broker_types = {}     # 记录每个broker的类型
    hub_names = {}        # 记录hub的名称
    broker_hub_history = {}  # 记录每个broker在每个epoch中所属的hub (包括"no_hub")
    broker_revenue_by_hub = {}  # 记录每个broker在不同hub状态下的收益
    
    # 累计所有epoch数据
    for epoch_data in epoch_data_list:
        epoch = int(epoch_data['epoch'])
        
        # 处理volunteers (brokers)
        for volunteer in epoch_data['volunteers']:
            broker_id = volunteer['id']
            balance = float(volunteer['balance']) / 1e18  # 转换为ETH
            revenue_rate = float(volunteer['revenue_rate']) * 100  # 转换为百分比
            current_hub = volunteer['current_brokerhub']  # 这里可能是null或hub_id
            
            if broker_id not in broker_balances:
                broker_balances[broker_id] = []
                broker_revenues[broker_id] = []
                broker_types[broker_id] = 'volunteer'
                hub_names[broker_id] = None
                broker_hub_history[broker_id] = {}
                broker_revenue_by_hub[broker_id] = {'no_hub': [], 'BrokerHub1': [], 'BrokerHub2': []}
            
            broker_balances[broker_id].append(balance)
            broker_revenues[broker_id].append(revenue_rate)
            
            # 记录该broker在此epoch所属的hub
            current_hub_id = current_hub if current_hub is not None else 'no_hub'
            if current_hub_id not in broker_hub_history[broker_id]:
                broker_hub_history[broker_id][current_hub_id] = 0
            broker_hub_history[broker_id][current_hub_id] += 1
            
            # 记录该broker在不同hub状态下的收益
            for hub_id in ['no_hub', 'BrokerHub1', 'BrokerHub2']:
                if hub_id == current_hub_id:
                    broker_revenue_by_hub[broker_id][hub_id].append(revenue_rate)
                else:
                    broker_revenue_by_hub[broker_id][hub_id].append(0)  # 不在该hub时收益为0
        
        # 处理hubs
        for hub in epoch_data['brokerhubs']:
            hub_id = hub['id']  # 使用hub的实际ID
            balance = float(hub['current_funds']) / 1e18  # 转换为ETH
            b2e_revenue = float(hub['b2e_revenue'])
            current_funds = float(hub['current_funds'])
            revenue_ratio = (b2e_revenue / current_funds if current_funds > 0 else 0) * 100  # 转换为百分比
            
            if hub_id not in broker_balances:
                broker_balances[hub_id] = []
                broker_revenues[hub_id] = []
                broker_types[hub_id] = 'hub'
                hub_names[hub_id] = hub_id
                broker_hub_history[hub_id] = {hub_id: end_epoch - start_epoch + 1}  # hub自己总是属于自己
                broker_revenue_by_hub[hub_id] = {hub_id: [], 'no_hub': [], 'BrokerHub1': [], 'BrokerHub2': []}
                broker_revenue_by_hub[hub_id][hub_id] = [revenue_ratio] * (end_epoch - start_epoch + 1)
            
            broker_balances[hub_id].append(balance)
            broker_revenues[hub_id].append(revenue_ratio)
    
    # 计算平均值和收益比例
    avg_balances = {}
    avg_revenues = {}
    hub_time_ratios = {}  # 存储每个broker在不同hub的时间比例
    hub_revenue_ratios = {}  # 存储每个broker在不同hub的收益比例
    
    total_epochs = end_epoch - start_epoch + 1
    
    for broker_id in broker_balances:
        if broker_types[broker_id] == 'volunteer':
            # volunteer的balance在第一个epoch就固定了，所以只取第一个值
            avg_balances[broker_id] = broker_balances[broker_id][0]
        else:
            # hub的balance需要计算平均值
            avg_balances[broker_id] = np.mean(broker_balances[broker_id])
        
        # 收益率计算平均值
        avg_revenues[broker_id] = np.mean(broker_revenues[broker_id])
        
        # 计算时间比例
        hub_time_ratios[broker_id] = {}
        # 确保所有可能的hub都有条目
        for hub_id in ['no_hub', 'BrokerHub1', 'BrokerHub2']:
            if hub_id not in broker_hub_history.get(broker_id, {}):
                broker_hub_history.setdefault(broker_id, {})[hub_id] = 0
            
            hub_time_ratios.setdefault(broker_id, {})[hub_id] = broker_hub_history[broker_id][hub_id] / total_epochs
        
        # 计算不同hub状态下的收益比例
        hub_revenue_ratios[broker_id] = {}
        total_revenue = sum([sum(broker_revenue_by_hub[broker_id].get(hub_id, [])) for hub_id in ['no_hub', 'BrokerHub1', 'BrokerHub2']])
        
        if total_revenue > 0:
            for hub_id in ['no_hub', 'BrokerHub1', 'BrokerHub2']:
                hub_revenue = sum(broker_revenue_by_hub[broker_id].get(hub_id, []))
                hub_revenue_ratios[broker_id][hub_id] = hub_revenue / total_revenue
        else:
            # 如果总收益为0，使用时间比例
            for hub_id in ['no_hub', 'BrokerHub1', 'BrokerHub2']:
                hub_revenue_ratios[broker_id][hub_id] = hub_time_ratios[broker_id][hub_id]
    
    # 整理数据为列表形式，便于后续处理
    balances = []
    revenue_ratios = []
    broker_ids = []
    broker_type_list = []
    hub_name_list = []
    hub_ratios = []  # 每个broker在不同hub的收益比例列表
    
    for broker_id in avg_balances:
        balances.append(avg_balances[broker_id])
        revenue_ratios.append(avg_revenues[broker_id])
        broker_ids.append(broker_id)
        broker_type_list.append(broker_types[broker_id])
        hub_name_list.append(hub_names[broker_id])
        
        # 添加hub收益比例数据
        ratios = {
            'no_hub': hub_revenue_ratios[broker_id].get('no_hub', 0),
            'BrokerHub1': hub_revenue_ratios[broker_id].get('BrokerHub1', 0),
            'BrokerHub2': hub_revenue_ratios[broker_id].get('BrokerHub2', 0)
        }
        hub_ratios.append(ratios)
    
    # 转换为numpy数组
    balances = np.array(balances)
    revenue_ratios = np.array(revenue_ratios)
    broker_ids = np.array(broker_ids)
    broker_type_list = np.array(broker_type_list)
    hub_name_list = np.array(hub_name_list)
    
    # 按余额降序排序
    sorted_indices = np.argsort(balances)[::-1]
    balances = balances[sorted_indices]
    revenue_ratios = revenue_ratios[sorted_indices]
    broker_ids = broker_ids[sorted_indices]
    broker_type_list = broker_type_list[sorted_indices]
    hub_name_list = hub_name_list[sorted_indices]
    # 对hub_ratios也进行相同排序
    hub_ratios = [hub_ratios[i] for i in sorted_indices]
    
    # 定义颜色
    colors = []
    hub_colors = {'BrokerHub1': '#00cc44', 'BrokerHub2': '#ff3333', 'no_hub': 'steelblue'}  # 亮绿色和亮红色和蓝色
    
    for i, broker_type in enumerate(broker_type_list):
        if broker_type == 'volunteer':
            colors.append('steelblue')
        else:
            # 根据hub名称分配颜色
            hub_name = hub_name_list[i]
            colors.append(hub_colors.get(hub_name, 'purple'))
    
    # 创建具有断轴效果的左图，调整图形大小以增加宽度
    fig = plt.figure(figsize=(18, 6))  # 从15增加到18
    
    # 创建两个子图，一个用于高值部分，一个用于低值部分
    # 增加width_ratios和wspace参数来调整两个子图之间的间距
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 3], hspace=0.1, 
                          width_ratios=[0.95, 0.95], wspace=0.2)  # 增加wspace来增加间距
    
    ax1_top = fig.add_subplot(gs[0, 0])      # 上部分（高值）
    ax1_bottom = fig.add_subplot(gs[1, 0])    # 下部分（低值）
    ax2 = fig.add_subplot(gs[:, 1])           # 右图占据整个右侧
    
    # 设置断轴的范围
    y_top_min = 70  # 上部分的最小值 - 断轴下方的上限
    y_top_max = max(balances) * 1.1  # 上部分的最大值 - 上图的上限
    y_bottom_max = 6.5  # 下部分的最大值 - 断轴上方的下限
    y_bottom_min = 0  # 下部分的最小值 - 下图的下限
    
    # 注意：为了断轴效果正确，必须确保 y_bottom_max < y_top_min

    # 绘制柱状图
    x_positions = np.arange(len(balances))
    x_positions = x_positions + 0.5  # 所有柱子都向右移动0.5个单位
    
    # 在上下两个子图上绘制柱状图
    bars1_top = ax1_top.bar(x_positions, balances, width=0.8, color=colors, edgecolor='black', linewidth=0.2)
    bars1_bottom = ax1_bottom.bar(x_positions, balances, width=0.8, color=colors, edgecolor='black', linewidth=0.2)
    
    # 设置上下子图的y轴范围
    ax1_top.set_ylim(y_top_min, y_top_max)
    ax1_bottom.set_ylim(y_bottom_min, y_bottom_max)
    
    # 隐藏上图的x轴刻度和标签
    ax1_top.set_xticks([])
    ax1_top.spines['bottom'].set_visible(False)
    ax1_bottom.spines['top'].set_visible(False)
    
    # 添加断轴标记
    d = 0.02  # 断轴标记的大小
    height_ratio = 1/3  # 根据height_ratios=[1, 3]设置
    
    # 为上图底部绘制斜线
    kwargs = dict(transform=ax1_top.transAxes, color='k', clip_on=False)
    ax1_top.plot((-d, +d), (-d, +d), **kwargs)        # 左下斜线
    ax1_top.plot((1-d, 1+d), (-d, +d), **kwargs)      # 右下斜线
    
    # 为下图顶部绘制斜线
    kwargs.update(transform=ax1_bottom.transAxes)
    ax1_bottom.plot((-d, +d), (1-d*height_ratio, 1+d*height_ratio), **kwargs)      # 左上斜线
    ax1_bottom.plot((1-d, 1+d), (1-d*height_ratio, 1+d*height_ratio), **kwargs)    # 右上斜线
    
    # 设置x轴范围和刻度
    ax1_bottom.set_xlim(-0.5, len(balances) + 0.5)
    ax1_top.set_xlim(-0.5, len(balances) + 0.5)
    ax1_bottom.xaxis.set_major_locator(plt.MultipleLocator(10))  # 对于大量数据，每100个显示一个刻度
    
    # 添加标签和标题
    ax1_bottom.set_xlabel('BrokerID', fontsize=20)
    ax1_bottom.set_ylabel('Balance (ETH)', fontsize=20, y=0.7)
    ax1_bottom.set_title('(a) Distribution of broker balances', fontsize=20, pad=20, y=-0.4)
    
    # 设置刻度大小
    ax1_top.tick_params(axis='both', labelsize=20)
    ax1_bottom.tick_params(axis='both', labelsize=20)
    
    # 右图：平均Revenue Ratio分布，使用堆叠条形图显示不同hub的收益比例
    revenue_positions = np.arange(len(revenue_ratios))
    revenue_positions = revenue_positions + 0.5  # 所有柱子都向右移动0.5个单位

    # 准备堆叠柱状图的数据
    stacked_data = {
        'no_hub': np.zeros(len(revenue_ratios)),
        'BrokerHub1': np.zeros(len(revenue_ratios)),
        'BrokerHub2': np.zeros(len(revenue_ratios))
    }

    # 计算每个柱子的堆叠值
    for i, (revenue, ratios) in enumerate(zip(revenue_ratios, hub_ratios)):
        broker_id = broker_ids[i]
        broker_type = broker_type_list[i]
        
        # 对于hub类型的broker，将全部收益归属到对应的hub
        if broker_type == 'hub':
            hub_id = hub_name_list[i]
            stacked_data[hub_id][i] = revenue
        else:
            # 对于普通broker，根据收益比例分配收益（将总收益按比例分配）
            for hub_id in ['no_hub', 'BrokerHub1', 'BrokerHub2']:
                stacked_data[hub_id][i] = revenue * ratios[hub_id]

    # 定义纹路样式 - 只为broker柱子的部分设置
    hatch_styles = {
        'no_hub': '+',    # 加号纹路
        'BrokerHub1': '\\',   # 反斜线纹路
        'BrokerHub2': '/'    # 斜线纹路
    }

    # 设置纹路参数
    plt.rcParams['hatch.color'] = 'white'  # 将纹路颜色设为白色
    plt.rcParams['hatch.linewidth'] = 0.8  # 减小纹路线宽

    # 绘制堆叠柱状图
    bottom = np.zeros(len(revenue_ratios))
    bars = []

    for hub_id in ['BrokerHub2', 'BrokerHub1', 'no_hub']:
        data_to_plot = stacked_data[hub_id]
        
        # 只绘制有值的部分
        if np.any(data_to_plot > 0):
            # 为每个柱子单独决定是否使用纹路
            hatches = []
            for i in range(len(revenue_ratios)):
                if broker_type_list[i] == 'hub' and hub_name_list[i] == hub_id:
                    # 如果是hub类型且对应当前hub，不使用纹路
                    hatches.append('')
                elif broker_type_list[i] == 'hub':
                    # 如果是其他hub类型，跳过（应该为0）
                    hatches.append('')
                else:
                    # 如果是普通broker，使用纹路
                    hatches.append(hatch_styles[hub_id])
            
            bar = ax2.bar(revenue_positions, data_to_plot, width=0.8, 
                         bottom=bottom, color=hub_colors[hub_id],
                         edgecolor='black', linewidth=0.2)
            
            # 为每个长方形单独设置纹路
            for j, patch in enumerate(bar):
                if hatches[j]:  # 如果有纹路
                    patch.set_hatch(hatches[j])
            
            bars.append(bar)
            bottom += data_to_plot

    ax2.set_xlabel('BrokerID', fontsize=20)
    ax2.set_ylabel('Revenue Ratio (%)', fontsize=20)
    ax2.set_title('(b) Average Revenue Ratio', fontsize=20, pad=20, y=-0.28)
    ax2.set_xlim(-0.5, len(revenue_ratios) + 0.5)
    ax2.set_ylim(0, 20)  # 设置固定的y轴上限为20%

    # 设置刻度和格式
    ax2.xaxis.set_major_locator(plt.MultipleLocator(10))  # 对于大量数据，每100个显示一个刻度
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0f}%'))
    ax2.tick_params(axis='both', labelsize=20)

    # 创建图例 - 普通broker的图例包含纹路，hub的不包含
    from matplotlib.patches import Patch

    # 创建图例元素
    legend_elements = [
        Patch(facecolor=hub_colors['no_hub'], edgecolor='black', linewidth=0.5, label='Other Brokers'),
        Patch(facecolor=hub_colors['BrokerHub1'], edgecolor='black', linewidth=0.5, label='BrokerHub1'),
        Patch(facecolor=hub_colors['BrokerHub2'], edgecolor='black', linewidth=0.5, label='BrokerHub2')
    ]

    # 在图中添加图例
    ax1_top.legend(handles=legend_elements, loc='upper right', fontsize=20)    
    
    # 创建图例 - 普通broker的图例包含纹路，hub的不包含
    legend_elements = [
        # 正确显示no_hub的+纹路
        Patch(facecolor=hub_colors['no_hub'], hatch='+', edgecolor='black', linewidth=0.5, label='Revenue from Broker2Earn'),
        # BrokerHub1和BrokerHub2的图例项，为volunteer类型时分别使用对应的纹路
        Patch(facecolor=hub_colors['BrokerHub1'], hatch='\\', edgecolor='black', linewidth=0.5, label='Revenue from BrokerHub1'),
        Patch(facecolor=hub_colors['BrokerHub2'], hatch='/', edgecolor='black', linewidth=0.5, label='Revenue from BrokerHub2'),
        # 纯色的Hub图例项（无纹路）
        Patch(facecolor=hub_colors['BrokerHub1'], edgecolor='black', linewidth=0.5, label='BrokerHub1'),
        Patch(facecolor=hub_colors['BrokerHub2'], edgecolor='black', linewidth=0.5, label='BrokerHub2')
    ]

    # 在图中添加图例，将loc改为lower right以避免遮挡数据，并调整字体大小
    ax2.legend(handles=legend_elements, loc='upper right', fontsize=20)

    # 调整整体布局 - 替换plt.tight_layout()
    plt.tight_layout(pad=2.0)  # 增加内边距
    
    # 额外调整子图之间的间距
    plt.subplots_adjust(wspace=0.4)  # 增加水平间距
    
    # 保存图形
    output_path = os.path.join(output_folder, f'broker_distribution_average_epochs_{start_epoch}_to_{end_epoch}.pdf')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"{end_epoch-start_epoch+1}个epoch的平均分布图已生成！")
    
    # 输出一些统计信息
    print(f"平均统计信息 (Epochs {start_epoch} to {end_epoch})：")
    print(f"- 总broker数（包括volunteers和hubs）: {len(balances)}")
    print(f"- Other Brokers数量: {sum(broker_type_list == 'volunteer')}")
    print(f"- Hubs数量: {sum(broker_type_list == 'hub')}")
    print(f"- 最大平均余额: {max(balances):.2f} ETH") 
    print(f"- 最小平均余额: {min(balances):.2f} ETH")
    print(f"- 最大平均收益率: {max(revenue_ratios):.2f}%")
    print(f"- 最小平均收益率: {min(revenue_ratios):.2f}%")
    
    # 输出每个broker的hub收益情况
    print("\n各broker在不同hub的收益比例：")
    for i, broker_id in enumerate(broker_ids):
        if broker_type_list[i] == 'volunteer' and i < 10:  # 只输出前10个，避免输出过多
            ratios = hub_ratios[i]
            print(f"Broker {broker_id}: no_hub={ratios['no_hub']*100:.1f}%, BrokerHub1={ratios['BrokerHub1']*100:.1f}%, BrokerHub2={ratios['BrokerHub2']*100:.1f}%")

if __name__ == "__main__":
    # =========================== 参数设置 ===========================
    # 实验参数
    experiment_name = "trump_20w_300_diff_motivation_balance"  # 实验名称，用于文件命名
    start_epoch = 0      # 起始epoch
    end_epoch = 299      # 结束epoch
    
    # 文件路径参数
    results_filename = f"simulation_results_{experiment_name}.json"  # 结果文件名
    input_folder = "../result/output"  # 输入文件夹（相对于当前脚本的路径）
    output_folder_base = "./exper1"  # 输出文件夹
    
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
    print(f"开始计算并绘制 Epoch {start_epoch} 到 {end_epoch} 的平均分布图...")
    print(f"输入文件: {results_path}")
    print(f"输出文件夹: {output_folder}")
    
    plot_average_broker_distribution(results_path, output_folder, start_epoch, end_epoch)
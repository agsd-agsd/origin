import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from matplotlib.ticker import MaxNLocator, MultipleLocator

# 添加项目根目录到Python路径，以便导入其他模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def convert_label_name(bh_id):
    """
    将BrokerHub标识符转换为LiquidityPool标识符
    例如: BrokerHub1 -> LiquidityPool1
    """
    return bh_id.replace('BrokerHub', 'LiquidityPool')
    
def plot_brokerhub_metrics(results_path, output_folder, epoch_limit):
    """
    为每个BrokerHub创建包含多个指标的图表
    """
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    # 加载JSON数据
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    # 获取所有BrokerHub的ID
    brokerhub_ids = list(set(bh['id'] for state in results for bh in state['brokerhubs']))
    brokerhub_ids.sort()
    
    print(f"\n=== 竞争动态分析报告 ===")
    print(f"分析的LiquidityPool: {[convert_label_name(bh_id) for bh_id in brokerhub_ids[:2]]}")
    print(f"分析epoch范围: 0-{epoch_limit}")
    
    # 创建图形
    fig = plt.figure(figsize=(30, 12))
    
    # 创建主 GridSpec - 把整个图分成2行2列的大格子
    gs_main = GridSpec(2, 2, 
                       hspace=0.25,     # 行之间的间距
                       wspace=0.1,      # 主要列之间的间距
                       left=0.05,       # 左边距
                       right=0.95,      # 右边距
                       top=0.95,        # 上边距
                       bottom=0.05)     # 下边距
    
    # 为左半部分创建嵌套的 GridSpec (包含 a&e 和 b&f)
    gs_left = GridSpecFromSubplotSpec(2, 2, 
                                      subplot_spec=gs_main[:, 0],
                                      width_ratios=[1, 1],  # b列更窄
                                      wspace=0.45,             # a和b之间的间距
                                      hspace=0.3)
    
    # 为右半部分创建嵌套的 GridSpec (包含 c&g 和 d&h)
    gs_right = GridSpecFromSubplotSpec(2, 2, 
                                       subplot_spec=gs_main[:, 1],
                                       width_ratios=[1, 1],  # c列更窄
                                       wspace=0.45,             # c和d之间的间距
                                      hspace=0.3)
    
    # 创建子图
    axes = []
    axes.append([fig.add_subplot(gs_left[0, 0]),    # a
                 fig.add_subplot(gs_left[0, 1]),    # b
                 fig.add_subplot(gs_right[0, 0]),   # c
                 fig.add_subplot(gs_right[0, 1])])  # d
    axes.append([fig.add_subplot(gs_left[1, 0]),    # e
                 fig.add_subplot(gs_left[1, 1]),    # f
                 fig.add_subplot(gs_right[1, 0]),   # g
                 fig.add_subplot(gs_right[1, 1])])  # h
    axes = np.array(axes)
    
    # 提取数据
    epochs = [int(state['epoch']) for state in results][:epoch_limit]
    
    # 用于存储分析数据
    analysis_data = {}
    
    # 为每个BrokerHub收集数据
    for row, bh_id in enumerate(brokerhub_ids[:2]):  # 只处理前两个BrokerHub
        pool_name = convert_label_name(bh_id)
        analysis_data[pool_name] = {
            'epochs': [],
            'mfr': [],
            'rank': [],
            'participation': [],
            'revenue_ratio': [],
            'funds': [],
            'net_revenue': [],
            'stakeholder_revenue': []
        }
        
        # 初始化数据列表
        mer_values = []
        broker_rank = []
        participation_rates = []
        revenue_ratios = []
        investor_funds = []
        net_revenue_ratios = []
        investor_revenue_ratios = []
        
        # 收集数据
        for state in results[:epoch_limit]:
            bh = next((bh for bh in state['brokerhubs'] if bh['id'] == bh_id), None)
            if bh:
                epoch = int(state['epoch'])
                # 管理费率 (MFR)
                mfr = float(bh['tax_rate']) * 100
                mer_values.append(mfr)
                
                # BrokerHub排名 - 计算在所有broker和hub中的总排名
                all_balances = []
                all_ids = []
                
                # 收集所有已加入hub的volunteer ID
                joined_volunteer_ids = set()
                for hub in state['brokerhubs']:
                    joined_volunteer_ids.update(hub['users'])
                
                # 只收集还未加入任何hub的volunteers的余额
                for volunteer in state['volunteers']:
                    if volunteer['id'] not in joined_volunteer_ids:
                        all_balances.append(float(volunteer['balance']))
                        all_ids.append(f"volunteer_{volunteer['id']}")
                
                # 收集所有hubs的余额
                for hub in state['brokerhubs']:
                    all_balances.append(float(hub['current_funds']))
                    all_ids.append(f"hub_{hub['id']}")
                
                # 按余额降序排序
                sorted_indices = np.argsort(all_balances)[::-1]
                
                # 找到当前hub在总排名中的位置
                hub_index = all_ids.index(f"hub_{bh_id}")
                rank = np.where(sorted_indices == hub_index)[0][0] + 1
                broker_rank.append(rank)
                
                # 参与率
                total_volunteers = len(state['volunteers'])
                participation_rate = (len(bh['users']) + 1) / (total_volunteers + 1) * 100
                participation_rates.append(participation_rate)
                
                # 收益率比例
                current_funds = float(bh['current_funds'])
                revenue_ratio = float(bh['b2e_revenue']) / current_funds * 100 if current_funds > 0 else 0
                revenue_ratios.append(revenue_ratio)
                
                # 投资者资金
                total_user_funds = float(bh['total_user_funds'])
                funds_eth = total_user_funds / 1e18
                investor_funds.append(funds_eth)
                
                # 净收益比例
                if total_user_funds > 0:
                    net_revenue_ratio = float(bh['net_revenue']) / total_user_funds * 100
                else:
                    net_revenue_ratio = 0
                net_revenue_ratios.append(net_revenue_ratio)
                
                # 投资者收益率
                if total_user_funds > 0:
                    investor_revenue_ratio = (float(bh['b2e_revenue']) * (1 - float(bh['tax_rate']))) / total_user_funds * 100
                else:
                    investor_revenue_ratio = 0
                investor_revenue_ratios.append(investor_revenue_ratio)
                
                # 存储到分析数据
                analysis_data[pool_name]['epochs'].append(epoch)
                analysis_data[pool_name]['mfr'].append(mfr)
                analysis_data[pool_name]['rank'].append(rank)
                analysis_data[pool_name]['participation'].append(participation_rate)
                analysis_data[pool_name]['revenue_ratio'].append(revenue_ratio)
                analysis_data[pool_name]['funds'].append(funds_eth)
                analysis_data[pool_name]['net_revenue'].append(net_revenue_ratio)
                analysis_data[pool_name]['stakeholder_revenue'].append(investor_revenue_ratio)
        
        # 绘制子图
        # (a) MFR & Rank Performance
        ax1 = axes[row, 0]
        ax1_twin = ax1.twinx()
        
        
        # 创建自定义的marker显示位置
        marker_indices = []
        # 前100个点，每2个显示一个
        marker_indices.extend(range(0, min(50, len(epochs)), 3))
        # 后续的点，每10个显示一个
        if len(epochs) > 50:
            marker_indices.extend(range(50, len(epochs), 10))

        
        ax1.plot(epochs, mer_values, '-', color='#1f77b4', label=f'{convert_label_name(bh_id)} MFR', linewidth=2,  marker='o', markevery = 5, markersize = 4)
        ax1_twin.plot(epochs, broker_rank, '-', color='#2ca02c', label=f'{convert_label_name(bh_id)} Rank', linewidth=2, marker='o', markevery = 5, markersize = 4)
        
        ax1.set_ylabel('Ratio (%)', fontsize=25, labelpad = -15)
        ax1_twin.set_ylabel('Rank', fontsize=25)
        
        # 设置左侧Y轴百分比格式
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
        
        # 设置左侧Y轴的刻度数字大小
        # ax1.tick_params(axis='y', labelsize=100)
        
        # 设置右侧Y轴为整数格式
        ax1_twin.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        # 设置右侧Y轴的刻度数字大小
        ax1_twin.tick_params(axis='y', labelsize=25)
        
        # 自动调整Y轴范围以适应数据
        ax1.set_ylim(0, 100)
        
        # 为Rank轴设置更合适的范围（整数）
        ax1_twin.set_ylim(0, 70)
        
        # 设置X轴刻度
        ax1.xaxis.set_major_locator(MultipleLocator(50))  # 每50个epoch显示一个刻度
        # 设置左侧Y轴刻度间隔
        ax1.yaxis.set_major_locator(MultipleLocator(20))  # Y轴每20%显示一个刻度
        
        ax1_twin.yaxis.set_major_locator(MultipleLocator(10))
        
        
        ax1.grid(True, alpha=0.3)
        
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax1_twin.get_legend_handles_labels()
        
        # 根据行号设置不同的图例位置
        if row == 0:  # 图 a
            ax1.legend(lines1 + lines2, labels1 + labels2, 
                      bbox_to_anchor=(1, 1), loc='upper right', fontsize=25, handlelength=1.2,handletextpad = 0.4)
        else:  # 图 e
            ax1.legend(lines1 + lines2, labels1 + labels2, 
                    bbox_to_anchor=(0.98, 0.98), loc='upper right', fontsize=25,  handlelength=1.2,handletextpad = 0.4)

        
        # 根据行号决定标题位置
        # 第一行 (row=0) abcd 的标题位置可以单独调整 y 值
        # 第二行 (row=1) efgh 的标题位置可以单独调整 y 值
        if row == 0:
            ax1.set_title(f'({chr(97+row*4)}) MFR & Rank Performance', 
                         fontsize=25, y=-0.22)  # 调整 abcd 的位置，可以修改这个值
        else:
            ax1.set_title(f'({chr(97+row*4)}) MFR & Rank Performance', 
                         fontsize=25, y=-0.27)  # 调整 efgh 的位置
        
        # (b) MFR & Participation - 共用一个Y轴
        ax2 = axes[row, 1]
        
        ax2.plot(epochs, mer_values, '-', color='#1f77b4', label=f'{convert_label_name(bh_id)} MFR', linewidth=2,  marker='o', markevery=5, markersize = 4)
        ax2.plot(epochs, participation_rates, '-', color='#ff7f0e', label='Participation Rate', linewidth=2,  marker='o', markevery=5, markersize = 4)
        
        ax2.set_ylabel('Ratio (%)', fontsize=25, labelpad = -15)  # 保持原来的标签
        
        # 设置Y轴百分比格式
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
        
        # 自动调整Y轴范围以适应数据
        all_data = mer_values + participation_rates
        ax2.set_ylim(min(all_data) * 0.9, 105)
        
        # 设置X轴刻度
        ax2.xaxis.set_major_locator(MultipleLocator(50))
        # 设置Y轴刻度间隔
        ax2.yaxis.set_major_locator(MultipleLocator(20))
        
        ax2.grid(True, alpha=0.3)
        
        # 调整右侧空白区域
        ax2.yaxis.set_label_position('left')
        ax2.yaxis.tick_left()
        
        # 根据行号设置不同的图例位置
        if row == 0:  # 图 b
            ax2.legend(bbox_to_anchor=(1.03, 0.8), loc='upper right', fontsize=25, handlelength=1.2,handletextpad = 0.4, borderpad = 0.19)

        else:  # 图 f
            ax2.legend(bbox_to_anchor=(1.03, 0.8), 
                    loc='upper right', 
                    fontsize=25, handlelength=1.2, handletextpad = 0.4, borderpad = 0.19)

        
        if row == 0:
            ax2.set_title(f'({chr(98+row*4)}) MFR & Participation ratio', 
                         fontsize=25, y=-0.22)
        else:
            ax2.set_title(f'({chr(98+row*4)}) MFR & Participation ratio', 
                         fontsize=25, y=-0.27)
        
        # (c) Revenue Ratio & Investor Funds
        ax3 = axes[row, 2]
        ax3_twin = ax3.twinx()
        
        ax3.plot(epochs, revenue_ratios, '-', color='#d62728', label=f'{convert_label_name(bh_id)}', linewidth=2,  marker='o', markevery=5, markersize = 4)
        ax3_twin.plot(epochs, investor_funds, '-', color='#ffbb33', label='Total staked Funds', linewidth=2,  marker='o', markevery=5, markersize = 4)
        
        ax3.set_ylabel('Revenue Ratio(%)', fontsize=25, labelpad = -2)
        ax3_twin.set_ylabel('Funds (ETH)', fontsize=25, labelpad = -10)  # 添加 ETH 单位
        
        # 设置右侧Y轴的刻度数字大小
        ax3_twin.tick_params(axis='y', labelsize=25)
        

        # 自动调整Y轴范围以适应数据，添加一点padding
        if revenue_ratios:
            # ax3.set_ylim(min(revenue_ratios) * 0.9, max(revenue_ratios) * 1.1)
            ax3.set_ylim(0, 20)
        if investor_funds:
            ax3_twin.set_ylim(min(investor_funds) * 0.9, max(investor_funds) * 1.1)
        
        
        ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
        
        # 设置X轴刻度
        ax3.xaxis.set_major_locator(MultipleLocator(50))
        
        ax3.grid(True, alpha=0.3)
        
        lines1, labels1 = ax3.get_legend_handles_labels()
        lines2, labels2 = ax3_twin.get_legend_handles_labels()
        
        # 根据行号设置不同的图例位置
        if row == 0:  # 图 c
            ax3.legend(lines1 + lines2, labels1 + labels2, 
                        bbox_to_anchor=(0.64, 0.9),
                      loc='upper center', fontsize=25, handlelength=1.2, handletextpad = 0.4, borderpad=0.2)
        else:  # 图 g
            ax3.legend(lines1 + lines2, labels1 + labels2,
                      bbox_to_anchor=(0.64, 0.9), loc='upper center', fontsize=25, handlelength=1.2, handletextpad = 0.4, borderpad=0.2)
        
        if row == 0:
            ax3.set_title(f'({chr(99+row*4)}) Revenue ratio & Total staked funds', 
                         fontsize=25, y=-0.22)
        else:
            ax3.set_title(f'({chr(99+row*4)}) Revenue ratio & Total staked funds', 
                         fontsize=25, y=-0.27)
                # (d) Net Revenue & Investor Revenue
        ax4 = axes[row, 3]
        ax4_twin = ax4.twinx()
        
        ax4.plot(epochs, net_revenue_ratios, '-', color='#17becf', label=f'{convert_label_name(bh_id)}', linewidth=2,  marker='o', markevery=5, markersize = 4)
        ax4_twin.plot(epochs, investor_revenue_ratios, '-', color='#9467bd', label='Stakeholder', linewidth=2,  marker='o', markevery=5, markersize = 4)
        
        ax4.set_ylabel('LiquidityPool revenue ratio (%)', fontsize=25)  # 保持原来的标签
        ax4_twin.set_ylabel('Stakeholder revenue ratio (%)', fontsize=25, labelpad = -10)  # 保持原来的标签
        
        # 根据数据范围设置不同的格式化方式
        max_net_revenue = max(net_revenue_ratios) if net_revenue_ratios else 0
        max_investor_revenue = max(investor_revenue_ratios) if investor_revenue_ratios else 0
        
        # 如果最大值小于1%，使用小数点格式
        ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
        ax4_twin.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
        
        # 设置右侧Y轴的刻度数字大小
        ax4_twin.tick_params(axis='y', labelsize=25)
        
        
        # 自动调整Y轴范围以适应数据
        ax4.set_ylim(0, 5)
        ax4_twin.set_ylim(0, 10)
        # ax4.set_ylim(0, 1)
        # ax4_twin.set_ylim(0, 3)
            
        # 设置X轴刻度
        ax4.xaxis.set_major_locator(MultipleLocator(50))
        
        ax4.grid(True, alpha=0.3)
        
        lines1, labels1 = ax4.get_legend_handles_labels()
        lines2, labels2 = ax4_twin.get_legend_handles_labels()
        
        # 根据行号设置不同的图例位置
        if row == 0:  # 图 d
            ax4.legend(lines1 + lines2, labels1 + labels2, handlelength=1.2,
                      bbox_to_anchor=(0.7, 1.01), 
                      loc='upper right', fontsize = 25, handletextpad = 0.4)
                      # loc='upper right', fontsize = 25, handletextpad = 0.4, borderpad = 0.19,labelspacing = 0.1)
        else:  # 图 h
            ax4.legend(lines1 + lines2, labels1 + labels2, handlelength=1.2, 
                      bbox_to_anchor=(0.7, 1.02), 
                      loc='upper right', fontsize = 25, handletextpad = 0.4)
        if row == 1:  # 只在图(h)中添加
            # 标记点位置（箭头头部指向的位置）
            mark_x = 80
            mark_y = 0
            
            # 使用散点图创建一个圆形标记
            ax4.scatter(mark_x, mark_y, s=300, facecolors='none', 
                        edgecolors='red', linewidths=2, clip_on=False)
            
            # 文本框位置（保持不变）
            text_x = 60  
            text_y = 2
            
            # 英文说明文字
            explanation = "LiquidityPool2 failed \nin competition. \nNo stakeholders join, \nno revenue earned."
            
            # 只添加文本框，不带箭头
            ax4.annotate(explanation, xy=(text_x, text_y), xytext=(text_x, text_y),
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="red", lw=1),
                        fontsize=25, clip_on=False)
            
            # 单独添加箭头 - 自定义箭头尾巴位置
            arrow_tail_x = 160  # 调整箭头尾巴的x位置
            arrow_tail_y = 1.9 # 调整箭头尾巴的y位置
            
            # 单独绘制箭头
            ax4.annotate('', xy=(mark_x, mark_y), xytext=(arrow_tail_x, arrow_tail_y),
                        arrowprops=dict(facecolor='red', shrink=0.05, width=1.5,
                                       headwidth=8, headlength=10, clip_on=False),
                        clip_on=False)
                         
        if row == 0:
            ax4.set_title(f'({chr(100+row*4)}) Revenue ratio', 
                         fontsize=25, y=-0.22)
        else:
            ax4.set_title(f'({chr(100+row*4)}) Revenue ratio', 
                         fontsize=25, y=-0.27)
    
    # 设置所有子图的X轴标签
    for i in range(4):
        # ② 调整横轴 label 的文字大小：修改 fontsize 参数
        # 可以尝试不同的数值，例如 12, 14, 16 等
        axes[1, i].set_xlabel('Epoch', fontsize=25)
    
    # ③ 调整所有子图的横轴数字大小
    for ax in axes.flat:
        # 修改 labelsize 参数来调整刻度数字大小
        # 可以尝试不同的数值，例如 10, 12, 14 等
        ax.tick_params(axis='x', labelsize=25)
        ax.tick_params(axis='y', labelsize=25)
    
        # =============== 添加关键数据分析和输出 ===============
    print(f"\n=== 竞争阶段分析 ===")
    
    # 分析早期竞争阶段 (0-50 epochs)
    early_epochs = range(0, min(50, epoch_limit))
    print(f"\n【早期竞争阶段 (Epochs 0-50)】")
    for pool_name in analysis_data.keys():
        if len(analysis_data[pool_name]['epochs']) > 0:
            early_data = {k: [v[i] for i in early_epochs if i < len(v)] 
                         for k, v in analysis_data[pool_name].items() if k != 'epochs'}
            if early_data['mfr']:
                print(f"{pool_name}:")
                print(f"  平均MFR: {np.mean(early_data['mfr']):.2f}%")
                print(f"  平均排名: {np.mean(early_data['rank']):.1f}")
                print(f"  平均参与率: {np.mean(early_data['participation']):.2f}%")
                print(f"  平均资金: {np.mean(early_data['funds']):.2f} ETH")
    
    # 分析中期阶段 (50-150 epochs)
    mid_epochs = range(50, min(150, epoch_limit))
    print(f"\n【中期竞争阶段 (Epochs 50-150)】")
    for pool_name in analysis_data.keys():
        if len(analysis_data[pool_name]['epochs']) > 50:
            mid_data = {k: [v[i] for i in mid_epochs if i < len(v)] 
                       for k, v in analysis_data[pool_name].items() if k != 'epochs'}
            if mid_data['mfr']:
                print(f"{pool_name}:")
                print(f"  平均MFR: {np.mean(mid_data['mfr']):.2f}%")
                print(f"  平均排名: {np.mean(mid_data['rank']):.1f}")
                print(f"  平均参与率: {np.mean(mid_data['participation']):.2f}%")
                print(f"  平均资金: {np.mean(mid_data['funds']):.2f} ETH")
    
    # 分析后期阶段 (150-300 epochs)
    late_epochs = range(150, epoch_limit)
    print(f"\n【后期垄断阶段 (Epochs 150-300)】")
    for pool_name in analysis_data.keys():
        if len(analysis_data[pool_name]['epochs']) > 150:
            late_data = {k: [v[i] for i in late_epochs if i < len(v)] 
                        for k, v in analysis_data[pool_name].items() if k != 'epochs'}
            if late_data['mfr']:
                print(f"{pool_name}:")
                print(f"  平均MFR: {np.mean(late_data['mfr']):.2f}%")
                print(f"  平均排名: {np.mean(late_data['rank']):.1f}")
                print(f"  平均参与率: {np.mean(late_data['participation']):.2f}%")
                print(f"  平均资金: {np.mean(late_data['funds']):.2f} ETH")
                print(f"  平均收益率: {np.mean(late_data['revenue_ratio']):.3f}%")
    
    # 找出关键转折点
    print(f"\n=== 关键转折点分析 ===")
    for pool_name in analysis_data.keys():
        data = analysis_data[pool_name]
        if len(data['participation']) > 100:
            # 找出参与率下降到5%以下的时间点
            for i, participation in enumerate(data['participation']):
                if participation < 5.0 and i > 50:  # 50 epoch后才算
                    print(f"{pool_name} 参与率跌破5%: Epoch {data['epochs'][i]}")
                    break
            
            # 找出资金归零的时间点
            for i, funds in enumerate(data['funds']):
                if funds < 1.0 and i > 50:  # 资金低于1 ETH
                    print(f"{pool_name} 资金跌破1 ETH: Epoch {data['epochs'][i]}")
                    break
    
    # 最终结果对比
    print(f"\n=== 最终结果对比 (Epoch {epoch_limit-1}) ===")
    for pool_name in analysis_data.keys():
        data = analysis_data[pool_name]
        if data['epochs']:
            print(f"{pool_name} 最终状态:")
            print(f"  MFR: {data['mfr'][-1]:.2f}%")
            print(f"  排名: {data['rank'][-1]}")
            print(f"  参与率: {data['participation'][-1]:.2f}%")
            print(f"  总资金: {data['funds'][-1]:.2f} ETH")
            print(f"  收益率: {data['revenue_ratio'][-1]:.3f}%")
    
    
    # 保存图形
    output_path = os.path.join(output_folder, 'diff_final_liquidityPool_multiple_metrics.pdf')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print("多指标对比图已生成！")




if __name__ == "__main__":
    # =========================== 参数设置 ===========================
    # 实验参数
    experiment_name = "trump_20w_300_diff_final_balance2"  # 实验名称，用于文件命名
    # experiment_name = "10hubs_20w_300_diff_final_balance"  # 实验名称，用于文件命名
    num_epochs = 300  # 总的epoch数量，决定绘图的x轴长度
    
    # 文件路径参数
    results_filename = f"simulation_results_{experiment_name}.json"  # 结果文件名
    input_folder = "../result/output"  # 输入文件夹（相对于当前脚本的路径）
    output_folder_base = "./exper23"  # 输出文件夹基础路径（相对于当前脚本的路径）
    
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
    print(f"开始绘制图表...")
    print(f"输入文件: {results_path}")
    print(f"输出文件夹: {output_folder}")
    print(f"Epoch限制: {num_epochs}")
    
    plot_brokerhub_metrics(results_path, output_folder, epoch_limit=num_epochs)
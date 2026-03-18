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

def plot_individual_charts(results_path, output_folder, epoch_limit):
    """
    为每个BrokerHub创建独立的图表
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
    
    # 提取数据
    epochs = [int(state['epoch']) for state in results][:epoch_limit]
    
    # 为每个BrokerHub收集数据
    for row, bh_id in enumerate(brokerhub_ids[:2]):  # 只处理前两个BrokerHub
        pool_name = convert_label_name(bh_id)
        
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
        
        # 创建4个独立的图表
        chart_letter = chr(97 + row * 4)  # a, e for row 0, 1
        
        # Chart 1: MFR & Rank Performance
        fig, ax1 = plt.subplots(figsize=(7, 5))
        ax1_twin = ax1.twinx()
        
        ax1.plot(epochs, mer_values, '-', color='#1f77b4', label=f'{convert_label_name(bh_id)} MFR', linewidth=2, marker='o', markevery=5, markersize=4)
        ax1_twin.plot(epochs, broker_rank, '-', color='#2ca02c', label=f'{convert_label_name(bh_id)} Rank', linewidth=2, marker='o', markevery=5, markersize=4)
        
        ax1.set_ylabel('Ratio (%)', fontsize=25, labelpad=-15)
        ax1_twin.set_ylabel('Rank', fontsize=25)
        ax1.set_xlabel('Epoch', fontsize=25)
        
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
        ax1_twin.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax1_twin.tick_params(axis='y', labelsize=25)
        
        ax1.set_ylim(0, 100)
        ax1_twin.set_ylim(0, 70)
        
        ax1.xaxis.set_major_locator(MultipleLocator(50))
        ax1.yaxis.set_major_locator(MultipleLocator(20))
        ax1_twin.yaxis.set_major_locator(MultipleLocator(10))
        
        ax1.grid(True, alpha=0.3)
        
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax1_twin.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=25, handlelength=1.2, handletextpad=0.4)
        
        # ax1.set_title(f'({chart_letter}) MFR & Rank Performance', fontsize=25)
        ax1.tick_params(axis='x', labelsize=25)
        ax1.tick_params(axis='y', labelsize=25)
        
        filename = f'{pool_name}_{chart_letter}_MFR_Rank_Performance'
        plt.savefig(os.path.join(output_folder, f'{filename}.pdf'), dpi=300, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, f'{filename}.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # Chart 2: MFR & Participation
        chart_letter = chr(98 + row * 4)  # b, f
        fig, ax2 = plt.subplots(figsize=(7, 5))
        
        ax2.plot(epochs, mer_values, '-', color='#1f77b4', label=f'{convert_label_name(bh_id)} MFR', linewidth=2, marker='o', markevery=5, markersize=4)
        ax2.plot(epochs, participation_rates, '-', color='#ff7f0e', label='Participation Rate', linewidth=2, marker='o', markevery=5, markersize=4)
        
        ax2.set_ylabel('Ratio (%)', fontsize=25, labelpad=-15)
        ax2.set_xlabel('Epoch', fontsize=25)
        
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
        
        all_data = mer_values + participation_rates
        ax2.set_ylim(min(all_data) * 0.9, 105)
        
        ax2.xaxis.set_major_locator(MultipleLocator(50))
        ax2.yaxis.set_major_locator(MultipleLocator(20))
        
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='upper right', fontsize=25, handlelength=1.2, handletextpad=0.4, borderpad=0.19)
        
        # ax2.set_title(f'({chart_letter}) MFR & Participation ratio', fontsize=25)
        ax2.tick_params(axis='x', labelsize=25)
        ax2.tick_params(axis='y', labelsize=25)
        
        filename = f'{pool_name}_{chart_letter}_MFR_Participation'
        plt.savefig(os.path.join(output_folder, f'{filename}.pdf'), dpi=300, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, f'{filename}.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # Chart 3: Revenue Ratio & Investor Funds
        chart_letter = chr(99 + row * 4)  # c, g
        fig, ax3 = plt.subplots(figsize=(7, 5))
        ax3_twin = ax3.twinx()
        
        ax3.plot(epochs, revenue_ratios, '-', color='#d62728', label=f'{convert_label_name(bh_id)}', linewidth=2, marker='o', markevery=5, markersize=4)
        ax3_twin.plot(epochs, investor_funds, '-', color='#ffbb33', label='Total staked Funds', linewidth=2, marker='o', markevery=5, markersize=4)
        
        ax3.set_ylabel('Revenue Ratio(%)', fontsize=25, labelpad=-2)
        ax3_twin.set_ylabel('Funds (ETH)', fontsize=25, labelpad=-10)
        ax3.set_xlabel('Epoch', fontsize=25)
        
        ax3_twin.tick_params(axis='y', labelsize=25)
        
        ax3.set_ylim(0, 20)
        if investor_funds:
            ax3_twin.set_ylim(min(investor_funds) * 0.9, max(investor_funds) * 1.1)
        
        ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
        ax3.xaxis.set_major_locator(MultipleLocator(50))
        
        ax3.grid(True, alpha=0.3)
        
        lines1, labels1 = ax3.get_legend_handles_labels()
        lines2, labels2 = ax3_twin.get_legend_handles_labels()
        ax3.legend(lines1 + lines2, labels1 + labels2, loc='upper center', fontsize=25, handlelength=1.2, handletextpad=0.4, borderpad=0.2)
        
        # # ax3.set_title(f'({chart_letter}) Revenue ratio & Total staked funds', fontsize=25)
        ax3.tick_params(axis='x', labelsize=25)
        ax3.tick_params(axis='y', labelsize=25)
        
        filename = f'{pool_name}_{chart_letter}_Revenue_Funds'
        plt.savefig(os.path.join(output_folder, f'{filename}.pdf'), dpi=300, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, f'{filename}.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # Chart 4: Net Revenue & Investor Revenue
        chart_letter = chr(100 + row * 4)  # d, h
        fig, ax4 = plt.subplots(figsize=(7, 5))
        ax4_twin = ax4.twinx()
        
        ax4.plot(epochs, net_revenue_ratios, '-', color='#17becf', label=f'{convert_label_name(bh_id)}', linewidth=2, marker='o', markevery=5, markersize=4)
        ax4_twin.plot(epochs, investor_revenue_ratios, '-', color='#9467bd', label='Stakeholder', linewidth=2, marker='o', markevery=5, markersize=4)
        
        ax4.set_ylabel('LiquidityPool revenue ratio (%)', fontsize=25)
        ax4_twin.set_ylabel('Stakeholder revenue ratio (%)', fontsize=25, labelpad=-10)
        ax4.set_xlabel('Epoch', fontsize=25)
        
        ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
        ax4_twin.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
        
        ax4_twin.tick_params(axis='y', labelsize=25)
        
        ax4.set_ylim(0, 5)
        ax4_twin.set_ylim(0, 10)
        
        ax4.xaxis.set_major_locator(MultipleLocator(50))
        
        ax4.grid(True, alpha=0.3)
        
        lines1, labels1 = ax4.get_legend_handles_labels()
        lines2, labels2 = ax4_twin.get_legend_handles_labels()
        ax4.legend(lines1 + lines2, labels1 + labels2, handlelength=1.2, loc='upper right', fontsize=25, handletextpad=0.4)
        
        # 特殊标记逻辑（仅在h图中）
        if row == 1:
            mark_x = 80
            mark_y = 0
            
            ax4.scatter(mark_x, mark_y, s=300, facecolors='none', edgecolors='red', linewidths=2, clip_on=False)
            
            text_x = 60
            text_y = 2
            
            explanation = "LiquidityPool2 failed \nin competition. \nNo stakeholders join, \nno revenue earned."
            
            ax4.annotate(explanation, xy=(text_x, text_y), xytext=(text_x, text_y),
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="red", lw=1),
                        fontsize=25, clip_on=False)
            
            arrow_tail_x = 160
            arrow_tail_y = 1.9
            
            ax4.annotate('', xy=(mark_x, mark_y), xytext=(arrow_tail_x, arrow_tail_y),
                        arrowprops=dict(facecolor='red', shrink=0.05, width=1.5,
                                       headwidth=8, headlength=10, clip_on=False),
                        clip_on=False)
        
        # ax4.set_title(f'({chart_letter}) Revenue ratio', fontsize=25)
        ax4.tick_params(axis='x', labelsize=25)
        ax4.tick_params(axis='y', labelsize=25)
        
        filename = f'{pool_name}_{chart_letter}_Revenue_Ratio'
        plt.savefig(os.path.join(output_folder, f'{filename}.pdf'), dpi=300, bbox_inches='tight')
        plt.savefig(os.path.join(output_folder, f'{filename}.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    print("所有独立图表已生成！")

if __name__ == "__main__":
    # =========================== 参数设置 ===========================
    # 实验参数
    experiment_name = "trump_20w_300_diff_final_balance2"  # 实验名称，用于文件命名
    num_epochs = 300  # 总的epoch数量，决定绘图的x轴长度
    
    # 文件路径参数
    results_filename = f"simulation_results_{experiment_name}.json"  # 结果文件名
    input_folder = "../result/output"  # 输入文件夹（相对于当前脚本的路径）
    output_folder_base = "./0801exper7"  # 输出文件夹基础路径（相对于当前脚本的路径）
    
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
    print(f"开始绘制独立图表...")
    print(f"输入文件: {results_path}")
    print(f"输出文件夹: {output_folder}")
    print(f"Epoch限制: {num_epochs}")
    
    plot_individual_charts(results_path, output_folder, epoch_limit=num_epochs)
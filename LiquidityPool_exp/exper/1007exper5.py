import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import MultipleLocator, MaxNLocator
import matplotlib.ticker as ticker

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def convert_label_name(bh_id):
    """
    将BrokerHub标识符转换为LiquidityPool标识符
    """
    return bh_id.replace('BrokerHub', 'LiquidityPool')

def plot_brokerhub_metrics(results_path, output_folder, epoch_limit):
    """
    绘制 2×2 对比图：Pool1 vs Pool2
    (a) Competition Dynamics - Ranking + MFR
    (b) Fund Aggregation Race
    (c) Pool Revenue Performance
    (d) Stakeholder Revenue Comparison [NEW]
    """
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    # 加载JSON数据
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    # 获取所有BrokerHub的ID
    brokerhub_ids = list(set(bh['id'] for state in results for bh in state['brokerhubs']))
    brokerhub_ids.sort()
    
    print(f"\n{'='*60}")
    print(f"🎨 Figure 5 竞争动态分析 - 重构版")
    print(f"{'='*60}")
    print(f"📊 分析的LiquidityPool: {[convert_label_name(bh_id) for bh_id in brokerhub_ids[:2]]}")
    print(f"⏱️  分析epoch范围: 0-{epoch_limit}")
    
    # ========== 全局样式设置 ==========
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans'],
        'font.size': 11,
        'axes.linewidth': 1.0,
        'axes.labelsize': 13,
        'axes.titlesize': 13,
        'axes.titleweight': 'bold',
        'xtick.labelsize': 11,
        'ytick.labelsize': 11,
        'legend.fontsize': 10,
        'legend.frameon': True,
        'legend.fancybox': False,
        'legend.edgecolor': '#cccccc',
        'grid.linewidth': 0.5,
        'grid.alpha': 0.3,
        'lines.linewidth': 2.0,
    })
    
    # 配色方案
    POOL1_DARK = '#1f77b4'   # Pool1 主色（深蓝）
    POOL1_LIGHT = '#a6cee3'  # Pool1 辅助色（浅蓝）
    POOL2_DARK = '#d62728'   # Pool2 主色（深红）
    POOL2_LIGHT = '#fb9a99'  # Pool2 辅助色（浅红）
    GRAY_DARK = '#333333'    # 深灰（主要文字）
    GRAY_MID = '#666666'     # 中灰（次要文字）
    GRAY_LIGHT = '#888888'   # 浅灰（baseline）
    
    # 转折点设置
    TURNING_POINTS = [14, 51, 75]
    VLINE_STYLE = {'color': 'gray', 'linestyle': '--', 
                   'alpha': 0.4, 'linewidth': 1, 'zorder': 1}
    
    # 创建图形 - 2×2 布局
    fig = plt.figure(figsize=(14, 10))
    gs = GridSpec(2, 2, figure=fig, hspace=0.18, wspace=0.30,
                  left=0.08, right=0.95, top=0.95, bottom=0.08)
    
    # 提取epochs
    epochs = [int(state['epoch']) for state in results][:epoch_limit]
    
    # ========== 收集两个Pool的所有数据 ==========
    pools_data = {}
    
    for bh_id in brokerhub_ids[:2]:  # 只处理前两个BrokerHub
        pool_name = convert_label_name(bh_id)
        
        # 初始化数据列表
        mfr_values = []
        rank_values = []
        participation_rates = []
        total_funds = []
        pool_revenue_ratios = []      # Pool operator 收益（来自管理费）
        stakeholder_revenue_ratios = []  # Stakeholder 收益
        
        # 收集数据
        for state in results[:epoch_limit]:
            bh = next((bh for bh in state['brokerhubs'] if bh['id'] == bh_id), None)
            if bh:
                # 1. 管理费率 (MFR)
                mfr = float(bh['tax_rate']) * 100
                mfr_values.append(mfr)
                
                # 2. 排名计算
                all_balances = []
                all_ids = []
                
                joined_volunteer_ids = set()
                for hub in state['brokerhubs']:
                    joined_volunteer_ids.update(hub['users'])
                
                for volunteer in state['volunteers']:
                    if volunteer['id'] not in joined_volunteer_ids:
                        all_balances.append(float(volunteer['balance']))
                        all_ids.append(f"volunteer_{volunteer['id']}")
                
                for hub in state['brokerhubs']:
                    all_balances.append(float(hub['current_funds']))
                    all_ids.append(f"hub_{hub['id']}")
                
                sorted_indices = np.argsort(all_balances)[::-1]
                hub_index = all_ids.index(f"hub_{bh_id}")
                rank = np.where(sorted_indices == hub_index)[0][0] + 1
                rank_values.append(rank)
                
                # 3. 参与率
                total_volunteers = len(state['volunteers'])
                participation_rate = (len(bh['users']) + 1) / (total_volunteers + 1) * 100
                participation_rates.append(participation_rate)
                
                # 4. 总资金 (ETH)
                total_user_funds = float(bh['total_user_funds'])
                funds_eth = total_user_funds / 1e18
                total_funds.append(funds_eth)
                
                # 5. Pool Revenue（Pool operator 的收益，来自管理费）
                if total_user_funds > 0:
                    pool_revenue_ratio = float(bh['net_revenue']) / total_user_funds * 100
                else:
                    pool_revenue_ratio = 0
                pool_revenue_ratios.append(pool_revenue_ratio)
                
                # 6. Stakeholder Revenue（参与者的收益）
                if total_user_funds > 0:
                    stakeholder_revenue_ratio = (float(bh['b2e_revenue']) * (1 - float(bh['tax_rate']))) / total_user_funds * 100
                else:
                    stakeholder_revenue_ratio = 0
                stakeholder_revenue_ratios.append(stakeholder_revenue_ratio)
        
        # 数据验证
        assert len(epochs) == len(mfr_values), f"{pool_name}: 数据长度不匹配"
        assert not np.any(np.isnan(total_funds)), f"{pool_name}: 存在 NaN 值"
        
        # 存储数据
        pools_data[pool_name] = {
            'mfr': np.array(mfr_values),
            'rank': np.array(rank_values),
            'participation': np.array(participation_rates),
            'funds': np.array(total_funds),
            'pool_revenue': np.array(pool_revenue_ratios),
            'stakeholder_revenue': np.array(stakeholder_revenue_ratios)
        }
        
        # 打印统计信息
        print(f"\n📈 {pool_name} 数据统计:")
        print(f"  Pool Revenue: mean={np.mean(pool_revenue_ratios):.4f}%, std={np.std(pool_revenue_ratios):.4f}%")
        print(f"  Stakeholder Revenue: mean={np.mean(stakeholder_revenue_ratios):.4f}%, std={np.std(stakeholder_revenue_ratios):.4f}%")
    
    # 获取两个Pool的名称
    pool1_name = convert_label_name(brokerhub_ids[0])
    pool2_name = convert_label_name(brokerhub_ids[1])
    
    pool1 = pools_data[pool1_name]
    pool2 = pools_data[pool2_name]
    
    # ========== 子图 (a): Competition Dynamics - Ranking + MFR ==========
    print(f"\n📊 绘制 (a) Competition Dynamics...")
    ax_a = fig.add_subplot(gs[0, 0])
    ax_a_right = ax_a.twinx()
    
    # 左Y轴：Ranking (反转，越低越好)
    ax_a.plot(epochs, pool1['rank'], 
              color=POOL1_DARK, linewidth=2.5, linestyle='-',
              label=f'{pool1_name} Ranking', zorder=3, 
              marker='o', markevery=10, markersize=5)
    ax_a.plot(epochs, pool2['rank'], 
              color=POOL2_DARK, linewidth=2.5, linestyle='-',
              label=f'{pool2_name} Ranking', zorder=3, 
              marker='s', markevery=10, markersize=5)
    
    ax_a.set_ylabel('Ranking Position', fontsize=22)
    ax_a.set_ylim([70, 0])
    ax_a.invert_yaxis()
    ax_a.tick_params(axis='y', labelsize=22, labelcolor=GRAY_DARK)
    ax_a.yaxis.set_major_locator(MaxNLocator(6))
    
    # 右Y轴：MFR
    ax_a_right.plot(epochs, pool1['mfr'],
                    color=POOL1_LIGHT, linewidth=1.5, linestyle='--',
                    label=f'{pool1_name} MFR', alpha=0.8, zorder=2)
    ax_a_right.plot(epochs, pool2['mfr'], 
                    color=POOL2_LIGHT, linewidth=1.5, linestyle='--',
                    label=f'{pool2_name} MFR', alpha=0.8, zorder=2)
    
    ax_a_right.set_ylabel('Management Fee Ratio (%)', fontsize=20, labelpad=-9)
    ax_a_right.set_ylim([0, 100])
    ax_a_right.tick_params(axis='y', labelsize=22)
    ax_a_right.yaxis.set_major_locator(MaxNLocator(6))
    
    # 转折点
    for tp in TURNING_POINTS:
        if tp < epoch_limit:
            ax_a.axvline(x=tp, **VLINE_STYLE)
    
    # Legend
    lines_left, labels_left = ax_a.get_legend_handles_labels()
    lines_right, labels_right = ax_a_right.get_legend_handles_labels()
    ax_a.legend(lines_left + lines_right, labels_left + labels_right, handlelength=1, handletextpad=0.4,
                loc='upper right', fontsize=22, frameon=True, fancybox=False)
    
    # ax_a.set_xlabel('Epoch', fontsize=13)
    ax_a.set_xlim([0, epoch_limit])
    ax_a.tick_params(axis='x', labelsize=22)
    ax_a.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
    ax_a.set_title(f'(a) Competition Dynamics', fontweight='bold',
             fontsize=22, y=-0.17, loc='center')  # y值可以根据需要微调
    
    # ========== 子图 (b): Fund Aggregation Race ==========
    print(f"📊 绘制 (b) Fund Aggregation Race...")
    ax_b = fig.add_subplot(gs[0, 1])
    
    # 两条对比线
    ax_b.plot(epochs, pool1['funds'],
              color=POOL1_DARK, linewidth=2.5, label=pool1_name, 
              zorder=3, marker='o', markevery=10, markersize=5)
    ax_b.plot(epochs, pool2['funds'],
              color=POOL2_DARK, linewidth=2.0, linestyle='--', 
              label=pool2_name, alpha=0.8, zorder=2, 
              marker='s', markevery=10, markersize=5)
    
    # 填充区域
    ax_b.fill_between(epochs, 0, pool1['funds'],
                      color=POOL1_DARK, alpha=0.15, zorder=1)
    ax_b.fill_between(epochs, 0, pool2['funds'],
                      color=POOL2_DARK, alpha=0.15, zorder=1)
    
    # 转折点
    for tp in TURNING_POINTS:
        if tp < epoch_limit:
            ax_b.axvline(x=tp, **VLINE_STYLE)
    
    ax_b.set_yscale('log')
    ax_b.yaxis.set_major_formatter(ticker.LogFormatterSciNotation())

    
    ax_b.set_ylabel('Total Staked Funds (ETH)', fontsize=20, labelpad=-8)
    # ax_b.set_xlabel('Epoch', fontsize=13)
    ax_b.set_ylim([0, max(pool1['funds']) * 1.1])
    ax_b.set_xlim([0, epoch_limit])
    ax_b.tick_params(labelsize=22)
    ax_b.legend(loc='best', fontsize=22, frameon=True, fancybox=False)
    ax_b.grid(True, alpha=0.3, axis='y', linestyle=':', linewidth=0.5)
    ax_b.set_title(f'(b) Fund Aggregation Race', fontweight='bold',
             fontsize=22, y=-0.17, loc='center')
    # ========== 子图 (c): Pool Revenue Performance ==========
    print(f"📊 绘制 (c) Pool Revenue Performance...")
    ax_c = fig.add_subplot(gs[1, 0])
    
    # 两条对比线
    ax_c.plot(epochs, pool1['pool_revenue'],
              color=POOL1_DARK, linewidth=2.5, label=pool1_name,
              zorder=3, marker='o', markevery=10, markersize=5)
    ax_c.plot(epochs, pool2['pool_revenue'],
              color=POOL2_DARK, linewidth=2.0, linestyle='--', 
              label=pool2_name, alpha=0.8, zorder=2, 
              marker='s', markevery=10, markersize=5)
    
    # 转折点
    for tp in TURNING_POINTS:
        if tp < epoch_limit:
            ax_c.axvline(x=tp, **VLINE_STYLE)
    
    ax_c.set_ylabel('Pool Revenue Ratio (%)', fontsize=25)
    ax_c.set_xlabel('Epoch', fontsize=22, labelpad = -5)
    max_pool_revenue = max(np.max(pool1['pool_revenue']), np.max(pool2['pool_revenue']))
    ax_c.set_ylim([0, max_pool_revenue * 1.15])
    ax_c.set_xlim([0, epoch_limit])
    ax_c.tick_params(labelsize=22)
    ax_c.legend(loc='best', fontsize=22, frameon=True, fancybox=False)
    ax_c.grid(True, alpha=0.3, axis='y', linestyle=':', linewidth=0.5)
    ax_c.set_title(f'(c) Pool Revenue Performance', fontweight='bold',
             fontsize=22, y=-0.23, loc='center')
    # ========== 子图 (d): Stakeholder Revenue Comparison ⭐️ 新增 ==========
    print(f"📊 绘制 (d) Stakeholder Revenue Comparison [NEW]...")
    ax_d = fig.add_subplot(gs[1, 1])
    
    # 两条对比线
    ax_d.plot(epochs, pool1['stakeholder_revenue'],
              color=POOL1_DARK, linewidth=2.5, 
              label=f'{pool1_name} Stakeholders',
              zorder=3, marker='o', markevery=10, markersize=5)
    ax_d.plot(epochs, pool2['stakeholder_revenue'],
              color=POOL2_DARK, linewidth=2.0, linestyle='--', 
              label=f'{pool2_name} Stakeholders', alpha=0.8, 
              zorder=2, marker='s', markevery=10, markersize=5)
    
    # 转折点
    for tp in TURNING_POINTS:
        if tp < epoch_limit:
            ax_d.axvline(x=tp, **VLINE_STYLE)
    
    # 标注稳定收益区（epoch 75-300）
    max_stakeholder_revenue = max(np.max(pool1['stakeholder_revenue']), 
                                  np.max(pool2['stakeholder_revenue']))
    
    if epoch_limit > 75:
        # 浅色背景区域
        ax_d.axvspan(75, epoch_limit, alpha=0.08, color=POOL1_DARK, zorder=0)
        
        # 文本标注
        stable_revenues = pool1['stakeholder_revenue'][75:]
        if len(stable_revenues) > 0:
            mean_stable = np.mean(stable_revenues)
            std_stable = np.std(stable_revenues)
            
            # text_y = max_stakeholder_revenue * 0.80
            text_y = 7
            text_content = (f'{pool1_name}: Stable returns\n'
                          f'({mean_stable:.2f}±{std_stable:.2f}% per epoch)')
            
            ax_d.text((75 + epoch_limit) / 2 - 30, text_y, text_content,
                     fontsize=22, ha='center', va='center', color=POOL1_DARK,
                     bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                              alpha=0.8, edgecolor=POOL1_DARK, linewidth=1.5))
    
    ax_d.set_ylabel('Stakeholder Revenue Ratio (%)', fontsize=25)
    ax_d.set_xlabel('Epoch', fontsize=22, labelpad = -5)
    ax_d.set_ylim([0, max_stakeholder_revenue * 1.20])  # 留20%空间给标注
    ax_d.set_xlim([0, epoch_limit])
    ax_d.tick_params(labelsize=22)
    ax_d.legend(loc='upper left', fontsize=22, bbox_to_anchor=(0,1.02), frameon=True, fancybox=False)
    ax_d.grid(True, alpha=0.3, axis='y', linestyle=':', linewidth=0.5)
    ax_d.set_title(f'(d) Stakeholder Revenue Comparison', fontweight='bold',
             fontsize=22, y=-0.23, loc='center')
    # ========== 数据分析输出 ==========
    print(f"\n{'='*60}")
    print(f"📊 竞争阶段分析")
    print(f"{'='*60}")
    
    # 三个阶段分析
    stages = {
        '早期竞争阶段 (0-50)': (0, 50),
        '中期竞争阶段 (50-150)': (50, 150),
        '后期垄断阶段 (150-300)': (150, epoch_limit)
    }
    
    for stage_name, (start, end) in stages.items():
        print(f"\n【{stage_name}】")
        for pool_name in [pool1_name, pool2_name]:
            data = pools_data[pool_name]
            if len(data['mfr']) >= end:
                print(f"{pool_name}:")
                print(f"  平均MFR: {np.mean(data['mfr'][start:end]):.2f}%")
                print(f"  平均排名: {np.mean(data['rank'][start:end]):.1f}")
                print(f"  平均参与率: {np.mean(data['participation'][start:end]):.2f}%")
                print(f"  平均资金: {np.mean(data['funds'][start:end]):.2f} ETH")
                print(f"  平均Pool收益: {np.mean(data['pool_revenue'][start:end]):.3f}%")
                print(f"  平均Stakeholder收益: {np.mean(data['stakeholder_revenue'][start:end]):.3f}%")
    
    # 关键转折点
    print(f"\n{'='*60}")
    print(f"🔍 关键转折点分析")
    print(f"{'='*60}")
    for pool_name in [pool1_name, pool2_name]:
        data = pools_data[pool_name]
        
        # 参与率跌破5%
        for i, participation in enumerate(data['participation']):
            if participation < 5.0 and i > 50:
                print(f"{pool_name} 参与率跌破5%: Epoch {i}")
                break
        
        # 资金跌破1 ETH
        for i, funds in enumerate(data['funds']):
            if funds < 1.0 and i > 50:
                print(f"{pool_name} 资金跌破1 ETH: Epoch {i}")
                break
    
    # 最终结果
    print(f"\n{'='*60}")
    print(f"🏆 最终结果对比 (Epoch {epoch_limit-1})")
    print(f"{'='*60}")
    for pool_name in [pool1_name, pool2_name]:
        data = pools_data[pool_name]
        print(f"{pool_name}:")
        print(f"  MFR: {data['mfr'][-1]:.2f}%")
        print(f"  排名: {data['rank'][-1]}")
        print(f"  参与率: {data['participation'][-1]:.2f}%")
        print(f"  总资金: {data['funds'][-1]:.2f} ETH")
        print(f"  Pool收益率: {data['pool_revenue'][-1]:.3f}%")
        print(f"  Stakeholder收益率: {data['stakeholder_revenue'][-1]:.3f}%")
    
    # 保存图形
    plt.tight_layout()
    
    output_path_pdf = os.path.join(output_folder, 'figure5_competition_dynamics.pdf')
    output_path_png = os.path.join(output_folder, 'figure5_competition_dynamics.png')
    
    plt.savefig(output_path_pdf, dpi=300, bbox_inches='tight')
    plt.savefig(output_path_png, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n{'='*60}")
    print(f"✅ Figure 5 竞争动态对比图已生成！")
    print(f"{'='*60}")
    print(f"📄 PDF: {output_path_pdf}")
    print(f"🖼️  PNG: {output_path_png}")
    
        # 获取两个Pool的名称
    pool1_name = convert_label_name(brokerhub_ids[0])
    pool2_name = convert_label_name(brokerhub_ids[1])
    
    pool1 = pools_data[pool1_name]
    pool2 = pools_data[pool2_name]
    
    # ========== 新增：关键数值输出 ==========
    print(f"\n{'='*80}")
    print(f"📊 CRITICAL DATA FOR PAPER - DETAILED ANALYSIS")
    print(f"{'='*80}")
    
    # 1. 转折点详细分析
    print(f"\n{'='*80}")
    print(f"🎯 1. TURNING POINTS ANALYSIS")
    print(f"{'='*80}")
    
    turning_points_data = {}
    for tp in TURNING_POINTS:
        if tp < epoch_limit:
            print(f"\n【Epoch {tp} - Critical Turning Point】")
            
            # Pool1数据
            pool1_rank_tp = pool1['rank'][tp]
            pool1_mfr_tp = pool1['mfr'][tp]
            pool1_funds_tp = pool1['funds'][tp]
            pool1_participation_tp = pool1['participation'][tp]
            pool1_pool_revenue_tp = pool1['pool_revenue'][tp]
            pool1_stakeholder_revenue_tp = pool1['stakeholder_revenue'][tp]
            
            # Pool2数据
            pool2_rank_tp = pool2['rank'][tp]
            pool2_mfr_tp = pool2['mfr'][tp]
            pool2_funds_tp = pool2['funds'][tp]
            pool2_participation_tp = pool2['participation'][tp]
            pool2_pool_revenue_tp = pool2['pool_revenue'][tp]
            pool2_stakeholder_revenue_tp = pool2['stakeholder_revenue'][tp]
            
            print(f"\n{pool1_name}:")
            print(f"  Rank: {pool1_rank_tp}")
            print(f"  MFR: {pool1_mfr_tp:.2f}%")
            print(f"  Total Funds: {pool1_funds_tp:.2f} ETH")
            print(f"  Participation Rate: {pool1_participation_tp:.2f}%")
            print(f"  Pool Revenue Ratio: {pool1_pool_revenue_tp:.4f}%")
            print(f"  Stakeholder Revenue Ratio: {pool1_stakeholder_revenue_tp:.4f}%")
            
            print(f"\n{pool2_name}:")
            print(f"  Rank: {pool2_rank_tp}")
            print(f"  MFR: {pool2_mfr_tp:.2f}%")
            print(f"  Total Funds: {pool2_funds_tp:.2f} ETH")
            print(f"  Participation Rate: {pool2_participation_tp:.2f}%")
            print(f"  Pool Revenue Ratio: {pool2_pool_revenue_tp:.4f}%")
            print(f"  Stakeholder Revenue Ratio: {pool2_stakeholder_revenue_tp:.4f}%")
            
            # 计算差异
            rank_diff = pool1_rank_tp - pool2_rank_tp
            mfr_diff = pool1_mfr_tp - pool2_mfr_tp
            funds_diff = pool1_funds_tp - pool2_funds_tp
            
            print(f"\n📊 Differences (Pool1 - Pool2):")
            print(f"  Rank Diff: {rank_diff:+.0f} {'(Pool1 better)' if rank_diff < 0 else '(Pool2 better)'}")
            print(f"  MFR Diff: {mfr_diff:+.2f}%")
            print(f"  Funds Diff: {funds_diff:+.2f} ETH")
            
            # 存储数据
            turning_points_data[f'epoch_{tp}'] = {
                'pool1_rank': float(pool1_rank_tp),
                'pool2_rank': float(pool2_rank_tp),
                'pool1_mfr': float(pool1_mfr_tp),
                'pool2_mfr': float(pool2_mfr_tp),
                'pool1_funds': float(pool1_funds_tp),
                'pool2_funds': float(pool2_funds_tp),
                'pool1_participation': float(pool1_participation_tp),
                'pool2_participation': float(pool2_participation_tp),
                'pool1_pool_revenue': float(pool1_pool_revenue_tp),
                'pool2_pool_revenue': float(pool2_pool_revenue_tp),
                'pool1_stakeholder_revenue': float(pool1_stakeholder_revenue_tp),
                'pool2_stakeholder_revenue': float(pool2_stakeholder_revenue_tp),
                'rank_diff': float(rank_diff),
                'mfr_diff': float(mfr_diff),
                'funds_diff': float(funds_diff)
            }
    
    # 2. Figure 5(a) - Competition Dynamics 详细分析
    print(f"\n{'='*80}")
    print(f"📈 2. FIGURE 5(a) - COMPETITION DYNAMICS DETAILS")
    print(f"{'='*80}")
    
    # 排名范围
    all_ranks = np.concatenate([pool1['rank'], pool2['rank']])
    print(f"\n【Ranking Range】")
    print(f"  Best (lowest) rank: {int(np.min(all_ranks))}")
    print(f"  Worst (highest) rank: {int(np.max(all_ranks))}")
    print(f"  Total entities competing: ~{int(np.max(all_ranks))}")
    
    # Pool1的ranking cycles
    print(f"\n【{pool1_name} Ranking Cycles】")
    cycles = [
        ('Epoch 0-13', 0, 14),
        ('Epoch 14-50', 14, 51),
        ('Epoch 51-74', 51, 75),
        ('Epoch 75-300', 75, min(epoch_limit, 301))
    ]
    
    for cycle_name, start, end in cycles:
        if end <= len(pool1['rank']):
            avg_rank = np.mean(pool1['rank'][start:end])
            min_rank = np.min(pool1['rank'][start:end])
            max_rank = np.max(pool1['rank'][start:end])
            std_rank = np.std(pool1['rank'][start:end])
            print(f"  {cycle_name}:")
            print(f"    Average rank: {avg_rank:.2f}")
            print(f"    Best rank: {int(min_rank)}")
            print(f"    Worst rank: {int(max_rank)}")
            print(f"    Std dev: {std_rank:.2f}")
    
    # MFR变化范围
    print(f"\n【MFR (Management Fee Ratio) Range】")
    print(f"  {pool1_name}:")
    print(f"    Min MFR: {np.min(pool1['mfr']):.2f}%")
    print(f"    Max MFR: {np.max(pool1['mfr']):.2f}%")
    print(f"    Mean MFR: {np.mean(pool1['mfr']):.2f}%")
    print(f"    Std MFR: {np.std(pool1['mfr']):.2f}%")
    print(f"  {pool2_name}:")
    print(f"    Min MFR: {np.min(pool2['mfr']):.2f}%")
    print(f"    Max MFR: {np.max(pool2['mfr']):.2f}%")
    print(f"    Mean MFR: {np.mean(pool2['mfr']):.2f}%")
    print(f"    Std MFR: {np.std(pool2['mfr']):.2f}%")
    
    # 3. Figure 5(b) - Fund Aggregation 详细分析
    print(f"\n{'='*80}")
    print(f"💰 3. FIGURE 5(b) - FUND AGGREGATION DETAILS")
    print(f"{'='*80}")
    
    # Pool1资金变化
    print(f"\n【{pool1_name} Fund Dynamics】")
    pool1_peak_idx = np.argmax(pool1['funds'])
    pool1_low_idx = np.argmin(pool1['funds'])
    print(f"  Peak: {pool1['funds'][pool1_peak_idx]:.2f} ETH at Epoch {pool1_peak_idx}")
    print(f"  Low: {pool1['funds'][pool1_low_idx]:.2f} ETH at Epoch {pool1_low_idx}")
    print(f"  Final: {pool1['funds'][-1]:.2f} ETH at Epoch {len(pool1['funds'])-1}")
    print(f"  Mean: {np.mean(pool1['funds']):.2f} ETH")
    
    print(f"\n【{pool2_name} Fund Dynamics】")
    pool2_peak_idx = np.argmax(pool2['funds'])
    pool2_low_idx = np.argmin(pool2['funds'])
    print(f"  Peak: {pool2['funds'][pool2_peak_idx]:.2f} ETH at Epoch {pool2_peak_idx}")
    print(f"  Low: {pool2['funds'][pool2_low_idx]:.2f} ETH at Epoch {pool2_low_idx}")
    print(f"  Final: {pool2['funds'][-1]:.2f} ETH at Epoch {len(pool2['funds'])-1}")
    print(f"  Mean: {np.mean(pool2['funds']):.2f} ETH")
    
    # 参与率说明
    print(f"\n【Participation Rate Explanation】")
    print(f"  Definition: (Pool stakeholders + 1) / (Total volunteers + 1) × 100%")
    print(f"  Represents: Percentage of stakeholders choosing this pool")
    print(f"  {pool1_name}:")
    print(f"    Max participation: {np.max(pool1['participation']):.2f}%")
    print(f"    Min participation: {np.min(pool1['participation']):.2f}%")
    print(f"    Final participation: {pool1['participation'][-1]:.2f}%")
    print(f"  {pool2_name}:")
    print(f"    Max participation: {np.max(pool2['participation']):.2f}%")
    print(f"    Min participation: {np.min(pool2['participation']):.2f}%")
    print(f"    Final participation: {pool2['participation'][-1]:.2f}%")
    
    # 4. Figure 5(c) - Pool Revenue 详细分析
    print(f"\n{'='*80}")
    print(f"💵 4. FIGURE 5(c) - POOL REVENUE PERFORMANCE")
    print(f"{'='*80}")
    
    print(f"\n【Pool Revenue Ratio Explanation】")
    print(f"  Definition: net_revenue / total_user_funds × 100%")
    print(f"  Represents: Pool operator's profit from management fees")
    
    print(f"\n【{pool1_name} Pool Revenue】")
    print(f"  Mean: {np.mean(pool1['pool_revenue']):.4f}%")
    print(f"  Max: {np.max(pool1['pool_revenue']):.4f}% at Epoch {np.argmax(pool1['pool_revenue'])}")
    print(f"  Min: {np.min(pool1['pool_revenue']):.4f}% at Epoch {np.argmin(pool1['pool_revenue'])}")
    print(f"  Stable phase (75-300) mean: {np.mean(pool1['pool_revenue'][75:]):.4f}%")
    
    print(f"\n【{pool2_name} Pool Revenue】")
    print(f"  Mean: {np.mean(pool2['pool_revenue']):.4f}%")
    print(f"  Max: {np.max(pool2['pool_revenue']):.4f}% at Epoch {np.argmax(pool2['pool_revenue'])}")
    print(f"  Min: {np.min(pool2['pool_revenue']):.4f}% at Epoch {np.argmin(pool2['pool_revenue'])}")
    
    # 5. Figure 5(d) - Stakeholder Revenue 详细分析（最重要！）
    print(f"\n{'='*80}")
    print(f"🌟 5. FIGURE 5(d) - STAKEHOLDER REVENUE COMPARISON (CRITICAL!)")
    print(f"{'='*80}")
    
    print(f"\n【Stakeholder Revenue Ratio Explanation】")
    print(f"  Definition: (b2e_revenue × (1 - tax_rate)) / total_user_funds × 100%")
    print(f"  Represents: Stakeholders' profit per epoch (after pool fees)")
    
    # Pool1 stable phase (epoch 75-300)
    stable_epochs = range(75, min(epoch_limit, 301))
    pool1_stable_stakeholder_revenue = pool1['stakeholder_revenue'][75:]
    pool1_stable_mfr = pool1['mfr'][75:]
    
    print(f"\n【{pool1_name} Stable Phase Analysis (Epoch 75-{epoch_limit-1})】")
    print(f"  Stakeholder Revenue:")
    print(f"    Mean: {np.mean(pool1_stable_stakeholder_revenue):.4f}%")
    print(f"    Median: {np.median(pool1_stable_stakeholder_revenue):.4f}%")
    print(f"    Std: {np.std(pool1_stable_stakeholder_revenue):.4f}%")
    print(f"    Min: {np.min(pool1_stable_stakeholder_revenue):.4f}%")
    print(f"    Max: {np.max(pool1_stable_stakeholder_revenue):.4f}%")
    print(f"    Range: [{np.min(pool1_stable_stakeholder_revenue):.4f}%, {np.max(pool1_stable_stakeholder_revenue):.4f}%]")
    print(f"  Pool MFR (stable phase):")
    print(f"    Mean: {np.mean(pool1_stable_mfr):.2f}%")
    print(f"    Median: {np.median(pool1_stable_mfr):.2f}%")
    
    print(f"\n【{pool2_name} Performance】")
    print(f"  Stakeholder Revenue:")
    print(f"    Mean: {np.mean(pool2['stakeholder_revenue']):.4f}%")
    print(f"    Median: {np.median(pool2['stakeholder_revenue']):.4f}%")
    print(f"    Final (Epoch {epoch_limit-1}): {pool2['stakeholder_revenue'][-1]:.4f}%")
    
    # Baseline comparison (direct participation)
    print(f"\n【Baseline Comparison】")
    print(f"  Note: Small stakeholders (minnows) without LP: ~0% revenue")
    print(f"  (Reference: Figure 3(b) from paper)")
    print(f"  {pool1_name} advantage over baseline: +{np.mean(pool1_stable_stakeholder_revenue):.4f}%")
    
    # 6. Zero-sum dynamics 量化
    print(f"\n{'='*80}")
    print(f"⚖️  6. ZERO-SUM DYNAMICS QUANTIFICATION")
    print(f"{'='*80}")
    
    # 计算竞争指标
    print(f"\n【Stakeholder Migration】")
    for i in [14, 51, 75]:
        if i < epoch_limit:
            pool1_change = pool1['participation'][i] - pool1['participation'][i-1]
            pool2_change = pool2['participation'][i] - pool2['participation'][i-1]
            print(f"  Epoch {i-1} → {i}:")
            print(f"    {pool1_name} participation change: {pool1_change:+.2f}%")
            print(f"    {pool2_name} participation change: {pool2_change:+.2f}%")
            print(f"    Sum (should ≈ 0): {pool1_change + pool2_change:+.2f}%")
    
    print(f"\n【Rank Competition】")
    rank_correlations = []
    for i in range(1, len(pool1['rank'])):
        pool1_rank_change = pool1['rank'][i] - pool1['rank'][i-1]
        pool2_rank_change = pool2['rank'][i] - pool2['rank'][i-1]
        if pool1_rank_change != 0 or pool2_rank_change != 0:
            rank_correlations.append((pool1_rank_change, pool2_rank_change))
    
    if rank_correlations:
        pool1_changes, pool2_changes = zip(*rank_correlations)
        correlation = np.corrcoef(pool1_changes, pool2_changes)[0, 1]
        print(f"  Correlation between Pool1 and Pool2 rank changes: {correlation:.4f}")
        print(f"  (Negative correlation indicates zero-sum competition)")
    
    # 输出Python字典格式的数据（方便直接使用）
    print(f"\n{'='*80}")
    print(f"📋 7. PYTHON DICTIONARY FORMAT FOR PAPER")
    print(f"{'='*80}")
    print(f"\nturning_points = {{")
    for tp_key, tp_data in turning_points_data.items():
        print(f"    '{tp_key}': {{")
        for key, value in tp_data.items():
            if isinstance(value, float):
                print(f"        '{key}': {value:.4f},")
            else:
                print(f"        '{key}': {value},")
        print(f"    }},")
    print(f"}}")

if __name__ == "__main__":
    # ========== 参数设置 ==========
    experiment_name = "trump_20w_300_diff_final_balance2"
    num_epochs = 300
    
    # 文件路径
    results_filename = f"simulation_results_{experiment_name}.json"
    input_folder = "../result/output"
    output_folder_base = "./1007exper5"
    
    # 构建完整路径
    results_path = os.path.join(os.path.dirname(__file__), input_folder, results_filename)
    output_folder = output_folder_base
    
    # 检查输入文件
    if not os.path.exists(results_path):
        print(f"❌ 错误：找不到输入文件 {results_path}")
        print(f"请确保文件存在并检查路径设置")
        sys.exit(1)
    
    # 绘制图表
    print(f"\n{'='*60}")
    print(f"🎨 Figure 5 重构版本 - 竞争动态分析")
    print(f"{'='*60}")
    print(f"📂 输入文件: {results_path}")
    print(f"📁 输出文件夹: {output_folder}")
    print(f"⏱️  Epoch范围: 0-{num_epochs}")
    
    plot_brokerhub_metrics(results_path, output_folder, epoch_limit=num_epochs)
    
    print(f"\n✨ 所有任务完成！")
import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys
from matplotlib.ticker import FuncFormatter, MultipleLocator
import matplotlib
from scipy import stats
from scipy.interpolate import interp1d

def plot_enhanced_pareto_distribution(balance_file, profits, output_folder):
    """
    绘制增强版帕累托图：双Y轴 + 嵌套柱状图 + 连线设计
    """
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)

    # 读取broker余额数据
    with open(balance_file, "r") as f:
      data = f.readlines()
      balances = [float(i.strip())/1e18 for i in data]

    # 计算收益率
    broker_ids = [i for i in range(len(balances))]
    revenue_ratios = []

    # 使用profits[0]作为代表性数据
    for i, broker_profit in enumerate(profits):
      if len(broker_profit) > 0 and broker_profit[0] and len(broker_profit[0]) > 0:
          profit_sum = sum(broker_profit[0])
          profit_avg = profit_sum / len(broker_profit[0]) if len(broker_profit[0]) > 0 else 0
          revenue_ratio = profit_avg / (balances[i] * 1e18) if balances[i] > 0 else 0
          revenue_ratios.append(revenue_ratio * 100)  # 转换为百分比
      else:
          revenue_ratios.append(0)

    # 按照余额从大到小排序
    sorted_indices = np.argsort(balances)[::-1]
    balances_sorted = np.array(balances)[sorted_indices]
    revenue_ratios_sorted = np.array(revenue_ratios)[sorted_indices]

    # 设置样式
    plt.style.use('default')
    plt.rcParams['font.size'] = 14
    plt.rcParams['axes.linewidth'] = 1.5

    # 创建主图和插图
    fig = plt.figure(figsize=(16, 10))

    # 主图
    ax1 = plt.subplot(111)  # 左Y轴 - 投资金额
    ax2 = ax1.twinx()       # 右Y轴 - 收益率

    # 准备数据
    broker_count = len(balances_sorted)
    x_positions = np.arange(broker_count)  # 0, 1, 2, ..., 49

    # 更新配色方案 - 使用更高对比度的颜色
    balance_color = '#2E4A66'    # 深海军蓝 - 投资金额柱子
    revenue_color = '#F39C12'    # 明亮橙色 - 收益率柱子  
    trend_color = '#E67E22'      # 深橙色 - 趋势线

    # 绘制投资金额柱状图（左Y轴）
    bars_balance = ax1.bar(x_positions, balances_sorted, 
                        width=0.8, 
                        color=balance_color,
                        alpha=0.9, 
                        label='Investment balance (ETH)',
                        edgecolor='black', linewidth=0.8)

    # 绘制收益率柱状图（右Y轴，嵌套在投资金额柱子内）
    # 为了创建嵌套效果，我们将收益率柱子画得稍窄一些
    bars_revenue = ax2.bar(x_positions, revenue_ratios_sorted, 
                        width=0.6,  # 比投资金额柱子稍窄
                        color=revenue_color,
                        alpha=0.8, 
                        label='Revenue ratio (%)',
                        edgecolor='black', linewidth=0.5)

    # 绘制收益率连线（右Y轴）- 使用更醒目的颜色
    line_revenue = ax2.plot(x_positions, revenue_ratios_sorted, 
                         color=trend_color,  # 深橙色，与柱子区分但保持协调
                         linewidth=4,  # 加粗线条
                         marker='D', markersize=16,  # 使用菱形marker，更醒目
                         markerfacecolor='white', 
                         markeredgecolor=trend_color, 
                         markeredgewidth=2,
                         label='Revenue Trend Line',
                         markevery = 3,
                         alpha=1.0,  # 完全不透明
                         zorder=5)  # 确保线条在最上层
  
  # 创建插图显示收益率分布（类似正态分布）
  # 在主图右上角创建插图
    ax_inset = fig.add_axes([0.60, 0.55, 0.3, 0.25])  # 右上角位置
  

  
  # 绘制收益率分布直方图和拟合的正态分布曲线
    if len(revenue_ratios_sorted) > 0:
        # 创建直方图
        n_bins = min(15, len(revenue_ratios_sorted) // 3 + 1)
        counts, bins, patches = ax_inset.hist(revenue_ratios_sorted, bins=n_bins, 
                                          density=True, alpha=0.7, 
                                          color='lightblue', edgecolor='navy', 
                                          linewidth=1)
        # 拟合正态分布
        mu = np.mean(revenue_ratios_sorted)
        sigma = np.std(revenue_ratios_sorted)
        # 生成平滑的x值用于绘制正态分布曲线
        x_range = np.linspace(min(revenue_ratios_sorted), max(revenue_ratios_sorted), 100)
        normal_curve = stats.norm.pdf(x_range, mu, sigma)
        # 绘制正态分布拟合曲线
        ax_inset.plot(x_range, normal_curve, color='red', linewidth=3, 
                   label=f'Gaussian fit\n(μ={mu:.1f}, σ={sigma:.1f})')
        # 添加均值线
        ax_inset.axvline(mu, color='red', linestyle='--', linewidth=2, alpha=0.8)
        
        # 添加指向μ的箭头
        mu_density = stats.norm.pdf(mu, mu, sigma)  # 计算μ位置的密度值
        ax_inset.annotate(f'μ = {mu:.1f}%',
                          xy=(mu, mu_density + 0.3),                    # 箭头指向的点
                          xytext=(mu + 1.5, mu_density),   # 文字位置
                          fontsize=30,
                          color='red',
                          arrowprops=dict(arrowstyle='->', 
                                        color='red', 
                                        lw=2,
                                        alpha=0.9))
                      
                      
                      
    
    # 插图设置
    ax_inset.set_xlabel('Revenue ratio (%)', fontsize=30, color='black')
    ax_inset.set_ylabel('PDF', fontsize=30, color='black')
    # ax_inset.set_title('PDF of the Revenue', fontsize=30, fontweight='bold', color='black', pad=20)
    ax_inset.grid(True, alpha=0.3)
    ax_inset.set_ylim(0, 1.5)
    
    ax_inset.set_yticks([0, 0.5, 1.0, 1.5])  # 指定具体的刻度值
    ax_inset.tick_params(axis='both', labelsize=30, colors='black')
    ax_inset.legend(fontsize=30, bbox_to_anchor=(1.05, 1), loc='upper right', handlelength = 1, handletextpad=0.4)

    # 计算并标注关键统计数据
    top_20_count = max(1, int(broker_count * 0.2))
    top_20_revenue_share = sum(revenue_ratios_sorted[:top_20_count]) / sum(revenue_ratios_sorted) * 100 if sum(revenue_ratios_sorted) > 0 else 0

    # 添加统计信息文本框
    textstr = f'Matthew Effect Analysis:\n• Top 20% brokers: {top_20_count} brokers\n• Earn {top_20_revenue_share:.1f}% of total revenue\n• Gini coefficient: {calculate_gini(revenue_ratios_sorted):.3f}\n• Balance-Revenue correlation: {np.corrcoef(balances_sorted, revenue_ratios_sorted)[0,1]:.3f}'

    props = dict(boxstyle='round', facecolor='lightgray', alpha=0.8, pad=1.0)

    # 文本框位置调整说明：
    # ax1.text(x, y, text, transform=ax1.transAxes, ...)
    # x: 0-1，水平位置（0=最左，1=最右）
    # y: 0-1，垂直位置（0=最底，1=最顶）
    # 当前位置 (0.02, 0.98) 表示左上角
    # 如果要移动到右上角：(0.98, 0.98), ha='right'
    # 如果要移动到左下角：(0.02, 0.02), va='bottom'
    # 如果要移动到右下角：(0.98, 0.02), ha='right', va='bottom'
    # 如果要移动到中间：(0.5, 0.5), ha='center', va='center'
    # ax1.text(0.02, 0.98, textstr, transform=ax1.transAxes, fontsize=12,
          # verticalalignment='top', horizontalalignment='left', 
          # bbox=props, fontweight='bold', color='black')

    # 设置主图轴标签和格式 - 保持您调整的字体大小
    ax1.set_xlabel('Broker ID (Sorted by balance)', fontsize=30, fontweight='bold', color='black')
    ax1.set_ylabel('Investment balance (ETH)', fontsize=30, fontweight='bold', color=balance_color)
    ax2.set_ylabel('Revenue ratio (%)', fontsize=30, fontweight='bold', color=revenue_color)

    # 设置x轴刻度
# 设置x轴刻度
    ax1.set_xlim(-0.5, broker_count - 0.5)

    # 确保显示包含50的刻度
    tick_step = max(1, broker_count // 10)  # 计算步长
    tick_labels = [1] + list(range(5, broker_count + 1, 5))  # [1, 5, 10, 15, ..., 50]
    tick_positions = [label - 1 for label in tick_labels]  # 转换为实际的数组位置 [0, 4, 9, 14, ..., 49]


    ax1.set_xticks(tick_positions)
    ax1.set_xticklabels([str(label) for label in tick_labels], color='black')

    # 设置左Y轴（投资金额）- 保持您调整的字体大小
    max_balance = max(balances_sorted) if len(balances_sorted) > 0 else 1
    ax1.set_ylim(0, 5.3)
    ax1.tick_params(axis='y', colors=balance_color, labelsize=30)
    ax1.tick_params(axis='x', colors='black', labelsize=30)

    # 设置右Y轴（收益率）- 保持您调整的字体大小
    max_revenue = max(revenue_ratios_sorted) if len(revenue_ratios_sorted) > 0 else 1
    ax2.set_ylim(0, max_revenue * 1.1)
    ax2.tick_params(axis='y', colors=revenue_color, labelsize=30)

    # 添加网格（只在主轴添加）
    ax1.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)

    # 创建综合图例 - 保持您调整的字体大小
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D

    legend_elements = [
      Patch(facecolor=balance_color, alpha=0.9, edgecolor='black', label='Investment balance (ETH)'),
      Patch(facecolor=revenue_color, alpha=0.8, edgecolor='black', label='Revenue ratio (%)')
      # Line2D([0], [0], color=trend_color, lw=4, marker='D', markersize=15, 
             # markerfacecolor='white', markeredgecolor=trend_color, label='Revenue Trend Line')
    ]

    # 放置图例 - 保持您调整的字体大小
    ax1.legend(handles=legend_elements, bbox_to_anchor=(0.29, 1), loc='upper center', fontsize=30,
           framealpha=0.8,      # 图例背景透明度 (0=完全透明, 1=完全不透明)
           facecolor='white',   # 背景颜色
           edgecolor='black',  # 边框颜色)
           handletextpad=0.4)   

    # 将标题放在图片下方
    # fig.text(0.5, 0.02, '(a) Investment Balance vs Revenue Performance: Dual-Axis Analysis with Trend Lines', 
           # ha='center', fontsize=18, fontweight='bold', color='black')

    # 调整布局
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.1)

    # 保存图形
    output_path = os.path.join(output_folder, 'dual_axis_trend_distribution.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')

    # 保存PDF版本
    output_path_pdf = os.path.join(output_folder, 'dual_axis_trend_distribution.pdf')
    plt.savefig(output_path_pdf, bbox_inches='tight', facecolor='white')

    plt.close()

    # 打印统计信息
    print(f"双Y轴趋势分布图已生成！")
    print(f"- 总broker数: {broker_count}")
    print(f"- 前20% broker数量: {top_20_count}")
    print(f"- 前20%的broker收益占比: {top_20_revenue_share:.1f}%")
    print(f"- 余额范围: {min(balances_sorted):.2f} - {max(balances_sorted):.2f} ETH")
    print(f"- 收益率范围: {min(revenue_ratios_sorted):.2f}% - {max(revenue_ratios_sorted):.2f}%")
    print(f"- 基尼系数: {calculate_gini(revenue_ratios_sorted):.3f}")
    print(f"- 收益率均值: {np.mean(revenue_ratios_sorted):.2f}%")
    print(f"- 收益率标准差: {np.std(revenue_ratios_sorted):.2f}%")

def calculate_gini(values):
    """计算基尼系数"""
    if len(values) == 0:
      return 0

    sorted_values = np.sort(values)
    n = len(values)
    cumsum = np.cumsum(sorted_values)

    if cumsum[-1] == 0:
      return 0

    return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n

if __name__ == "__main__":
    # =========================== 参数设置 ===========================
    # 文件路径参数
    balance_file = r"D:\博一\BrokerHub\code\BrokerHub\BrokerHub_exp\config\motivation_brokerBalance.txt"
    output_folder = "./motivation/"

    # 导入数据处理模块
    import motivation_sta

    # 数据路径设置
    basePath = r"D:\博一\BrokerHub\motivation\B2E\data"
    resultPath = "BalanceAdd_5wCtx"

    try:
        # 获取profits数据
        percentage, balance_broker_ctx, profits = motivation_sta.get_percentage(basePath, resultPath, 1)

        # 绘制双Y轴趋势图
        print(f"开始绘制双Y轴趋势分布图...")
        print(f"输入文件: {balance_file}")
        print(f"输出文件夹: {output_folder}")

        plot_enhanced_pareto_distribution(balance_file, profits, output_folder)
      
    except Exception as e:
        print(f"错误: {e}")
        print("请确保 motivation_sta 模块和数据文件路径正确")
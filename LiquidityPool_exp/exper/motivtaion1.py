import matplotlib.pyplot as plt
import numpy as np
import os
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec

def plot_enhanced_broker_distribution(balance_file, profits, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    
    # 读取数据
    with open(balance_file, "r") as f:
        data = f.readlines()
        balances = [float(i.strip())/1e18 for i in data]
    
    # 计算收益率
    revenue_ratios = []
    for i, broker_profit in enumerate(profits):
        if len(broker_profit) > 0 and broker_profit[0] and len(broker_profit[0]) > 0:
            profit_sum = sum(broker_profit[0])
            profit_avg = profit_sum / len(broker_profit[0])
            revenue_ratio = profit_avg / (balances[i] * 1e18) if balances[i] > 0 else 0
            revenue_ratios.append(revenue_ratio * 100)
        else:
            revenue_ratios.append(0)
    
    # 排序
    sorted_indices = np.argsort(balances)[::-1]
    balances = np.array(balances)[sorted_indices]
    revenue_ratios = np.array(revenue_ratios)[sorted_indices]
    
    # 颜色方案
    blue_colors = ['#1f4e79', '#2e75b6', '#5b9bd5', '#9dc3e6']
    orange_colors = ['#c5504b', '#e07a5f', '#f4a261', '#f9ca9b']
    
    n_bars = len(balances)
    balance_colors = []
    revenue_colors = []
    
    for i in range(n_bars):
        if i < len(blue_colors):
            balance_colors.append(blue_colors[i])
        else:
            alpha = 0.3 + 0.7 * (n_bars - i) / n_bars
            base_color = mcolors.to_rgb(blue_colors[-1])
            balance_colors.append((*base_color, alpha))
        
        if i < len(orange_colors):
            revenue_colors.append(orange_colors[i])
        else:
            alpha = 0.3 + 0.7 * (n_bars - i) / n_bars
            base_color = mcolors.to_rgb(orange_colors[-1])
            revenue_colors.append((*base_color, alpha))
    
    # 创建图形 - 使用原始论文比例
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 左图：Balance分布
    x_positions = np.arange(len(balances)) + 0.5
    ax1.bar(x_positions, balances, width=0.8, color=balance_colors)
    
    # 标注前5个数值
    for i in range(min(5, len(balances))):
        ax1.annotate(f'{balances[i]:.1f}', 
                     xy=(x_positions[i], balances[i]), 
                     xytext=(0, 5), textcoords='offset points',
                     ha='center', va='bottom', fontsize=25, fontweight='bold',
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    ax1.set_xlabel('BrokerID', fontsize=25)
    ax1.set_ylabel('Balance of broker (ETH)', fontsize=25)
    ax1.set_title('(a) Distribution of broker balances', fontsize=25, pad=20, y=-0.35)
    ax1.set_xlim(-0.5, 50)
    ax1.set_ylim(0, 6)
    ax1.tick_params(axis='both', labelsize=25)
    ax1.xaxis.set_major_locator(plt.MultipleLocator(10))
    ax1.yaxis.set_major_locator(plt.MultipleLocator(1))
    ax1.ticklabel_format(style='plain', axis='y', useOffset=False)
    
    # 右图：Revenue Ratio分布
    revenue_positions = np.arange(len(revenue_ratios)) + 0.5
    ax2.bar(revenue_positions, revenue_ratios, width=0.8, color=revenue_colors)
    
    # Matthew效应文本框
    ax2.text(8, 8.5, 
             "Revenue ratio exhibits \nhyperbolic decay pattern \ncorrelating with initial \nbalance distribution,\nindicating a Matthew effect",
             fontsize=25, ha='left', va='top',
             bbox=dict(facecolor='white', alpha=0.7, edgecolor='red', 
                       boxstyle='round,pad=0.5', linewidth=2))
    
    # 箭头
    ax2.annotate('', 
                 xy=(5, 2),
                 xytext=(8, 3.5),
                 arrowprops=dict(facecolor='red', shrink=0.05, width=2, headwidth=8))
    
    # 帕累托分布小图
    ax_inset = fig.add_axes([0.58, 0.15, 0.25, 0.25])
    sorted_revenue = np.sort(revenue_ratios)[::-1]
    cumulative_revenue = np.cumsum(sorted_revenue) / np.sum(sorted_revenue) * 100
    broker_percentile = np.arange(1, len(sorted_revenue) + 1) / len(sorted_revenue) * 100
    
    ax_inset.plot(broker_percentile, cumulative_revenue, 'b-', linewidth=3)
    ax_inset.plot([0, 100], [0, 100], 'k--', alpha=0.5, linewidth=2)
    ax_inset.fill_between(broker_percentile, cumulative_revenue, broker_percentile, 
                         alpha=0.3, color='red')
    
    ax_inset.set_xlabel('Broker Percentile (%)', fontsize=12, fontweight='bold')
    ax_inset.set_ylabel('Cumulative Revenue (%)', fontsize=12, fontweight='bold')
    ax_inset.set_title('Pareto Distribution\n(80-20 Rule)', fontsize=14, fontweight='bold')
    ax_inset.tick_params(labelsize=10)
    ax_inset.grid(True, alpha=0.3)
    
    ax2.set_xlabel('BrokerID', fontsize=25)
    ax2.set_ylabel('Revenue Ratio (%)', fontsize=25)
    ax2.set_title('(b) Revenue Distribution from Broker2Earn', fontsize=25, pad=20, y=-0.35)
    ax2.set_xlim(-0.5, len(revenue_ratios))
    ax2.set_ylim(0, 10)
    ax2.xaxis.set_major_locator(plt.MultipleLocator(10))
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0f}%'))
    ax2.tick_params(axis='both', labelsize=25)
    
    plt.tight_layout()
    
    # 保存
    output_path_pdf = os.path.join(output_folder, 'enhanced_broker_distribution.pdf')
    plt.savefig(output_path_pdf, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    balance_file = r"D:\博一\BrokerHub\code\BrokerHub\BrokerHub_exp\config\motivation_brokerBalance.txt"
    output_folder = "./motivation/"
    
    import motivation_sta
    basePath = r"D:\博一\BrokerHub\motivation\B2E\data"
    resultPath = "BalanceAdd_5wCtx"
    percentage, balance_broker_ctx, profits = motivation_sta.get_percentage(basePath, resultPath, 1)
    
    plot_enhanced_broker_distribution(balance_file, profits, output_folder)
import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys
from matplotlib.ticker import FuncFormatter, MultipleLocator
import matplotlib

def plot_broker_distribution(balance_file, profits, output_folder):
    """
    绘制broker余额分布和收益率，按照第二份代码的数据处理方式和第一份代码的绘图风格
    """
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    # 读取broker余额数据
    with open(balance_file, "r") as f:
        data = f.readlines()
        balances = [float(i.strip())/1e18 for i in data]
    
    # 计算收益率（基于第二份代码中的profit_sort函数）
    broker_ids = [i for i in range(len(balances))]
    revenue_ratios = []
    
    # 使用profits[0]作为代表性数据（第二份代码中的per_index=0）
    for i, broker_profit in enumerate(profits):
        # 参考第二份代码中的计算方式
        if len(broker_profit) > 0 and broker_profit[0] and len(broker_profit[0]) > 0:
            # 计算平均收益并除以余额得到收益率
            profit_sum = sum(broker_profit[0])
            profit_avg = profit_sum / len(broker_profit[0]) if len(broker_profit[0]) > 0 else 0
            revenue_ratio = profit_avg / (balances[i] * 1e18) if balances[i] > 0 else 0
            revenue_ratios.append(revenue_ratio * 100)  # 转换为百分比
        else:
            revenue_ratios.append(0)
    
    # 按照余额从大到小排序
    sorted_indices = np.argsort(balances)[::-1]
    balances = np.array(balances)[sorted_indices]
    revenue_ratios = np.array(revenue_ratios)[sorted_indices]
    broker_ids = np.array(broker_ids)[sorted_indices]
    
    # 定义颜色 - 全部是普通broker
    colors = ['steelblue'] * len(balances)  # 所有broker为蓝色
    
    # 创建图形 - 使用第一份代码的风格
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 左图：Balance分布
    x_positions = np.arange(len(balances))
    x_positions = x_positions + 0.5  # 所有柱子都向右移动0.5个单位

    bars1 = ax1.bar(x_positions, balances, width=0.8, color=colors)
    ax1.set_xlabel('BrokerID', fontsize=25)
    ax1.set_ylabel('Balance of broker (ETH)', fontsize=25)
    ax1.set_title('(a) Distribution of broker balances', fontsize=25, pad=20, y=-0.35)  # 子标题放在图片下面
    ax1.set_xlim(-0.5, 50)
    ax1.set_ylim(0, 6)
    
    # 设置刻度
    ax1.xaxis.set_major_locator(plt.MultipleLocator(10))
    ax1.yaxis.set_major_locator(plt.MultipleLocator(1))
    ax1.tick_params(axis='both', labelsize=25)
    
    # 移除科学记数法的偏移文本
    ax1.ticklabel_format(style='plain', axis='y', useOffset=False)
    # 或者如果想使用自定义的格式，可以使用以下方式
    # def custom_formatter(x, pos):
    #     return f'{x:.0f}'
    
    # 右图：Revenue Ratio分布
    revenue_positions = np.arange(len(revenue_ratios))
    revenue_positions = revenue_positions + 0.5  # 所有柱子都向右移动0.5个单位
    bars2 = ax2.bar(revenue_positions, revenue_ratios, width=0.8, color=colors)
    
    # 添加说明文字到右图并用红框框起来
    text_x = 17  # 横向位置，调整为图表宽度的60%处
    text_y = 8  # 纵向位置，接近但不超过y轴上限

    # 添加框起来的文字
    # text_box = ax2.text(text_x, text_y, 
                       # "Revenue ratio exhibits \nhyperbolic decay pattern \ncorrelating with initial \nbalance distribution,\nindicating a Matthew effect",
                       # fontsize=25, ha='left', va='top',
                       # bbox=dict(facecolor='white', alpha=0.7, edgecolor='red', 
                                 # boxstyle='round,pad=0.5', linewidth=2))
    text_box = ax2.text(text_x, text_y, 
                       "Matthew Effect: \nTop 20% brokers \nearn 80% revenue",
                       fontsize=25, ha='left', va='top',
                       bbox=dict(facecolor='lightgray', alpha=0.7, edgecolor='black', 
                                 boxstyle='round,pad=0.5', linewidth=2))
             
    # 添加箭头指向特定位置
    # 假设我们想指向收益率曲线的某个特定点，比如第10个broker
    arrow_target_x = 5  # 目标broker ID位置
    arrow_target_y = 2  # 该broker的收益率

    # 计算箭头的起点（从文本框的左下角）
    arrow_start_x = text_x  # 稍微向左偏移
    arrow_start_y = text_y - 3.3  # 从文本框底部偏移

    # 添加箭头
    ax2.annotate('', 
                 xy=(arrow_target_x, arrow_target_y),  # 箭头指向的位置
                 xytext=(arrow_start_x, arrow_start_y),  # 箭头起始位置
                 arrowprops=dict(facecolor='red', shrink=0.05, width=2, headwidth=8),
                 )
    
    
    ax2.set_xlabel('BrokerID', fontsize=25)
    ax2.set_ylabel('Revenue Ratio (%)', fontsize=25)
    ax2.set_title('(b) Revenue Distribution from Broker2Earn', fontsize=25, pad=20, y=-0.35)  # 子标题放在图片下面
    ax2.set_xlim(-0.5, len(revenue_ratios))
    ax2.set_ylim(0, 10)
    
    # 设置刻度和格式
    ax2.xaxis.set_major_locator(plt.MultipleLocator(10))
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0f}%'))
    ax2.tick_params(axis='both', labelsize=25)
    
    # 创建图例（只有普通Broker）
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='steelblue', label='Brokers')
    ]
    
    # 在右图添加图例
    # ax2.legend(handles=legend_elements, loc='upper right', fontsize=12)
    
    # 调整子图间距
    plt.tight_layout()
    
    # 保存图形
    output_path = os.path.join(output_folder, 'broker_distribution.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    # 保存PDF版本
    output_path_pdf = os.path.join(output_folder, 'broker_distribution.pdf')
    plt.savefig(output_path_pdf, bbox_inches='tight')
    
    plt.close()
    
    print(f"分布图已生成！")
    print(f"- 总broker数: {len(balances)}")
    print(f"- 最大余额: {max(balances):.2f} ETH")
    print(f"- 最小余额: {min(balances):.2f} ETH")
    print(f"- 最大收益率: {max(revenue_ratios):.2f}%")
    print(f"- 最小收益率: {min(revenue_ratios):.2f}%")

if __name__ == "__main__":
    # =========================== 参数设置 ===========================
    # 文件路径参数
    balance_file = r"D:\博一\BrokerHub\code\BrokerHub\BrokerHub_exp\config\motivation_brokerBalance.txt"  # broker余额文件
    output_folder = "./motivation/"  # 输出文件夹
    
    # 导入第二份代码中的数据
    import sys
    
    # 添加第二份代码所在的目录到系统路径
    # 假设第二份代码在同一目录或已知目录中
    # sys.path.append("路径到第二份代码所在目录")
    
    import motivation_sta
    
    # 按照第二份代码的方式获取profits数据
    basePath = r"D:\博一\BrokerHub\motivation\B2E\data"
    resultPath = "BalanceAdd_5wCtx"
    
    # 调用motivation_sta模块获取profits数据
    percentage, balance_broker_ctx, profits = motivation_sta.get_percentage(basePath, resultPath, 1)
    
    # 绘制图表
    print(f"开始绘制分布图...")
    print(f"输入文件: {balance_file}")
    print(f"输出文件夹: {output_folder}")
    
    plot_broker_distribution(balance_file, profits, output_folder)
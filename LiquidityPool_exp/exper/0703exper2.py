import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys

def categorize_accounts_by_balance(accounts_data):
    """根据原始余额将账户分类到不同层级"""
    categories = {
        '≥300 ETH': [],
        '10-100 ETH': [],
        '1-10 ETH': [],
        '<0.1 ETH': []
    }
    
    for account_id, balance_eth in accounts_data.items():
        if balance_eth >= 300:  # 修正：原来是100，现在是300
            categories['≥300 ETH'].append(account_id)
        elif 10 <= balance_eth < 100:  # 保持不变
            categories['10-100 ETH'].append(account_id)
        elif 1 <= balance_eth < 10:   # 保持不变
            categories['1-10 ETH'].append(account_id)
        else:  # balance < 0.1，删除了0.1-1 ETH这个层级
            categories['<0.1 ETH'].append(account_id)
    
    return categories

def calculate_meaningful_participation_rate(account_ids, accounts_with_revenue):
    """计算有意义参与率 - 基于是否有收益"""
    if not account_ids:
        return 0.0
    
    meaningful_count = sum(1 for account_id in account_ids if account_id in accounts_with_revenue)
    return (meaningful_count / len(account_ids)) * 100

def analyze_no_aggregation_participation(base_path, num_epochs):
    """分析无聚合场景的参与率"""
    all_accounts_balance = {}  # account_id -> original_balance_eth
    all_accounts_with_revenue = set()  # 有收益的账户集合
    
    for item_id in range(num_epochs):
        item_path = os.path.join(base_path, f"item{item_id}", "b2e_test_results.json")
        
        if os.path.exists(item_path):
            with open(item_path, 'r') as f:
                data = json.load(f)[0]
            
            # 收集原始余额（排除BrokerHub）
            for participant_id, balance_wei in data['original_funds'].items():
                if participant_id not in ['BrokerHub1', 'BrokerHub2']:
                    balance_eth = float(balance_wei) / 1e18
                    all_accounts_balance[participant_id] = balance_eth
            
            # 收集有收益的账户（排除BrokerHub）
            for participant_id, earning in data['earnings'].items():
                if participant_id not in ['BrokerHub1', 'BrokerHub2'] and float(earning) > 0:
                    all_accounts_with_revenue.add(participant_id)
    
    # 按层级分类（基于原始余额）
    categories = categorize_accounts_by_balance(all_accounts_balance)
    
    # 计算各层级参与率
    participation_rates = {}
    for tier, account_ids in categories.items():
        participation_rates[tier] = calculate_meaningful_participation_rate(
            account_ids, all_accounts_with_revenue)
    
    print(f"无聚合场景统计:")
    print(f"总账户数: {len(all_accounts_balance)}")
    print(f"有收益账户数: {len(all_accounts_with_revenue)}")
    for tier, account_ids in categories.items():
        revenue_count = sum(1 for aid in account_ids if aid in all_accounts_with_revenue)
        print(f"{tier}: {len(account_ids)}个账户, {revenue_count}个有收益")
    
    return participation_rates

def analyze_aggregation_participation(results_path):
    """分析聚合场景的参与率"""
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    all_accounts_balance = {}  # account_id -> original_balance_eth
    all_accounts_with_revenue = set()  # 有收益的账户集合
    
    for state in results:
        # 收集所有volunteers的原始余额
        for volunteer in state['volunteers']:
            account_id = volunteer['id']
            balance_eth = float(volunteer['balance']) / 1e18
            all_accounts_balance[account_id] = balance_eth
            
            # 检查是否有收益（total_earnings > 0）
            if float(volunteer['total_earnings']) > 0:
                all_accounts_with_revenue.add(account_id)
        
        # 检查加入Hub的用户（他们通过Hub获得收益）
        for bh in state['brokerhubs']:
            if float(bh['b2e_revenue']) > 0:  # Hub有收益
                for user_id in bh['users']:
                    all_accounts_with_revenue.add(user_id)
    
    # 按层级分类（基于原始余额）
    categories = categorize_accounts_by_balance(all_accounts_balance)
    
    # 计算各层级参与率
    participation_rates = {}
    for tier, account_ids in categories.items():
        participation_rates[tier] = calculate_meaningful_participation_rate(
            account_ids, all_accounts_with_revenue)
    
    print(f"聚合场景统计:")
    print(f"总账户数: {len(all_accounts_balance)}")
    print(f"有收益账户数: {len(all_accounts_with_revenue)}")
    for tier, account_ids in categories.items():
        revenue_count = sum(1 for aid in account_ids if aid in all_accounts_with_revenue)
        print(f"{tier}: {len(account_ids)}个账户, {revenue_count}个有收益")
    
    return participation_rates

def plot_meaningful_participation_comparison(aggregation_path, no_aggregation_path, 
                                           num_epochs, output_folder, figure_name):
    """绘制有意义参与率对比图"""
    
    # 检查文件是否存在
    if not os.path.exists(aggregation_path):
        print(f"错误：找不到聚合数据文件 {aggregation_path}")
        return
    
    if not os.path.exists(no_aggregation_path):
        print(f"错误：找不到无聚合数据文件夹 {no_aggregation_path}")
        return
    
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    # 分析数据
    print("正在分析无聚合场景...")
    no_agg_rates = analyze_no_aggregation_participation(no_aggregation_path, num_epochs)
    
    print("\n正在分析聚合场景...")
    with_agg_rates = analyze_aggregation_participation(aggregation_path)
    
    # 更新层级定义
    tiers = ['≥300 ETH', '10-100 ETH', '1-10 ETH', '<0.1 ETH']
    
    # 打印分析结果
    print(f"\n各层级参与率对比:")
    for tier in tiers:
        no_agg_rate = no_agg_rates.get(tier, 0)
        with_agg_rate = with_agg_rates.get(tier, 0)
        print(f"{tier}: 无聚合 {no_agg_rate:.1f}%, 有聚合 {with_agg_rate:.1f}%")
    
    # 绘图
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 数据准备
    x = np.arange(len(tiers))
    width = 0.35
    
    no_agg_values = [no_agg_rates.get(tier, 0) for tier in tiers]
    with_agg_values = [with_agg_rates.get(tier, 0) for tier in tiers]
    
    # 绘制柱状图
    bars1 = ax.bar(x - width/2, no_agg_values, width, label='No Aggregation', 
                   color='lightgray', alpha=0.8)
    bars2 = ax.bar(x + width/2, with_agg_values, width, label='With AggreHub', 
                   color='green', alpha=0.8)
    
    # 添加数值标签
    def add_value_labels(bars, values):
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{value:.1f}%',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    add_value_labels(bars1, no_agg_values)
    add_value_labels(bars2, with_agg_values)
    
    # 设置标题和标签
    ax.set_title('Meaningful Participation Rate by Account Tier', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Account Tier', fontsize=14)
    ax.set_ylabel('Meaningful Participation Rate (%)', fontsize=14)
    
    # 设置X轴标签
    ax.set_xticks(x)
    ax.set_xticklabels(tiers, fontsize=12)
    
    # 设置Y轴范围
    ax.set_ylim(0, 105)
    
    # 添加图例
    ax.legend(fontsize=12, loc='upper left')
    
    # 添加网格
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_axisbelow(True)
    
    # 添加说明文字
    explanation = ("Meaningful participation defined as having positive revenue from Broker2Earn protocol.\n"
                  "AggreHub enables fund aggregation allowing small investors to earn through collective participation.")
    
    # 将说明文字放在图表内部上方
    ax.text(0.02, 0.98, explanation, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle="round,pad=0.4", 
            facecolor="lightyellow", alpha=0.8))
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图像
    output_path = os.path.join(output_folder, f"{figure_name}.pdf")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"\n图表已保存至: {output_path}")
    
    return {
        'no_aggregation_rates': no_agg_rates,
        'with_aggregation_rates': with_agg_rates
    }

def main():
    """主函数 - 配置所有输入参数"""
    
    # =========================== 参数配置区域 ===========================
    
    # 实验基本参数
    aggregation_experiment_name = "trump_20w_300_diff_final_balance2"  # 聚合实验名称
    no_aggregation_experiment_name = "without_trump_20w_300_diff_final_balance"  # 无聚合实验名称
    num_epochs = 300  # epoch数量 (0-299)
    
    # 文件路径配置
    # 聚合AggreHub数据路径
    aggregation_data_file = f"simulation_results_{aggregation_experiment_name}.json"
    aggregation_base_folder = "../result/output"  # 相对于当前脚本的路径
    
    # 无聚合Direct B2E数据路径
    no_aggregation_base_folder = "../src/data/processed_data/witouthub"  # 相对于当前脚本的路径
    
    # 输出配置
    output_folder = "./0703exper2"  # 输出文件夹
    figure_name = "meaningful_participation_comparison"  # 图片文件名（不含扩展名）
    
    # =================================================================
    
    # 构建完整路径
    aggregation_path = os.path.join(aggregation_base_folder, aggregation_data_file)
    no_aggregation_path = os.path.join(no_aggregation_base_folder, no_aggregation_experiment_name)
    
    # 打印配置信息
    print("=" * 70)
    print("有意义参与率分析（基于实际收益）")
    print("=" * 70)
    print(f"聚合实验名称: {aggregation_experiment_name}")
    print(f"无聚合实验名称: {no_aggregation_experiment_name}")
    print(f"Epoch数量: {num_epochs}")
    print(f"聚合数据路径: {aggregation_path}")
    print(f"无聚合数据路径: {no_aggregation_path}")
    print(f"输出文件夹: {output_folder}")
    print(f"图片名称: {figure_name}")
    print("层级划分: ≥300 ETH, 10-100 ETH, 1-10 ETH, <0.1 ETH")
    print("=" * 70)
    
    # 执行分析
    try:
        results = plot_meaningful_participation_comparison(
            aggregation_path=aggregation_path,
            no_aggregation_path=no_aggregation_path,
            num_epochs=num_epochs,
            output_folder=output_folder,
            figure_name=figure_name
        )
        
        print("\n" + "=" * 70)
        print("分析完成")
        print("=" * 70)
        
    except Exception as e:
        print(f"分析过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
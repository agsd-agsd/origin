import random
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def generate_medium_balanced_distribution():
    """
    生成中等均衡配置 (α≈0.6-0.7)
    1000个用户，1000 ETH总量
    财富分布相对均衡，但仍有层次差异
    """
    print("=== 生成中等均衡配置 (α≈0.6-0.7) ===")
    
    # 定义中等均衡的层级结构
    # 避免极端集中，但保持一定层次性
    tiers = [
        # 格式: (账户数量, 总额ETH, 最小金额ETH, 最大金额ETH)
        (50, 200, 3, 5),      # 高级用户: 占20%资金
        (150, 250, 1.2, 2.8), # 中高级用户: 占25%资金  
        (300, 300, 0.8, 1.5), # 中级用户: 占30%资金
        (500, 250, 0.3, 0.8)  # 普通用户: 占25%资金
    ]
    
    all_balances = []
    
    for tier_idx, (num_accounts, total_eth, min_eth, max_eth) in enumerate(tiers):
        print(f"处理第{tier_idx+1}层: {num_accounts}个账户, 总额{total_eth} ETH")
        
        # 为每个层级生成余额
        tier_balances = []
        
        if num_accounts == 1:
            tier_balances = [total_eth]
        else:
            # 使用轻微的指数分布，避免过度集中
            decay_factor = 0.8 + tier_idx * 0.1  # 递增的衰减因子
            
            # 生成权重
            weights = []
            for i in range(num_accounts):
                weight = np.exp(-decay_factor * i / num_accounts)
                weights.append(weight)
            
            # 归一化权重
            weights = np.array(weights)
            weights = weights / weights.sum()
            
            # 分配金额
            tier_balances = weights * total_eth
            
            # 确保在指定范围内
            tier_balances = np.clip(tier_balances, min_eth, max_eth)
            
            # 重新调整总额
            current_sum = np.sum(tier_balances)
            tier_balances = tier_balances * (total_eth / current_sum)
        
        # 添加轻微随机扰动使分布更自然
        for i in range(len(tier_balances)):
            perturbation = random.uniform(-0.02, 0.02)
            tier_balances[i] = tier_balances[i] * (1 + perturbation)
            tier_balances[i] = max(tier_balances[i], 0.1)  # 确保最小值
        
        # 最终调整以确保总额正确
        current_sum = sum(tier_balances)
        tier_balances = [b * (total_eth / current_sum) for b in tier_balances]
        
        all_balances.extend(tier_balances)
    
    # 转换为Wei单位并排序
    all_balances_wei = [int(eth * 1e18) for eth in all_balances]
    all_balances_wei.sort(reverse=True)
    
    # 验证和统计
    total_accounts = len(all_balances_wei)
    total_eth_actual = sum(all_balances_wei) / 1e18
    max_balance = max(all_balances_wei) / 1e18
    min_balance = min(all_balances_wei) / 1e18
    
    print(f"\n中等均衡配置统计:")
    print(f"总账户数: {total_accounts}")
    print(f"总ETH: {total_eth_actual:.2f}")
    print(f"最大余额: {max_balance:.4f} ETH")
    print(f"最小余额: {min_balance:.4f} ETH")
    print(f"最大/最小比例: {max_balance/min_balance:.2f}")
    
    # 计算基尼系数估算α值
    alpha_estimate = calculate_asymmetry_parameter(all_balances_wei)
    print(f"估算α值: {alpha_estimate:.3f}")
    
    return all_balances_wei

def generate_fully_balanced_distribution():
    """
    生成完全均衡配置 (α≈0.9)
    1000个用户，1000 ETH总量
    每个用户持有1 ETH，完全均等分布
    """
    print("\n=== 生成完全均衡配置 (α≈0.9) ===")
    
    # 1000个用户，每人1 ETH
    num_accounts = 1000
    eth_per_account = 1.0
    
    all_balances_wei = []
    
    for i in range(num_accounts):
        # 添加极小的随机扰动以避免完全相同（模拟真实情况）
        perturbation = random.uniform(-0.001, 0.001)
        balance_eth = eth_per_account + perturbation
        balance_wei = int(balance_eth * 1e18)
        all_balances_wei.append(balance_wei)
    
    # 排序
    all_balances_wei.sort(reverse=True)
    
    # 确保总额正确
    current_total = sum(all_balances_wei)
    target_total = int(1000 * 1e18)  # 1000 ETH in Wei
    
    # 按比例调整
    if current_total != target_total:
        adjustment_factor = target_total / current_total
        all_balances_wei = [int(balance * adjustment_factor) for balance in all_balances_wei]
    
    # 验证和统计
    total_accounts = len(all_balances_wei)
    total_eth_actual = sum(all_balances_wei) / 1e18
    max_balance = max(all_balances_wei) / 1e18
    min_balance = min(all_balances_wei) / 1e18
    
    print(f"\n完全均衡配置统计:")
    print(f"总账户数: {total_accounts}")
    print(f"总ETH: {total_eth_actual:.2f}")
    print(f"最大余额: {max_balance:.6f} ETH")
    print(f"最小余额: {min_balance:.6f} ETH")
    print(f"最大/最小比例: {max_balance/min_balance:.6f}")
    
    # 计算α值
    alpha_estimate = calculate_asymmetry_parameter(all_balances_wei)
    print(f"估算α值: {alpha_estimate:.3f}")
    
    return all_balances_wei

def calculate_asymmetry_parameter(balances_wei):
    """
    计算不对称参数α的估算值
    α接近1表示高度对称，α接近0表示高度不对称
    """
    balances_eth = [b / 1e18 for b in balances_wei]
    n = len(balances_eth)
    
    if n <= 1:
        return 1.0
    
    # 计算标准差与均值的比值（变异系数）
    mean_balance = np.mean(balances_eth)
    std_balance = np.std(balances_eth)
    
    if mean_balance == 0:
        return 1.0
    
    cv = std_balance / mean_balance  # 变异系数
    
    # 将变异系数映射到α值 (0,1)
    # 变异系数越小，α值越大（越对称）
    alpha = 1 / (1 + cv * 2)  # 简单的映射函数
    
    return min(max(alpha, 0.0), 1.0)

def save_balances_to_file(balances, filename):
    """保存余额到文件"""
    with open(filename, 'w') as f:
        for balance in balances:
            f.write(f"{balance}\n")
    print(f"余额已保存到: {filename}")

def plot_distribution_comparison(medium_balances, full_balances):
    """绘制两种分布的对比图"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 转换为ETH单位
    medium_eth = [b / 1e18 for b in medium_balances]
    full_eth = [b / 1e18 for b in full_balances]
    
    # 中等均衡分布
    ax1.hist(medium_eth, bins=50, alpha=0.7, color='blue', edgecolor='black')
    ax1.set_title('中等均衡配置 (α≈0.6-0.7)', fontsize=14)
    ax1.set_xlabel('账户余额 (ETH)')
    ax1.set_ylabel('账户数量')
    ax1.grid(True, alpha=0.3)
    
    # 完全均衡分布
    ax2.hist(full_eth, bins=50, alpha=0.7, color='green', edgecolor='black')
    ax2.set_title('完全均衡配置 (α≈0.9)', fontsize=14)
    ax2.set_xlabel('账户余额 (ETH)')
    ax2.set_ylabel('账户数量')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('balance_distribution_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()
    print("分布对比图已保存到: balance_distribution_comparison.png")

def analyze_distribution_stats(balances, config_name):
    """分析分布统计信息"""
    balances_eth = [b / 1e18 for b in balances]
    balances_eth.sort(reverse=True)
    
    n = len(balances_eth)
    total = sum(balances_eth)
    
    print(f"\n=== {config_name} 详细统计 ===")
    print(f"总账户数: {n}")
    print(f"总ETH: {total:.2f}")
    
    # 分位数分析
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    print("\n分位数分析:")
    for p in percentiles:
        idx = int(n * p / 100) - 1
        idx = max(0, min(idx, n-1))
        print(f"前{p}%账户最小余额: {balances_eth[idx]:.4f} ETH")
    
    # 财富集中度分析
    top_1_percent = int(n * 0.01)
    top_5_percent = int(n * 0.05)
    top_10_percent = int(n * 0.10)
    
    wealth_top_1 = sum(balances_eth[:top_1_percent])
    wealth_top_5 = sum(balances_eth[:top_5_percent])
    wealth_top_10 = sum(balances_eth[:top_10_percent])
    
    print(f"\n财富集中度:")
    print(f"前1%账户持有: {wealth_top_1:.2f} ETH ({wealth_top_1/total*100:.1f}%)")
    print(f"前5%账户持有: {wealth_top_5:.2f} ETH ({wealth_top_5/total*100:.1f}%)")
    print(f"前10%账户持有: {wealth_top_10:.2f} ETH ({wealth_top_10/total*100:.1f}%)")

def main():
    """主函数"""
    random.seed(42)  # 确保结果可重现
    np.random.seed(42)
        
    # 生成中等均衡配置
    medium_balances = generate_medium_balanced_distribution()
    save_balances_to_file(medium_balances, 'brokerBalance_medium_balanced.txt')
    analyze_distribution_stats(medium_balances, "中等均衡配置")
    
    print("\n" + "="*60 + "\n")
    
    # 生成完全均衡配置  
    full_balances = generate_fully_balanced_distribution()
    save_balances_to_file(full_balances, 'brokerBalance_fully_balanced.txt')
    analyze_distribution_stats(full_balances, "完全均衡配置")
    
    # 绘制对比图
    plot_distribution_comparison(medium_balances, full_balances)
    
    print("\n" + "="*60)
    print("配置生成完成！")
    print("文件输出:")
    print("- brokerBalance_medium_balanced.txt (中等均衡配置)")
    print("- brokerBalance_fully_balanced.txt (完全均衡配置)")
    print("- balance_distribution_comparison.png (分布对比图)")

if __name__ == "__main__":
    main()
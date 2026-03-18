import random
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def generate_simple_linear_tiers(tiers):
    """
    使用简单线性分布生成账户余额，保持层级结构，
    严格确保账户余额在每个层级的最小值和最大值范围内
    
    :param tiers: 层级定义列表，格式为 [(账户数量, 总额, 最小金额, 最大金额), ...]
    :return: 排序后的余额列表（Wei为单位）
    """
    all_balances = []
    all_eth_balances = []  # 临时存储ETH单位的余额
    
    # 处理每个层级
    for tier_idx, (num_accounts, total_eth, min_eth, max_eth) in enumerate(tiers):
        if num_accounts <= 0 or total_eth <= 0:
            continue
        
        # 如果只有一个账户，直接赋值为总额（但确保在范围内）
        if num_accounts == 1:
            account_value = min(max(total_eth, min_eth), max_eth)
            all_eth_balances.append(account_value)
            continue
        
        # 首先检查总额和账户数量是否合理
        if total_eth > num_accounts * max_eth:
            print(f"警告: 层级{tier_idx+1}的总额过高! 无法在范围限制内分配。调整为最大可能值。")
            total_eth = num_accounts * max_eth
        elif total_eth < num_accounts * min_eth:
            print(f"警告: 层级{tier_idx+1}的总额过低! 无法在范围限制内分配。调整为最小可能值。")
            total_eth = num_accounts * min_eth
        
        # 创建初始线性序列
        step = (max_eth - min_eth) / (num_accounts - 1)
        values = [max_eth - i * step for i in range(num_accounts)]
        
        
        # 创建指数分布的序列（差异更大）
        if(total_eth >= 20):
            x = np.linspace(0, 1, num_accounts)
            skew_factor = 3  # 控制分布倾斜程度，值越大差异越大
            raw_values = np.exp(skew_factor * (1 - x)) - 1
            normalized = (raw_values - min(raw_values)) / (max(raw_values) - min(raw_values))
            values = min_eth + normalized * (max_eth - min_eth)
            values = sorted(values, reverse=True)  # 降序排列
        
        # 添加小随机扰动使分布更自然，但确保值仍在范围内
        # for i in range(len(values)):
            # 添加±0.5%的随机扰动（减小扰动以降低超出范围的可能性）
            # max_perturbation = min(values[i] - min_eth, max_eth - values[i], values[i] * 0.005)
            # perturbation = random.uniform(-max_perturbation, max_perturbation)
            # values[i] += perturbation
        
        # 确保所有值都严格在范围内
        values = [min(max(v, min_eth), max_eth) for v in values]
        
        # 重新排序（降序）
        values.sort(reverse=True)
        
        # 迭代调整以满足总和要求，同时保持范围约束
        current_sum = sum(values)
        target_sum = total_eth
        max_iterations = 50
        iteration = 0
        
        while abs(current_sum - target_sum) > 0.00001 and iteration < max_iterations:
            # 计算需要的调整比例
            adjustment_needed = target_sum - current_sum
            
            if adjustment_needed > 0:  # 需要增加值
                # 找出可以增加的账户（未达到max_eth的账户）
                adjustable_indices = [i for i in range(len(values)) if values[i] < max_eth]
                if not adjustable_indices:
                    print(f"警告: 层级{tier_idx+1}的所有账户都已达到最大值，无法进一步调整")
                    break
                
                # 按比例增加这些账户的值
                total_adjustable = sum(max_eth - values[i] for i in adjustable_indices)
                for i in adjustable_indices:
                    max_adjustment = max_eth - values[i]
                    values[i] += (max_adjustment / total_adjustable) * adjustment_needed
                    values[i] = min(values[i], max_eth)  # 确保不超过最大值
            
            else:  # 需要减少值
                # 找出可以减少的账户（未达到min_eth的账户）
                adjustable_indices = [i for i in range(len(values)) if values[i] > min_eth]
                if not adjustable_indices:
                    print(f"警告: 层级{tier_idx+1}的所有账户都已达到最小值，无法进一步调整")
                    break
                
                # 按比例减少这些账户的值
                total_adjustable = sum(values[i] - min_eth for i in adjustable_indices)
                for i in adjustable_indices:
                    max_adjustment = values[i] - min_eth
                    values[i] += (max_adjustment / total_adjustable) * adjustment_needed
                    values[i] = max(values[i], min_eth)  # 确保不低于最小值
            
            # 更新当前总和
            current_sum = sum(values)
            iteration += 1
        
        # 最终检查
        if iteration >= max_iterations:
            print(f"警告: 层级{tier_idx+1}未能精确达到目标总额，但仍在尝试范围内")
        
        print(f"层级{tier_idx+1}: 目标总额={total_eth:.4f}, 实际总额={sum(values):.4f}, "
              f"偏差={((sum(values)/total_eth)-1)*100:.4f}%, 迭代次数={iteration}")
        
        # 添加到总余额列表
        all_eth_balances.extend(values)
    
    # 最终全局排序
    all_eth_balances = sorted(all_eth_balances, reverse=True)
    
    # 转换为Wei
    all_balances = [int(eth * 1e18) for eth in all_eth_balances]
    
    # 打印统计信息
    print(f"生成完成: 总账户数 {len(all_balances)}")
    print(f"最大账户: {all_eth_balances[0]:.4f} ETH")
    print(f"最小账户: {all_eth_balances[-1]:.6f} ETH")
    print(f"总量: {sum(all_eth_balances):.4f} ETH")
    
    # 检查相邻账户的差异
    print("\n相邻账户差异分析:")
    for i in range(0, min(10, len(all_eth_balances)-1)):
        ratio = all_eth_balances[i] / all_eth_balances[i+1]
        diff = all_eth_balances[i] - all_eth_balances[i+1]
        print(f"账户{i}-{i+1}: {all_eth_balances[i]:.6f} vs {all_eth_balances[i+1]:.6f}, 差异: {diff:.6f} ETH, 比例: {ratio:.4f}")
    
    # 验证每个层次的数据
    verify_tier_data(tiers, all_eth_balances)
    
    return all_balances

def verify_tier_data(tiers, balances):
    """验证生成的数据是否符合每个层次的要求"""
    current_idx = 0
    
    print("\n各层级数据验证:")
    for tier_idx, (num, total, min_val, max_val) in enumerate(tiers):
        if num <= 0:
            continue
            
        # 提取此层级的数据
        tier_balances = balances[current_idx:current_idx+num]
        tier_sum = sum(tier_balances)
        tier_min = min(tier_balances)
        tier_max = max(tier_balances)
        
        print(f"层级 {tier_idx+1}:")
        print(f"  账户数: {len(tier_balances)}")
        print(f"  总额: {tier_sum:.2f} ETH (预期: {total} ETH, 偏差: {((tier_sum/total)-1)*100:.2f}%)")
        print(f"  范围: {tier_min:.6f} - {tier_max:.6f} ETH (预期: {min_val} - {max_val} ETH)")
        
        # 检查值的多样性
        unique_values = len(set([round(b, 6) for b in tier_balances]))
        print(f"  唯一值数量: {unique_values}/{len(tier_balances)} ({unique_values/len(tier_balances)*100:.1f}%)")
        
        # 检查相邻值的典型差异
        if len(tier_balances) > 1:
            diffs = [tier_balances[i] - tier_balances[i+1] for i in range(len(tier_balances)-1)]
            avg_diff = sum(diffs) / len(diffs)
            min_diff = min(diffs)
            max_diff = max(diffs)
            print(f"  相邻差异: 平均 {avg_diff:.6f}, 最小 {min_diff:.6f}, 最大 {max_diff:.6f}")
        
        print()
        current_idx += num


def plot_distribution(balances, accounts_distribution):
    """
    按照预定义的区间绘制分布图
    :param balances: 所有余额（Wei单位）
    :param accounts_distribution: 账户分布定义 [(num, min_eth, max_eth),...]
    """
    # 转换为ETH单位
    balances_eth = [b / 1e18 for b in balances]
    
    # 创建数据框架
    brackets = []
    addresses = []
    total_values = []  # 每个区间的总价值
    
    for num, min_eth, max_eth in accounts_distribution:
        bracket = f"{min_eth}-{max_eth} ETH"
        brackets.append(bracket)
        # 计算在此区间内的地址数量和总价值
        bracket_balances = [b for b in balances_eth if min_eth <= b < max_eth]
        addresses.append(len(bracket_balances))
        total_values.append(sum(bracket_balances))
        
    data = {
        'bracket': brackets,
        'addresses': addresses,
        'total_value': total_values
    }
    df = pd.DataFrame(data)
    
    # 计算百分比
    total_addresses = sum(df['addresses'])
    total_value = sum(df['total_value'])
    df['percentage'] = (df['addresses'] / total_addresses) * 100
    df['total_value_percentage'] = (df['total_value'] / total_value) * 100
    print(df)
    
    # 设置图表样式
    plt.style.use('default')
    plt.figure(figsize=(12, 8))
    plt.grid(True, alpha=0.3)
    
    # 创建水平条形图
    bars = plt.barh(range(len(df)), df['addresses'], color='#1f77b4')
    
    # 设置坐标轴
    plt.yticks(range(len(df)), df['bracket'])
    plt.xscale('log')
    plt.title('ETH Address Distribution by Balance (Log Scale)', pad=20)
    plt.xlabel('Number of Addresses (Log Scale)')
    plt.ylabel('Balance Bracket')
    
    # 在条形上添加数值标签
    for i, bar in enumerate(bars):
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2,
                f'{df["addresses"].iloc[i]:,} ({df["percentage"].iloc[i]:.2f}% addr, {df["total_value_percentage"].iloc[i]:.2f}% value)',
                va='center', ha='left', fontsize=8)
    
    # 添加汇总统计
    summary_text = f"""
Summary Statistics:
Total Addresses: {total_addresses:,}
Total ETH Value: {total_value:.2f}
Smallest Bracket ({accounts_distribution[-1][1]}-{accounts_distribution[-1][2]} ETH): 
Addresses: {df['addresses'].iloc[-1]:,} ({df['percentage'].iloc[-1]:.2f}%)
Value: {df['total_value'].iloc[-1]:.2f} ETH ({df['total_value_percentage'].iloc[-1]:.2f}%)
Largest Bracket ({accounts_distribution[0][1]}-{accounts_distribution[0][2]} ETH):
Addresses: {df['addresses'].iloc[0]:,} ({df['percentage'].iloc[0]:.2f}%)
Value: {df['total_value'].iloc[0]:.2f} ETH ({df['total_value_percentage'].iloc[0]:.2f}%)
"""
    plt.figtext(0.1, 0.01, summary_text, fontsize=9)
    
    # 调整布局
    plt.subplots_adjust(bottom=0.2)
    
    # 保存图像
    plt.savefig('balance_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 打印数据
    print("\nData ordered by balance brackets (high to low):")
    print(df[['bracket', 'addresses', 'percentage', 'total_value_percentage']])
    
    print("\n已保存分布图到 balance_distribution.png")
    
def generate_win_finall_balances():
    '''
    2025-03-15 : 生成的数值
    
    主要是博弈获胜的数据
    '''
    """生成全部账户余额，使用简单线性分布"""
    random.seed(42)
    
    # 定义500个账户的tier结构（与原代码相同）
    corrected_tiers_500 = [
        # 格式: (账户数量, 总额ETH, 最小金额ETH, 最大金额ETH)
        
        # 超高级账户 (占总资金的45%)
        (2, 700, 300, 600),    # >$100M 级别
        
        # 高级账户 (占总资金的28%)
        (12, 200, 10, 100),     # $10M-$100M 级别
        
        # 中高级账户 (占总资金的12%) - 最低值提高到1 ETH
        (46, 95, 1, 10),      # $1M-$10M 级别
        
        # 下中级账户 (6%) - 最高值降低到0.05 ETH
        (940, 5, 0.001, 0.01), # 避开波动区域
        
    ]
    
    # 使用简单线性生成方法
    all_balances = generate_simple_linear_tiers(corrected_tiers_500)
    
    # 保存到文件
    with open('brokerBalance.txt', 'w') as f:
        for balance in all_balances:
            f.write(f"{balance}\n")
    
    # 打印统计信息
    print("\n=== 账户余额分布统计 ===")
    print(f"总账户数: {len(all_balances)}")
    print(f"\n余额范围：")
    print(f"最大余额: {all_balances[0] / 1e18:.2f} ETH")
    print(f"最小余额: {all_balances[-1] / 1e18:.2f} ETH")
    print(f"\n已将所有余额保存到 brokerBalance.txt")
    
    return all_balances

def generate_game_finall_balances():
    '''
    2025-03-15 : 生成的数值
    
    主要是博弈获胜的数据
    '''
    """生成全部账户余额，使用简单线性分布"""
    random.seed(42)
    
    # 定义500个账户的tier结构（与原代码相同）
    corrected_tiers_500 = [
        # 格式: (账户数量, 总额ETH, 最小金额ETH, 最大金额ETH)
        
        (2, 940, 150, 300),    # >$100M 级别
        
        (8, 21, 20, 100),     # $10M-$100M 级别
        
        (90, 180, 1, 20),      # $1M-$10M 级别
        
        (150, 17, 0.02, 0.05), # 避开波动区域
        
        (250, 22, 0.008, 0.02), 
        
    ]
    
    # 使用简单线性生成方法
    all_balances = generate_simple_linear_tiers(corrected_tiers_500)
    
    # 保存到文件
    with open('brokerBalance.txt', 'w') as f:
        for balance in all_balances:
            f.write(f"{balance}\n")
    
    # 打印统计信息
    print("\n=== 账户余额分布统计 ===")
    print(f"总账户数: {len(all_balances)}")
    print(f"\n余额范围：")
    print(f"最大余额: {all_balances[0] / 1e18:.2f} ETH")
    print(f"最小余额: {all_balances[-1] / 1e18:.2f} ETH")
    print(f"\n已将所有余额保存到 brokerBalance.txt")
    
    return all_balances
# 运行程序
if __name__ == "__main__":
    balances = generate_win_finall_balances()
    # balances = generate_balances()
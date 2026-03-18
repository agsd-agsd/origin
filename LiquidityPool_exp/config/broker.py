import random
import matplotlib.pyplot as plt

# 1e17    1e20
def generate_wealth_distribution(num_users=20, min_amount=100000000000000000, max_amount=10000000000000000000):
    random.seed(42)
    
    scale = (max_amount - min_amount) // 5
    amounts = [int(min_amount + random.expovariate(1/scale)) for _ in range(num_users)]
    
    # 确保所有金额在指定范围内
    amounts = [max(min_amount, min(amount, max_amount)) for amount in amounts]
    
    # 确保没有重复的金额
    while len(set(amounts)) < num_users:
        duplicates = [item for item in amounts if amounts.count(item) > 1]
        for d in duplicates:
            idx = amounts.index(d)
            amounts[idx] += random.randint(1, 1000000000000000)
            amounts[idx] = min(amounts[idx], max_amount)
    
    # 按金额从大到小排序
    amounts.sort(reverse=True)
    
    return amounts

# 生成数据
wealth_data = generate_wealth_distribution(num_users=20)

# 打印生成的数据
print("生成的财富分布数据 (从大到小排序):")
for i, amount in enumerate(wealth_data, 1):
    print(f"用户 {i}: {amount:}")

# 将数据写入文件
with open("brokerBalance.txt", "w") as f:
    wealth_data[0] = sum(wealth_data[1:]) * 2
    for amount in wealth_data:
        f.write(f"{amount:d}\n")
        
print("\n数据已写入 brokerBalance.txt 文件")

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 绘制条形图
plt.figure(figsize=(12, 6))
plt.bar(range(len(wealth_data)), wealth_data)
plt.title('财富分布图 (从大到小排序)')
plt.xlabel('用户排名')
plt.ylabel('金额')
plt.ticklabel_format(style='plain', axis='y')
plt.xticks(range(0, len(wealth_data), 5), range(1, len(wealth_data)+1, 5))
plt.show()

# 绘制对数刻度的条形图
plt.figure(figsize=(12, 6))
plt.bar(range(len(wealth_data)), wealth_data)
plt.yscale('log')
plt.title('brokerBalance(从大到小排序，对数刻度)')
plt.xlabel('用户排名')
plt.ylabel('金额 (对数刻度)')
plt.xticks(range(0, len(wealth_data), 5), range(1, len(wealth_data)+1, 5))
plt.show()

# 计算统计信息
print(f"\n最大金额: {max(wealth_data)}")
print(f"最小金额: {min(wealth_data)}")
print(f"平均金额: {sum(wealth_data) / len(wealth_data):.2f}")
print(f"中位数金额: {sorted(wealth_data)[len(wealth_data)//2]}")
print(f"不同金额的数量: {len(set(wealth_data))}")
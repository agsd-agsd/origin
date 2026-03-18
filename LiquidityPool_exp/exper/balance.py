import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys

# 设置matplotlib后端和字体
plt.rcParams['font.size'] = 10
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'

def plot_balance_distribution_horizontal(results_path, output_folder):
    """
    绘制epoch 0的账户余额分布情况 - 水平条形图版本
    """
    try:
        # 创建输出文件夹
        os.makedirs(output_folder, exist_ok=True)
        print(f"输出文件夹已创建: {output_folder}")
        
        # 加载JSON数据
        print("正在加载JSON数据...")
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        # 获取epoch 0的数据
        epoch_0_data = results[0]
        print(f"已加载 epoch 0 数据")
        
        # 提取所有账户余额
        balances_wei = []
        
        # 收集volunteers的余额
        volunteers_count = len(epoch_0_data['volunteers'])
        print(f"发现 {volunteers_count} 个 volunteers")
        
        for volunteer in epoch_0_data['volunteers']:
            balance_wei = float(volunteer['balance'])
            balances_wei.append(balance_wei)
        
        # 收集brokerhubs的余额
        # brokerhubs_count = len(epoch_0_data['brokerhubs'])
        # print(f"发现 {brokerhubs_count} 个 brokerhubs")
        
        # for brokerhub in epoch_0_data['brokerhubs']:
            # balance_wei = float(brokerhub['current_funds'])
            # balances_wei.append(balance_wei)
        
        # 转换为ETH单位
        balances_eth = [balance / 1e18 for balance in balances_wei]
        print(f"总账户数: {len(balances_eth)}")
        print(f"余额范围: {min(balances_eth):.4f} - {max(balances_eth):.4f} ETH")
        
        # 选项2的分层统计
        tiers = [
            ("≥300 ETH", [b for b in balances_eth if b >= 100]),
            ("10-100 ETH", [b for b in balances_eth if 10 <= b < 100]),
            ("1-10 ETH", [b for b in balances_eth if 1 <= b < 10]),
            ("Small (0.1-1 ETH)", [b for b in balances_eth if 0.1 <= b < 1]),
            ("<0.1 ETH", [b for b in balances_eth if b < 0.1])
        ]
        
        # 计算统计数据
        account_counts = []
        tier_names = []
        total_values = []
        
        total_accounts = len(balances_eth)
        total_value = sum(balances_eth)
        
        print("\n分层统计:")
        for tier_name, accounts in tiers:
            count = len(accounts)
            value = sum(accounts)
            
            account_counts.append(count)
            tier_names.append(tier_name)
            total_values.append(value)
            
            print(f"{tier_name}: {count} 账户, {value:.2f} ETH")
        
        # 过滤掉计数为0的层级
        filtered_data = [(name, count, value, (count/total_accounts)*100) 
                        for name, count, value in zip(tier_names, account_counts, total_values) 
                        if count > 0]
        
        if not filtered_data:
            print("警告: 没有找到有效的账户数据")
            return None
        
        # 重新组织数据
        tier_names_filtered = [item[0] for item in filtered_data]
        account_counts_filtered = [item[1] for item in filtered_data]
        total_values_filtered = [item[2] for item in filtered_data]
        account_percentages_filtered = [item[3] for item in filtered_data]
        
        print(f"\n有效分层数: {len(filtered_data)}")
        print("\n开始绘图...")
        
        # 创建图形
        fig = plt.figure(figsize=(10, 4))
        ax = fig.add_subplot(111)
        
        # Y轴位置 (从上到下)
        y_positions = list(range(len(tier_names_filtered)))
        
        # ② 绘制水平条形图 - 修改柱子间隙
        # height参数控制柱子的高度（间接控制间隙）
        # height越小，柱子越细，间隙越大
        # height取值范围通常是0.1到1.0
        # bars = ax.barh(y_positions, account_counts_filtered, color='#1f77b4', alpha=0.8, 
        bars = ax.barh(y_positions, account_counts_filtered, color='#4C92C4', 
                       edgecolor='black', linewidth=0.2, 
                       height=0.6)  # ② 修改这里：0.6是默认值，减小数值增大间隙，增大数值减小间隙
        
        print("条形图已绘制")
        
        # 设置坐标轴
        max_count = max(account_counts_filtered)
        min_count = min([c for c in account_counts_filtered if c > 0], default=1)
        
        # 如果数据范围适合，使用对数刻度
        if max_count > min_count * 10 and max_count > 10:
            ax.set_xscale('log')
            ax.set_xlim(max(0.5, min_count * 0.5), max_count * 3)
            ax.set_xlabel('Number of Accounts (Log Scale)', fontsize=12, fontweight='bold')
        else:
            ax.set_xlim(0, max_count * 1.2)
            ax.set_xlabel('Number of Accounts', fontsize=12, fontweight='bold')
        
        # 设置Y轴
        ax.set_yticks(y_positions)
        ax.set_yticklabels(tier_names_filtered, fontsize=11)
        
        # 反转Y轴（让Large在顶部）
        ax.invert_yaxis()
        
        # 启用网格
        ax.grid(True, alpha=0.3, axis='x')
        ax.set_axisbelow(True)
        
        print("坐标轴已设置")
        
        # 在每个条形右侧添加标签 - 优化长标签位置
        for i, (count, percentage, value) in enumerate(zip(account_counts_filtered, 
                                                           account_percentages_filtered, 
                                                           total_values_filtered)):
            # 格式化ETH数量显示
            if value >= 1000:
                eth_str = f"{value/1000:.0f}K ETH"
            elif value >= 1:
                eth_str = f"{value:.0f} ETH"
            else:
                eth_str = f"{value:.2f} ETH"
            
            label_text = f"{count} accounts ({eth_str})"
            
            # 特殊处理最长的条形（通常是Micro账户）
            # if count > min(account_counts_filtered):  # 如果是最长的条形
            if count == max(account_counts_filtered):  # 如果是最长的条形
                # 将标签放在条形内部右侧
                label_x = count * 0.09  # 放在条形的70%位置
                text_color = 'black'   # 使用白色文字
                fontweight = 'bold'
            else:
                # 其他标签放在条形外部
                if ax.get_xscale() == 'log':
                    label_x = count * 1.15
                else:
                    label_x = count + max_count * 0.02
                text_color = 'black'
                fontweight = 'bold'
            
            ax.text(label_x, i, label_text, 
                    va='center', ha='left', fontsize=12,
                    fontweight=fontweight, color=text_color,
                    clip_on=True)
        
        print("标签已添加")
        
        # ① 设置主标题 - 修改图片上方标题
        ax.set_title('Account Balance Distribution in AggreHub DeFi Protocol',  # ① 修改这里：更改主标题文字
                     fontsize=16, fontweight='bold', pad=20)
        
        # ① 添加副标题 - 修改图片上方副标题  
        # ax.text(0.5, 1.05, 'Distribution highlights the participation barrier for small investors',  # ① 修改这里：更改副标题文字
                # transform=ax.transAxes, ha='center', fontsize=12, 
                # style='italic', color='gray')
        
        print("标题已设置")
        
        # 计算关键统计数据
        # 找到小额投资者(≤1 ETH)
        small_indices = [i for i, name in enumerate(tier_names) if '0.1-1 ETH' in name or '<0.1 ETH' in name]
        small_accounts = sum(account_counts[i] for i in small_indices)
        small_value = sum(total_values[i] for i in small_indices)
        
        small_percentage = (small_accounts / total_accounts) * 100 if total_accounts > 0 else 0
        small_value_percentage = (small_value / total_value) * 100 if total_value > 0 else 0
        
        # 创建关键统计信息
        # key_stats = [
            # f"Total: {total_accounts} accounts, {total_value:.0f} ETH",
            # f"Small investors (≤1 ETH): {small_accounts} accounts ({small_percentage:.1f}%)",
            # f"Small investors hold: {small_value_percentage:.1f}% of total value"
        # ]
        # f"Overview: {total_accounts} accounts managing {total_value:.0f} ETH",
        # f"Small investors (≤1 ETH): {small_accounts} participants ({small_percentage:.1f}%)",
        # f"Small investor share: {small_value_percentage:.1f}% of system value",
        # f"Average account balance: {total_value/total_accounts:.2f} ETH"

        # ③ 添加统计信息框 - 修改文本框位置
        # stats_text = "\n".join(key_stats)
        # ax.text(0.38, 0.79,  # ③ 修改这里：第一个数字控制左右位置(0-1)，第二个数字控制上下位置(0-1)
                # stats_text, 
                # transform=ax.transAxes, 
                # fontsize=13, 
                # va='top',    # ③ 修改这里：'top'=文本框顶部对齐, 'bottom'=底部对齐, 'center'=中心对齐
                # ha='left',   # ③ 修改这里：'left'=文本框左对齐, 'right'=右对齐, 'center'=中心对齐
                # bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", 
                         # edgecolor="orange", alpha=0.9, linewidth=1))
        
        print("统计信息已添加")
        
        # 调整X轴和Y轴刻度文字大小
        ax.tick_params(axis='x', labelsize=14)  # X轴刻度文字大小
        ax.tick_params(axis='y', labelsize=14)  # Y轴刻度文字大小
        
        # 调整布局
        plt.subplots_adjust(left=0.25, right=0.75, top=0.88, bottom=0.12)
        plt.tight_layout()

        # 保存图形
        output_path = os.path.join(output_folder, 'account_balance_distribution1.png')
        print(f"正在保存图片到: {output_path}")
        
        plt.savefig(output_path, dpi=200, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        
        # 也保存PDF版本
        output_path_pdf = os.path.join(output_folder, 'account_balance_distribution1.pdf')
        plt.savefig(output_path_pdf, dpi=200, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        
        plt.close()
        
        print("图片保存成功!")
        
        # 打印详细统计信息
        print("\n=== 最终统计结果 ===")
        print(f"总账户数: {total_accounts}")
        print(f"总价值: {total_value:.2f} ETH")
        
        if total_accounts > 0:
            print(f"平均余额: {total_value/total_accounts:.4f} ETH")
            print(f"中位数余额: {np.median(balances_eth):.4f} ETH")
        
        print("\n各层级分布:")
        for name, count, value in zip(tier_names, account_counts, total_values):
            percentage = (count / total_accounts) * 100 if total_accounts > 0 else 0
            value_percentage = (value / total_value) * 100 if total_value > 0 else 0
            print(f"{name}: {count} 账户 ({percentage:.1f}%), {value:.2f} ETH ({value_percentage:.1f}%)")
        
        print(f"\n图表已保存到:")
        print(f"PNG: {output_path}")
        print(f"PDF: {output_path_pdf}")
        
        return {
            'tier_names': tier_names,
            'account_counts': account_counts,
            'total_accounts': total_accounts,
            'total_value': total_value,
            'balances_eth': balances_eth
        }
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # =========================== 参数设置 ===========================
    experiment_name = "trump_20w_300_diff_final_balance2"
    
    results_filename = f"simulation_results_{experiment_name}.json"
    input_folder = "../result/output"
    output_folder_base = "./balance"
    
    # =================================================================
    
    # 构建完整路径
    results_path = os.path.join(os.path.dirname(__file__), input_folder, results_filename)
    output_folder = output_folder_base
    
    # 检查输入文件是否存在
    if not os.path.exists(results_path):
        print(f"错误：找不到输入文件 {results_path}")
        print(f"请确保文件存在并检查路径设置")
        sys.exit(1)
    
    print(f"开始分析 Epoch 0 的账户余额分布...")
    print(f"输入文件: {results_path}")
    print(f"输出文件夹: {output_folder}")
    
    balance_stats = plot_balance_distribution_horizontal(results_path, output_folder)
    
    if balance_stats is None:
        print("绘图失败，请检查错误信息")
    else:
        print("绘图完成!")
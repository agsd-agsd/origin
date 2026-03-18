import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys
from matplotlib.ticker import MultipleLocator
import glob
import random

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_experiment_data(base_path, experiment_pattern, num_files=None):
    """
    加载实验数据
    """
    experiment_files = []
    
    if num_files is None:
        # 对于3hubs, 4hubs, 5hubs, 10hubs的情况
        # 查找所有匹配的文件
        pattern = f"simulation_results_{experiment_pattern}*.json"
        files = glob.glob(os.path.join(base_path, pattern))
        experiment_files = sorted(files)
    else:
        # 对于2hubs的情况，有特定的命名规则
        for i in range(1, num_files + 1):
            filename = f"simulation_results_{experiment_pattern}{i}.json"
            filepath = os.path.join(base_path, filename)
            if os.path.exists(filepath):
                experiment_files.append(filepath)
    
    data_list = []
    for filepath in experiment_files:
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                data_list.append(data)
        except Exception as e:
            print(f"⚠️ 加载文件 {filepath} 时出错: {e}")
    
    return data_list

def calculate_total_revenue(data_list):
    """
    修正版：使用 revenue_rate * balance 计算volunteer的epoch收益
    """
    experiment_revenues = []
    
    for data in data_list:
        total_experiment_revenue = 0
        
        for epoch_data in data:
            # Hub的收益
            epoch_hub_revenue = sum(float(hub['revenue']) for hub in epoch_data['brokerhubs'])
            
            # Volunteer的收益：revenue_rate * balance
            epoch_volunteer_revenue = 0
            for volunteer in epoch_data['volunteers']:
                revenue_rate = float(volunteer['revenue_rate'])
                balance = float(volunteer['balance'])
                volunteer_epoch_revenue = revenue_rate * balance
                epoch_volunteer_revenue += volunteer_epoch_revenue
            
            # 该epoch总收益
            epoch_total_revenue = epoch_hub_revenue + epoch_volunteer_revenue
            total_experiment_revenue += epoch_total_revenue
        
        # 转换为ETH
        experiment_revenue_eth = total_experiment_revenue / 1e18
        experiment_revenues.append(experiment_revenue_eth)
    
    return experiment_revenues

def load_without_hub_data(base_path):
    """
    加载No Hub数据
    """
    total_experiment_revenue = 0
    valid_epochs = 0
    
    # 查找所有item文件夹
    for epoch in range(300):
        item_folder = os.path.join(base_path, f"item{epoch}")
        result_file = os.path.join(item_folder, "b2e_test_results.json")
        
        if os.path.exists(result_file):
            try:
                with open(result_file, 'r') as f:
                    data = json.load(f)
                    
                # 计算该epoch所有参与者的总收益
                epoch_earnings = data[0]['earnings']
                epoch_total = sum(epoch_earnings.values())
                total_experiment_revenue += epoch_total
                valid_epochs += 1
                
            except Exception as e:
                print(f"⚠️ 加载文件 {result_file} 时出错: {e}")
    
    if valid_epochs > 0:
        return total_experiment_revenue / 1e18
    else:
        return None

def plot_welfare_comparison_with_bars(ax, all_hub_data_by_config, social_optimum_revenue, no_hub_revenues_by_config):
    """绘制福利比较 - 柱状图+误差棒版本"""
    
    # 三种配置的设置
    config_colors = {'severe': 'g', 'medium': 'tab:blue', 'fully': 'darkorange'}
    config_names = {'severe': 'Whale-dominated', 'medium': 'Mixed participant', 'fully': 'Equal distribution'}
    
    categories = []
    means_severe = []
    means_medium = []
    means_fully = []
    errors_severe = []
    errors_medium = []
    errors_fully = []
    
    # 1. Social Optimum (通用基准线)
    if social_optimum_revenue is not None:
        ax.axhline(y=social_optimum_revenue, color='red', linestyle=':', linewidth=6, alpha=1, label='Social optimum (W*)')
    
    # 2. 收集No Hub数据
    categories.append('0')
    
    # No Hub只有单个值，没有误差棒
    for config_key in ['severe', 'medium', 'fully']:
        if config_key in no_hub_revenues_by_config and no_hub_revenues_by_config[config_key] is not None:
            revenue = no_hub_revenues_by_config[config_key]
            if config_key == 'severe':
                means_severe.append(revenue)
                errors_severe.append(0)
            elif config_key == 'medium':
                means_medium.append(revenue)
                errors_medium.append(0)
            elif config_key == 'fully':
                means_fully.append(revenue)
                errors_fully.append(0)
        else:
            # 如果没有数据，填入NaN
            if config_key == 'severe':
                means_severe.append(np.nan)
                errors_severe.append(0)
            elif config_key == 'medium':
                means_medium.append(np.nan)
                errors_medium.append(0)
            elif config_key == 'fully':
                means_fully.append(np.nan)
                errors_fully.append(0)
    
    # 3. 收集Hub数据
    for num_hubs in sorted(all_hub_data_by_config.keys()):
        if num_hubs == 0:
            continue
            
        categories.append(f'{num_hubs}')
        
        print(f"\n=== 处理 {num_hubs} Hubs 柱状图数据 ===")
        
        # 为三种配置收集数据
        for config_key in ['severe', 'medium', 'fully']:
            if (config_key in all_hub_data_by_config[num_hubs] and 
                all_hub_data_by_config[num_hubs][config_key]):
                
                revenues = calculate_total_revenue(all_hub_data_by_config[num_hubs][config_key])
                if revenues:
                    mean_revenue = np.mean(revenues)
                    std_revenue = np.std(revenues) if len(revenues) > 1 else 0
                    
                    print(f"  ✅ {config_key}: 均值={mean_revenue:.1f} ETH, 标准差={std_revenue:.1f}, 样本数={len(revenues)}")
                    
                    if config_key == 'severe':
                        means_severe.append(mean_revenue)
                        errors_severe.append(std_revenue)
                    elif config_key == 'medium':
                        means_medium.append(mean_revenue)
                        errors_medium.append(std_revenue)
                    elif config_key == 'fully':
                        means_fully.append(mean_revenue)
                        errors_fully.append(std_revenue)
                else:
                    print(f"  ❌ {config_key}: 无有效收益数据")
                    if config_key == 'severe':
                        means_severe.append(np.nan)
                        errors_severe.append(0)
                    elif config_key == 'medium':
                        means_medium.append(np.nan)
                        errors_medium.append(0)
                    elif config_key == 'fully':
                        means_fully.append(np.nan)
                        errors_fully.append(0)
            else:
                print(f"  ❌ {config_key}: 无原始数据")
                if config_key == 'severe':
                    means_severe.append(np.nan)
                    errors_severe.append(0)
                elif config_key == 'medium':
                    means_medium.append(np.nan)
                    errors_medium.append(0)
                elif config_key == 'fully':
                    means_fully.append(np.nan)
                    errors_fully.append(0)
    
    # 4. 绘制柱状图
    x = np.arange(len(categories))
    width = 0.25  # 柱子宽度
    
    # 绘制三组柱子
    bars1 = ax.bar(x - width, means_severe, width, yerr=errors_severe, 
                   color=config_colors['severe'], alpha=0.8, capsize=5,
                   label=config_names['severe'], edgecolor='black', linewidth=0.5)
    
    bars2 = ax.bar(x, means_medium, width, yerr=errors_medium,
                   color=config_colors['medium'], alpha=0.8, capsize=5,
                   label=config_names['medium'], edgecolor='black', linewidth=0.5)
    
    bars3 = ax.bar(x + width, means_fully, width, yerr=errors_fully,
                   color=config_colors['fully'], alpha=0.8, capsize=5,
                   label=config_names['fully'], edgecolor='black', linewidth=0.5)
    
    # 5. 设置坐标轴
    ax.set_ylabel('Welfare (ETH)', fontsize=25)
    ax.set_xlabel('Number of LiqudityPools', fontsize=25)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=25)
    ax.set_ylim(9300, 9400)
    ax.yaxis.set_major_locator(MultipleLocator(50))
    ax.tick_params(axis='x', labelsize=25)
    ax.tick_params(axis='y', labelsize=25)
    ax.grid(True, linestyle='--', alpha=0.3, color='gray', axis='y')
    
    # 6. 创建图例
    legend_elements = []
    legend_elements.append(plt.Line2D([0], [0], color='red', linestyle=':', linewidth=6, 
                                     label='Social Optimum (W*)'))
    
    for config_key, config_color in config_colors.items():
        legend_elements.append(plt.Rectangle((0, 0), 1, 1, facecolor=config_color, 
                                           edgecolor='black', alpha=0.8,
                                           label=config_names[config_key]))
    
    ax.legend(handles=legend_elements, loc='upper right', fontsize=20, frameon=True,
             bbox_to_anchor=(1.0, 0.6), 
             fancybox=True, framealpha=0.9)

def plot_welfare_violin_analysis(output_folder):
    """
    绘制福利分析图 - 柱状图版本
    """
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    # 数据路径
    base_path = os.path.join(os.path.dirname(__file__), "../result/output")
    
    print("=" * 60)
    print("🚀 开始加载数据...")
    print("=" * 60)
    
    # ========== 加载2hubs数据 ==========
    print("\n📊 加载 2 Hubs 数据...")
    
    # Whale-dominated (severe) - 只用hub2的5个文件
    print("  ├─ Whale-dominated (severe)...")
    data_severe_2hubs = load_experiment_data(base_path, "2hubs_hub2_20w_300_diff_final_balance", 5)
    print(f"     └─ 已加载 {len(data_severe_2hubs)} 个实验")
    
    # Mixed participant (medium)
    print("  ├─ Mixed participant (medium)...")
    data_medium_2hubs = load_experiment_data(base_path, "2hubs_20w_300_diff_final_balance_medium", 5)
    print(f"     └─ 已加载 {len(data_medium_2hubs)} 个实验")
    
    # Equal distribution (fully)
    print("  ├─ Equal distribution (fully)...")
    data_fully_2hubs = load_experiment_data(base_path, "2hubs_20w_300_diff_final_balance_fully", 5)
    print(f"     └─ 已加载 {len(data_fully_2hubs)} 个实验")
    
    # ========== 加载3/4/5/10 hubs数据 ==========
    hub_configs = [3, 4, 5, 10]
    data_by_config = {num_hubs: {'severe': [], 'medium': [], 'fully': []} for num_hubs in hub_configs}
    
    for num_hubs in hub_configs:
        print(f"\n📊 加载 {num_hubs} Hubs 数据...")
        
        # Whale-dominated (severe)
        print(f"  ├─ Whale-dominated (severe)...")
        pattern_severe = f"{num_hubs}hubs_20w_300_diff_final_balance"
        data_severe = load_experiment_data(base_path, pattern_severe)
        data_by_config[num_hubs]['severe'] = data_severe
        print(f"     └─ 已加载 {len(data_severe)} 个实验")
        
        # Mixed participant (medium)
        print(f"  ├─ Mixed participant (medium)...")
        pattern_medium = f"{num_hubs}hubs_20w_300_diff_final_balance_medium"
        data_medium = load_experiment_data(base_path, pattern_medium)
        data_by_config[num_hubs]['medium'] = data_medium
        print(f"     └─ 已加载 {len(data_medium)} 个实验")
        
        # Equal distribution (fully)
        print(f"  ├─ Equal distribution (fully)...")
        pattern_fully = f"{num_hubs}hubs_20w_300_diff_final_balance_fully"
        data_fully = load_experiment_data(base_path, pattern_fully)
        data_by_config[num_hubs]['fully'] = data_fully
        print(f"     └─ 已加载 {len(data_fully)} 个实验")
    
    # ========== 整理所有hub数据 ==========
    all_hub_data_by_config = {
        2: {
            'severe': data_severe_2hubs,
            'medium': data_medium_2hubs,
            'fully': data_fully_2hubs
        }
    }
    
    # 添加其他hub数量的数据
    for num_hubs in hub_configs:
        all_hub_data_by_config[num_hubs] = data_by_config[num_hubs]
    
    # ========== 加载基准数据 ==========
    print("\n" + "=" * 60)
    print("📌 加载基准数据...")
    print("=" * 60)
    
    # Social Optimum
    print("\n🎯 加载 Social Optimum 数据...")
    social_optimum_path = os.path.join(os.path.dirname(__file__), 
                                     "../src/data/processed_data/witouthub/without_one_trump_20w_300_diff_final_balance")
    social_optimum_revenue = load_without_hub_data(social_optimum_path)
    if social_optimum_revenue:
        print(f"   └─ Social Optimum: {social_optimum_revenue:.1f} ETH")
    else:
        print(f"   └─ ⚠️ Social Optimum: 未找到数据")
    
    # No Hub数据
    print("\n📍 加载 No Hub 数据...")
    
    # Whale-dominated
    print("  ├─ Whale-dominated...")
    no_hub_severe_path = os.path.join(os.path.dirname(__file__), 
                                    "../src/data/processed_data/witouthub/without_trump_20w_300_diff_final_balance")
    no_hub_severe_revenue = load_without_hub_data(no_hub_severe_path)
    print(f"     └─ {no_hub_severe_revenue:.1f} ETH" if no_hub_severe_revenue else "     └─ ⚠️ 未找到数据")
    
    # Mixed participant
    print("  ├─ Mixed participant...")
    no_hub_medium_path = os.path.join(os.path.dirname(__file__), 
                                    "../src/data/processed_data/witouthub/without_2hubs_20w_300_diff_final_balance_medium1")
    no_hub_medium_revenue = load_without_hub_data(no_hub_medium_path)
    print(f"     └─ {no_hub_medium_revenue:.1f} ETH" if no_hub_medium_revenue else "     └─ ⚠️ 未找到数据")
    
    # Equal distribution
    print("  ├─ Equal distribution...")
    no_hub_fully_path = os.path.join(os.path.dirname(__file__), 
                                   "../src/data/processed_data/witouthub/without_2hubs_20w_300_diff_final_balance_fully1")
    no_hub_fully_revenue = load_without_hub_data(no_hub_fully_path)
    print(f"     └─ {no_hub_fully_revenue:.1f} ETH" if no_hub_fully_revenue else "     └─ ⚠️ 未找到数据")
    
    no_hub_revenues_by_config = {
        'severe': no_hub_severe_revenue,
        'medium': no_hub_medium_revenue,
        'fully': no_hub_fully_revenue
    }
    
    # ========== 绘制图表 ==========
    print("\n" + "=" * 60)
    print("📈 开始绘制图表...")
    print("=" * 60)
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(7, 5))
    
    # 绘制柱状图
    plot_welfare_comparison_with_bars(ax, all_hub_data_by_config, social_optimum_revenue, no_hub_revenues_by_config)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存PDF和PNG格式
    output_path_pdf = os.path.join(output_folder, 'welfare_bar_analysis.pdf')
    output_path_png = os.path.join(output_folder, 'welfare_bar_analysis.png')
    
    plt.savefig(output_path_pdf, dpi=300, bbox_inches='tight')
    plt.savefig(output_path_png, dpi=300, bbox_inches='tight')
    plt.close()
    
    print("\n" + "=" * 60)
    print("✅ 福利分析柱状图已生成!")
    print("=" * 60)
    print(f"📄 PDF: {output_path_pdf}")
    print(f"🖼️  PNG: {output_path_png}")

if __name__ == "__main__":
    output_folder = "./1007exper4"
    
    print("\n" + "=" * 60)
    print("🎨 福利分析图表生成器")
    print("=" * 60)
    print(f"📁 输出文件夹: {output_folder}")
    
    # 生成图表
    plot_welfare_violin_analysis(output_folder)
    
    print("\n✨ 所有任务完成！")
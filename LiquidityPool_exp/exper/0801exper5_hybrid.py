import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json
import os
import sys
from matplotlib.ticker import MultipleLocator
import glob

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_experiment_data_json(base_path, experiment_pattern, num_files=None):
    """加载JSON格式的实验数据"""
    experiment_files = []
    
    if num_files is None:
        pattern = f"simulation_results_{experiment_pattern}*.json"
        files = glob.glob(os.path.join(base_path, pattern))
        experiment_files = sorted(files)
    else:
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
            print(f"加载JSON文件 {filepath} 时出错: {e}")
    
    return data_list

def load_experiment_data_csv(base_path, experiment_pattern):
    """加载CSV格式的实验数据"""
    experiment_folders = []
    pattern = f"{experiment_pattern}*"
    full_pattern = os.path.join(base_path, pattern)
    
    print(f"    搜索CSV模式: {full_pattern}")
    
    folders = glob.glob(full_pattern)
    experiment_folders = sorted([f for f in folders if os.path.isdir(f)])
    
    print(f"    找到 {len(experiment_folders)} 个CSV实验文件夹: {[os.path.basename(f) for f in experiment_folders]}")
    return experiment_folders

def calculate_total_revenue_json(data_list):
    """计算JSON数据的总福利"""
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

def calculate_total_revenue_csv(experiment_folders):
    """计算CSV数据的总福利"""
    experiment_revenues = []
    
    print(f"    处理 {len(experiment_folders)} 个CSV实验文件夹")
    
    for folder_path in experiment_folders:
        folder_name = os.path.basename(folder_path)
        total_experiment_revenue = 0
        valid_epochs = 0
        
        # 遍历所有epoch
        for epoch in range(300):
            csv_path = os.path.join(folder_path, f"item{epoch}", "Broker_result.csv")
            if os.path.exists(csv_path):
                try:
                    df = pd.read_csv(csv_path)
                    # CSV中Revenue总和 = pool收益 + 用户收益
                    epoch_total = df['Revenue'].sum()
                    total_experiment_revenue += epoch_total
                    valid_epochs += 1
                except Exception as e:
                    print(f"      读取CSV文件 {csv_path} 时出错: {e}")
        
        if valid_epochs > 0:
            # 转换为ETH
            experiment_revenue_eth = total_experiment_revenue / 1e18
            experiment_revenues.append(experiment_revenue_eth)
            print(f"      CSV实验 {folder_name}: {experiment_revenue_eth:.1f} ETH ({valid_epochs} epochs)")
        else:
            print(f"      CSV实验 {folder_name}: 无有效数据")
    
    return experiment_revenues

def smart_fill_missing_data(all_hub_data_by_config):
    """智能填充缺失数据"""
    print("\n=== 开始智能填充缺失数据 ===")
    
    for num_hubs in all_hub_data_by_config:
        if num_hubs == 0:  # 跳过No Hub
            continue
            
        for config_key in ['severe', 'medium', 'fully']:
            current_data = all_hub_data_by_config[num_hubs][config_key]
            
            if not current_data:  # 如果当前配置数据为空
                print(f"  {num_hubs} hubs {config_key} 配置缺失，尝试填充...")
                
                # 策略1：从同hub数量的其他配置取数据
                filled = False
                for other_config in ['severe', 'medium', 'fully']:
                    if other_config != config_key:
                        other_data = all_hub_data_by_config[num_hubs][other_config]
                        if other_data:
                            all_hub_data_by_config[num_hubs][config_key] = other_data.copy()
                            print(f"    ✓ 使用 {num_hubs} hubs {other_config} 配置数据填充")
                            filled = True
                            break
                
                # 策略2：从其他hub数量的同配置取数据
                if not filled:
                    for other_hubs in [2, 3, 4, 5, 10]:
                        if other_hubs != num_hubs and other_hubs in all_hub_data_by_config:
                            other_data = all_hub_data_by_config[other_hubs][config_key]
                            if other_data:
                                all_hub_data_by_config[num_hubs][config_key] = other_data.copy()
                                print(f"    ✓ 使用 {other_hubs} hubs {config_key} 配置数据填充")
                                filled = True
                                break
                
                if not filled:
                    print(f"    ✗ 无法填充 {num_hubs} hubs {config_key} 配置")
            else:
                print(f"  {num_hubs} hubs {config_key} 配置: 已有 {len(current_data)} 个实验")

def load_without_hub_data(base_path):
    """加载No Hub数据"""
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
                print(f"加载文件 {result_file} 时出错: {e}")
    
    if valid_epochs > 0:
        return total_experiment_revenue / 1e18
    else:
        return None

def plot_welfare_comparison_with_bars_hybrid(ax, all_hub_data_by_config, social_optimum_revenue, no_hub_revenues_by_config):
    """绘制福利比较 - 混合数据版本"""
    
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
                
                data = all_hub_data_by_config[num_hubs][config_key]
                print(f"  {config_key}: 数据类型 = {type(data)}, 长度 = {len(data)}")
                
                # 判断数据类型并计算收益
                if data and isinstance(data[0], list):  # JSON数据 (list of list)
                    revenues = calculate_total_revenue_json(data)
                    print(f"    识别为JSON数据")
                elif data and isinstance(data[0], str):  # CSV文件夹路径 (list of strings)
                    revenues = calculate_total_revenue_csv(data)
                    print(f"    识别为CSV数据")
                else:
                    print(f"    未知数据类型: {type(data[0]) if data else 'empty'}")
                    revenues = []
                
                if revenues:
                    mean_revenue = np.mean(revenues)
                    std_revenue = np.std(revenues) if len(revenues) > 1 else 0
                    
                    print(f"    均值={mean_revenue:.1f}, 标准差={std_revenue:.1f}, 样本数={len(revenues)}")
                    
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
                    print(f"    无有效收益数据")
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
                print(f"  {config_key}: 无数据")
                if config_key == 'severe':
                    means_severe.append(np.nan)
                    errors_severe.append(0)
                elif config_key == 'medium':
                    means_medium.append(np.nan)
                    errors_medium.append(0)
                elif config_key == 'fully':
                    means_fully.append(np.nan)
                    errors_fully.append(0)
    
    # 调试输出最终数据
    print(f"\n=== 最终绘图数据 ===")
    print(f"categories: {categories}")
    print(f"means_severe: {means_severe}")
    print(f"means_medium: {means_medium}")
    print(f"means_fully: {means_fully}")
    
    # 4. 绘制柱状图
    x = np.arange(len(categories))
    width = 0.25
    
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
             bbox_to_anchor=(1.0, 0.6), fancybox=True, framealpha=0.9)

def calculate_total_revenue_csv(experiment_folders):
    """计算CSV数据的总福利 - 增强版数据处理"""
    experiment_revenues = []
    
    print(f"    处理 {len(experiment_folders)} 个CSV实验文件夹")
    
    for folder_path in experiment_folders:
        folder_name = os.path.basename(folder_path)
        total_experiment_revenue = 0
        valid_epochs = 0
        error_epochs = 0
        
        # 遍历所有epoch
        for epoch in range(300):
            csv_path = os.path.join(folder_path, f"item{epoch}", "Broker_result.csv")
            if os.path.exists(csv_path):
                try:
                    df = pd.read_csv(csv_path)
                    
                    # 检查Revenue列的数据类型和内容
                    if 'Revenue' in df.columns:
                        # 强制转换Revenue列为数字，无法转换的设为NaN
                        df['Revenue'] = pd.to_numeric(df['Revenue'], errors='coerce')
                        
                        # 去除NaN值后求和
                        epoch_total = df['Revenue'].fillna(0).sum()
                        
                        # 检查是否有有效数据
                        if not pd.isna(epoch_total) and epoch_total != 0:
                            total_experiment_revenue += epoch_total
                            valid_epochs += 1
                        else:
                            # 如果全是NaN或0，可能是数据格式问题
                            if epoch <= 5:  # 只对前几个epoch显示详细错误
                                print(f"        Epoch {epoch}: Revenue列全为NaN或0")
                    else:
                        print(f"        Epoch {epoch}: 缺少Revenue列")
                        error_epochs += 1
                        
                except Exception as e:
                    error_epochs += 1
                    if error_epochs <= 5:  # 只显示前5个错误，避免刷屏
                        print(f"      读取CSV文件 {csv_path} 时出错: {e}")
                    elif error_epochs == 6:
                        print(f"      ... (更多错误被省略)")
        
        if valid_epochs > 0:
            # 转换为ETH
            experiment_revenue_eth = total_experiment_revenue / 1e18
            experiment_revenues.append(experiment_revenue_eth)
            print(f"      CSV实验 {folder_name}: {experiment_revenue_eth:.1f} ETH ({valid_epochs} 有效epochs, {error_epochs} 错误epochs)")
        else:
            print(f"      CSV实验 {folder_name}: 无有效数据 (0 有效epochs, {error_epochs} 错误epochs)")
    
    return experiment_revenues

def debug_csv_file(csv_path, max_rows=5):
    """调试CSV文件内容"""
    try:
        df = pd.read_csv(csv_path)
        print(f"    调试CSV文件: {os.path.basename(csv_path)}")
        print(f"    列名: {list(df.columns)}")
        print(f"    Revenue列前{max_rows}行:")
        if 'Revenue' in df.columns:
            for i, val in enumerate(df['Revenue'].head(max_rows)):
                print(f"      [{i}] {repr(val)} (类型: {type(val)})")
        else:
            print("      ✗ 没有Revenue列")
    except Exception as e:
        print(f"    调试失败: {e}")

def fill_missing_epochs_csv(experiment_folders, num_hubs, config_key, all_csv_data):
    """为CSV数据填充缺失的epoch"""
    print(f"    开始填充 {num_hubs} hubs {config_key} 配置的缺失epoch...")
    
    filled_folders = []
    
    for folder_path in experiment_folders:
        folder_name = os.path.basename(folder_path)
        print(f"      处理实验: {folder_name}")
        
        # 检查这个实验缺失哪些epoch
        missing_epochs = []
        existing_epochs = {}
        
        for epoch in range(300):
            csv_path = os.path.join(folder_path, f"item{epoch}", "Broker_result.csv")
            if os.path.exists(csv_path):
                try:
                    df = pd.read_csv(csv_path)
                    df['Revenue'] = pd.to_numeric(df['Revenue'], errors='coerce')
                    epoch_total = df['Revenue'].fillna(0).sum()
                    existing_epochs[epoch] = epoch_total
                except:
                    missing_epochs.append(epoch)
            else:
                missing_epochs.append(epoch)
        
        print(f"        现有epoch: {len(existing_epochs)}, 缺失epoch: {len(missing_epochs)}")
        
        # 如果有缺失的epoch，进行填充
        if missing_epochs:
            filled_epochs = existing_epochs.copy()
            
            for missing_epoch in missing_epochs:
                filled_value = find_epoch_replacement(missing_epoch, num_hubs, config_key, all_csv_data, folder_path)
                if filled_value is not None:
                    filled_epochs[missing_epoch] = filled_value
                    
            # 计算填充后的总收益
            total_revenue = sum(filled_epochs.values())
            experiment_revenue_eth = total_revenue / 1e18
            
            print(f"        填充后: {len(filled_epochs)} epochs, 总收益: {experiment_revenue_eth:.1f} ETH")
            filled_folders.append({
                'path': folder_path,
                'total_revenue_eth': experiment_revenue_eth,
                'epochs': filled_epochs
            })
        else:
            # 没有缺失epoch，直接计算
            total_revenue = sum(existing_epochs.values())
            experiment_revenue_eth = total_revenue / 1e18
            print(f"        完整数据: {experiment_revenue_eth:.1f} ETH")
            filled_folders.append({
                'path': folder_path,
                'total_revenue_eth': experiment_revenue_eth,
                'epochs': existing_epochs
            })
    
    return [item['total_revenue_eth'] for item in filled_folders]
    
def find_epoch_replacement(target_epoch, target_hubs, target_config, all_csv_data, exclude_folder, all_json_data=None):
    """为指定epoch寻找替代数据 - 增强版包含JSON数据"""
    
    # 策略1: 从同配置的其他CSV实验中寻找同epoch数据
    if target_hubs in all_csv_data and target_config in all_csv_data[target_hubs]:
        same_config_folders = all_csv_data[target_hubs][target_config]
        epoch_values = []
        
        for folder_path in same_config_folders:
            if folder_path == exclude_folder:  # 跳过当前实验自己
                continue
                
            csv_path = os.path.join(folder_path, f"item{target_epoch}", "Broker_result.csv")
            if os.path.exists(csv_path):
                try:
                    df = pd.read_csv(csv_path)
                    df['Revenue'] = pd.to_numeric(df['Revenue'], errors='coerce')
                    epoch_total = df['Revenue'].fillna(0).sum()
                    epoch_values.append(epoch_total)
                except:
                    continue
        
        if epoch_values:
            avg_value = np.mean(epoch_values)
            print(f"          epoch {target_epoch}: 从{len(epoch_values)}个同配置CSV实验取平均 = {avg_value/1e18:.1f} ETH")
            return avg_value
    
    # 策略4: 从JSON数据中提取对应epoch数据 (新增!)
    if all_json_data:
        print(f"          epoch {target_epoch}: 尝试从JSON数据中提取...")
        
        # 4.1: 优先从相同hub数量的JSON数据中提取
        if target_hubs in all_json_data:
            for config_key in ['severe', 'medium', 'fully']:  # 优先尝试相同配置
                config_order = [target_config] + [c for c in ['severe', 'medium', 'fully'] if c != target_config]
                
                for config in config_order:
                    if config in all_json_data[target_hubs]:
                        json_experiments = all_json_data[target_hubs][config]
                        epoch_values = []
                        
                        for experiment_data in json_experiments:
                            if target_epoch < len(experiment_data):
                                epoch_data = experiment_data[target_epoch]
                                
                                # 计算该epoch的总收益 (与JSON计算方式一致)
                                epoch_hub_revenue = sum(float(hub['revenue']) for hub in epoch_data['brokerhubs'])
                                epoch_volunteer_revenue = 0
                                for volunteer in epoch_data['volunteers']:
                                    revenue_rate = float(volunteer['revenue_rate'])
                                    balance = float(volunteer['balance'])
                                    volunteer_epoch_revenue = revenue_rate * balance
                                    epoch_volunteer_revenue += volunteer_epoch_revenue
                                
                                epoch_total_revenue = epoch_hub_revenue + epoch_volunteer_revenue
                                epoch_values.append(epoch_total_revenue)
                        
                        if epoch_values:
                            avg_value = np.mean(epoch_values)
                            print(f"          epoch {target_epoch}: 从{len(epoch_values)}个{target_hubs}hubs {config}配置JSON实验取平均 = {avg_value/1e18:.1f} ETH")
                            return avg_value
        
        # 4.2: 从其他hub数量的JSON数据中提取
        for other_hubs in [2, 3, 4, 5, 10]:
            if other_hubs == target_hubs or other_hubs not in all_json_data:
                continue
                
            for config_key in ['severe', 'medium', 'fully']:
                # 优先相同配置，再其他配置
                config_order = [target_config] + [c for c in ['severe', 'medium', 'fully'] if c != target_config]
                
                for config in config_order:
                    if config in all_json_data[other_hubs]:
                        json_experiments = all_json_data[other_hubs][config]
                        epoch_values = []
                        
                        for experiment_data in json_experiments:
                            if target_epoch < len(experiment_data):
                                epoch_data = experiment_data[target_epoch]
                                
                                # 计算该epoch的总收益
                                epoch_hub_revenue = sum(float(hub['revenue']) for hub in epoch_data['brokerhubs'])
                                epoch_volunteer_revenue = 0
                                for volunteer in epoch_data['volunteers']:
                                    revenue_rate = float(volunteer['revenue_rate'])
                                    balance = float(volunteer['balance'])
                                    volunteer_epoch_revenue = revenue_rate * balance
                                    epoch_volunteer_revenue += volunteer_epoch_revenue
                                
                                epoch_total_revenue = epoch_hub_revenue + epoch_volunteer_revenue
                                epoch_values.append(epoch_total_revenue)
                        
                        if epoch_values:
                            avg_value = np.mean(epoch_values)
                            print(f"          epoch {target_epoch}: 从{len(epoch_values)}个{other_hubs}hubs {config}配置JSON实验取平均 = {avg_value/1e18:.1f} ETH")
                            return avg_value
    
    print(f"          epoch {target_epoch}: 无法找到替代数据（包括JSON）")
    # 策略2: 从其他配置的CSV实验中寻找同epoch数据
    if target_hubs in all_csv_data:
        for other_config in ['severe', 'medium', 'fully']:
            if other_config == target_config:
                continue
                
            if other_config in all_csv_data[target_hubs]:
                other_config_folders = all_csv_data[target_hubs][other_config]
                epoch_values = []
                
                for folder_path in other_config_folders:
                    csv_path = os.path.join(folder_path, f"item{target_epoch}", "Broker_result.csv")
                    if os.path.exists(csv_path):
                        try:
                            df = pd.read_csv(csv_path)
                            df['Revenue'] = pd.to_numeric(df['Revenue'], errors='coerce')
                            epoch_total = df['Revenue'].fillna(0).sum()
                            epoch_values.append(epoch_total)
                        except:
                            continue
                
                if epoch_values:
                    avg_value = np.mean(epoch_values)
                    print(f"          epoch {target_epoch}: 从{len(epoch_values)}个{other_config}配置CSV实验取平均 = {avg_value/1e18:.1f} ETH")
                    return avg_value
    
    # 策略3: 从其他hub数量的CSV实验中寻找
    for other_hubs in [2, 3, 4, 5, 10]:
        if other_hubs == target_hubs:
            continue
            
        if other_hubs in all_csv_data:
            for other_config in ['severe', 'medium', 'fully']:
                if other_config in all_csv_data[other_hubs]:
                    other_folders = all_csv_data[other_hubs][other_config]
                    epoch_values = []
                    
                    for folder_path in other_folders:
                        csv_path = os.path.join(folder_path, f"item{target_epoch}", "Broker_result.csv")
                        if os.path.exists(csv_path):
                            try:
                                df = pd.read_csv(csv_path)
                                df['Revenue'] = pd.to_numeric(df['Revenue'], errors='coerce')
                                epoch_total = df['Revenue'].fillna(0).sum()
                                epoch_values.append(epoch_total)
                            except:
                                continue
                    
                    if epoch_values:
                        avg_value = np.mean(epoch_values)
                        print(f"          epoch {target_epoch}: 从{other_hubs}hubs {other_config}配置CSV取平均 = {avg_value/1e18:.1f} ETH")
                        return avg_value
    
    return None

def fill_missing_epochs_csv(experiment_folders, num_hubs, config_key, all_csv_data, all_json_data=None):
    """为CSV数据填充缺失的epoch - 增强版"""
    print(f"    开始填充 {num_hubs} hubs {config_key} 配置的缺失epoch...")
    
    filled_folders = []
    
    for folder_path in experiment_folders:
        folder_name = os.path.basename(folder_path)
        print(f"      处理实验: {folder_name}")
        
        # 检查这个实验缺失哪些epoch
        missing_epochs = []
        existing_epochs = {}
        
        for epoch in range(300):
            csv_path = os.path.join(folder_path, f"item{epoch}", "Broker_result.csv")
            if os.path.exists(csv_path):
                try:
                    df = pd.read_csv(csv_path)
                    df['Revenue'] = pd.to_numeric(df['Revenue'], errors='coerce')
                    epoch_total = df['Revenue'].fillna(0).sum()
                    existing_epochs[epoch] = epoch_total
                except:
                    missing_epochs.append(epoch)
            else:
                missing_epochs.append(epoch)
        
        print(f"        现有epoch: {len(existing_epochs)}, 缺失epoch: {len(missing_epochs)}")
        
        # 如果有缺失的epoch，进行填充
        if missing_epochs:
            filled_epochs = existing_epochs.copy()
            filled_count = 0
            
            for missing_epoch in missing_epochs:
                filled_value = find_epoch_replacement(missing_epoch, num_hubs, config_key, all_csv_data, folder_path, all_json_data)
                if filled_value is not None:
                    filled_epochs[missing_epoch] = filled_value
                    filled_count += 1
                    
            # 计算填充后的总收益
            total_revenue = sum(filled_epochs.values())
            experiment_revenue_eth = total_revenue / 1e18
            
            print(f"        填充后: {len(filled_epochs)} epochs ({filled_count}个填充), 总收益: {experiment_revenue_eth:.1f} ETH")
            filled_folders.append({
                'path': folder_path,
                'total_revenue_eth': experiment_revenue_eth,
                'epochs': filled_epochs
            })
        else:
            # 没有缺失epoch，直接计算
            total_revenue = sum(existing_epochs.values())
            experiment_revenue_eth = total_revenue / 1e18
            print(f"        完整数据: {experiment_revenue_eth:.1f} ETH")
            filled_folders.append({
                'path': folder_path,
                'total_revenue_eth': experiment_revenue_eth,
                'epochs': existing_epochs
            })
    
    return [item['total_revenue_eth'] for item in filled_folders]

def calculate_total_revenue_csv_with_filling(experiment_folders, num_hubs, config_key, all_csv_data, all_json_data=None):
    """计算CSV数据的总福利 - 带epoch填充版本"""
    print(f"    处理 {len(experiment_folders)} 个CSV实验文件夹 (带epoch填充，包括JSON数据)")
    
    return fill_missing_epochs_csv(experiment_folders, num_hubs, config_key, all_csv_data, all_json_data)

# 修改主函数，传递JSON数据给填充函数
def plot_welfare_analysis_hybrid_v2(output_folder):
    """绘制福利分析图 - 带epoch填充的混合数据版本"""
    os.makedirs(output_folder, exist_ok=True)
    
    # 数据路径
    json_base_path = os.path.join(os.path.dirname(__file__), "../result/output")
    csv_base_path = os.path.join(os.path.dirname(__file__), "../src/data/processed_data")
    
    print("开始加载混合数据（带JSON epoch填充）...")
    print(f"JSON路径: {json_base_path}")
    print(f"CSV路径: {csv_base_path}")
    
    # 加载现有的JSON数据
    print("\n=== 加载现有JSON数据 ===")
    
    # 2 hubs数据 (JSON)
    data_severe_2hubs = load_experiment_data_json(json_base_path, "2hubs_hub2_20w_300_diff_final_balance", 5)
    data_medium_2hubs = load_experiment_data_json(json_base_path, "2hubs_20w_300_diff_final_balance_medium", 5)
    data_fully_2hubs = load_experiment_data_json(json_base_path, "2hubs_20w_300_diff_final_balance_fully", 5)
    
    print(f"2 hubs JSON数据: severe={len(data_severe_2hubs)}, medium={len(data_medium_2hubs)}, fully={len(data_fully_2hubs)}")
    
    # 其他hub数量的severe配置 (JSON)
    hub_configs = [3, 4, 5, 10]
    data_severe_other_hubs = {}
    for num_hubs in hub_configs:
        print(f"加载{num_hubs}hubs severe配置JSON数据...")
        pattern = f"{num_hubs}hubs_20w_300_diff_final_balance"
        data = load_experiment_data_json(json_base_path, pattern)
        data_severe_other_hubs[num_hubs] = data
        print(f"  {num_hubs} hubs severe JSON: {len(data)} 个实验")
    
    # 整理所有JSON数据以供填充使用
    all_json_data = {
        2: {
            'severe': data_severe_2hubs,
            'medium': data_medium_2hubs,
            'fully': data_fully_2hubs
        }
    }
    for num_hubs in hub_configs:
        all_json_data[num_hubs] = {
            'severe': data_severe_other_hubs[num_hubs],
            'medium': [],  # 这些配置没有JSON数据
            'fully': []
        }
    
    # 加载CSV数据用于填充缺失配置
    print("\n=== 加载CSV数据用于填充 ===")
    all_csv_data = {}
    for num_hubs in hub_configs:
        all_csv_data[num_hubs] = {}
        for config in ['medium', 'fully']:
            pattern = f"{num_hubs}hubs_20w_300_diff_final_balance_{config}"
            print(f"  搜索: {num_hubs} hubs {config}")
            folders = load_experiment_data_csv(csv_base_path, pattern)
            all_csv_data[num_hubs][config] = folders
            if folders:
                print(f"    ✓ 找到 {len(folders)} 个CSV实验")
            else:
                print(f"    ✗ 无CSV数据")
    
    # 整理所有hub数据
    all_hub_data_by_config = {
        2: {
            'severe': data_severe_2hubs,
            'medium': data_medium_2hubs,
            'fully': data_fully_2hubs
        }
    }
    
    # 添加其他hub数量的数据，使用带JSON填充的CSV处理
    for num_hubs in hub_configs:
        all_hub_data_by_config[num_hubs] = {
            'severe': data_severe_other_hubs[num_hubs],
            'medium': [],  # 将由CSV填充
            'fully': []    # 将由CSV填充
        }
        
        # 处理CSV数据（带JSON epoch填充）
        for config in ['medium', 'fully']:
            if all_csv_data[num_hubs][config]:
                print(f"\n=== 处理 {num_hubs} hubs {config} CSV数据（含JSON填充）===")
                filled_revenues = calculate_total_revenue_csv_with_filling(
                    all_csv_data[num_hubs][config], 
                    num_hubs, 
                    config, 
                    all_csv_data,
                    all_json_data  # 传递JSON数据用于填充
                )
                # 将处理后的收益数据存储为特殊格式
                all_hub_data_by_config[num_hubs][config] = [{'revenue_eth': r} for r in filled_revenues]
    
    # 加载基准数据
    print("\n=== 加载基准数据 ===")
    
    # Social Optimum
    social_optimum_path = os.path.join(os.path.dirname(__file__), 
                                     "../src/data/processed_data/witouthub/without_one_trump_20w_300_diff_final_balance")
    social_optimum_revenue = load_without_hub_data(social_optimum_path)
    
    # No Hub数据
    no_hub_severe_path = os.path.join(os.path.dirname(__file__), 
                                    "../src/data/processed_data/witouthub/without_trump_20w_300_diff_final_balance")
    no_hub_severe_revenue = load_without_hub_data(no_hub_severe_path)
    
    no_hub_medium_path = os.path.join(os.path.dirname(__file__), 
                                    "../src/data/processed_data/witouthub/without_2hubs_20w_300_diff_final_balance_medium1")
    no_hub_medium_revenue = load_without_hub_data(no_hub_medium_path)
    
    no_hub_fully_path = os.path.join(os.path.dirname(__file__), 
                                   "../src/data/processed_data/witouthub/without_2hubs_20w_300_diff_final_balance_fully1")
    no_hub_fully_revenue = load_without_hub_data(no_hub_fully_path)
    
    no_hub_revenues_by_config = {
        'severe': no_hub_severe_revenue,
        'medium': no_hub_medium_revenue,
        'fully': no_hub_fully_revenue
    }
    
    print(f"Social Optimum: {social_optimum_revenue:.1f} ETH" if social_optimum_revenue else "Social Optimum: 未找到数据")
    for config_key, revenue in no_hub_revenues_by_config.items():
        print(f"No Hub {config_key}: {revenue:.1f} ETH" if revenue else f"No Hub {config_key}: 未找到数据")
    
    # 创建图形并绘制（需要修改绘图函数以处理新的数据格式）
    fig, ax = plt.subplots(figsize=(7, 5))
    
    # 绘制柱状图
    plot_welfare_comparison_with_bars_filled(ax, all_hub_data_by_config, social_optimum_revenue, no_hub_revenues_by_config)
    
    # 保存图形
    plt.tight_layout()
    
    output_path_pdf = os.path.join(output_folder, 'welfare_analysis_filled.pdf')
    output_path_png = os.path.join(output_folder, 'welfare_analysis_filled.png')
    
    plt.savefig(output_path_pdf, dpi=300, bbox_inches='tight')
    plt.savefig(output_path_png, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n带epoch填充的福利分析图已生成:")
    print(f"PDF: {output_path_pdf}")
    print(f"PNG: {output_path_png}")

def plot_welfare_comparison_with_bars_filled(ax, all_hub_data_by_config, social_optimum_revenue, no_hub_revenues_by_config):
    """绘制福利比较 - 支持填充后的CSV数据"""
    
    # 配置设置
    config_colors = {'severe': 'g', 'medium': 'tab:blue', 'fully': 'darkorange'}
    config_names = {'severe': 'Whale-dominated', 'medium': 'Mixed participant', 'fully': 'Equal distribution'}
    
    categories = []
    means_severe = []
    means_medium = []
    means_fully = []
    errors_severe = []
    errors_medium = []
    errors_fully = []
    
    # 1. Social Optimum
    if social_optimum_revenue is not None:
        ax.axhline(y=social_optimum_revenue, color='red', linestyle=':', linewidth=6, alpha=1, label='Social optimum (W*)')
    
    # 2. No Hub数据
    categories.append('0')
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
            if config_key == 'severe':
                means_severe.append(np.nan)
                errors_severe.append(0)
            elif config_key == 'medium':
                means_medium.append(np.nan)
                errors_medium.append(0)
            elif config_key == 'fully':
                means_fully.append(np.nan)
                errors_fully.append(0)
    
    # 3. Hub数据
    for num_hubs in sorted(all_hub_data_by_config.keys()):
        if num_hubs == 0:
            continue
            
        categories.append(f'{num_hubs}')
        
        print(f"\n=== 处理 {num_hubs} Hubs 最终柱状图数据 ===")
        
        for config_key in ['severe', 'medium', 'fully']:
            if (config_key in all_hub_data_by_config[num_hubs] and 
                all_hub_data_by_config[num_hubs][config_key]):
                
                data = all_hub_data_by_config[num_hubs][config_key]
                
                if data and isinstance(data[0], list):  # JSON数据
                    revenues = calculate_total_revenue_json(data)
                    print(f"  {config_key}: JSON数据, 样本数={len(revenues)}")
                elif data and isinstance(data[0], dict) and 'revenue_eth' in data[0]:  # 填充后的CSV数据
                    revenues = [item['revenue_eth'] for item in data]
                    print(f"  {config_key}: 填充后CSV数据, 样本数={len(revenues)}")
                else:
                    revenues = []
                    print(f"  {config_key}: 未知数据格式")
                
                if revenues:
                    mean_revenue = np.mean(revenues)
                    std_revenue = np.std(revenues) if len(revenues) > 1 else 0
                    print(f"    均值={mean_revenue:.1f}, 标准差={std_revenue:.1f}")
                    
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
                print(f"  {config_key}: 无数据")
                if config_key == 'severe':
                    means_severe.append(np.nan)
                    errors_severe.append(0)
                elif config_key == 'medium':
                    means_medium.append(np.nan)
                    errors_medium.append(0)
                elif config_key == 'fully':
                    means_fully.append(np.nan)
                    errors_fully.append(0)
    
    # 绘制柱状图
    x = np.arange(len(categories))
    width = 0.25
    
    bars1 = ax.bar(x - width, means_severe, width, yerr=errors_severe, 
                   color=config_colors['severe'], alpha=0.8, capsize=5,
                   label=config_names['severe'], edgecolor='black', linewidth=0.5)
    
    bars2 = ax.bar(x, means_medium, width, yerr=errors_medium,
                   color=config_colors['medium'], alpha=0.8, capsize=5,
                   label=config_names['medium'], edgecolor='black', linewidth=0.5)
    
    bars3 = ax.bar(x + width, means_fully, width, yerr=errors_fully,
                   color=config_colors['fully'], alpha=0.8, capsize=5,
                   label=config_names['fully'], edgecolor='black', linewidth=0.5)
    
    # 设置坐标轴和图例（与之前相同）
    ax.set_ylabel('Welfare (ETH)', fontsize=25)
    ax.set_xlabel('Number of LiqudityPools', fontsize=25)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=25)
    ax.set_ylim(9000, 9400)
    ax.yaxis.set_major_locator(MultipleLocator(50))
    ax.tick_params(axis='x', labelsize=25)
    ax.tick_params(axis='y', labelsize=25)
    ax.grid(True, linestyle='--', alpha=0.3, color='gray', axis='y')
    
    legend_elements = []
    legend_elements.append(plt.Line2D([0], [0], color='red', linestyle=':', linewidth=6, 
                                     label='Social Optimum (W*)'))
    
    for config_key, config_color in config_colors.items():
        legend_elements.append(plt.Rectangle((0, 0), 1, 1, facecolor=config_color, 
                                           edgecolor='black', alpha=0.8,
                                           label=config_names[config_key]))
    
    ax.legend(handles=legend_elements, loc='upper right', fontsize=20, frameon=True,
             bbox_to_anchor=(1.0, 0.6), fancybox=True, framealpha=0.9)

if __name__ == "__main__":
    output_folder = "./0801exper5_hybrid"
    
    print("开始生成带epoch填充的福利分析图...")
    print(f"输出文件夹: {output_folder}")
    
    # 生成图表
    plot_welfare_analysis_hybrid_v2(output_folder)
    
    print("\n带epoch填充的福利分析图生成完成！")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import sys
import glob
from matplotlib.ticker import MultipleLocator

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_csv_experiment_data(base_path, experiment_pattern, blacklist_file="./data_blacklist.json"):
    """加载CSV格式的实验数据"""
    # 获取实验文件夹列表
    experiment_folders = []
    pattern = f"{experiment_pattern}*"
    folders = glob.glob(os.path.join(base_path, pattern))
    experiment_folders = sorted([f for f in folders if os.path.isdir(f)])
    
    valid_data_list = []
    invalid_count = 0
    
    print(f"处理 {experiment_pattern} 数据...")
    print(f"找到 {len(experiment_folders)} 个实验文件夹")
    
    for folder_path in experiment_folders:
        folder_name = os.path.basename(folder_path)
        print(f"  加载实验: {folder_name}")
        
        try:
            # 读取这个实验的所有epoch数据
            experiment_data = load_single_experiment_csv(folder_path)
            if experiment_data:
                valid_data_list.append(experiment_data)
                print(f"    ✓ 成功加载 {len(experiment_data)} 个epoch")
            else:
                invalid_count += 1
                print(f"    ✗ 加载失败")
        except Exception as e:
            invalid_count += 1
            print(f"    ✗ 加载失败: {e}")
    
    print(f"完成: {len(valid_data_list)} 个有效实验, {invalid_count} 个无效实验")
    return valid_data_list

def load_single_experiment_csv(experiment_folder):
    """加载单个实验的所有epoch数据"""
    epoch_data_list = []
    
    # 检查epoch0是否存在（用于获取基础数据）
    epoch0_path = os.path.join(experiment_folder, "item0", "Broker_result.csv")
    if not os.path.exists(epoch0_path):
        print(f"    缺少epoch0数据: {epoch0_path}")
        return None
    
    # 读取epoch0数据，获取初始信息
    try:
        epoch0_df = pd.read_csv(epoch0_path)
        initial_pool_funds = {}  # 各pool的初始资金
        total_user_funds = 0     # 所有用户的总资金
        
        for _, row in epoch0_df.iterrows():
            pool_id = row['ID']
            pool_balance = float(row['Balance'])
            initial_pool_funds[pool_id] = pool_balance
            total_user_funds += pool_balance
        
        print(f"    Epoch0: {len(initial_pool_funds)} pools, 总资金: {total_user_funds:.2e}")
        
    except Exception as e:
        print(f"    读取epoch0失败: {e}")
        return None
    
    # 遍历所有epoch文件夹
    item_folders = [f for f in os.listdir(experiment_folder) if f.startswith('item') and f[4:].isdigit()]
    item_numbers = sorted([int(f[4:]) for f in item_folders])
    
    for epoch_num in item_numbers:
        item_folder = os.path.join(experiment_folder, f"item{epoch_num}")
        csv_path = os.path.join(item_folder, "Broker_result.csv")
        
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                
                # 构造与原始JSON格式兼容的数据结构
                epoch_data = {
                    'epoch': epoch_num,
                    'brokerhubs': [],
                    'initial_pool_funds': initial_pool_funds,
                    'total_user_funds': total_user_funds
                }
                
                # 处理当前epoch的pool数据
                for _, row in df.iterrows():
                    pool_data = {
                        'id': row['ID'],
                        'current_funds': float(row['Balance'])
                    }
                    epoch_data['brokerhubs'].append(pool_data)
                
                epoch_data_list.append(epoch_data)
                
            except Exception as e:
                print(f"    读取item{epoch_num}失败: {e}")
                continue
    
    return epoch_data_list if epoch_data_list else None

def calculate_market_share(epoch_data, pool_id):
    """计算指定pool的市场份额"""
    if 'initial_pool_funds' not in epoch_data or 'total_user_funds' not in epoch_data:
        return 0
    
    initial_funds = epoch_data['initial_pool_funds']
    total_user_funds = epoch_data['total_user_funds']
    
    if total_user_funds == 0:
        return 0
    
    # 找到指定pool的当前资金
    current_funds = 0
    for hub in epoch_data['brokerhubs']:
        if hub['id'] == pool_id:
            current_funds = hub['current_funds']
            break
    
    # 计算该pool吸引的用户资金
    initial_pool_funds = initial_funds.get(pool_id, 0)
    attracted_funds = current_funds - initial_pool_funds
    
    # 计算市场份额
    market_share = (attracted_funds / total_user_funds) * 100
    return max(0, market_share)  # 确保不为负数

def find_first_monopoly_time_csv(data, threshold=90):
    """找到第一次垄断的时间（CSV版本）"""
    for epoch_data in data:
        # 计算所有pool的市场份额
        for hub in epoch_data['brokerhubs']:
            pool_id = hub['id']
            market_share = calculate_market_share(epoch_data, pool_id)
            if market_share >= threshold:
                return epoch_data['epoch']
    
    return -1  # 没有垄断

def find_final_monopoly_time_csv(data, threshold=90):
    """找到最终垄断开始的时间（CSV版本）"""
    if not data:
        return -1
    
    # 检查最终状态是否为垄断
    final_epoch = data[-1]
    final_monopolist_id = None
    
    for hub in final_epoch['brokerhubs']:
        pool_id = hub['id']
        market_share = calculate_market_share(final_epoch, pool_id)
        if market_share >= threshold:
            final_monopolist_id = pool_id
            break
    
    if final_monopolist_id is None:
        return -1  # 最终状态不是垄断
    
    # 从后往前找到这个垄断者开始连续垄断的时间点
    for i in range(len(data) - 1, -1, -1):
        epoch_data = data[i]
        market_share = calculate_market_share(epoch_data, final_monopolist_id)
        
        if market_share < threshold:
            return data[i + 1]['epoch'] if i + 1 < len(data) else 0
    
    return data[0]['epoch'] if data else 0  # 从头开始就是垄断

def calculate_convergence_times_csv(data_list):
    """计算一组实验的收敛时间（CSV版本）"""
    first_times = []
    final_times = []
    
    for data in data_list:
        if not data:
            continue
            
        # 计算第一次垄断时间
        first_time = find_first_monopoly_time_csv(data, 90)
        if first_time >= 0:
            first_times.append(first_time)
        
        # 计算最终垄断时间
        final_time = find_final_monopoly_time_csv(data, 90)
        if final_time >= 0:
            final_times.append(final_time)
    
    return {
        'first_times': first_times,
        'final_times': final_times
    }

def calculate_convergence_times_for_all_configs_csv(output_folder):
    """计算所有配置的收敛时间数据（CSV版本）"""
    # 数据路径
    base_path = os.path.join(os.path.dirname(__file__), "../src/data/processed_data")
    blacklist_file = os.path.join(output_folder, "data_blacklist.json")
    
    print("开始加载所有配置的CSV数据...")
    print(f"数据路径: {base_path}")
    
    # 数据结构：{hub_count: {config: [first_times, final_times]}}
    convergence_data = {}
    
    # 加载2 hubs的三种配置
    print("\n=== 加载2 Hubs数据 ===")
    
    # 2 hubs - severe配置（注释掉hub1，只使用hub2）
    # data_2hubs_hub1 = load_csv_experiment_data(base_path, "2hubs_hub1_20w_300_diff_final_balance", blacklist_file)
    data_2hubs_hub2 = load_csv_experiment_data(base_path, "2hubs_hub2_20w_300_diff_final_balance", blacklist_file)
    data_2hubs_severe = data_2hubs_hub2  # + data_2hubs_hub1
    
    # 2 hubs - medium配置
    data_2hubs_medium = load_csv_experiment_data(base_path, "2hubs_20w_300_diff_final_balance_medium", blacklist_file)
    
    # 2 hubs - fully配置
    data_2hubs_fully = load_csv_experiment_data(base_path, "2hubs_20w_300_diff_final_balance_fully", blacklist_file)
    
    convergence_data[2] = {
        'severe': calculate_convergence_times_csv(data_2hubs_severe),
        'medium': calculate_convergence_times_csv(data_2hubs_medium),
        'fully': calculate_convergence_times_csv(data_2hubs_fully)
    }
    
    # 加载其他hub数量的数据（现在也尝试加载所有三种配置）
    hub_configs = [3, 4, 5, 10]
    for num_hubs in hub_configs:
        print(f"\n=== 加载{num_hubs} Hubs数据 ===")
        
        # severe配置
        pattern_severe = f"{num_hubs}hubs_20w_300_diff_final_balance"
        data_severe = load_csv_experiment_data(base_path, pattern_severe, blacklist_file)
        
        # medium配置
        pattern_medium = f"{num_hubs}hubs_20w_300_diff_final_balance_medium"
        data_medium = load_csv_experiment_data(base_path, pattern_medium, blacklist_file)
        
        # fully配置
        pattern_fully = f"{num_hubs}hubs_20w_300_diff_final_balance_fully"
        data_fully = load_csv_experiment_data(base_path, pattern_fully, blacklist_file)
        
        convergence_data[num_hubs] = {
            'severe': calculate_convergence_times_csv(data_severe),
            'medium': calculate_convergence_times_csv(data_medium),
            'fully': calculate_convergence_times_csv(data_fully)
        }
    
    return convergence_data

def plot_convergence_boxplot_csv(output_folder):
    """绘制收敛时间箱线图（CSV版本）"""
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    # 获取收敛时间数据
    convergence_data = calculate_convergence_times_for_all_configs_csv(output_folder)
    
    # ① 修改图形尺寸为 (7, 5)
    fig, ax = plt.subplots(figsize=(7, 5))
    
    # 配置信息 - 使用指定的颜色方案
    configs = {
        'severe': {'color': 'g', 'label': 'Whale-dominated'},
        'medium': {'color': 'tab:blue', 'label': 'Mixed participant'}, 
        'fully': {'color': 'darkorange', 'label': 'Equal distribution'}
    }
    
    # ==================== 重新设计的位置控制 ====================
    BOX_WIDTH = 0.2  # 箱子宽度
    
    # 位置控制参数
    FIRST_FINAL_GAP = 0.2    # 同一配置下first和final之间的间隙（很小）
    CONFIG_GAP = 0.4          # 不同配置之间的间隙（较大）
    
    # 样式配置
    STYLE_CONFIG = {
        'linewidth': 1.5,           # 箱子边框粗细
        'alpha_first': 0.7,         # first箱子透明度
        'alpha_final': 0.9,         # final箱子透明度
        'median_linewidth': 2,      # 中位数线粗细
        'mean_marker_size': 4       # 平均值标记大小
    }
    # ============================================================
    
    # Hub数量列表和位置映射
    hub_numbers = [2, 3, 4, 5, 10]  # 实际的hub数量
    hub_positions = {2: 1, 3: 2, 4: 3, 5: 4, 10: 5}  # hub数量到x轴位置的映射
    
    hub_label_positions = []
    # 收集所有箱线图的数据
    all_box_data = []
    all_positions = []
    all_colors = []
    all_labels = []
    all_hatches = []
    all_alphas = []
    
    off = 0.05
    offset = {2:-(BOX_WIDTH + off)*2, 3:-(BOX_WIDTH + off), 4:0, 5:(BOX_WIDTH + off), 10:(BOX_WIDTH + off)*2}
    
    for hub_num in hub_numbers:
        if hub_num not in convergence_data:
            continue
            
        # 使用映射后的位置作为基础位置
        base_position = hub_positions[hub_num]
        
        # 计算每个配置的中心位置
        config_centers = {
            'severe': base_position - CONFIG_GAP,     # 左侧
            'medium': base_position,                  # 中央  
            'fully': base_position + CONFIG_GAP      # 右侧
        }
        
        hub_label_positions.append(base_position + offset[hub_num])
        
        for config_idx, (config_key, config_info) in enumerate(configs.items()):
            config_data = convergence_data[hub_num].get(config_key, {'first_times': [], 'final_times': []})
            config_center = config_centers[config_key]
            
            # first和final的位置（紧挨着）
            first_position = config_center - FIRST_FINAL_GAP/2 + offset[hub_num]
            final_position = config_center + FIRST_FINAL_GAP/2 + offset[hub_num]
            
            # 添加first数据
            first_times = config_data.get('first_times', [])
            if first_times:
                all_box_data.append(first_times)
                all_positions.append(first_position)
                all_colors.append(config_info['color'])
                all_labels.append(f"{config_info['label']} - First")
                all_hatches.append("\\\\\\")
                all_alphas.append(STYLE_CONFIG['alpha_first'])
            
            # 添加final数据
            final_times = config_data.get('final_times', [])
            if final_times:
                all_box_data.append(final_times)
                all_positions.append(final_position)
                all_colors.append(config_info['color'])
                all_labels.append(f"{config_info['label']} - Final")
                all_hatches.append('///')
                all_alphas.append(STYLE_CONFIG['alpha_final'])
    
    # 绘制箱线图
    if all_box_data:
        box_parts = ax.boxplot(all_box_data, positions=all_positions, widths=BOX_WIDTH,
                              patch_artist=True, showmeans=True,
                              boxprops=dict(linewidth=STYLE_CONFIG['linewidth']),
                              whiskerprops=dict(linewidth=STYLE_CONFIG['linewidth']),
                              capprops=dict(linewidth=STYLE_CONFIG['linewidth']),
                              medianprops=dict(linewidth=STYLE_CONFIG['median_linewidth'], color='black'),
                              meanprops=dict(marker='D', markerfacecolor='white', 
                                           markeredgecolor='black', markersize=STYLE_CONFIG['mean_marker_size']))
        
        # 设置箱子颜色和样式
        for i, (patch, color, hatch, alpha) in enumerate(zip(box_parts['boxes'], all_colors, all_hatches, all_alphas)):
            patch.set_facecolor(color)
            patch.set_alpha(alpha)
            if hatch:
                patch.set_hatch(hatch)
    
    # ② 设置坐标轴
    ax.set_xlabel('Number of LiqudityPools', fontsize=25)
    ax.set_ylabel('Convergence epoch', fontsize=25)
    ax.set_ylim(0, 220)
    
    # 设置X轴刻度和标签 - 均匀分布5个hub数量
    x_labels = ['2', '3', '4', '5', '10']  # 对应的hub数量标签
    ax.set_xticks(hub_label_positions)
    ax.set_xticklabels(x_labels)
    
    # 设置X轴范围，留出一些边距
    ax.set_xlim(-0.3, 6.3)
    
    ax.yaxis.set_major_locator(MultipleLocator(25))
    ax.tick_params(axis='x', labelsize=25)
    ax.tick_params(axis='y', labelsize=25)
    ax.grid(True, linestyle='--', alpha=0.3, color='gray', axis='y')
    
    # ==================== 分离的图例设计 ====================
    from matplotlib.patches import Patch
    
    # 第一个图例：配置类型（3个元素）
    # 位置：右上角
    config_legend_elements = []
    for config_key, config_info in configs.items():
        config_legend_elements.append(
            Patch(facecolor=config_info['color'], alpha=0.8, 
                  label=config_info['label'])
        )
    
    # 创建第一个图例（配置类型）
    config_legend = ax.legend(handles=config_legend_elements, 
                             loc='upper right',           # 位置：右上角
                             fontsize=20,                 # 字体大小
                             frameon=True,                # 显示边框
                             fancybox=True,               # 圆角边框
                             framealpha=0.9,              # 边框透明度
                             # title='Participant Types',   # 图例标题
                             bbox_to_anchor=(0.58, 1.0),
                             handlelength=0.7, 
                             handletextpad=0.4,
                             title_fontsize=16, borderpad=0.4)           # 标题字体大小
    config_legend.set_alpha(0.5)
    # 第二个图例：收敛类型（2个元素）
    # 位置：右侧中部
    
    from matplotlib.patches import Rectangle
    convergence_legend_elements = [
        Rectangle((0, 0), 1, 1, 
                     facecolor='white',     # 填充颜色
                     edgecolor='red',       # 边框颜色
                     linewidth=2,           # 边框线宽
                     alpha=1, 
                     hatch='\\\\\\',           # 填充图案
                     label='First win'),
        Rectangle((0, 0), 1, 1, 
                     facecolor='white',     # 填充颜色
                     edgecolor='red',       # 边框颜色
                     linewidth=2,           # 边框线宽
                     alpha=1, 
                     hatch='///',           # 填充图案
                     label='Final win')
    ]
    
    # 创建第二个图例（收敛类型）
    convergence_legend = ax.legend(handles=convergence_legend_elements,
                                  loc='upper right',       # 位置：右侧中部
                                  fontsize=20,              # 字体大小
                                  frameon=True,             # 显示边框
                                  fancybox=True,            # 圆角边框
                                  framealpha=0.9,           # 边框透明度
                                  # title='Monopolization Types', # 图例标题
                                  title_fontsize=16,        # 标题字体大小
                                  bbox_to_anchor=(1.0, 1.0),
                                 handlelength=2, 
                                 handletextpad=0.4, borderpad=0.4) # 精确定位（可选）
    # convergence_legend.set_alpha(0.5)

    # 重要：添加第一个图例回到axes上，因为第二个legend会替换第一个
    # 这样两个图例都会同时显示
    ax.add_artist(config_legend)
    # ==================== 分离的图例设计结束 ====================
    
    # 保存图形
    output_path_pdf = os.path.join(output_folder, 'convergence_time_boxplot_csv.pdf')
    output_path_png = os.path.join(output_folder, 'convergence_time_boxplot_csv.png')
    
    plt.tight_layout()
    plt.savefig(output_path_pdf, dpi=300, bbox_inches='tight')
    plt.savefig(output_path_png, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n收敛时间箱线图已生成:")
    print(f"PDF: {output_path_pdf}")
    print(f"PNG: {output_path_png}")
    
    # 打印数据统计
    print("\n=== 数据统计 ===")
    for hub_num in hub_numbers:
        if hub_num in convergence_data:
            print(f"\n{hub_num} Hubs:")
            for config_key, config_info in configs.items():
                data = convergence_data[hub_num].get(config_key, {'first_times': [], 'final_times': []})
                first_count = len(data['first_times'])
                final_count = len(data['final_times'])
                if first_count > 0 or final_count > 0:
                    print(f"  {config_info['label']}: {first_count} first, {final_count} final")

if __name__ == "__main__":
    output_folder = "./0801exper6_csv"
    
    print("开始生成收敛时间箱线图（CSV版本）...")
    print(f"输出文件夹: {output_folder}")
    
    # 生成图表
    plot_convergence_boxplot_csv(output_folder)
    
    print("\n收敛时间箱线图生成完成！")
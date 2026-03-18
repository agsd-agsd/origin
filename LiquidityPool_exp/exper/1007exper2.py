import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import sys
import glob
from matplotlib.ticker import MultipleLocator
from matplotlib.patches import Rectangle
import matplotlib.patches as patches


# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_csv_experiment_data(base_path, experiment_pattern, blacklist_file="./data_blacklist.json"):
    """加载CSV格式的实验数据"""
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
    
    epoch0_path = os.path.join(experiment_folder, "item0", "Broker_result.csv")
    if not os.path.exists(epoch0_path):
        print(f"    缺少epoch0数据: {epoch0_path}")
        return None
    
    try:
        epoch0_df = pd.read_csv(epoch0_path)
        initial_pool_funds = {}
        total_user_funds = 0
        
        for _, row in epoch0_df.iterrows():
            pool_id = row['ID']
            pool_balance = float(row['Balance'])
            initial_pool_funds[pool_id] = pool_balance
            total_user_funds += pool_balance
        
        print(f"    Epoch0: {len(initial_pool_funds)} pools, 总资金: {total_user_funds:.2e}")
        
    except Exception as e:
        print(f"    读取epoch0失败: {e}")
        return None
    
    item_folders = [f for f in os.listdir(experiment_folder) if f.startswith('item') and f[4:].isdigit()]
    item_numbers = sorted([int(f[4:]) for f in item_folders])
    
    for epoch_num in item_numbers:
        item_folder = os.path.join(experiment_folder, f"item{epoch_num}")
        csv_path = os.path.join(item_folder, "Broker_result.csv")
        
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                
                epoch_data = {
                    'epoch': epoch_num,
                    'brokerhubs': [],
                    'initial_pool_funds': initial_pool_funds,
                    'total_user_funds': total_user_funds
                }
                
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
    
    current_funds = 0
    for hub in epoch_data['brokerhubs']:
        if hub['id'] == pool_id:
            current_funds = hub['current_funds']
            break
    
    initial_pool_funds = initial_funds.get(pool_id, 0)
    attracted_funds = current_funds - initial_pool_funds
    
    market_share = (attracted_funds / total_user_funds) * 100
    return max(0, market_share)

def find_first_monopoly_time_csv(data, threshold=90):
    """找到第一次垄断的时间"""
    for epoch_data in data:
        for hub in epoch_data['brokerhubs']:
            pool_id = hub['id']
            market_share = calculate_market_share(epoch_data, pool_id)
            if market_share >= threshold:
                return epoch_data['epoch']
    
    return -1

def find_final_monopoly_time_csv(data, threshold=90):
    """找到最终垄断开始的时间"""
    if not data:
        return -1
    
    final_epoch = data[-1]
    final_monopolist_id = None
    
    for hub in final_epoch['brokerhubs']:
        pool_id = hub['id']
        market_share = calculate_market_share(final_epoch, pool_id)
        if market_share >= threshold:
            final_monopolist_id = pool_id
            break
    
    if final_monopolist_id is None:
        return -1
    
    for i in range(len(data) - 1, -1, -1):
        epoch_data = data[i]
        market_share = calculate_market_share(epoch_data, final_monopolist_id)
        
        if market_share < threshold:
            return data[i + 1]['epoch'] if i + 1 < len(data) else 0
    
    return data[0]['epoch'] if data else 0

def calculate_convergence_times_csv(data_list):
    """计算一组实验的收敛时间"""
    first_times = []
    final_times = []
    
    for data in data_list:
        if not data:
            continue
            
        first_time = find_first_monopoly_time_csv(data, 90)
        if first_time >= 0:
            first_times.append(first_time)
        
        final_time = find_final_monopoly_time_csv(data, 90)
        if final_time >= 0:
            final_times.append(final_time)
    
    return {
        'first_times': first_times,
        'final_times': final_times
    }

def calculate_convergence_times_for_all_configs_csv(output_folder):
    """计算所有配置的收敛时间数据"""
    base_path = os.path.join(os.path.dirname(__file__), "../src/data/processed_data")
    blacklist_file = os.path.join(output_folder, "data_blacklist.json")
    
    print("开始加载所有配置的CSV数据...")
    print(f"数据路径: {base_path}")
    
    convergence_data = {}
    
    print("\n=== 加载2 Hubs数据 ===")
    data_2hubs_hub2 = load_csv_experiment_data(base_path, "2hubs_hub2_20w_300_diff_final_balance", blacklist_file)
    data_2hubs_severe = data_2hubs_hub2
    
    data_2hubs_medium = load_csv_experiment_data(base_path, "2hubs_20w_300_diff_final_balance_medium", blacklist_file)
    data_2hubs_fully = load_csv_experiment_data(base_path, "2hubs_20w_300_diff_final_balance_fully", blacklist_file)
    
    convergence_data[2] = {
        'severe': calculate_convergence_times_csv(data_2hubs_severe),
        'medium': calculate_convergence_times_csv(data_2hubs_medium),
        'fully': calculate_convergence_times_csv(data_2hubs_fully)
    }
    
    hub_configs = [3, 4, 5, 10]
    for num_hubs in hub_configs:
        print(f"\n=== 加载{num_hubs} Hubs数据 ===")
        
        pattern_severe = f"{num_hubs}hubs_20w_300_diff_final_balance"
        data_severe = load_csv_experiment_data(base_path, pattern_severe, blacklist_file)
        
        pattern_medium = f"{num_hubs}hubs_20w_300_diff_final_balance_medium"
        data_medium = load_csv_experiment_data(base_path, pattern_medium, blacklist_file)
        
        pattern_fully = f"{num_hubs}hubs_20w_300_diff_final_balance_fully"
        data_fully = load_csv_experiment_data(base_path, pattern_fully, blacklist_file)
        
        convergence_data[num_hubs] = {
            'severe': calculate_convergence_times_csv(data_severe),
            'medium': calculate_convergence_times_csv(data_medium),
            'fully': calculate_convergence_times_csv(data_fully)
        }
    
    return convergence_data

def plot_convergence_boxplot_csv(output_folder):
    """绘制收敛时间箱线图 - 双Y轴版本"""
    os.makedirs(output_folder, exist_ok=True)
    
    convergence_data = calculate_convergence_times_for_all_configs_csv(output_folder)
    
    # 图片尺寸 4.5×2.5 英寸
    fig, ax = plt.subplots(figsize=(4.5, 2.5))
    
    # 配置信息    
    configs = {
        'severe': {
            'color': '#1f77b4',    # 深蓝色 (原色)
            'color_light': '#aec7e8',   # 浅蓝色
            'label': 'Whale-dominated'
        },
        'medium': {
            'color': '#ff7f0e',    # 深橙色 (原色)
            'color_light': '#ffbb78',   # 浅橙色
            'label': 'Mixed participant'
        }, 
        'fully': {
            'color': '#2ca02c',    # 深绿色 (原色)
            'color_light': '#98df8a',   # 浅绿色
            'label': 'Equal distribution'
        }
    }
    
    # ==================== 调整后的位置布局 ====================
    BOX_WIDTH = 0.35  # ④ 增大箱子尺寸
    BOX_GAP = 0.07
    GROUP_GAP = 0.9
    
    # ③ 缩小区域间隔
    REGION_STARTS = {
        'severe': 0,
        'medium': 4.6,   # 从5.5改为5.0
        'fully': 9.3    # 从11改为10.0
    }
    
    hub_numbers = [2, 3, 4, 5, 10]
    
    STYLE_CONFIG = {
        'linewidth': 1.0,
        'alpha_first': 0.9,
        'alpha_final': 0.9,
        'median_linewidth': 1,
        'mean_marker_size': 2
    }
    # ========================================================
    
    # 分别收集first和final的数据
    first_box_data = []
    first_positions = []
    first_colors = []
    first_alphas = []
    
    final_box_data = []
    final_positions = []
    final_colors = []
    final_alphas = []
    
    region_x_ranges = {}
    
    # 按配置类型组织数据
    for config_key, config_info in configs.items():
        region_start = REGION_STARTS[config_key]
        region_positions = []
        
        for i, hub_num in enumerate(hub_numbers):
            if hub_num not in convergence_data:
                continue
            
            config_data = convergence_data[hub_num].get(config_key, {'first_times': [], 'final_times': []})
            
            group_x = region_start + i * GROUP_GAP
            first_x = group_x - BOX_WIDTH/2 - BOX_GAP/2
            final_x = group_x + BOX_WIDTH/2 + BOX_GAP/2
            
            # First数据（右Y轴）
            first_times = config_data.get('first_times', [])
            if first_times:
                first_box_data.append(first_times)
                first_positions.append(first_x)
                first_colors.append(config_info['color_light'])
                first_alphas.append(STYLE_CONFIG['alpha_first'])
            
            # Final数据（左Y轴）
            final_times = config_data.get('final_times', [])
            if final_times:
                final_box_data.append(final_times)
                final_positions.append(final_x)
                final_colors.append(config_info['color'])
                final_alphas.append(STYLE_CONFIG['alpha_final'])
            
            region_positions.append(group_x)
        
        if region_positions:
            region_x_ranges[config_key] = {
                'start': min(region_positions) - GROUP_GAP/2,
                'end': max(region_positions) + GROUP_GAP/2,
                'center': (min(region_positions) + max(region_positions)) / 2,
                'positions': region_positions
            }
    
    # ==================== ② 创建双Y轴并分别绘制 ====================
    # 左Y轴（ax）：Final Win
    if final_box_data:
        box_parts_final = ax.boxplot(final_box_data, positions=final_positions, widths=BOX_WIDTH,
                                     patch_artist=True, showmeans=True,
                                     boxprops=dict(linewidth=STYLE_CONFIG['linewidth']),
                                     whiskerprops=dict(linewidth=STYLE_CONFIG['linewidth']),
                                     capprops=dict(linewidth=STYLE_CONFIG['linewidth']),
                                     medianprops=dict(linewidth=STYLE_CONFIG['median_linewidth'], color='black'),
                                     meanprops=dict(marker='D', markerfacecolor='white', 
                                                  markeredgecolor='black', markersize=STYLE_CONFIG['mean_marker_size']),
                                     flierprops=dict(marker='o',           # 标记样式
                                       markersize=2,          # 大小
                                       markerfacecolor='white', # 填充颜色
                                       markeredgecolor='black', # 边框颜色
                                       alpha=1))            # 透明度)
        
        for patch, color, alpha in zip(box_parts_final['boxes'], final_colors, final_alphas):
            patch.set_facecolor(color)
            patch.set_alpha(alpha)
            patch.set_hatch('///')
    
    # 创建右Y轴
    ax2 = ax.twinx()
    
    # 右Y轴（ax2）：First Win
    if first_box_data:
        box_parts_first = ax2.boxplot(first_box_data, positions=first_positions, widths=BOX_WIDTH,
                                      patch_artist=True, showmeans=True,
                                      boxprops=dict(linewidth=STYLE_CONFIG['linewidth']),
                                      whiskerprops=dict(linewidth=STYLE_CONFIG['linewidth']),
                                      capprops=dict(linewidth=STYLE_CONFIG['linewidth']),
                                      medianprops=dict(linewidth=STYLE_CONFIG['median_linewidth'], color='black'),
                                      meanprops=dict(marker='D', markerfacecolor='white', 
                                                   markeredgecolor='black', markersize=STYLE_CONFIG['mean_marker_size']),
                                     flierprops=dict(marker='o',           # 标记样式
                                       markersize=2,          # 大小
                                       markerfacecolor='white', # 填充颜色
                                       markeredgecolor='black', # 边框颜色
                                       alpha=1))
        
        for patch, color, alpha in zip(box_parts_first['boxes'], first_colors, first_alphas):
            patch.set_facecolor(color)
            patch.set_alpha(alpha)
            patch.set_hatch('\\\\\\')
    # ================================================================
    


    # 添加背景色和区域标签
    for config_key, config_info in configs.items():
        if config_key in region_x_ranges:
            x_range = region_x_ranges[config_key]
            
            # 添加背景色
            ax.axvspan(x_range['start'], x_range['end'], 
                      color=config_info['color'], alpha=0.05, zorder=0)
            
            # 在背景区域顶部添加标签
            ax.text(x_range['center'], 10,  # y坐标（根据你的ylim=210调整）
                   config_info['label'], 
                   fontsize=7, ha='center', va='top', 
                   fontweight='bold',color=config_info['color'])

   
    # 在框内添加文字        
    # ax.text(6.5, 200, '                    100% → Monopoly                    ', 
    ax.text(6.5, 200, '          100% convergence to monopoly          ', 
                   fontsize=10, ha='center', va='bottom',
                   bbox=dict(boxstyle='round,pad=0.1', facecolor='white', alpha=0.5))
    
    # ==================== 设置坐标轴 ====================
    # 左Y轴（Final Win）
    ax.set_ylabel('Final win conv. epoch', fontsize=13, color='darkblue')
    ax.set_ylim(-5, 220)
    ax.yaxis.set_major_locator(MultipleLocator(25))
    ax.tick_params(axis='y', labelsize=11, colors='darkblue')
    
    # 右Y轴（First Win）
    ax2.set_ylabel('First win conv. epoch', fontsize=13, color='darkred')
    ax2.set_ylim(-0.5, 24)
    ax2.yaxis.set_major_locator(MultipleLocator(5))
    ax2.tick_params(axis='y', labelsize=11, colors='darkred')
    
    # ① X轴范围缩小右边距
    ax.set_xlim(-0.5, 13.5)  # 从15.5改为14.5
    
    ax.set_xticks([])
    ax.set_xlabel('')
    
    # 双层X轴标签
    # for config_key, config_info in configs.items():
        # if config_key in region_x_ranges:
            # x_center = region_x_ranges[config_key]['center']
            # ax.text(x_center, -35, config_info['label'], 
    ax.text(region_x_ranges["medium"]['center'], -30, "Number of LiquidityPools", 
           fontsize=11, ha='center', va='top', fontweight='bold')
    
                   
    for config_key in region_x_ranges:
        positions = region_x_ranges[config_key]['positions']
        for i, (hub_num, x_pos) in enumerate(zip(hub_numbers, positions)):
            ax.text(x_pos, -10,  # ← y坐标从-15改为-10，因为上面标签没了
                   str(hub_num), 
                   fontsize=10, ha='center', va='top', fontweight='bold')
    
    ax.grid(True, linestyle='--', alpha=0.3, color='gray', axis='y')
    # ===================================================
    
    # 图例
    convergence_legend_elements = [
        Rectangle((0, 0), 1, 1, 
                 facecolor='white', edgecolor='darkred', linewidth=1,
                 alpha=1, hatch='\\\\\\', label='First win'),
        Rectangle((0, 0), 1, 1, 
                 facecolor='white', edgecolor='darkblue', linewidth=1,
                 alpha=1, hatch='///', label='Final win')
    ]
    
    convergence_legend = ax.legend(handles=convergence_legend_elements,
                                  loc='upper right', fontsize=10,
                                  frameon=True, fancybox=True, framealpha=0.9,
                                  bbox_to_anchor=(0.8, 0.9),
                                  handlelength=1.5, handletextpad=0.4, borderpad=0.4)
    
    # 保存图形
    output_path_pdf = os.path.join(output_folder, '1007exper2_convergence_boxplot.pdf')
    output_path_png = os.path.join(output_folder, '1007exper2_convergence_boxplot.png')
    
    # plt.tight_layout()
    # plt.tight_layout(rect=[0, 0, 1, 1])
    plt.subplots_adjust(top=1, bottom=0.15)
    
    plt.savefig(output_path_pdf, dpi=300, bbox_inches='tight', pad_inches=0.05)
    plt.savefig(output_path_png, dpi=300, bbox_inches='tight', pad_inches=0.05)
    plt.close()
    
    print(f"\n收敛时间箱线图已生成:")
    print(f"PDF: {output_path_pdf}")
    print(f"PNG: {output_path_png}")

if __name__ == "__main__":
    output_folder = "./1007exper2"
    
    print("开始生成收敛时间箱线图（双Y轴版本）...")
    print(f"输出文件夹: {output_folder}")
    
    plot_convergence_boxplot_csv(output_folder)
    
    print("\n收敛时间箱线图生成完成！")
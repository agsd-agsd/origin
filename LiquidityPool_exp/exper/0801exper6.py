import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys
import glob
from matplotlib.ticker import MultipleLocator

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_blacklist(blacklist_file):
    """加载黑名单文件"""
    if os.path.exists(blacklist_file):
        try:
            with open(blacklist_file, 'r') as f:
                blacklist = json.load(f)
            print(f"已加载黑名单文件: {blacklist_file}")
            return blacklist
        except Exception as e:
            print(f"加载黑名单文件失败: {e}")
            return {}
    else:
        print(f"黑名单文件不存在: {blacklist_file}")
        return {}

def load_experiment_data_with_blacklist(base_path, experiment_pattern, num_files=None, blacklist_file="./data_blacklist.json"):
    """使用黑名单机制加载实验数据（简化版，只包含加载逻辑）"""
    blacklist = load_blacklist(blacklist_file)
    
    # 获取文件列表
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
    
    valid_data_list = []
    invalid_count = 0
    
    print(f"处理 {experiment_pattern} 数据...")
    
    # 检查是否已有黑名单
    if experiment_pattern in blacklist:
        print(f"  使用现有黑名单，包含 {len(blacklist[experiment_pattern])} 个无效实验")
        print(f"  非黑名单文件将直接加载，不进行验证")
        
        for file_idx, filepath in enumerate(experiment_files):
            file_number = file_idx + 1
            
            if file_number in blacklist[experiment_pattern]:
                invalid_count += 1
                print(f"  实验 {file_number}: ✗ 黑名单中 - 已跳过")
                continue
            
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                valid_data_list.append(data)
                print(f"  实验 {file_number}: ✓ 已加载（信任）")
            except Exception as e:
                invalid_count += 1
                print(f"  实验 {file_number}: ✗ 加载失败: {e}")
    else:
        print(f"  未找到黑名单，直接加载所有文件...")
        for filepath in experiment_files:
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                valid_data_list.append(data)
            except Exception as e:
                print(f"加载文件 {filepath} 时出错: {e}")
    
    print(f"完成: {len(valid_data_list)} 个有效实验, {invalid_count} 个无效实验")
    return valid_data_list

def find_first_monopoly_time(data, threshold=90):
    """找到第一次垄断的时间"""
    for epoch_idx, epoch_data in enumerate(data):
        total_market = 0
        
        # 计算总市场
        for volunteer in epoch_data['volunteers']:
            if volunteer['current_brokerhub'] is None:
                total_market += float(volunteer['balance'])
        
        for hub in epoch_data['brokerhubs']:
            total_market += float(hub['current_funds'])
        
        # 检查是否有hub达到垄断阈值
        if total_market > 0:
            for hub in epoch_data['brokerhubs']:
                hub_share = float(hub['current_funds']) / total_market * 100
                if hub_share >= threshold:
                    return epoch_idx
    
    return -1  # 没有垄断

def find_final_monopoly_time(data, threshold=90):
    """找到最终垄断开始的时间"""
    if not data:
        return -1
    
    # 检查最终状态是否为垄断
    final_epoch = data[-1]
    total_market = 0
    
    for volunteer in final_epoch['volunteers']:
        if volunteer['current_brokerhub'] is None:
            total_market += float(volunteer['balance'])
    
    for hub in final_epoch['brokerhubs']:
        total_market += float(hub['current_funds'])
    
    final_monopolist_id = None
    if total_market > 0:
        for hub in final_epoch['brokerhubs']:
            hub_share = float(hub['current_funds']) / total_market * 100
            if hub_share >= threshold:
                final_monopolist_id = hub['id']
                break
    
    if final_monopolist_id is None:
        return -1  # 最终状态不是垄断
    
    # 从后往前找到这个垄断者开始连续垄断的时间点
    for epoch_idx in range(len(data) - 1, -1, -1):
        epoch_data = data[epoch_idx]
        total_market = 0
        
        for volunteer in epoch_data['volunteers']:
            if volunteer['current_brokerhub'] is None:
                total_market += float(volunteer['balance'])
        
        for hub in epoch_data['brokerhubs']:
            total_market += float(hub['current_funds'])
        
        is_monopoly = False
        if total_market > 0:
            for hub in epoch_data['brokerhubs']:
                if hub['id'] == final_monopolist_id:
                    hub_share = float(hub['current_funds']) / total_market * 100
                    if hub_share >= threshold:
                        is_monopoly = True
                    break
        
        if not is_monopoly:
            return epoch_idx + 1
    
    return 0  # 从头开始就是垄断

def calculate_convergence_times_for_all_configs(output_folder):
    """计算所有配置的收敛时间数据"""
    # 数据路径
    base_path = os.path.join(os.path.dirname(__file__), "../result/output")
    blacklist_file = os.path.join(output_folder, "data_blacklist.json")
    
    print("开始加载所有配置的数据...")
    
    # 数据结构：{hub_count: {config: [first_times, final_times]}}
    convergence_data = {}
    
    # 加载2 hubs的三种配置
    print("\n=== 加载2 Hubs数据 ===")
    
    # 2 hubs - severe配置
    data_2hubs_hub1 = load_experiment_data_with_blacklist(base_path, "2hubs_hub1_20w_300_diff_final_balance", 10, blacklist_file)
    data_2hubs_hub2 = load_experiment_data_with_blacklist(base_path, "2hubs_hub2_20w_300_diff_final_balance", 10, blacklist_file)
    data_2hubs_severe = data_2hubs_hub1 + data_2hubs_hub2
    
    # 2 hubs - medium配置
    data_2hubs_medium = load_experiment_data_with_blacklist(base_path, "2hubs_20w_300_diff_final_balance_medium", 5, blacklist_file)
    
    # 2 hubs - fully配置
    data_2hubs_fully = load_experiment_data_with_blacklist(base_path, "2hubs_20w_300_diff_final_balance_fully", 5, blacklist_file)
    
    convergence_data[2] = {
        'severe': calculate_convergence_times(data_2hubs_severe),
        'medium': calculate_convergence_times(data_2hubs_medium),
        'fully': calculate_convergence_times(data_2hubs_fully)
    }
    
    # 加载其他hub数量的数据（目前只有severe配置）
    hub_configs = [3, 4, 5, 10]
    for num_hubs in hub_configs:
        print(f"\n=== 加载{num_hubs} Hubs数据 ===")
        pattern = f"{num_hubs}hubs_20w_300_diff_final_balance"
        data_severe = load_experiment_data_with_blacklist(base_path, pattern, None, blacklist_file)
        
        convergence_data[num_hubs] = {
            'severe': calculate_convergence_times(data_severe),
            'medium': {'first_times': [], 'final_times': []},  # 空数据
            'fully': {'first_times': [], 'final_times': []}    # 空数据
        }
    
    return convergence_data

def calculate_convergence_times(data_list):
    """计算一组实验的收敛时间"""
    first_times = []
    final_times = []
    
    for data in data_list:
        if not data:
            continue
            
        # 计算第一次垄断时间
        first_time = find_first_monopoly_time(data, 90)
        if first_time >= 0:
            first_times.append(first_time)
        
        # 计算最终垄断时间
        final_time = find_final_monopoly_time(data, 90)
        if final_time >= 0:
            final_times.append(final_time)
    
    return {
        'first_times': first_times,
        'final_times': final_times
    }

def plot_convergence_boxplot(output_folder):
    """绘制收敛时间箱线图"""
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    # 获取收敛时间数据
    convergence_data = calculate_convergence_times_for_all_configs(output_folder)
    
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
    
    # ==================== 辅助柱状图 - 用于位置调试 ====================
    # 绘制所有可能位置的辅助柱子
    
    # ==================== 辅助柱状图结束 ====================
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
                all_hatches.append(None)
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
    ax.set_ylim(0, 150)
    
    # 设置X轴刻度和标签 - 均匀分布5个hub数量
    # x_positions = [1, 2, 3, 4, 5]  # 对应位置
    x_labels = ['2', '3', '4', '5', '10']  # 对应的hub数量标签
    ax.set_xticks(hub_label_positions)
    ax.set_xticklabels(x_labels)
    
    
    # 设置X轴范围，留出一些边距
    ax.set_xlim(-0.3, 6.3)
    
    ax.yaxis.set_major_locator(MultipleLocator(25))
    ax.tick_params(axis='x', labelsize=25)
    ax.tick_params(axis='y', labelsize=25)
    ax.grid(True, linestyle='--', alpha=0.3, color='gray', axis='y')
    
    # 创建图例
    from matplotlib.patches import Patch
    
    legend_elements = []
    
    # 配置类型图例
    for config_key, config_info in configs.items():
        legend_elements.append(Patch(facecolor=config_info['color'], alpha=0.8, 
                                   label=config_info['label']))
    
    # 收敛类型图例  
    legend_elements.extend([
        Patch(facecolor='gray', alpha=0.7, label='First Monopolization'),
        Patch(facecolor='gray', alpha=0.9, hatch='///', label='Final Monopolization')
    ])
    
    ax.legend(handles=legend_elements, loc='upper right', fontsize=15, 
             frameon=True, fancybox=True, framealpha=0.9)
    
    # 保存图形
    output_path_pdf = os.path.join(output_folder, 'convergence_time_boxplot.pdf')
    output_path_png = os.path.join(output_folder, 'convergence_time_boxplot.png')
    
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
    output_folder = "./0801exper6"
    
    print("开始生成收敛时间箱线图...")
    print(f"输出文件夹: {output_folder}")
    
    # 生成图表
    plot_convergence_boxplot(output_folder)
    
    print("\n收敛时间箱线图生成完成！")
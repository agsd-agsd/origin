import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json
import os
import glob
from matplotlib.patches import Rectangle
from matplotlib.ticker import MultipleLocator
import warnings
warnings.filterwarnings('ignore')

def calculate_tier_statistics(tier_data):
    """计算tier数据的统计信息"""
    if not tier_data or len(tier_data) == 0:
        return {
            'count': 0,
            'median': 0,
            'mean': 0,
            'std': 0,
            'q25': 0,
            'q75': 0,
            'min': 0,
            'max': 0,
            'above_threshold': 0,
            'above_threshold_pct': 0
        }
    
    # 过滤掉过小的值
    valid_data = [x for x in tier_data if x > 0.001]
    
    if len(valid_data) == 0:
        return {
            'count': 0,
            'median': 0,
            'mean': 0,
            'std': 0,
            'q25': 0,
            'q75': 0,
            'min': 0,
            'max': 0,
            'above_threshold': 0,
            'above_threshold_pct': 0
        }
    
    # 计算有意义收益（>0.5%）的比例
    above_threshold = sum(1 for x in valid_data if x >= 0.5)
    above_threshold_pct = (above_threshold / len(valid_data)) * 100
    
    return {
        'count': len(valid_data),
        'median': np.median(valid_data),
        'mean': np.mean(valid_data),
        'std': np.std(valid_data),
        'q25': np.percentile(valid_data, 25),
        'q75': np.percentile(valid_data, 75),
        'min': np.min(valid_data),
        'max': np.max(valid_data),
        'above_threshold': above_threshold,
        'above_threshold_pct': above_threshold_pct
    }

def print_comprehensive_statistics(all_data):
    """打印完整的统计数据"""
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE REVENUE STATISTICS")
    print("="*80)
    
    tier_names = {
        'whale': 'Whale (≥20 ETH)',
        'medium': 'Medium (0.5-20 ETH)',
        'minnow': 'Minnow (<0.5 ETH)'
    }
    
    for config_key in ['whale_dominated', 'mixed', 'equal']:
        config_info = all_data[config_key]['info']
        print(f"\n{'─'*80}")
        print(f"🔹 Configuration: {config_info['name'].upper()}")
        print(f"{'─'*80}")
        
        for tier in ['whale', 'medium', 'minnow']:
            print(f"\n  📌 {tier_names[tier]}")
            print(f"  {'-'*76}")
            
            # Without LP statistics
            without_data = all_data[config_key]['without'][tier]
            without_stats = calculate_tier_statistics(without_data)
            
            # With LP statistics
            with_data = all_data[config_key]['with'][tier]
            with_stats = calculate_tier_statistics(with_data)
            
            print(f"  {'Metric':<25} {'Without LP':<20} {'With LP':<20} {'Change':<15}")
            print(f"  {'-'*76}")
            print(f"  {'Sample Count':<25} {without_stats['count']:<20} {with_stats['count']:<20}")
            print(f"  {'Median (%)':<25} {without_stats['median']:<20.4f} {with_stats['median']:<20.4f} {with_stats['median']-without_stats['median']:+.4f}")
            print(f"  {'Mean (%)':<25} {without_stats['mean']:<20.4f} {with_stats['mean']:<20.4f} {with_stats['mean']-without_stats['mean']:+.4f}")
            print(f"  {'Std Dev (%)':<25} {without_stats['std']:<20.4f} {with_stats['std']:<20.4f}")
            print(f"  {'Q25 (%)':<25} {without_stats['q25']:<20.4f} {with_stats['q25']:<20.4f}")
            print(f"  {'Q75 (%)':<25} {without_stats['q75']:<20.4f} {with_stats['q75']:<20.4f}")
            print(f"  {'Min (%)':<25} {without_stats['min']:<20.4f} {with_stats['min']:<20.4f}")
            print(f"  {'Max (%)':<25} {without_stats['max']:<20.4f} {with_stats['max']:<20.4f}")
            print(f"  {'-'*76}")
            print(f"  {'Above 0.5% threshold':<25} {without_stats['above_threshold_pct']:<20.2f}% {with_stats['above_threshold_pct']:<20.2f}%")
    
    # Print summary for the "94%" claim
    print(f"\n{'='*80}")
    print("🎯 KEY FINDING - MINNOW PARTICIPATION RATE")
    print(f"{'='*80}")
    
    for config_key in ['whale_dominated', 'mixed', 'equal']:
        config_info = all_data[config_key]['info']
        
        without_data = all_data[config_key]['without']['minnow']
        without_stats = calculate_tier_statistics(without_data)
        
        with_data = all_data[config_key]['with']['minnow']
        with_stats = calculate_tier_statistics(with_data)
        
        print(f"\n{config_info['name']}:")
        print(f"  Without LP: {without_stats['above_threshold_pct']:.2f}% of minnows earn >0.5%")
        print(f"  With LP:    {with_stats['above_threshold_pct']:.2f}% of minnows earn >0.5%")
        print(f"  Improvement: {with_stats['above_threshold_pct'] - without_stats['above_threshold_pct']:+.2f} percentage points")

def load_tier_classification(base_path, config_name=""):
    """从epoch 0建立tier分类标准 - 按固定ETH金额阈值"""
    item0_path = os.path.join(base_path, "item0", "b2e_test_results.json")
    
    if not os.path.exists(item0_path):
        raise FileNotFoundError(f"缺失文件: {item0_path}")
    
    with open(item0_path, 'r') as f:
        data = json.load(f)[0]
    
    whale_ids = set()
    medium_ids = set()
    minnow_ids = set()
    
    WHALE_THRESHOLD = 20e18
    MINNOW_THRESHOLD = 0.5e18
    
    funds_list = []
    
    for id_str, funds in data['original_funds'].items():
        if 'BrokerHub' in id_str:
            continue
        
        funds_float = float(funds)
        funds_eth = funds_float / 1e18
        funds_list.append(funds_eth)
        
        if funds_float >= WHALE_THRESHOLD:
            whale_ids.add(id_str)
        elif funds_float >= MINNOW_THRESHOLD:
            medium_ids.add(id_str)
        else:
            minnow_ids.add(id_str)
    
    print(f"\n{'='*60}")
    print(f"配置: {config_name}")
    print(f"{'='*60}")
    print(f"分层标准 (ETH阈值):")
    print(f"  Whale (≥20 ETH):     {len(whale_ids):4d} 个")
    print(f"  Medium (0.5-20 ETH): {len(medium_ids):4d} 个")
    print(f"  Minnow (<0.5 ETH):   {len(minnow_ids):4d} 个")
    
    if funds_list:
        print(f"\n账户资金分布:")
        print(f"  最大值: {max(funds_list):.4f} ETH")
        print(f"  最小值: {min(funds_list):.6f} ETH")
        print(f"  平均值: {np.mean(funds_list):.4f} ETH")
        print(f"  中位数: {np.median(funds_list):.4f} ETH")
    
    return {'whale': whale_ids, 'medium': medium_ids, 'minnow': minnow_ids}

def load_without_pool_data(base_path, tier_classification, config_name, start_epoch=250, end_epoch=300):
    """加载Without Pool数据"""
    tier_revenues = {'whale': [], 'medium': [], 'minnow': []}
    
    abnormal_data = []
    
    for epoch in range(start_epoch, end_epoch):
        item_path = os.path.join(base_path, f"item{epoch}", "b2e_test_results.json")
        
        if not os.path.exists(item_path):
            continue
        
        with open(item_path, 'r') as f:
            data = json.load(f)[0]
        
        for id_str, rate in data.get('rates', {}).items():
            if 'BrokerHub' in id_str:
                continue
            
            revenue_ratio_pct = float(rate) * 100
            
            if revenue_ratio_pct > 100:
                abnormal_data.append({
                    'config': config_name,
                    'type': 'Without Pool',
                    'epoch': epoch,
                    'id': id_str,
                    'revenue_ratio': revenue_ratio_pct,
                    'file': item_path
                })
            
            if id_str in tier_classification['whale']:
                tier_revenues['whale'].append(revenue_ratio_pct)
            elif id_str in tier_classification['medium']:
                tier_revenues['medium'].append(revenue_ratio_pct)
            elif id_str in tier_classification['minnow']:
                tier_revenues['minnow'].append(revenue_ratio_pct)
    
    if abnormal_data:
        print(f"\n⚠️ {config_name} - Without Pool 发现异常收益率 (>100%):")
        for item in abnormal_data[:5]:
            print(f"   Epoch {item['epoch']}, ID={item['id']}, Revenue={item['revenue_ratio']:.2f}%")
        if len(abnormal_data) > 5:
            print(f"   ... 共 {len(abnormal_data)} 条异常数据")
    
    return tier_revenues

def calculate_market_share_csv(epoch_data, pool_id):
    """计算pool的市场份额"""
    if 'initial_pool_funds' not in epoch_data or 'total_user_funds' not in epoch_data:
        return 0
    
    total_user_funds = epoch_data['total_user_funds']
    if total_user_funds == 0:
        return 0
    
    current_funds = 0
    for hub in epoch_data['brokerhubs']:
        if hub['id'] == pool_id:
            current_funds = hub['current_funds']
            break
    
    initial_pool_funds = epoch_data['initial_pool_funds'].get(pool_id, 0)
    attracted_funds = current_funds - initial_pool_funds
    
    return max(0, (attracted_funds / total_user_funds) * 100)

def find_final_monopoly_csv(csv_base_path, experiment_pattern, threshold=90):
    """从CSV数据找到Final Win epoch"""
    pattern = f"{experiment_pattern}*"
    folders = glob.glob(os.path.join(csv_base_path, pattern))
    folders = sorted([f for f in folders if os.path.isdir(f)])
    
    if not folders:
        return 200
    
    folder_path = folders[0]
    
    epoch0_path = os.path.join(folder_path, "item0", "Broker_result.csv")
    if not os.path.exists(epoch0_path):
        return 200
    
    epoch0_df = pd.read_csv(epoch0_path)
    initial_pool_funds = {}
    total_user_funds = 0
    
    for _, row in epoch0_df.iterrows():
        pool_id = row['ID']
        pool_balance = float(row['Balance'])
        initial_pool_funds[pool_id] = pool_balance
        total_user_funds += pool_balance
    
    epoch_data_list = []
    for epoch_num in range(300):
        csv_path = os.path.join(folder_path, f"item{epoch_num}", "Broker_result.csv")
        
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            epoch_data = {
                'epoch': epoch_num,
                'brokerhubs': [],
                'initial_pool_funds': initial_pool_funds,
                'total_user_funds': total_user_funds
            }
            
            for _, row in df.iterrows():
                epoch_data['brokerhubs'].append({
                    'id': row['ID'],
                    'current_funds': float(row['Balance'])
                })
            
            epoch_data_list.append(epoch_data)
    
    if not epoch_data_list:
        return 200
    
    final_epoch = epoch_data_list[-1]
    final_monopolist_id = None
    
    for hub in final_epoch['brokerhubs']:
        pool_id = hub['id']
        market_share = calculate_market_share_csv(final_epoch, pool_id)
        if market_share >= threshold:
            final_monopolist_id = pool_id
            break
    
    if final_monopolist_id is None:
        return 200
    
    for i in range(len(epoch_data_list) - 1, -1, -1):
        epoch_data = epoch_data_list[i]
        market_share = calculate_market_share_csv(epoch_data, final_monopolist_id)
        
        if market_share < threshold:
            return epoch_data_list[i + 1]['epoch'] if i + 1 < len(epoch_data_list) else 0
    
    return epoch_data_list[0]['epoch'] if epoch_data_list else 0

def load_with_pool_data(json_base_path, csv_base_path, experiment_pattern, csv_pattern, tier_classification, config_name, num_files=5):
    """加载With Pool数据"""
    pattern = f"simulation_results_{experiment_pattern}*.json"
    files = glob.glob(os.path.join(json_base_path, pattern))
    files = sorted(files)[:num_files]
    
    if not files:
        raise FileNotFoundError(f"缺失文件: {os.path.join(json_base_path, pattern)}")
    
    final_win_epoch = find_final_monopoly_csv(csv_base_path, csv_pattern)
    
    start_epoch = final_win_epoch
    end_epoch = min(final_win_epoch + 50, 300)
    
    tier_revenues = {'whale': [], 'medium': [], 'minnow': []}
    
    abnormal_data = []
    
    for filepath in files:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        for epoch_data in data:
            epoch_num = int(epoch_data.get('epoch', -1))
            
            if epoch_num < start_epoch or epoch_num >= end_epoch:
                continue
            
            for vol in epoch_data.get('volunteers', []):
                vol_id = str(vol.get('id'))
                revenue_rate = float(vol.get('revenue_rate', 0))
                revenue_ratio_pct = revenue_rate * 100
                
                if revenue_ratio_pct > 100:
                    abnormal_data.append({
                        'config': config_name,
                        'type': 'With Pool',
                        'epoch': epoch_num,
                        'id': vol_id,
                        'revenue_ratio': revenue_ratio_pct,
                        'file': filepath
                    })
                
                if vol_id in tier_classification['whale']:
                    tier_revenues['whale'].append(revenue_ratio_pct)
                elif vol_id in tier_classification['medium']:
                    tier_revenues['medium'].append(revenue_ratio_pct)
                elif vol_id in tier_classification['minnow']:
                    tier_revenues['minnow'].append(revenue_ratio_pct)
    
    if abnormal_data:
        print(f"\n⚠️ {config_name} - With Pool 发现异常收益率 (>100%):")
        for item in abnormal_data[:5]:
            print(f"   Epoch {item['epoch']}, ID={item['id']}, Revenue={item['revenue_ratio']:.2f}%")
        if len(abnormal_data) > 5:
            print(f"   ... 共 {len(abnormal_data)} 条异常数据")
    
    return tier_revenues

def plot_empty_marker(ax, position, width, color, edge_color):
    """绘制空数据标记"""
    line_width = width * 0.6
    ax.plot([position - line_width/2, position + line_width/2], 
           [0, 0], 
           color=edge_color, 
           linewidth=3, 
           linestyle='-',
           marker='|',
           markersize=10,
           markeredgewidth=2,
           alpha=0.8,
           zorder=10)
    
    rect = Rectangle((position - width/2, -0.3), width, 0.6,
                     facecolor='lightgray', 
                     edgecolor="black",
                     linewidth=1,
                     alpha=0.3,
                     linestyle='--')
    ax.add_patch(rect)

def plot_single_tier_violins(ax, tier_data, positions_base, width, config_keys, all_data, tier, isBottom):
    """在指定ax上绘制单个tier的所有violins"""
    base_pos = positions_base
    
    for config_idx, config_key in enumerate(config_keys):
        config_data = all_data[config_key]
        config_info = config_data['info']
        
        offset = (config_idx - 1) * width * 2.5
        pos_without = base_pos + offset - width/2
        pos_with = base_pos + offset + width/2
        
        # ========== Without Pool ==========
        data_w_out = [x for x in config_data['without'][tier] if x > 0.001]
        
        if data_w_out:
            parts_without = ax.violinplot([data_w_out], positions=[pos_without], 
                                         widths=width, showmeans=False, showmedians=True)
            
            for pc in parts_without['bodies']:
                pc.set_facecolor(config_info['color_without'])
                pc.set_edgecolor(config_info['edge'])
                pc.set_linewidth(1.2)
                pc.set_alpha(0.7)
            
            for partname in ('cbars', 'cmins', 'cmaxes', 'cmedians'):
                if partname in parts_without:
                    vp = parts_without[partname]
                    vp.set_edgecolor(config_info['edge'])
                    if partname == 'cmedians':
                        vp.set_linewidth(2)
        else:
            if(isBottom):
                plot_empty_marker(ax, pos_without, width, 
                            config_info['color_without'], 
                            config_info['color_without'])
        
        # ========== With Pool ==========
        data_w_in = [x for x in config_data['with'][tier] if x > 0.001]
        
        if data_w_in:
            parts_with = ax.violinplot([data_w_in], positions=[pos_with],
                                      widths=width, showmeans=False, showmedians=True)
            
            for pc in parts_with['bodies']:
                pc.set_facecolor(config_info['color_with'])
                pc.set_edgecolor(config_info['edge'])
                pc.set_linewidth(1.2)
                pc.set_alpha(0.9)
            
            for partname in ('cbars', 'cmins', 'cmaxes', 'cmedians'):
                if partname in parts_with:
                    vp = parts_with[partname]
                    vp.set_edgecolor(config_info['edge'])
                    if partname == 'cmedians':
                        vp.set_linewidth(2)
        else:
            if(isBottom):
                plot_empty_marker(ax, pos_with, width,
                            config_info['color_with'],
                            config_info['color_with'])

def plot_revenue_tier_comparison(output_folder):
    """绘制Figure 3(b) - 断轴版本（修复版）"""
    os.makedirs(output_folder, exist_ok=True)
    
    BREAK_LOWER = 6
    BREAK_UPPER = 10
    UPPER_MAX = 450
    LOWER_TICK_INTERVAL = 2
    UPPER_TICK_INTERVAL = 200
    HEIGHT_RATIO = [1, 2]
    
    configs = {
        'whale_dominated': {
            'name': 'Whale-dominated',
            'without_path': 'without_trump_20w_300_diff_final_balance',
            'with_json': '2hubs_20w_300_diff_final_balance',
            'with_csv': '2hubs_hub2_20w_300_diff_final_balance',
            'color_without': '#aec7e8',
            'color_with': '#1f77b4',
            'edge': 'black'
        },
        'mixed': {
            'name': 'Mixed participant',
            'without_path': 'without_2hubs_20w_300_diff_final_balance_medium1',
            'with_json': '2hubs_20w_300_diff_final_balance_medium',
            'with_csv': '2hubs_20w_300_diff_final_balance_medium',
            'color_without': '#ffbb78',
            'color_with': '#ff7f0e',
            'edge': 'black'
        },
        'equal': {
            'name': 'Equal distribution',
            'without_path': 'without_2hubs_20w_300_diff_final_balance_fully1',
            'with_json': '2hubs_20w_300_diff_final_balance_fully',
            'with_csv': '2hubs_20w_300_diff_final_balance_fully',
            'color_without': '#98df8a',
            'color_with': '#2ca02c',
            'edge': 'black'
        }
    }
    
    witouthub_base = os.path.join(os.path.dirname(__file__), "../src/data/processed_data/witouthub")
    json_base = os.path.join(os.path.dirname(__file__), "../result/output")
    csv_base = os.path.join(os.path.dirname(__file__), "../src/data/processed_data")
    
    all_data = {}
    
    for config_key, config_info in configs.items():
        without_pool_path = os.path.join(witouthub_base, config_info['without_path'])
        
        tier_classification = load_tier_classification(without_pool_path, config_info['name'])
        
        data_without = load_without_pool_data(without_pool_path, tier_classification, 
                                             config_info['name'], 250, 300)
        
        data_with = load_with_pool_data(json_base, csv_base, 
                                       config_info['with_json'],
                                       config_info['with_csv'],
                                       tier_classification,
                                       config_info['name'],
                                       num_files=5)
        
        all_data[config_key] = {
            'without': data_without,
            'with': data_with,
            'info': config_info,
            'tier_classification': tier_classification
        }
    
    # 🔥 在这里调用统计打印函数 🔥
    print_comprehensive_statistics(all_data)
    
    fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(7, 5), 
                                             gridspec_kw={'height_ratios': HEIGHT_RATIO, 
                                                         'hspace': 0.05})
    
    tiers = ['whale', 'medium', 'minnow']
    tier_labels = ['≥20 ETH', '0.5-20 ETH', '<0.5 ETH']
    
    positions_base = [1, 3, 5]
    width = 0.25
    config_keys = ['whale_dominated', 'mixed', 'equal']
    
    tier_colors = ['gray', 'gray', 'gray']
    tier_names = ['Whale', 'Medium', 'Minnow']

    for tier_idx, tier in enumerate(tiers):
        base_pos = positions_base[tier_idx]
        left_edge = base_pos + (-1) * width * 3 - 0.17
        right_edge = base_pos + (1) * width * 3 + 0.17
        
        ax_top.axvspan(left_edge, right_edge, alpha=0.15, 
                       color=tier_colors[tier_idx], zorder=0)
        ax_bottom.axvspan(left_edge, right_edge, alpha=0.15, 
                          color=tier_colors[tier_idx], zorder=0)
    
    for tier_idx, tier in enumerate(tiers):
        plot_single_tier_violins(ax_top, tier, positions_base[tier_idx], width, 
                                config_keys, all_data, tier,False)
        plot_single_tier_violins(ax_bottom, tier, positions_base[tier_idx], width, 
                                config_keys, all_data, tier,True)
    
    ax_top.set_ylim(BREAK_UPPER, UPPER_MAX)
    ax_bottom.set_ylim(-0.5, BREAK_LOWER)
    
    ax_top.yaxis.set_major_locator(MultipleLocator(UPPER_TICK_INTERVAL))
    ax_bottom.yaxis.set_major_locator(MultipleLocator(LOWER_TICK_INTERVAL))
    
    ax_top.spines['bottom'].set_visible(False)
    ax_bottom.spines['top'].set_visible(False)
    ax_top.xaxis.tick_top()
    ax_top.tick_params(labeltop=False)
    ax_bottom.xaxis.tick_bottom()
    
    d = .015
    kwargs = dict(transform=ax_top.transAxes, color='k', clip_on=False, linewidth=1)
    ax_top.plot((-d, +d), (-d, +d), **kwargs)
    ax_top.plot((1 - d, 1 + d), (-d, +d), **kwargs)
    
    kwargs.update(transform=ax_bottom.transAxes)
    ax_bottom.plot((-d, +d), (1 - d, 1 + d), **kwargs)
    ax_bottom.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)
    
    ax_top.set_ylabel('Revenue Ratio (%)', fontsize=25, y = -0.5)
    ax_bottom.set_xlabel('Stakeholder Tiers', fontsize=25)
    
    ax_bottom.set_xticks(positions_base)
    ax_bottom.set_xticklabels(tier_labels, fontsize=20)
    ax_top.set_xticks(positions_base)
    
    ax_top.tick_params(axis='y', labelsize=20)
    ax_bottom.tick_params(axis='y', labelsize=20)
    
    ax_top.grid(True, axis='y', linestyle='--', alpha=0.3)
    ax_bottom.grid(True, axis='y', linestyle='--', alpha=0.3)
    
    ax_top.set_xlim(0, 6)
    ax_bottom.set_xlim(0, 6)
    
    minnow_pos = positions_base[2]

    ax_bottom.text(minnow_pos - 0.45, 5.8, 
                  '94% gain meaningful\nreturns', 
                  fontsize=15, 
                  weight='bold', 
                  ha='center', 
                  va='bottom',
                  color='black',
                  bbox=dict(boxstyle='round,pad=0.2',
                           facecolor='white',
                           edgecolor='#d62728',
                           linewidth=1.5,
                           alpha=0.9))

    offset_without = (-1)*width/2
    offset_with = width/2

    arrow_start_x = minnow_pos + offset_without
    arrow_end_x = minnow_pos + offset_with

    ax_bottom.annotate('', 
                      xy=(arrow_end_x, 5),
                      xytext=(arrow_start_x, 4.1),
                      arrowprops=dict(arrowstyle='->', 
                                     lw=2, 
                                     color='#d62728',
                                     connectionstyle='angle3'))
    
    legends = []
    for i, config_key in enumerate(['whale_dominated', 'mixed', 'equal']):
        config_info = all_data[config_key]['info']
        
        handles = [
            Rectangle((0, 0), 1, 1, facecolor=config_info['color_without'], 
                     edgecolor=config_info['edge'], linewidth=1.2, alpha=0.7),
            Rectangle((0, 0), 1, 1, facecolor=config_info['color_with'], 
                     edgecolor=config_info['edge'], linewidth=1.2, alpha=0.7)
        ]
        
        pos = (i*0.33, 1.05)
        if(i == 1):        
            pos = (0.03, 1.2)
            ax_bottom.legend(handles=handles, labels=['w/o', 'With'],
                               title=config_info['name'], 
                               title_fontsize=18,
                               loc='upper left', 
                               fontsize=18,
                               ncol=2,
                               bbox_to_anchor=pos,
                               frameon=True, 
                               fancybox=True, 
                               framealpha=0.9,
                               handlelength=1.5,
                               handletextpad=0.4, borderpad=0.4,
                               columnspacing=0.8)
            continue
        
        if(i == 2): 
            pos = (0.5, 1.05)   
        leg = ax_top.legend(handles=handles, labels=['w/o', 'With'],
                           title=config_info['name'], 
                           title_fontsize=18,
                           loc='upper left', 
                           fontsize=18,
                           ncol=2,
                           bbox_to_anchor=pos,
                           frameon=True, 
                           fancybox=True, 
                           framealpha=0.9,
                           handlelength=1.5,
                           handletextpad=0.4, borderpad=0.4,
                           columnspacing=0.8)
        
        if i > 0:
            ax_top.add_artist(legends[-1])
        legends.append(leg)
    
    output_path_pdf = os.path.join(output_folder, 'fig3b_revenue_tier_comparison_broken.pdf')
    output_path_png = os.path.join(output_folder, 'fig3b_revenue_tier_comparison_broken.png')
    
    plt.savefig(output_path_pdf, dpi=300, bbox_inches='tight')
    plt.savefig(output_path_png, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n{'='*60}")
    print(f"✅ 已生成断轴版本: {output_path_pdf}")
    print(f"{'='*60}")

if __name__ == "__main__":
    output_folder = "./1007exper3"
    plot_revenue_tier_comparison(output_folder)
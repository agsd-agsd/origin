import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path

class ExperimentAnalyzer:
    def __init__(self):
        self.small_investor_threshold = 0.1  # ETH
        self.convergence_threshold = 0.95  # 95%市场份额
        
    def analyze_baseline_scenario(self, no_aggregation_path, num_epochs):
        """分析无聚合基准场景"""
        total_revenue = 0
        small_investor_count = 0
        small_investor_revenue = 0
        participating_small_investors = 0
        
        for item_id in range(num_epochs):
            item_path = os.path.join(no_aggregation_path, f"item{item_id}", "b2e_test_results.json")
            
            if os.path.exists(item_path):
                with open(item_path, 'r') as f:
                    data = json.load(f)[0]
                
                # 计算总收益
                for participant_id, earning in data['earnings'].items():
                    if participant_id not in ['BrokerHub1', 'BrokerHub2']:
                        total_revenue += float(earning)
                
                # 分析小投资者
                for participant_id, balance_wei in data['original_funds'].items():
                    if participant_id not in ['BrokerHub1', 'BrokerHub2']:
                        balance_eth = float(balance_wei) / 1e18
                        if balance_eth < self.small_investor_threshold:
                            small_investor_count += 1
                            earning = float(data['earnings'].get(participant_id, 0))
                            small_investor_revenue += earning
                            if earning > 0:
                                participating_small_investors += 1
        
        # 计算平均值
        avg_total_revenue = total_revenue / 1e18 / num_epochs if num_epochs > 0 else 0
        small_investor_participation_rate = (participating_small_investors / small_investor_count * 100) if small_investor_count > 0 else 0
        avg_revenue_per_small_investor = (small_investor_revenue / 1e18 / small_investor_count) if small_investor_count > 0 else 0
        
        return {
            'scenario': 'Baseline (No Aggregation)',
            'first_monopoly_time': 'N/A',
            'first_monopolist': 'N/A',
            'convergence_time': 'N/A',
            'final_monopolist': 'N/A',
            'convergence_fee_rate': 'N/A',
            'total_revenue': f"{avg_total_revenue:.2f}",
            'small_investor_participation': f"{small_investor_participation_rate:.1f}%",
            'avg_revenue_per_small_investor': f"{avg_revenue_per_small_investor:.4f}"
        }
    
    def identify_monopolist_with_share(self, state):
        """识别垄断者并返回市场份额信息"""
        hub_funds = {}
        total_funds = 0
        
        for bh in state['brokerhubs']:
            hub_id = bh['id']
            current_funds = float(bh['current_funds'])
            hub_funds[hub_id] = current_funds
            total_funds += current_funds
        
        if total_funds == 0:
            return None
        
        # 找到资金最多的Hub
        max_funds = 0
        monopolist_id = None
        
        for hub_id, funds in hub_funds.items():
            if funds > max_funds:
                max_funds = funds
                monopolist_id = hub_id
        
        if monopolist_id:
            market_share = max_funds / total_funds
            return {
                'id': monopolist_id,
                'share': market_share,
                'funds': max_funds
            }
        
        return None
    
    def find_first_monopoly_time(self, results):
        """找到第一次垄断的时间和垄断者"""
        for epoch, state in enumerate(results):
            monopolist = self.identify_monopolist_with_share(state)
            if monopolist and monopolist['share'] >= self.convergence_threshold:
                return epoch, monopolist['id']
        return -1, None
    
    def find_convergence_time(self, results):
        """找到收敛时间：从最后往前推，找到最后一次开始垄断的时间"""
        if not results:
            return -1
        
        # 首先确认最终状态是否为垄断状态
        final_state = results[-1]
        final_monopolist = self.identify_monopolist_with_share(final_state)
        
        print(final_monopolist, final_monopolist['share'], self.convergence_threshold)
        
        if not final_monopolist or final_monopolist['share'] < self.convergence_threshold:
            return -1  # 最终状态不是垄断，无收敛
        
        final_monopolist_id = final_monopolist['id']
        
        # 从最后往前推，找到这个monopolist最后一次开始连续垄断的时间点
        convergence_epoch = len(results) - 1  # 从最后一个epoch开始
        
        for epoch in range(len(results) - 2, -1, -1):  # 从倒数第二个epoch往前
            state = results[epoch]
            current_monopolist = self.identify_monopolist_with_share(state)
            
            print(epoch,current_monopolist)
            
            # 检查当前epoch是否仍然是同一个monopolist且达到垄断阈值
            if (current_monopolist and 
                current_monopolist['id'] == final_monopolist_id and 
                current_monopolist['share'] >= self.convergence_threshold):
                convergence_epoch = epoch
            else:
                # 找到了垄断开始的地方，停止搜索
                break
        
        return convergence_epoch
    
    def get_monopolist_fee_rate(self, state, monopolist_id):
        """获取指定垄断者的管理费率"""
        if monopolist_id == "None" or not monopolist_id:
            return -1
        
        for bh in state['brokerhubs']:
            if bh['id'] == monopolist_id:
                return float(bh['tax_rate'])
        
        return -1
    
    def analyze_aggregation_scenario(self, results_path, scenario_name):
        """分析聚合场景"""
        if not os.path.exists(results_path):
            print(f"警告: 找不到文件 {results_path}")
            return None
            
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        # 找到第一次垄断
        first_monopoly_epoch, first_monopolist_id = self.find_first_monopoly_time(results)
        
        # 找到收敛时间（最后一次开始垄断）
        convergence_epoch = self.find_convergence_time(results)
        
        print(results_path,convergence_epoch)
        
        # 分析最终状态
        final_state = results[-1]
        final_monopolist = self.identify_final_monopolist(final_state)
        
        # 获取收敛时的管理费率
        convergence_fee_rate = self.get_monopolist_fee_rate(final_state, final_monopolist)
        
        # 计算总收益（使用新方法）
        total_revenue = self.calculate_total_revenue_new(final_state)
        
        # 分析小投资者（使用新方法）
        small_investor_stats = self.analyze_small_investors_new(results)
        
        return {
            'scenario': scenario_name,
            'first_monopoly_time': f"{first_monopoly_epoch}" if first_monopoly_epoch != -1 else "No monopoly",
            'first_monopolist': first_monopolist_id if first_monopolist_id else "None",
            'convergence_time': f"{convergence_epoch}" if convergence_epoch != -1 else "No convergence",
            'final_monopolist': final_monopolist,
            'convergence_fee_rate': f"{convergence_fee_rate:.1%}" if convergence_fee_rate != -1 else "N/A",
            'total_revenue': f"{total_revenue:.2f}",
            'small_investor_participation': f"{small_investor_stats['participation_rate']:.1f}%",
            'avg_revenue_per_small_investor': f"{small_investor_stats['avg_revenue']:.4f}"
        }
    
    def identify_final_monopolist(self, final_state):
        """识别最终垄断者"""
        max_funds = 0
        monopolist = "None"
        
        for bh in final_state['brokerhubs']:
            current_funds = float(bh['current_funds'])
            if current_funds > max_funds:
                max_funds = current_funds
                monopolist = bh['id']
        
        return monopolist
    
    def calculate_total_revenue_new(self, final_state):
        """计算总收益（使用revenue_rate * balance）"""
        total_revenue = 0
        
        # 所有投资者的收益：balance * revenue_rate
        for volunteer in final_state['volunteers']:
            balance = float(volunteer['balance'])
            revenue_rate = float(volunteer['revenue_rate'])
            total_revenue += balance * revenue_rate
        
        return total_revenue / 1e18
    
    def analyze_small_investors_new(self, results):
        """分析小投资者参与情况（使用revenue_rate * balance）"""
        # 使用第一个epoch的数据来确定小投资者
        first_state = results[0]
        small_investors = set()
        
        for volunteer in first_state['volunteers']:
            balance_eth = float(volunteer['balance']) / 1e18
            if balance_eth < self.small_investor_threshold:
                small_investors.add(volunteer['id'])
        
        # 分析最终状态的小投资者参与情况
        final_state = results[-1]
        participating_small_investors = 0
        total_small_investor_revenue = 0
        
        # 遍历所有volunteers，计算小投资者的收益
        for volunteer in final_state['volunteers']:
            if volunteer['id'] in small_investors:
                # 使用 revenue_rate * balance 计算收益
                balance = float(volunteer['balance'])
                revenue_rate = float(volunteer['revenue_rate'])
                revenue = balance * revenue_rate  # 实际收益（Wei）
                
                if revenue > 0:
                    participating_small_investors += 1
                
                total_small_investor_revenue += revenue
        
        participation_rate = (participating_small_investors / len(small_investors) * 100) if len(small_investors) > 0 else 0
        avg_revenue = (total_small_investor_revenue / 1e18 / len(small_investors)) if len(small_investors) > 0 else 0
        
        return {
            'participation_rate': participation_rate,
            'avg_revenue': avg_revenue
        }
    
    def analyze_multiple_hub_experiments(self, base_folder, hub_count):
        """分析多个hub数量的多次实验"""
        results = []
        
        # 基础文件
        base_file = f"simulation_results_{hub_count}hubs_20w_300_diff_final_balance.json"
        base_path = os.path.join(base_folder, base_file)
        
        if os.path.exists(base_path):
            result = self.analyze_aggregation_scenario(base_path, f"{hub_count}hubs_base")
            if result:
                results.append(result)
        
        # 扩展文件 (2, 3, 4, 5)
        for i in range(2, 6):
            ext_file = f"simulation_results_{hub_count}hubs_20w_300_diff_final_balance{i}.json"
            ext_path = os.path.join(base_folder, ext_file)
            
            result = self.analyze_aggregation_scenario(ext_path, f"{hub_count}hubs_run{i}")
            print(result)
            if result:
                results.append(result)
        
        return results
    
    def analyze_2hub_experiments(self, base_folder):
        """分析所有2hub实验（包括原trump + 20个2hubs文件）"""
        results = []
        
        # 原trump实验
        trump_path = os.path.join(base_folder, "simulation_results_trump_20w_300_diff_final_balance2.json")
        if os.path.exists(trump_path):
            result = self.analyze_aggregation_scenario(trump_path, "2hubs_trump")
            if result:
                results.append(result)
        
        # 2hubs_hub1系列文件
        for i in range(1, 11):
            file_path = os.path.join(base_folder, f"simulation_results_2hubs_hub1_20w_300_diff_final_balance{i}.json")
            if os.path.exists(file_path):
                result = self.analyze_aggregation_scenario(file_path, f"2hubs_hub1_run{i}")
                if result:
                    results.append(result)
            else:
                print(f"警告: 找不到文件 {file_path}")
        
        # 2hubs_hub2系列文件
        for i in range(1, 11):
            file_path = os.path.join(base_folder, f"simulation_results_2hubs_hub2_20w_300_diff_final_balance{i}.json")
            if os.path.exists(file_path):
                result = self.analyze_aggregation_scenario(file_path, f"2hubs_hub2_run{i}")
                if result:
                    results.append(result)
            else:
                print(f"警告: 找不到文件 {file_path}")
        
        return results
    
    def summarize_multiple_runs(self, results, scenario_name):
        """汇总多次实验的结果"""
        if not results:
            return {
                'scenario': scenario_name,
                'first_monopoly_time': "No Data",
                'first_monopolist': "No Data", 
                'convergence_time': "No Data",
                'final_monopolist': "No Data",
                'convergence_fee_rate': "No Data",
                'total_revenue': "No Data",
                'small_investor_participation': "No Data",
                'avg_revenue_per_small_investor': "No Data"
            }
        
        # 提取数值进行统计
        first_monopoly_times = []
        convergence_times = []
        total_revenues = []
        participation_rates = []
        avg_revenues = []
        fee_rates = []
        first_monopolists = []
        final_monopolists = []
        
        for result in results:
            # 处理第一次垄断时间
            if result['first_monopoly_time'] != "No monopoly" and result['first_monopoly_time'].replace('.', '').replace('-', '').isdigit():
                first_monopoly_times.append(float(result['first_monopoly_time']))
            
            # 处理收敛时间
            if result['convergence_time'] != "No convergence" and result['convergence_time'].replace('.', '').replace('-', '').isdigit():
                convergence_times.append(float(result['convergence_time']))
            
            # 处理总收益
            if result['total_revenue'] != "N/A":
                total_revenues.append(float(result['total_revenue']))
            
            # 处理参与率
            if result['small_investor_participation'] != "N/A":
                participation_rates.append(float(result['small_investor_participation'].rstrip('%')))
            
            # 处理平均收益
            if result['avg_revenue_per_small_investor'] != "N/A":
                avg_revenues.append(float(result['avg_revenue_per_small_investor']))
            
            # 处理费率
            if result['convergence_fee_rate'] != "N/A" and '%' in result['convergence_fee_rate']:
                fee_rates.append(float(result['convergence_fee_rate'].rstrip('%')))
            
            # 收集垄断者
            first_monopolists.append(result['first_monopolist'])
            final_monopolists.append(result['final_monopolist'])
        
        # 计算统计数据
        first_monopolist_dist = {}
        for m in first_monopolists:
            if m and m != "None":
                first_monopolist_dist[m] = first_monopolist_dist.get(m, 0) + 1
        
        final_monopolist_dist = {}
        for m in final_monopolists:
            if m and m != "None":
                final_monopolist_dist[m] = final_monopolist_dist.get(m, 0) + 1
        
        first_monopolist_str = ", ".join([f"{k}: {v}/{len(results)}" for k, v in first_monopolist_dist.items()])
        final_monopolist_str = ", ".join([f"{k}: {v}/{len(results)}" for k, v in final_monopolist_dist.items()])
        
        return {
            'scenario': f"{scenario_name} ({len(results)} runs)",
            'first_monopoly_time': f"{np.mean(first_monopoly_times):.1f}±{np.std(first_monopoly_times):.1f}" if first_monopoly_times else "N/A",
            'first_monopolist': first_monopolist_str if first_monopolist_str else "N/A",
            'convergence_time': f"{np.mean(convergence_times):.1f}±{np.std(convergence_times):.1f}" if convergence_times else "N/A",
            'final_monopolist': final_monopolist_str if final_monopolist_str else "N/A",
            'convergence_fee_rate': f"{np.mean(fee_rates):.1f}±{np.std(fee_rates):.1f}%" if fee_rates else "N/A",
            'total_revenue': f"{np.mean(total_revenues):.2f}±{np.std(total_revenues):.2f}" if total_revenues else "N/A",
            'small_investor_participation': f"{np.mean(participation_rates):.1f}±{np.std(participation_rates):.1f}%" if participation_rates else "N/A",
            'avg_revenue_per_small_investor': f"{np.mean(avg_revenues):.4f}±{np.std(avg_revenues):.4f}" if avg_revenues else "N/A"
        }

def generate_experiment_summary_table(base_folder, output_folder, table_name):
    """生成实验结果汇总表"""
    analyzer = ExperimentAnalyzer()
    
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)
    
    results = []
    
    print("正在分析实验数据...")
    
    # 1. 分析基准场景（无聚合）
    baseline_path = "../src/data/processed_data/witouthub/without_trump_20w_300_diff_final_balance"
    print("分析基准场景...")
    baseline_result = analyzer.analyze_baseline_scenario(baseline_path, 300)
    results.append(baseline_result)
    
    # 2. 分析2Hub竞争场景（合并所有2hub文件）
    print("分析2Hub竞争场景...")
    two_hub_results = analyzer.analyze_2hub_experiments(base_folder)
    if two_hub_results:
        two_hub_summary = analyzer.summarize_multiple_runs(two_hub_results, "2 Hubs Competition")
        results.append(two_hub_summary)
    
    # 3. 分析多Hub竞争场景
    hub_counts = [3, 4, 5, 10]
    
    for hub_count in hub_counts:
        print(f"分析{hub_count}Hub竞争场景...")
        hub_results = analyzer.analyze_multiple_hub_experiments(base_folder, hub_count)
        
        if hub_results:
            hub_summary = analyzer.summarize_multiple_runs(hub_results, f"{hub_count} Hubs Competition")
            results.append(hub_summary)
        else:
            print(f"警告: 找不到{hub_count}Hub实验文件")
            # 添加占位符数据
            results.append({
                'scenario': f"{hub_count} Hubs Competition",
                'first_monopoly_time': "Data Not Available",
                'first_monopolist': "Data Not Available",
                'convergence_time': "Data Not Available",
                'final_monopolist': "Data Not Available",
                'convergence_fee_rate': "Data Not Available",
                'total_revenue': "Data Not Available",
                'small_investor_participation': "Data Not Available",
                'avg_revenue_per_small_investor': "Data Not Available"
            })
    
    # 创建DataFrame
    df = pd.DataFrame(results)
    
    # 重新排列列的顺序
    column_order = [
        'scenario', 'first_monopoly_time', 'first_monopolist',
        'convergence_time', 'final_monopolist', 'convergence_fee_rate', 
        'total_revenue', 'small_investor_participation', 'avg_revenue_per_small_investor'
    ]
    df = df[column_order]
    
    # 设置列名
    df.columns = [
        'Scenario', 'First Monopoly Time (Epochs)', 'First Monopolist',
        'Convergence Time (Epochs)', 'Final Monopolist', 'Convergence Fee Rate (%)', 
        'Total Revenue (ETH)', 'Small Investor Participation (%)', 
        'Avg Revenue per Small Investor (ETH)'
    ]
    
    # 保存为CSV
    csv_path = os.path.join(output_folder, f"{table_name}.csv")
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    # 保存为Excel
    excel_path = os.path.join(output_folder, f"{table_name}.xlsx")
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Experiment Results', index=False)
        
        # 获取工作表
        worksheet = writer.sheets['Experiment Results']
        
        # 调整列宽
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    # 打印表格
    print("\n" + "="*160)
    print("实验结果汇总表")
    print("="*160)
    print(df.to_string(index=False))
    print("="*160)
    
    # 添加注释说明
    notes = """
表格说明:
- 第一次垄断时间：任意Hub首次达到95%市场份额的时间点
- 收敛时间：从最终状态往前推，找到最后一次开始连续垄断的时间点
- 小投资者定义：余额 < 0.1 ETH的账户
- 参与率计算：能获得正收益的小投资者账户比例
- 收益计算：使用 revenue_rate * balance 公式
- 2 Hubs Competition：包含trump实验 + 20个2hubs文件
- 多Hub竞争：包含基础文件 + 扩展文件(2,3,4,5)
- 对于多次实验：显示平均值±标准差
- 垄断者分布：显示各Hub成为垄断者的次数比例
    """
    
    print(notes)
    
    # 保存说明到文件
    notes_path = os.path.join(output_folder, f"{table_name}_notes.txt")
    with open(notes_path, 'w', encoding='utf-8') as f:
        f.write(notes)
    
    print(f"\n表格已保存至:")
    print(f"CSV格式: {csv_path}")
    print(f"Excel格式: {excel_path}")
    print(f"说明文件: {notes_path}")
    
    return df

def main():
    """主函数"""
    
    # 实验数据基础文件夹
    base_folder = "../result/output"
    
    # 输出配置
    output_folder = "./0703exper3"
    table_name = "experiment_summary_table_v2"
    
    print("=" * 70)
    print("实验结果汇总表生成器 v2.0")
    print("=" * 70)
    print(f"数据源文件夹: {base_folder}")
    print(f"输出文件夹: {output_folder}")
    print(f"表格名称: {table_name}")
    print("\n数据合并策略:")
    print("- 2 Hubs: trump + 2hubs_hub1 + 2hubs_hub2 (共21个文件)")
    print("- 3 Hubs: 基础 + 扩展2,3,4,5 (共5个文件)")
    print("- 4 Hubs: 基础 + 扩展2,3,4,5 (共5个文件)")
    print("- 5 Hubs: 基础 + 扩展2,3,4,5 (共5个文件)")
    print("- 10 Hubs: 基础 + 扩展2,3,4,5 (共5个文件)")
    print("\n收益计算方法: revenue_rate * balance")
    print("=" * 70)
    
    try:
        df = generate_experiment_summary_table(base_folder, output_folder, table_name)
        print("\n汇总表生成完成！")
        
    except Exception as e:
        print(f"生成汇总表时出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
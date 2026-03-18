import os
import json
import shutil
from src.market.b2etest import B2ETester
from src.b2e.b2erounding import B2ERounding, wait_for_write_tasks
import pandas as pd

def read_broker_data(csv_path):
    """
    读取并处理broker数据，确保数据类型正确
    """
    # 读取CSV文件
    df = pd.read_csv(csv_path)
    
    # 确保必要的列存在
    required_columns = [
        'ID', 
        'Number of CTXs served', 
        'revenue rate(Fee * feeRatio / brokerAmount)', 
        'Balance', 
        'Usage'
    ]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"CSV文件缺少必要的列: {col}")
    
    # 转换数据类型
    df['Balance'] = pd.to_numeric(df['Balance'], errors='coerce')
    df['revenue rate(Fee * feeRatio / brokerAmount)'] = pd.to_numeric(
        df['revenue rate(Fee * feeRatio / brokerAmount)'], 
        errors='coerce'
    )
    
    # 按余额降序排序
    df = df.sort_values(by='Balance', ascending=False)
    
    return df

def copy_data_to_without_folder(base_path, source_folder, num_items=300):
    """
    将原始文件夹中的数据复制到witouthub/without_文件夹名目录中
    仅复制data1.txt文件，不复制brokerBalance.txt
    """
    source_path = os.path.join(base_path, source_folder)
    
    # 创建固定的witouthub父目录
    witouthub_path = os.path.join(base_path, "witouthub")
    if not os.path.exists(witouthub_path):
        os.makedirs(witouthub_path)
        print(f"创建父目录: {witouthub_path}")
    
    # 在witouthub下创建without_文件夹名子目录
    target_folder = f"without_{source_folder}"
    target_path = os.path.join(witouthub_path, target_folder)
    
    # 创建目标文件夹（如果不存在）
    if not os.path.exists(target_path):
        os.makedirs(target_path)
        print(f"创建目录: {target_path}")
    
    # 复制每一个item的data1.txt文件
    copied_count = 0
    for i in range(num_items):
        item_folder = f"item{i}"
        source_item_path = os.path.join(source_path, item_folder)
        target_item_path = os.path.join(target_path, item_folder)
        
        # 创建目标item文件夹
        if not os.path.exists(target_item_path):
            os.makedirs(target_item_path)
        
        # 复制data1.txt文件
        source_file = os.path.join(source_item_path, "data1.txt")
        target_file = os.path.join(target_item_path, "data1.txt")
        
        # 复制 Ctx.csv文件
        source_file1 = os.path.join(source_item_path, "Ctx.csv")
        target_file1 = os.path.join(target_item_path, "Ctx.csv")
        
        if os.path.exists(source_file):
            shutil.copy2(source_file, target_file)
            shutil.copy2(source_file1, target_file1)
            copied_count += 1
            # 每50个文件打印一次进度，减少控制台输出
            if copied_count % 50 == 0 or copied_count == 1:
                print(f"已复制: {copied_count}/{num_items} 个文件")
        else:
            print(f"警告：找不到源文件 {source_file}")
    
    print(f"复制完成：共复制了 {copied_count}/{num_items} 个文件")
    return target_path

def run_b2e_on_folder(folder_path, num_items=300, broker_balance_path=None, additional_brokers=None):
    """
    在指定文件夹中的每个item上运行B2E算法
    
    参数:
    folder_path - 要处理的文件夹路径
    num_items - 要处理的item数量
    broker_balance_path - broker资金文件路径
    additional_brokers - 要添加的额外broker账户列表，格式为[(broker_id, balance),...]
    """
    # 测试配置
    config = {
        "output_path": folder_path,  # 输出路径
        "b2e": {
            "varType": "LINEAR",  # 变量类型
            "iterNum": 1,  # 迭代次数
            "alpha": 1,  # alpha参数
            "feeRatio": 0.1  # 费率比例
        }
    }
    
    # 进度统计
    successful_runs = 0
    failed_runs = 0
    
    # 为每个item运行B2E算法
    for i in range(num_items):
        item_folder = f"item{i}"
        item_path = os.path.join(folder_path, item_folder)
        data_file = os.path.join(item_path, "data1.txt")
        
        
        # 更新输出路径
        config["output_path"] = item_path
        
        # 创建测试器
        tester = B2ETester(config, B2ERoundingClass=B2ERounding)
        
        # 加载数据
        tester.load_data(data_file)
        
        # 如果提供了经纪人资金文件，则加载它
        if broker_balance_path and os.path.exists(broker_balance_path):
            tester.load_broker_funds_from_file(broker_balance_path)
            
            # 添加额外的broker账户（如果有）
            if additional_brokers:
                tester.add_broker_fund(additional_brokers)
                print(f"已添加 {len(additional_brokers)} 个额外broker账户")
        
        print(item_path)
        # 执行单次B2E测试
        tester.run_single_test()
        
        # 保存结果
        tester.save_results()
        
        # 等待写入任务完成
        
        # 打印统计信息
        broker_result_path = os.path.join(item_path, "Broker_result.csv")
        if os.path.exists(broker_result_path):
            df = read_broker_data(broker_result_path)
            
            # 打印数据统计信息
            print(f"\n[{item_folder}] 数据统计信息:")
            print(f"总计 Broker 数量: {len(df)}")
            print(f"最大余额: {df['Balance'].max()/1e18:.2e} Ether")
            print(f"最小余额: {df['Balance'].min()/1e18:.2e} Ether")
            print(f"平均收益率: {df['revenue rate(Fee * feeRatio / brokerAmount)'].mean()*100:.4f}%")
        
        successful_runs += 1
        print(f"成功处理 {item_folder} ({successful_runs}/{num_items})")
        
    
    wait_for_write_tasks()
    print(f"\n处理完成! 成功: {successful_runs}, 失败: {failed_runs}")

def main():
    # 设置基础路径
    base_path = r"D:\博一\BrokerHub\code\BrokerHub\BrokerHub_exp\src\data\processed_data"
    
    # 原始文件夹名称
    # original_folder = "trump_20w_300_same_motivation_balance2"
    # original_folder = "trump_20w_300_same_final_balance2"
    # original_folder = "trump_20w_300_diff_final_balance"
    # original_folder = "trump_20w_300_diff_motivation_balance"
    # original_folder = "one_trump_20w_300_diff_final_balance"
    # original_folder = "trump_20w_300_diff_final_balance3"
    # original_folder = "2hubs_20w_300_diff_final_balance_medium1"
    original_folder = "2hubs_20w_300_diff_final_balance_fully1"
    
    # 项目数量
    num_items = 300
    
    # 复制数据到新文件夹
    new_folder_path = copy_data_to_without_folder(base_path, original_folder, num_items)
    
    # 指定broker余额文件的路径
    # broker_balance_path = "D:/博一/BrokerHub/code/BrokerHub/BrokerHub_exp/config/brokerBalance_medium_balanced.txt"
    broker_balance_path = "D:/博一/BrokerHub/code/BrokerHub/BrokerHub_exp/config/brokerBalance_fully_balanced.txt"
    # broker_balance_path = "D:/博一/BrokerHub/code/BrokerHub/BrokerHub_exp/config/brokerBalance.txt"
    # broker_balance_path = "D:/博一/BrokerHub/code/BrokerHub/BrokerHub_exp/config/motivation_brokerBalance.txt"
    # broker_balance_path = "D:/博一/BrokerHub/code/BrokerHub/BrokerHub_exp/config/brokerBalance_one.txt"
    
    if not os.path.exists(broker_balance_path):
        broker_balance_path = None
        print("警告: 找不到brokerBalance.txt文件，将不会加载经纪人资金数据")
    
    # 可选：添加额外的broker账户，格式为[(broker_id, balance),...]
    # 示例: [("ExtraBroker1", 1000000000000000000), ("ExtraBroker2", 2000000000000000000)]
    # additional_brokers = [("BrokerHub1", 1e18), ("BrokerHub2", 1e18)]
    additional_brokers = []
    
    # 在新文件夹上运行B2E算法
    print(f"\n开始在 {new_folder_path} 上运行B2E算法...")
    run_b2e_on_folder(new_folder_path, num_items, broker_balance_path, additional_brokers)

if __name__ == "__main__":
    main()
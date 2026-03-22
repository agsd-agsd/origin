from src.b2e.MKP_gurobi import slove2Gurobi
from src.b2e.data import read_data
from src.b2e.rounding import Rounding
import numpy as np
import time
import json
import random
import threading
import queue

with open('config/simulation_config.json') as config_file:
    config = json.load(config_file)

txsPath = config['txsPath']
limit_time = int(config['limit_time'])

def update(new_ctxs, new_capacities, mapped_ctxs, mapped_capacities, s_x, ns_x):
    for index0, ctx in enumerate(new_ctxs):
        for index1, k_num in enumerate(new_capacities):
            if s_x[index0, index1] > 0.0:
                ns_x[mapped_ctxs[index0], mapped_capacities[index1]] = s_x[index0, index1]
                break
    return ns_x

def iter(iter_num, var_type, data, ori_ns_x):
    start_time_all = time.time()
    ori_ctxs, ori_capacities, txsNumber = data
    k_number = len(ori_capacities)
    ori_weights_capacities = [0 for _ in ori_capacities]
    
    if iter_num == 0:
        for key in ori_ns_x.keys():
            ori_weights_capacities[key[1]] += ori_ns_x[key] * ori_ctxs[key[0]][1]
    
    cpu_times = []; round_times = []
    print(f"DEBUG: Starting B2E iterations. iter_num={iter_num}, limit_time={limit_time}")
    for it_idx in range(iter_num):
        iter_start = time.time()
        ori_weights_capacities = [0 for _ in ori_capacities]
        
        for key in ori_ns_x.keys():
            ori_weights_capacities[key[1]] += ori_ns_x[key] * ori_ctxs[key[0]][1]

        new_ctxs = []; new_capacities = []; mapped_ctxs = {}; mapped_capacities = {}
        
        for ctx in range(len(ori_ctxs)):
            ctx_used = sum([ori_ns_x[(ctx, k_num)] for k_num in range(len(ori_capacities))])
            if ctx_used > 0.0:
                continue
            new_ctxs.append(ori_ctxs[ctx])
            mapped_ctxs[len(new_ctxs) - 1] = ctx
        
        for k_num in range(len(ori_capacities)):
            if ori_capacities[k_num] > ori_weights_capacities[k_num]:
                new_capacities.append(ori_capacities[k_num] - ori_weights_capacities[k_num])
                mapped_capacities[len(new_capacities) - 1] = k_num

        scale = 1e14
        
        s_x, obj, cpu_time, others = slove2Gurobi.value_desity_first_linear([[[i[0] * scale, i[1] * scale, i[2]] for i in new_ctxs], [i * scale for i in new_capacities], txsNumber], var_type)
        k_number, txsNumber, ctxs, capacities, status = others
        cpu_times.append(cpu_time)
        
        round_time = time.time()
        n_x = Rounding.b2e_rounding(s_x, k_number, ctxs, capacities)
        round_times.append(time.time() - round_time)
        
        ns_x = {}
        value = 0
        keys = list(s_x.keys())
        weights_capacities = [i for i in ori_weights_capacities]

        for i in range(len(keys)):
            ns_x[keys[i]] = n_x[keys[i][1], keys[i][0]]
            value += ns_x[keys[i]] * ctxs[keys[i][0]][0]
            weights_capacities[mapped_capacities[keys[i][1]]] += ns_x[keys[i]] * ctxs[keys[i][0]][1]
        
        if status == "OPTIMAL":
            ori_ns_x = update(new_ctxs, new_capacities, mapped_ctxs, mapped_capacities, ns_x, ori_ns_x)            
        
        using_time = sum(cpu_times) + sum(round_times)
        elapsed_time = time.time() - start_time_all
        print(f"DEBUG: I{it_idx+1}/{iter_num} | Time: {elapsed_time:.2f}s | Val: {value:.2f}")
        if value == 0.0 or elapsed_time >= limit_time:
            break
    
    if check(ori_ctxs, k_number, ori_weights_capacities, ori_capacities, ori_ns_x):     
        new_items = []
        for index, ctx in enumerate(ori_ctxs):
            to_sum = sum(ori_ns_x[(index, k)] for k in range(k_number))
            if to_sum >= 0.5:
                continue
            new_items.append([index, ctx[0], ctx[1]])
        new_items.sort(key=lambda x: x[1] / (x[2] + 1e-8), reverse=True)
        for ctx in new_items:
            for k in range(k_number):
                if ori_weights_capacities[k] + ctx[2] <= ori_capacities[k]:
                    ori_weights_capacities[k] += ctx[2]
                    ori_ns_x[(ctx[0], k)] = 1.0
                    break
    return ori_ns_x, cpu_times, round_times

def check(ctxs, k_number, weights_capacities, capacitys, ns_x):
    for num, ctx in enumerate(ctxs):
        sum_x = sum(ns_x[(num, k)] for k in range(k_number))
        if sum_x < 1.0 and any(weights_capacities[k] + ctx[1] <= capacitys[k] for k in range(k_number)):
            return True
    return False

# 创建一个全局队列来存储写入任务
write_queue = queue.Queue()

class FileWriterThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True  # 设置为守护线程
        self.stop_event = threading.Event()

    def run(self):
        while not self.stop_event.is_set():
            try:
                # 从队列中获取写入任务，设置超时以便定期检查停止事件
                task = write_queue.get(timeout=1)
                task()
                write_queue.task_done()
            except queue.Empty:
                continue

    def stop(self):
        self.stop_event.set()

# 创建并启动文件写入线程
file_writer_thread = FileWriterThread()
file_writer_thread.start()

def enqueue_write_task(func, *args, **kwargs):
    write_queue.put(lambda: func(*args, **kwargs))
    
def B2ERounding(dataEpoch, var_type, resultPath, iter_num=5, alpha=1, feeRatio=0.1, sorted_ids=None):
    start_time = time.time()
    round_times = []
    cpu_times = []
    
    s_x, obj, cpu_time, others = slove2Gurobi.value_desity_first_linear(dataEpoch, var_type, alpha=alpha)
    k_number, txsNumber, ctxs, capacities, status = others
    
    cpu_times.append(cpu_time)
    
    basePath = resultPath
    resultPath += "/Broker_result"
    
    round_start = time.time()
    n_x = Rounding.b2e_rounding(s_x, k_number, ctxs, capacities)
    round_times.append(time.time() - round_start)
    
    ns_x = {}
    value = 0
    keys = list(s_x.keys())
    weights_capacities = [0 for _ in capacities]
    
    for i in range(len(keys)):
        ns_x[keys[i]] = n_x[keys[i][1], keys[i][0]]
        value += ns_x[keys[i]] * ctxs[keys[i][0]][0]
        weights_capacities[keys[i][1]] += ns_x[keys[i]] * ctxs[keys[i][0]][1]
    
    for index, ctx in enumerate(ctxs):
        if ctx[1] != 0:
            continue
        if all(ns_x.get((index, i), 0) == 0 for i in range(len(capacities))):
            broker_num = random.randint(0, len(capacities) - 1)
            key = (index, broker_num)
            ns_x[key] = 1
            value += ns_x[key] * ctxs[index][0]
    
    cpu_times0 = []; round_times0 = []
    if check(ctxs, k_number, weights_capacities, capacities, ns_x):
        ns_x, cpu_times0, round_times0 = iter(iter_num, var_type, [ctxs, capacities, txsNumber], ns_x)
    else:
        cpu_times0, round_times0 = [0], [0]
    
    ori_weights_capacities = [0 for _ in capacities]
    brokerVaule = [0 for _ in capacities]
    
    value = 0
    nums = 0
    for key, x_value in ns_x.items():
        ori_weights_capacities[key[1]] += x_value * ctxs[key[0]][1]
        brokerVaule[key[1]] += x_value * ctxs[key[0]][0]
        value += x_value * ctxs[key[0]][0]
        nums += x_value

    end_time = time.time()
    using_time = end_time - start_time
    round_times += round_times0
    cpu_times += cpu_times0
    
    scale = 1
    utiles = value * 0.1 + nums
    
    # read_data.writeSol(status, round_times, cpu_times, using_time, k_number, txsNumber, ctxs, capacities, ns_x, resultPath)
    # read_data.write_csv(k_number, txsNumber, ctxs, capacities, ns_x, feeRatio, resultPath, scale)
    # read_data.write_ctx_csv(k_number, txsNumber, ctxs, capacities, ns_x, feeRatio, basePath)
    
    brokerVaule = [i * scale for i in brokerVaule]
        
    # 在写入结果时使用 sorted_ids
    enqueue_write_task(read_data.writeSol, status, round_times, cpu_times, using_time, k_number, txsNumber, ctxs, capacities, ns_x, resultPath)
    enqueue_write_task(read_data.write_csv, k_number, txsNumber, ctxs, capacities, ns_x, feeRatio, resultPath, scale, sorted_ids)
    enqueue_write_task(read_data.write_ctx_csv, k_number, txsNumber, ctxs, capacities, ns_x, feeRatio, basePath, sorted_ids)
    
    
    return using_time, value, brokerVaule
    

# 在主程序结束时，确保所有写入任务完成
def wait_for_write_tasks():
    write_queue.join()
    file_writer_thread.stop()
    file_writer_thread.join()

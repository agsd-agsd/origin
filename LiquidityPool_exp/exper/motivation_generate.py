import shutil
import os
import random

basePath = "D:\博一\BrokerHub\motivation\B2E\data"
# resultPath = "BalanceAdd_bigSmall"
# resultPath = "BalanceNormal"
# resultPath = "BalanceAdd_10broker"
# resultPath = "BalanceAdd_bigSmall0"
resultPath = "BalanceAdd_bigSmall19"
    
def cal_balance(balance, ratio):
    return  balance * (ratio/(1-ratio))
 
def copy_directory(src, dst):
    shutil.copytree(src, dst)

def generate_broker_rate(balance, num, ratio):
    # balances = [cal_balance(balance * (num-1), ratio)]
    # balances.extend([balance for i in range(num - 1)])
    balances = []
    for i in range(num):
        # 2e17, 2e18
        balances.append(2000000000000000000 + 1000000000000000000 * (num - i))
    return balances
    
def change_broker_value(filePath, broker, tmpFilePath):
    
    new_data = ""
    with open(tmpFilePath, "r") as f:
        data = f.readlines()
        data[-1] = ", ".join("%i"%i for i in broker)
        data[0] = data[0].split(" : ")
        data[0][1] = len(broker)
        data[0] = data[0][0] + " : " + str(data[0][1]) + "\n"
        new_data = data
    with open(filePath, "w") as f:
        for i in new_data:
            f.write(i)
    
def copy_path(path0, path1):
    for i in range(17, 50): 
        copy_directory(path0 + "/item" + str(i), path1 + "/item" + str(i))
    
def copy_generate_example(path0, path1, broker):
    copy_directory(path0, path1)
    # copy_path(path0, path1)
    
    filelist = os.listdir(path1)
    # sorted(broker, reverse = True)
    for i in range(len(filelist)):
        filePath = path1 + "/item" + str(i) + "/data1.txt"
        # random.shuffle(broker)
        change_broker_value(filePath, broker, path1 + "/item" + str(i) + "/data1.txt")
        # shutil.copy2(path1 + "/item0/Ctx.csv", path1 + "/item" + str(i) + "/Ctx.csv")

balance = 2e18

def generate_data():

    # broker = generate_broker_rate(balance, 50, 0)
    # copy_generate_example(basePath + "/example", basePath + "/" + resultPath + "/example0", broker)

    for i in range(100):
        broker = generate_broker_rate(balance, 50, 0.01 * i)
        copy_generate_example(basePath + "/BalanceAdd_5wCtx", basePath + "/" + resultPath + "/example" + str(i), broker)
        # copy_generate_example(basePath + "/example", basePath + "/" + resultPath + "/example" + str(i), broker)

if __name__ == "__main__":
    
    if not os.path.isdir(resultPath):
        os.mkdir(resultPath)
    generate_data()

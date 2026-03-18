import os
import motivation_generate

basePath = "D:\博一\BrokerHub\motivation\B2E\data"
resultPath = "BalanceAdd"

brokerNum = 50
# def cal_balance(balance, ratio):
    # return  balance * (ratio/(1-ratio))
# balance = 2e18
balance = 2500000000000000000
brokerage = 0.1

def get_data(file):
    brokerNum = 0
    allBalance = 0
    # get Broker id, because the broker is random in each example
    brokerIndex = 0
    with open(file + "/data1.txt", "r") as f:
        data = f.readlines()
        brokerBalances = [int(i) for i in data[-1].strip().split(", ")]
        # brokerIndex = sum([i if int(brokerBalances[i]) != balance else 0 for i in range(len(brokerBalances))])
        brokerIndex = sum([0 if int(brokerBalances[i]) != balance else i for i in range(len(brokerBalances))])
        
        allBalance = sum(brokerBalances)
        
        brokerNum = int(data[0].strip().split(" : ")[1])
        
    allCtxBalance = 0
    
    # get the served ctxs'id though broker id 
    ctxIds = []
    for i in range(brokerNum):
        ctxIds.append([])
    allctxIds = []
    with open(file + "/Broker_result_Ctx.csv", "r") as f:
        data = f.readlines()
        
        for brokerId in range(brokerNum):
            ctxsServed = data[1:][brokerId].split(",")[1].strip().split(" ")
            # print(file,brokerId,len(ctxsServed))
            for i in ctxsServed:
                if(i != ""):
                    ctxIds[brokerId].append(int(i))
        
        # brokerHub to the last
        # if(brokerIndex != brokerNum - 1):
            # lastElement = ctxIds[brokerIndex]
            # ctxIds = ctxIds[:brokerIndex] + ctxIds[brokerIndex + 1:]
            # ctxIds.append(lastElement)
        
        # ctxsServed = data[1:][brokerIndex].split(",")[1].strip().split(" ")
        # for i in ctxsServed:
            # if(i != ""):
                # ctxIds.append(int(i))
        
        allCtxsIds = [i.split(",")[1].strip().split(" ") for i in data[1:]]
        for i in allCtxsIds:
            for j in i:
                if(j != ""):
                    allctxIds.append(int(j))
    
    # get the fee of the ctx which is going to cal the profit
    ctxsFee = []
    for i in range(brokerNum):
        ctxsFee.append([])
    allCtxsFee = []
    with open(file + "/Ctx.csv", "r") as f:
        ctxs = f.readlines()[1:]
        for i in range(brokerNum):
            for ctxid in ctxIds[i]:
                ctxsFee[i].append(int(ctxs[ctxid].strip().split(",")[3]))
            
        for ctxid in allctxIds:
            # print(ctxid, len(ctxs))
            # print(ctxs[ctxid].strip().split(","))
            # print(len(ctxs[ctxid].strip().split(",")))
            allCtxsFee.append(int(ctxs[ctxid].strip().split(",")[3]))
            
            allCtxBalance += int(ctxs[ctxid].strip().split(",")[4])
    
    # print(brokerIndex)
    # print(ctxIds)
    # print(ctxsFee)
    # print(allCtxsFee)
    
    
    ctxNums = len(ctxIds)
    profit = [sum([i * brokerage for i in j]) for j in ctxsFee]
    allProfit = sum([i * brokerage for i in allCtxsFee])
    
    # print(profit, allProfit)
    
    
    return [i / allProfit if allProfit != 0 else 0 for i in profit], allBalance, allCtxBalance, [i for i in profit]

def get_percentage(basePath, resultPath, num):
    global brokerNum
    targetPath = basePath + "/" + resultPath
    percentage = []
    profits = []
    balance_broker_ctx = []
    
    for i in range(brokerNum):
        percentage.append([])
        profits.append([])
    
    for i in range(num):
        filePath = targetPath + "/example" + str(i) + "/"
        # filelist = os.listdir(filePath)
        
        # itemNum * brokerNum
        example = []
        exampleP = []
        for i in range(brokerNum):
            example.append([])
            exampleP.append([])
        for file in range(50):
            # print(filePath + "/item" + str(file))
            
            # [brokerNum]
            brokerRatio, allBalance, allCtxBalance, profit = get_data(filePath + "/item" + str(file))
            
            for k, brokerR in enumerate(brokerRatio):
                example[k].append(brokerR)
                exampleP[k].append(profit[k])
            
            if(len(balance_broker_ctx) <= num):
                balance_broker_ctx.append([allBalance, allCtxBalance])
        
        
        for i in range(brokerNum):
            percentage[i].append(example[i]) 
            profits[i].append(exampleP[i]) 
    
    
    return percentage, balance_broker_ctx, profits

if __name__ == "__main__":
    percentage, balance_broker_ctx, profits = get_percentage(basePath, resultPath, 100)
    # print(percentage)
    # for i in percentage:
        # print(i)
    # for i in balance_broker_ctx:
        # print(i)
// Mock版本的blockchain服务
import mockData from '@/mock'

// 模拟延迟
const delay = (ms = 300) => new Promise(resolve => setTimeout(resolve, ms))

// Web3 utils for conversions (从真实服务复制)
function toWei(ether) {
    // Convert ether (or token amount) to wei
    if (typeof ether === 'number') {
        ether = ether.toString();
    }
    // 18 decimals
    const wei = BigInt(Math.floor(parseFloat(ether) * 10**18));
    return '0x' + wei.toString(16);
}

function fromWei(hexWei) {
    // Convert wei (hex or number) to ether
    let wei;
    if (hexWei.startsWith('0x')) {
        wei = BigInt(hexWei);
    } else {
        wei = BigInt(hexWei);
    }
    return (Number(wei) / 10**18).toString();
}

const blockchainMock = {
    // Convert between wei and ether
    toWei,
    fromWei,
    // 获取wBKC余额
    async getWbkcBalance(address) {
        await delay(300)
        return await mockData.wallet.getWbkcBalance(address)
    },

    // 获取E20C余额
    async getE20cBalance(address) {
        await delay(300)
        return await mockData.wallet.getE20cBalance(address)
    },

    // 获取兑换率
    async getExchangeRate() {
        await delay(300)
        return await mockData.swap.getExchangeRate()
    },

    // 获取池信息
    async getPoolInfo() {
        await delay(300)
        return await mockData.swap.getPoolInfo()
    },

    // 计算兑换输出
    async getAmountBOut(amountIn) {
        await delay(300)
        return await mockData.swap.getAmountBOut(amountIn)
    },

    async getAmountAOut(amountIn) {
        await delay(300)
        return await mockData.swap.getAmountAOut(amountIn)
    },

    // 执行兑换 (状态管理器会自动处理余额更新)
    async swapAforB(amountIn) {
        await delay(1000)
        return await mockData.swap.swapAForB(amountIn)
    },

    async swapBforA(amountIn) {
        await delay(1000)
        return await mockData.swap.swapBForA(amountIn)
    },

    // 流动性相关
    async addLiquidity(amountA, amountB) {
        await delay(1000)
        return await mockData.liquidity.addLiquidity(amountA, amountB)
    },

    async removeLiquidity(lpAmount) {
        await delay(1000)
        return await mockData.liquidity.removeLiquidity(lpAmount)
    },

    async getLPBalance(address) {
        await delay(300)
        return await mockData.liquidity.getLPBalance(address)
    },

    // 兼容性方法 - 有些地方使用getUserLPBalance
    async getUserLPBalance(address) {
        await delay(300)
        return await mockData.liquidity.getLPBalance(address)
    },

    // 交易历史
    async getTransactions(address) {
        await delay(300)
        return await mockData.transactions.getTransactions(address)
    },

    async addTransaction(transaction) {
        await delay(100)
        return await mockData.transactions.addTransaction(transaction)
    }
}

export default blockchainMock 
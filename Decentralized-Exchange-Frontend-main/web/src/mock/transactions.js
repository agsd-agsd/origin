// 交易历史Mock数据 - 使用状态管理器
import mockState from './mockState.js'

const delay = (ms = 300) => new Promise(resolve => setTimeout(resolve, ms))

export default {
    // 获取交易历史 (从状态管理器获取实时数据)
    getTransactions: async (address) => {
        await delay()
        return mockState.getTransactions()
    },
    
    // 添加新交易
    addTransaction: async (transaction) => {
        await delay(100)
        return mockState.addTransaction(transaction)
    },
    
    // 获取交易详情
    getTransaction: async (txHash) => {
        await delay()
        const transactions = mockState.getTransactions()
        return transactions.find(tx => tx.txHash === txHash)
    }
} 
// 钱包Mock数据 - 使用状态管理器
import mockState from './mockState.js'

// 模拟延迟
const delay = (ms = 300) => new Promise(resolve => setTimeout(resolve, ms))

export default {
    // 获取钱包地址
    getAddress: async () => {
        await delay(200)
        return '0x634eef859bf06845f4f0a165e8430c82760239b4'
    },
    
    // 获取wBKC余额
    getWbkcBalance: async (address) => {
        await delay(300)
        return mockState.getUserBalance('wbkc')
    },
    
    // 获取E20C余额
    getE20cBalance: async (address) => {
        await delay(300)
        return mockState.getUserBalance('e20c')
    },
    
    // 获取所有余额
    getAllBalances: async (address) => {
        await delay(400)
        return {
            wbkc: mockState.getUserBalance('wbkc'),
            e20c: mockState.getUserBalance('e20c')
        }
    },
    
    // 获取USD价值 (动态计算)
    getUsdValues: async () => {
        await delay(200)
        const wbkcBalance = parseFloat(mockState.getUserBalance('wbkc'))
        const e20cBalance = parseFloat(mockState.getUserBalance('e20c'))
        
        return {
            wbkc: (wbkcBalance * 0.1).toFixed(2), // 1 wBKC = 0.1 USD
            e20c: (e20cBalance * 0.05).toFixed(2)  // 1 E20C = 0.05 USD
        }
    },
    
    // 获取总USD价值 (动态计算)
    getTotalUsdValue: async () => {
        await delay(200)
        const wbkcBalance = parseFloat(mockState.getUserBalance('wbkc'))
        const e20cBalance = parseFloat(mockState.getUserBalance('e20c'))
        
        const totalValue = (wbkcBalance * 0.1) + (e20cBalance * 0.05)
        return totalValue.toFixed(2)
    },
    
    // 更新余额（模拟交易后的余额变化）
    updateBalance: async (token, newBalance) => {
        await delay(100)
        mockState.updateUserBalance(token, newBalance)
        return true
    }
} 
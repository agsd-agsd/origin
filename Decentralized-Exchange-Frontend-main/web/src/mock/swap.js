// Swap Mock数据 - 使用状态管理器
import mockState from './mockState.js'

const delay = (ms = 300) => new Promise(resolve => setTimeout(resolve, ms))

export default {
    // 获取兑换率 (基于当前池状态动态计算)
    getExchangeRate: async () => {
        await delay()
        return mockState.getCurrentRates()
    },
    
    // 获取池信息 (从状态管理器获取实时数据)
    getPoolInfo: async () => {
        await delay()
        return mockState.getPoolState()
    },
    
    // 计算兑换输出 (使用恒定乘积公式)
    getAmountBOut: async (amountIn) => {
        await delay()
        return mockState.calculateSwapOutput(amountIn, 'e20c')
    },
    
    getAmountAOut: async (amountIn) => {
        await delay()
        return mockState.calculateSwapOutput(amountIn, 'wbkc')
    },
    
    // 执行兑换 (E20C -> wBKC) - A=E20C, B=wBKC
    swapAForB: async (amountIn) => {
        await delay(1000)
        const result = mockState.executeSwapAToB(amountIn)
        return result.txHash
    },
    
    // 执行兑换 (wBKC -> E20C) - B=wBKC, A=E20C
    swapBForA: async (amountIn) => {
        await delay(1000)
        const result = mockState.executeSwapBToA(amountIn)
        return result.txHash
    }
} 
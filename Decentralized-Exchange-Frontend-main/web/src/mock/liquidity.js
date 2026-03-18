// 流动性Mock数据 - 使用状态管理器
import mockState from './mockState.js'

const delay = (ms = 300) => new Promise(resolve => setTimeout(resolve, ms))

export default {
    // 获取流动性池信息 (从状态管理器获取实时数据)
    getPoolInfo: async () => {
        await delay()
        return mockState.getPoolState()
    },
    
    // 添加流动性
    addLiquidity: async (amountA, amountB) => {
        await delay(1000)
        try {
            const result = mockState.addLiquidity(amountA, amountB)
            return {
                success: true,
                txHash: result.txHash,
                lpTokens: result.lpTokens
            }
        } catch (error) {
            return {
                success: false,
                error: error.message
            }
        }
    },
    
    // 移除流动性
    removeLiquidity: async (lpAmount) => {
        await delay(1000)
        try {
            const result = mockState.removeLiquidity(lpAmount)
            return {
                success: true,
                txHash: result.txHash,
                amountA: result.amountA,
                amountB: result.amountB
            }
        } catch (error) {
            return {
                success: false,
                error: error.message
            }
        }
    },
    
    // 获取用户LP代币余额 (从状态管理器获取实时数据)
    getLPBalance: async (address) => {
        await delay()
        return mockState.getUserLPBalance()
    }
} 
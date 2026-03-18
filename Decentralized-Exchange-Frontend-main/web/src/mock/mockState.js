// Mock状态管理器 - 管理所有可变的模拟数据
class MockState {
    constructor() {
        this.reset()
    }

    // 重置到初始状态
    reset() {
        // 用户余额
        this.userBalances = {
            wbkc: '1000',
            e20c: '500'
        }

        // 流动性池状态
        this.poolState = {
            tokenABalance: '10000', // E20C
            tokenBBalance: '20000', // wBKC
            totalLPSupply: '14142'
        }

        // 用户LP代币余额
        this.userLPBalance = '5'

        // 交易历史
        this.transactions = [
            {
                id: '1',
                type: 'swap',
                from: 'wBKC',
                to: 'E20C',
                amount: '100',
                amountOut: '50',
                txHash: '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
                timestamp: Date.now() - 3600000,
                status: 'confirmed'
            },
            {
                id: '2',
                type: 'swap',
                from: 'E20C',
                to: 'wBKC',
                amount: '50',
                amountOut: '100',
                txHash: '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
                timestamp: Date.now() - 7200000,
                status: 'confirmed'
            },
            {
                id: '3',
                type: 'liquidity',
                action: 'add',
                amountA: '100',
                amountB: '200',
                lpTokens: '1',
                txHash: '0x9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba',
                timestamp: Date.now() - 86400000,
                status: 'confirmed'
            }
        ]
    }

    // 获取用户余额
    getUserBalance(token) {
        return this.userBalances[token] || '0'
    }

    // 更新用户余额
    updateUserBalance(token, amount) {
        this.userBalances[token] = amount.toString()
    }

    // 获取池状态
    getPoolState() {
        // 计算k值
        const k = (parseFloat(this.poolState.tokenABalance) * parseFloat(this.poolState.tokenBBalance)).toString()
        
        return {
            tokenABalance: this.poolState.tokenABalance,
            tokenBBalance: this.poolState.tokenBBalance,
            totalLPSupply: this.poolState.totalLPSupply,
            k: k
        }
    }

    // 更新池状态
    updatePoolState(newState) {
        if (newState.tokenABalance !== undefined) {
            this.poolState.tokenABalance = newState.tokenABalance.toString()
        }
        if (newState.tokenBBalance !== undefined) {
            this.poolState.tokenBBalance = newState.tokenBBalance.toString()
        }
        if (newState.totalLPSupply !== undefined) {
            this.poolState.totalLPSupply = newState.totalLPSupply.toString()
        }
    }

    // 获取用户LP余额
    getUserLPBalance() {
        return this.userLPBalance
    }

    // 更新用户LP余额
    updateUserLPBalance(amount) {
        this.userLPBalance = amount.toString()
    }

    // 执行兑换 (wBKC -> E20C)
    executeSwapBToA(amountIn) {
        const amountInNum = parseFloat(amountIn)
        const poolA = parseFloat(this.poolState.tokenABalance) // E20C
        const poolB = parseFloat(this.poolState.tokenBBalance) // wBKC
        
        // 使用恒定乘积公式计算输出
        // amountOut = (amountIn * poolA) / (poolB + amountIn)
        const amountOut = (amountInNum * poolA) / (poolB + amountInNum)
        
        // 更新用户余额
        const currentWbkc = parseFloat(this.userBalances.wbkc)
        const currentE20c = parseFloat(this.userBalances.e20c)
        
        if (currentWbkc < amountInNum) {
            throw new Error('wBKC余额不足')
        }
        
        this.updateUserBalance('wbkc', (currentWbkc - amountInNum).toFixed(6))
        this.updateUserBalance('e20c', (currentE20c + amountOut).toFixed(6))
        
        // 更新池状态
        this.updatePoolState({
            tokenABalance: poolA - amountOut,
            tokenBBalance: poolB + amountInNum
        })
        
        // 生成交易哈希
        const txHash = '0x' + Math.random().toString(16).substr(2, 64)
        
        // 添加交易记录
        this.addTransaction({
            type: 'swap',
            from: 'wBKC',
            to: 'E20C',
            amount: amountIn,
            amountOut: amountOut.toFixed(6),
            txHash: txHash
        })
        
        return { txHash, amountOut: amountOut.toString() }
    }

    // 执行兑换 (E20C -> wBKC)
    executeSwapAToB(amountIn) {
        const amountInNum = parseFloat(amountIn)
        const poolA = parseFloat(this.poolState.tokenABalance) // E20C
        const poolB = parseFloat(this.poolState.tokenBBalance) // wBKC
        
        // 使用恒定乘积公式计算输出
        // amountOut = (amountIn * poolB) / (poolA + amountIn)
        const amountOut = (amountInNum * poolB) / (poolA + amountInNum)
        
        // 更新用户余额
        const currentE20c = parseFloat(this.userBalances.e20c)
        const currentWbkc = parseFloat(this.userBalances.wbkc)
        
        if (currentE20c < amountInNum) {
            throw new Error('E20C余额不足')
        }
        
        this.updateUserBalance('e20c', (currentE20c - amountInNum).toFixed(6))
        this.updateUserBalance('wbkc', (currentWbkc + amountOut).toFixed(6))
        
        // 更新池状态
        this.updatePoolState({
            tokenABalance: poolA + amountInNum,
            tokenBBalance: poolB - amountOut
        })
        
        // 生成交易哈希
        const txHash = '0x' + Math.random().toString(16).substr(2, 64)
        
        // 添加交易记录
        this.addTransaction({
            type: 'swap',
            from: 'E20C',
            to: 'wBKC',
            amount: amountIn,
            amountOut: amountOut.toFixed(6),
            txHash: txHash
        })
        
        return { txHash, amountOut: amountOut.toString() }
    }

    // 添加流动性
    addLiquidity(amountA, amountB) {
        const amountANum = parseFloat(amountA)
        const amountBNum = parseFloat(amountB)
        const currentA = parseFloat(this.userBalances.e20c)
        const currentB = parseFloat(this.userBalances.wbkc)
        
        if (currentA < amountANum || currentB < amountBNum) {
            throw new Error('余额不足')
        }
        
        // 计算LP代币数量 (简化计算)
        const poolA = parseFloat(this.poolState.tokenABalance)
        const poolB = parseFloat(this.poolState.tokenBBalance)
        const totalLP = parseFloat(this.poolState.totalLPSupply)
        
        // LP = sqrt(amountA * amountB) 或者按比例计算
        let lpTokens
        if (totalLP === 0) {
            lpTokens = Math.sqrt(amountANum * amountBNum)
        } else {
            // 按现有比例计算
            lpTokens = Math.min(
                (amountANum / poolA) * totalLP,
                (amountBNum / poolB) * totalLP
            )
        }
        
        // 更新用户余额
        this.updateUserBalance('e20c', currentA - amountANum)
        this.updateUserBalance('wbkc', currentB - amountBNum)
        
        // 更新用户LP余额
        const currentLP = parseFloat(this.userLPBalance)
        this.updateUserLPBalance(currentLP + lpTokens)
        
        // 更新池状态
        this.updatePoolState({
            tokenABalance: poolA + amountANum,
            tokenBBalance: poolB + amountBNum,
            totalLPSupply: totalLP + lpTokens
        })
        
        const txHash = '0x' + Math.random().toString(16).substr(2, 64)
        
        // 添加交易记录
        this.addTransaction({
            type: 'liquidity',
            action: 'add',
            amountA: amountA,
            amountB: amountB,
            lpTokens: lpTokens.toFixed(6),
            txHash: txHash
        })
        
        return { txHash, lpTokens: lpTokens.toString() }
    }

    // 移除流动性
    removeLiquidity(lpAmount) {
        const lpAmountNum = parseFloat(lpAmount)
        const currentLP = parseFloat(this.userLPBalance)
        
        if (currentLP < lpAmountNum) {
            throw new Error('LP代币余额不足')
        }
        
        const poolA = parseFloat(this.poolState.tokenABalance)
        const poolB = parseFloat(this.poolState.tokenBBalance)
        const totalLP = parseFloat(this.poolState.totalLPSupply)
        
        // 计算可提取的代币数量
        const shareRatio = lpAmountNum / totalLP
        const amountA = poolA * shareRatio
        const amountB = poolB * shareRatio
        
        // 更新用户余额
        const currentA = parseFloat(this.userBalances.e20c)
        const currentB = parseFloat(this.userBalances.wbkc)
        
        this.updateUserBalance('e20c', currentA + amountA)
        this.updateUserBalance('wbkc', currentB + amountB)
        this.updateUserLPBalance(currentLP - lpAmountNum)
        
        // 更新池状态
        this.updatePoolState({
            tokenABalance: poolA - amountA,
            tokenBBalance: poolB - amountB,
            totalLPSupply: totalLP - lpAmountNum
        })
        
        const txHash = '0x' + Math.random().toString(16).substr(2, 64)
        
        // 添加交易记录
        this.addTransaction({
            type: 'liquidity',
            action: 'remove',
            amountA: amountA.toFixed(6),
            amountB: amountB.toFixed(6),
            lpTokens: lpAmount,
            txHash: txHash
        })
        
        return { 
            txHash, 
            amountA: amountA.toString(), 
            amountB: amountB.toString() 
        }
    }

    // 计算兑换输出
    calculateSwapOutput(amountIn, fromToken) {
        const amountInNum = parseFloat(amountIn)
        const poolA = parseFloat(this.poolState.tokenABalance) // E20C
        const poolB = parseFloat(this.poolState.tokenBBalance) // wBKC
        
        if (fromToken === 'wbkc') {
            // wBKC -> E20C
            return ((amountInNum * poolA) / (poolB + amountInNum)).toString()
        } else {
            // E20C -> wBKC
            return ((amountInNum * poolB) / (poolA + amountInNum)).toString()
        }
    }

    // 获取当前汇率
    getCurrentRates() {
        const poolA = parseFloat(this.poolState.tokenABalance) // E20C
        const poolB = parseFloat(this.poolState.tokenBBalance) // wBKC
        
        // 边际汇率（小额兑换的汇率）
        const rateAToB = (poolB / poolA).toFixed(6) // E20C -> wBKC
        const rateBToA = (poolA / poolB).toFixed(6) // wBKC -> E20C
        
        return {
            rateAToB: rateAToB,
            rateBToA: rateBToA
        }
    }

    // 添加交易记录
    addTransaction(tx) {
        const newTx = {
            id: (this.transactions.length + 1).toString(),
            timestamp: Date.now(),
            status: 'confirmed',
            ...tx
        }
        this.transactions.unshift(newTx)
        return newTx
    }

    // 获取交易记录
    getTransactions() {
        return [...this.transactions] // 返回副本
    }
}

// 创建全局实例
const mockState = new MockState()

export default mockState 
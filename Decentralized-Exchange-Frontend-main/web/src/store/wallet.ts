import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import blockchainService, { SwapResult } from '@/services/blockchain'

export const useWalletStore = defineStore('wallet', () => {
    // 状态
    const address = ref<string | null>(localStorage.getItem('walletAddress')) // 从本地存储初始化地址
    const isLoggedIn = ref<boolean>(!!localStorage.getItem('walletAddress')) // 根据本地存储判断初始登录状态
    const wbkcBalance = ref<string>('0') // wBKC余额
    const e20cBalance = ref<string>('0') // E20C余额
    const isLoading = ref<boolean>(false)
    const error = ref<string | null>(null)
    const transactions = ref<Array<any>>([]) // 交易记录
    
    // 计算属性
    const usdValue = computed(() => {
        try {
            // wBKC 到 USD 的汇率：1 wBKC = 0.1 USD
            if (!address.value) return '0.00';
            const balanceNum = parseFloat(wbkcBalance.value);
            if (isNaN(balanceNum)) return '0.00';
            return (balanceNum * 0.1).toFixed(2)
        } catch {
            return '0.00'
        }
    })

    // 格式化余额，显示为整数
    const formatBalance = (balance: string | number): string => {
        try {
            if (!balance) return '0';
            
            // 处理字符串类型的大整数
            if (typeof balance === 'string') {
                // 尝试转换为整数
                try {
                    const bigIntValue = BigInt(balance);
                    return bigIntValue.toString();
                } catch {
                    // 如果无法转换为BigInt，尝试作为常规数字处理
                    const num = parseFloat(balance);
                    if (!isNaN(num)) {
                        return Math.floor(num).toString();
                    }
                }
            } else if (typeof balance === 'number') {
                // 处理数字类型
                return Math.floor(balance).toString();
            }
            
            // 默认值
            return '0';
        } catch {
            return '0';
        }
    }

    // 设置钱包地址
    const setAddress = (newAddress: string | null) => {
        address.value = newAddress;
        if (newAddress) {
            localStorage.setItem('walletAddress', newAddress);
        } else {
            localStorage.removeItem('walletAddress');
        }
        isLoggedIn.value = !!newAddress; // 地址存在即视为登录
    }

    // 设置登录状态
    const setLoggedIn = (loggedIn: boolean) => {
        isLoggedIn.value = loggedIn;
        // 如果设置为未登录，同时清除地址
        if (!loggedIn) {
            setAddress(null);
        }
    }

    // 刷新余额 - 使用blockchain.js
    const refreshBalances = async () => {
        if (!isLoggedIn.value || !address.value) {
            console.warn('Wallet not unlocked, cannot refresh balances.');
            // 未登录时清空余额显示
            wbkcBalance.value = '0';
            e20cBalance.value = '0';
            return;
        }

        isLoading.value = true;
        error.value = null;

        try {
            // 调用blockchain.js获取真实余额
            const [wbkcResult, e20cResult] = await Promise.all([
                blockchainService.getWbkcBalance(address.value),
                blockchainService.getE20cBalance(address.value)
            ]);

            // 直接使用原始余额值，不进行任何转换
            wbkcBalance.value = wbkcResult;
            e20cBalance.value = e20cResult;
            
        } catch (err: any) {
            console.error('获取余额失败：', err);
            error.value = '获取余额失败，请稍后再试';
        } finally {
            isLoading.value = false;
        }
    }

    // 获取预计兑换金额
    const getEstimatedOutput = async (fromCurrency: string, amount: string) => {
        if (!amount || parseFloat(amount) <= 0) return '0';
        
        try {
            // 直接使用原始数值，但修正代币映射关系
            let outputAmount;
            
            if (fromCurrency === 'wBKC') {
                // wBKC对应代币B，调用getAmountAOut
                outputAmount = await blockchainService.getAmountAOut(amount);
            } else {
                // E20C对应代币A，调用getAmountBOut
                outputAmount = await blockchainService.getAmountBOut(amount);
            }
            
            // 不进行fromWei转换，直接返回原始输出量
            return outputAmount;
        } catch (err) {
            console.error('获取预计兑换金额失败：', err);
            return '0';
        }
    }

    // 获取当前汇率
    const getCurrentRates = async () => {
        try {
            const rates = await blockchainService.getExchangeRate();
            // 现在汇率是简单的数字字符串，直接使用
            return {
                // 修正映射关系：wBKC对应B，E20C对应A
                wbkcToE20c: rates.rateBToA,  // B→A: wBKC→E20C (1 wBKC = 0.5 E20C)
                e20cToWbkc: rates.rateAToB,  // A→B: E20C→wBKC (1 E20C = 2 wBKC)
                rateAToB: rates.rateAToB,  // 保留原字段，表示A→B (E20C→wBKC)
                rateBToA: rates.rateBToA   // 保留原字段，表示B→A (wBKC→E20C)
            };
        } catch (err) {
            console.error('获取汇率失败：', err);
            return {
                wbkcToE20c: '0.5',
                e20cToWbkc: '2',
                rateAToB: '2',
                rateBToA: '0.5'
            };
        }
    }

    // 获取两种代币之间的汇率 (为了兼容SwapView)
    const getExchangeRate = async (fromCurrency: string, toCurrency: string) => {
        try {
            const rates = await getCurrentRates()
            
            if (fromCurrency === 'wBKC' && toCurrency === 'E20C') {
                // wBKC -> E20C, 使用rates.wbkcToE20c
                const rate = rates.wbkcToE20c
                // 现在汇率是简单的数字字符串
                if (typeof rate === 'string') {
                    return parseFloat(rate).toFixed(2)
                }
                return '0.50' // 默认值：1 wBKC = 0.5 E20C
            } else if (fromCurrency === 'E20C' && toCurrency === 'wBKC') {
                // E20C -> wBKC, 使用rates.e20cToWbkc  
                const rate = rates.e20cToWbkc
                // 现在汇率是简单的数字字符串
                if (typeof rate === 'string') {
                    return parseFloat(rate).toFixed(2)
                }
                return '2.00' // 默认值：1 E20C = 2 wBKC
            }
            
            return '1.00' // 默认汇率
        } catch (error) {
            console.error('获取汇率失败:', error)
            // 返回默认汇率
            if (fromCurrency === 'wBKC' && toCurrency === 'E20C') {
                return '0.50'
            } else if (fromCurrency === 'E20C' && toCurrency === 'wBKC') {
                return '2.00'
            }
            return '1.00'
        }
    }

    // 执行代币兑换 - 使用blockchain.js
    const swap = async (params: { fromCurrency: string; toCurrency: string; amount: string }) => {
        if (!isLoggedIn.value) {
            error.value = '请先解锁钱包';
            return { success: false, error: error.value };
        }

        isLoading.value = true;
        error.value = null;
        
        try {
            const { fromCurrency, toCurrency, amount } = params;
            
            // 验证输入
            const inputAmount = parseFloat(amount);
            if (isNaN(inputAmount) || inputAmount <= 0) {
                error.value = '请输入有效金额';
                return { success: false, error: error.value };
            }

            // 检查余额是否足够
            if (fromCurrency === 'wBKC' && inputAmount > parseFloat(wbkcBalance.value)) {
                error.value = 'wBKC 余额不足';
                return { success: false, error: error.value };
            }
            if (fromCurrency === 'E20C' && inputAmount > parseFloat(e20cBalance.value)) {
                error.value = 'E20C 余额不足';
                return { success: false, error: error.value };
            }

            // 转换为wei - 在Mock模式下使用原始数字
            let amountForSwap: string;
            try {
                // 检查是否为Mock模式，通过检查CONFIG来判断
                const CONFIG = await import('@/config.js').then(m => m.CONFIG || m.default);
                if (CONFIG.USE_MOCK_DATA) {
                    // Mock模式：直接使用数字
                    amountForSwap = amount;
                } else {
                    // 真实模式：转换为wei
                    amountForSwap = blockchainService.toWei(amount);
                }
            } catch {
                // 如果无法获取配置，尝试toWei，失败则使用原数字
                try {
                    amountForSwap = blockchainService.toWei(amount);
                } catch {
                    amountForSwap = amount;
                }
            }
            
            // 调用合适的兑换方法
            let txHash: string;
            let outputAmount: string = '0';
            
            if (fromCurrency === 'wBKC' && toCurrency === 'E20C') {
                // 修正映射关系：wBKC对应代币B，E20C对应代币A
                const result = await blockchainService.swapBforA(amountForSwap);
                if (typeof result === 'string') {
                    txHash = result;
                } else {
                    txHash = result.txHash;
                    outputAmount = result.outputAmount;
                }
            } else if (fromCurrency === 'E20C' && toCurrency === 'wBKC') {
                // 修正映射关系：E20C对应代币A，wBKC对应代币B
                const result = await blockchainService.swapAforB(amountForSwap);
                if (typeof result === 'string') {
                    txHash = result;
                } else {
                    txHash = result.txHash;
                    outputAmount = result.outputAmount;
                }
            } else {
                error.value = '不支持的兑换对';
                return { success: false, error: error.value };
            }
            
            
            // 刷新余额
            await refreshBalances();
            
            // 添加交易记录，使用实际输出金额而不是估算值
            const finalOutputAmount = outputAmount !== '0' ? 
                outputAmount : 
                await getEstimatedOutput(fromCurrency, amount);
                
            addTransaction({
                type: 'swap',
                status: 'confirmed',
                amount: amount,
                currency: fromCurrency,
                toAmount: finalOutputAmount,
                toCurrency: toCurrency,
                timestamp: Date.now(),
                from: address.value,
                to: address.value,
                txHash: txHash
            });
            
            return { 
                success: true, 
                txHash,
                outputAmount: finalOutputAmount
            };
        } catch (e: any) {
            console.error('兑换失败:', e);
            error.value = e.message || '兑换失败，请稍后再试';
            return { success: false, error: error.value };
        } finally {
            isLoading.value = false;
        }
    }

    // 添加交易记录
    const addTransaction = (tx: any) => {
        tx.id = `tx-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
        transactions.value.unshift(tx);
    }

    // 添加示例交易记录（仅用于测试）
    const addDemoTransactions = (txs: Array<any>) => {
        transactions.value = [...txs, ...transactions.value];
    }

    // 初始化钱包
    const init = async () => {
        const storedAddress = localStorage.getItem('walletAddress');
        if (storedAddress) {
            address.value = storedAddress;
            isLoggedIn.value = true;
            await refreshBalances();
        } else {
            address.value = null;
            isLoggedIn.value = false;
        }
    }

    // 重置钱包状态
    const resetWalletState = () => {
        setAddress(null);
        isLoggedIn.value = false;
        wbkcBalance.value = '0';
        e20cBalance.value = '0';
        isLoading.value = false;
        error.value = null;
        localStorage.removeItem('walletPassword');
    }

    return {
        address,
        isLoggedIn,
        wbkcBalance,
        e20cBalance,
        isLoading,
        error,
        transactions,
        usdValue,
        formatBalance,
        refreshBalances,
        swap,
        getEstimatedOutput,
        getCurrentRates,
        getExchangeRate,
        init,
        setAddress,
        setLoggedIn,
        resetWalletState,
        addDemoTransactions
    }
})
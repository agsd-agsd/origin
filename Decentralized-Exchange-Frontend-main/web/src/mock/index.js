// Mock数据主入口文件
import mockWallet from './wallet.js'
import mockSwap from './swap.js'
import mockLiquidity from './liquidity.js'
import mockTransactions from './transactions.js'

const mockData = {
    wallet: mockWallet,
    swap: mockSwap,
    liquidity: mockLiquidity,
    transactions: mockTransactions
}

export default mockData 
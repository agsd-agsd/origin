// DEX演示系统配置文件
// 请根据您的实际部署情况填写以下配置信息

export const CONFIG = {
    // 运行模式配置
    // true: 使用Mock数据（演示模式）
    // false: 使用真实区块链交互（生产模式）
    USE_MOCK_DATA: true,
    
    // 区块链网络配置
    RPC_URL: 'http://127.0.0.1:25484/',
    
    // 演示账户地址
    DEMO_ACCOUNT: '0x634eef859bf06845f4f0a165e8430c82760239b4',

    // 钱包私钥 (生产环境请勿硬编码，仅用于演示)
    PRIVATE_KEY: '35852383431271913866751802705784976390714188045451917526323106147384591776485',
    
    // 合约地址 (请替换为实际部署的地址)
    CONTRACTS: {
        WBKC: '0x605Ea3f67d09bdFf604c7B0d9FE8A477cdF831fb', // wBKC代币合约地址
        E20C: '0xe12551Cb9E03B1c20D944943C82fB52A07302E30', // E20C代币合约地址
        AMM: '0x76270242b5E3Ec5282e293e645026d409bCdc019'   // AMM兑换合约地址
    },
    
    // 合约ABI (只包含需要使用的接口)
    ABIS: {
        // wBKC代币合约ABI (只保留余额查询)
        WBKC: [
            {
                "constant": true,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }
        ],
        
        // E20C代币合约ABI (只保留余额查询)
        E20C: [
            {
                "constant": true,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }
        ],
        
        // AMM兑换合约ABI (只保留需要使用的方法)
        AMM: [
            {
                "constant": false,
                "inputs": [{"name": "amountIn", "type": "uint256"}],
                "name": "swapAForB",
                "outputs": [{"name": "amountOut", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": false,
                "inputs": [{"name": "amountIn", "type": "uint256"}],
                "name": "swapBForA",
                "outputs": [{"name": "amountOut", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": true,
                "inputs": [],
                "name": "getPoolInfo",
                "outputs": [
                    {"name": "tokenABalance", "type": "uint256"},
                    {"name": "tokenBBalance", "type": "uint256"},
                    {"name": "totalLPSupply", "type": "uint256"},
                    {"name": "k", "type": "uint256"}
                ],
                "type": "function"
            },
            {
                "constant": true,
                "inputs": [{"name": "amountAIn", "type": "uint256"}],
                "name": "getAmountBOut",
                "outputs": [{"name": "amountBOut", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": true,
                "inputs": [{"name": "amountBIn", "type": "uint256"}],
                "name": "getAmountAOut",
                "outputs": [{"name": "amountAOut", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": true,
                "inputs": [],
                "name": "getExchangeRate",
                "outputs": [
                    {"name": "rateAToB", "type": "uint256"},
                    {"name": "rateBToA", "type": "uint256"}
                ],
                "type": "function"
            }
        ]
    },
    
    // 代币配置
    TOKENS: {
        WBKC: {
            symbol: 'wBKC',
            decimals: 18,
            name: 'Wrapped BKC'
        },
        E20C: {
            symbol: 'E20C',
            decimals: 18,
            name: 'E20C Token'
        }
    }
};

// 导出配置
export default CONFIG;

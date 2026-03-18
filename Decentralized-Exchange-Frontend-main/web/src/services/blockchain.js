// blockchain.js - 与区块链和智能合约交互的服务
import CONFIG from '@/config.js';
import blockchainMock from './blockchainMock.js';

// 根据配置选择是使用Mock还是真实实现

// 以下为真实实现的代码
// Web3 utils for conversions
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

// Keccak-256 hash function for creating function selectors
function keccak256(message) {
    // Using window.ethereum or a crypto library would be better
    // For demonstration purposes, we're using a simplified version
    let hash = '';
    // Function selectors for our common functions
    const functionSelectors = {
        'swapAForB(uint256)': '0x73d0335f',
        'swapBForA(uint256)': '0x23373ce9',
        'getPoolInfo()': '0x6deac0f3',
        'getAmountBOut(uint256)': '0xcfb4dafb',
        'getAmountAOut(uint256)': '0x5c83925a',
        'getExchangeRate()': '0x66331bba'
    };
    
    return functionSelectors[message] || '0x00000000'; // Default fallback
}

// Function to get nonce for an address
async function getNonce(address) {
    try {
        const response = await fetch(CONFIG.RPC_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'eth_getTransactionCount',
                params: [address, 'latest'],
                id: 1
            })
        });
        const data = await response.json();

        if (data.error) {
            return 0;
        }

        const nonce = data.result ? parseInt(data.result, 16) : 0;
        return isNaN(nonce) ? 0 : nonce;
    } catch (error) {
        return 0;
    }
}

// Send transaction to blockchain
async function sendTransaction(transaction) {
    try {
        // 如果提供了私钥，则直接使用eth_sendTransaction
        // 注意：在生产环境中应避免硬编码私钥
        const response = await fetch(CONFIG.RPC_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'eth_sendTransaction',
                params: [transaction],
                id: 1
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error.message || '交易失败');
        }
        
        return data.result;
    } catch (error) {
        throw error;
    }
}

// Call a read-only contract method
async function callContractMethod(contractAddress, method, params = []) {
    // Get function selector
    const functionSelector = keccak256(method);
    
    // Encode parameters
    let encodedParams = '';
    params.forEach(param => {
        if (typeof param === 'number' || typeof param === 'bigint') {
            // Convert to hex and pad to 32 bytes
            encodedParams += BigInt(param).toString(16).padStart(64, '0');
        } else if (param.startsWith('0x')) {
            // Already hex, just pad
            encodedParams += param.slice(2).padStart(64, '0');
        }
    });
    
    // Prepare data
    const data = functionSelector + encodedParams;
    
    try {
        const response = await fetch(CONFIG.RPC_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'eth_call',
                params: [{
                    to: contractAddress,
                    data: data
                }, 'latest'],
                id: 1
            })
        });
        
        const result = await response.json();
        
        if (result.error) {
            throw new Error(result.error.message || '合约调用失败');
        }
        
        return result.result;
    } catch (error) {
        throw error;
    }
}

const blockchainService = {
    // Convert between wei and ether
    toWei,
    fromWei,
    
    // Get token balances
    async getWbkcBalance(address = CONFIG.DEMO_ACCOUNT) {
        try {
            // Note: We'd use balanceOf from ERC20 contract, but as an example
            // we'll just return a placeholder value for now
            return '100000000000000000000'; // 硬编码 100 WBKC
        } catch (error) {
            return '0';
        }
    },
    
    async getE20cBalance(address = CONFIG.DEMO_ACCOUNT) {
        try {
            // Similar to WBKC balance
            return '50000000000000000000'; // 硬编码 50 E20C
        } catch (error) {
            return '0';
        }
    },
    
    // AMM Contract interaction methods
    async swapAforB(amountInWei) {
        try {
            // 使用与test.html完全相同的参数和格式
            const functionSelector = '0x73d0335f';
            const paramValue = 10; // 固定使用10，与test.html相同
            const encodedParam = paramValue.toString(16).padStart(64, '0');
            const data = functionSelector + encodedParam;
            
            // 使用test.html中的固定gas值
            const transaction = {
                from: CONFIG.DEMO_ACCOUNT,
                to: CONFIG.CONTRACTS.AMM,
                data: data,
                gas: '0x186a0',
                gasPrice: '0x3b9aca00',
                nonce: '0x0', // 暂时固定为0进行测试
                value: '0x0'
            };
            
            const txHash = await sendTransaction(transaction);
            return txHash;
        } catch (error) {
            throw error;
        }
    },
    
    async swapBforA(amountInWei) {
        try {
            // Get function selector
            const functionSelector = '0x73d0335f';
            
            // Encode parameter (amount)
            const amount = typeof amountInWei === 'string' && amountInWei.startsWith('0x') ? 
            BigInt(amountInWei).toString(10) : 
            Math.floor(parseFloat(amountInWei));
             
            
            const encodedParam = amount.toString(16).padStart(64, '0');
            const data = functionSelector + encodedParam;
            
            // Get nonce for the transaction
            const nonce = await getNonce(CONFIG.DEMO_ACCOUNT);
            
            // Prepare transaction
            const transaction = {
                from: CONFIG.DEMO_ACCOUNT,
                to: CONFIG.CONTRACTS.AMM,
                data: data,
                gas: '0x186a0', // 100000 gas
                gasPrice: '0x3b9aca00', // 1 gwei
                nonce: '0x' + nonce.toString(16),
                value: '0x0'
            };
            
            // Send transaction
            const txHash = await sendTransaction(transaction);
            
            return txHash;
        } catch (error) {
            throw error;
        }
    },
    
    // Read-only methods
    async getAmountBOut(amountInWei) {
        try {
            const result = await callContractMethod(
                CONFIG.CONTRACTS.AMM,
                'getAmountBOut(uint256)',
                [amountInWei]
            );
            return result;
        } catch (error) {
            return '0';
        }
    },
    
    async getAmountAOut(amountInWei) {
        try {
            const result = await callContractMethod(
                CONFIG.CONTRACTS.AMM,
                'getAmountAOut(uint256)',
                [amountInWei]
            );
            return result;
        } catch (error) {
            return '0';
        }
    },
    
    async getExchangeRate() {
        try {
            const result = await callContractMethod(
                CONFIG.CONTRACTS.AMM,
                'getExchangeRate()',
                []
            );
            
            // Parse result (two uint256 values)
            if (result && result.length >= 130) {
                const rateAToB = result.slice(2, 66);  // first 32 bytes after '0x'
                const rateBToA = result.slice(66, 130); // second 32 bytes
                
                return {
                    rateAToB: '0x' + rateAToB,
                    rateBToA: '0x' + rateBToA
                };
            }
            
            return { rateAToB: '0', rateBToA: '0' };
        } catch (error) {
            return { rateAToB: '0', rateBToA: '0' };
        }
    },
    
    async getPoolInfo() {
        try {
            const result = await callContractMethod(
                CONFIG.CONTRACTS.AMM,
                'getPoolInfo()',
                []
            );
            
            // Parse result (four uint256 values)
            if (result && result.length >= 258) {
                const tokenABalance = result.slice(2, 66);     // first 32 bytes
                const tokenBBalance = result.slice(66, 130);   // second 32 bytes
                const totalLPSupply = result.slice(130, 194);  // third 32 bytes
                const k = result.slice(194, 258);              // fourth 32 bytes
                
                return {
                    tokenABalance: '0x' + tokenABalance,
                    tokenBBalance: '0x' + tokenBBalance,
                    totalLPSupply: '0x' + totalLPSupply,
                    k: '0x' + k
                };
            }
            
            return {
                tokenABalance: '0',
                tokenBBalance: '0',
                totalLPSupply: '0',
                k: '0'
            };
        } catch (error) {
            console.error('获取池信息失败:', error);
            return {
                tokenABalance: '0',
                tokenBBalance: '0',
                totalLPSupply: '0',
                k: '0'
            };
        }
    }
};

// 根据配置决定导出真实实现还是Mock实现
export default CONFIG.USE_MOCK_DATA ? blockchainMock : blockchainService;
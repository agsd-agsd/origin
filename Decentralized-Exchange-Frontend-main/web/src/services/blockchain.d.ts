// blockchain.d.ts
declare module '@/services/blockchain' {
    export interface PoolInfo {
        tokenABalance: string;
        tokenBBalance: string;
        totalLPSupply: string;
        k: string;
    }
    
    export interface ExchangeRate {
        rateAToB: string;
        rateBToA: string;
    }
    
    export interface SwapResult {
        txHash: string;
        outputAmount: string;
    }
    
    const blockchainService: {
        getWbkcBalance(address?: string): Promise<string>;
        getE20cBalance(address?: string): Promise<string>;
        swapAforB(amountInWei: string): Promise<SwapResult>;
        swapBforA(amountInWei: string): Promise<string | SwapResult>;
        getAmountBOut(amountInWei: string): Promise<string>;
        getAmountAOut(amountInWei: string): Promise<string>;
        getExchangeRate(): Promise<ExchangeRate>;
        getPoolInfo(): Promise<PoolInfo>;
        fromWei(hexWei: string): string;
        toWei(ether: string | number): string;
    };
    
    export default blockchainService;
}

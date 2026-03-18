// API 基础配置
const BASE_URL = 'http://127.0.0.1:8545/broker-fi'

// 定义请求和响应类型
export interface ApiResponse<T = any> {
    success: boolean
    data?: T
    error?: string
    code?: string
    message?: string
    msg?: string
}

export interface BalanceResponse {
    balance: string
}

export interface SwapRequest {
    addr: string  // 账户地址
    token: string // 交换金额（整数）
    type_from: 'wBKC' | 'E20C' // 源货币类型
    type_to: 'wBKC' | 'E20C'   // 目标货币类型
}

// API 服务
export class ApiService {
    /**
     * 获取账户余额
     * @param address 账户地址
     * @param type 货币类型
     */
    static async getBalance(address: string, type: 'wBKC' | 'E20C'): Promise<ApiResponse<BalanceResponse>> {
        try {
            const url = `${BASE_URL}/query-g?addr=${address}&type=${type}`

            const response = await fetch(url)
            const data = await response.json()

            return {
                success: true,
                data
            }
        } catch (error) {
            console.error('获取余额失败:', error)
            return {
                success: false,
                error: error instanceof Error ? error.message : '网络请求失败'
            }
        }
    }

    /**
     * 执行代币兑换
     * @param params 兑换参数
     */
    static async swap(params: SwapRequest): Promise<ApiResponse> {
        try {
            // 确保金额是整数
            const intAmount = Math.floor(parseFloat(params.token))

            const url = `${BASE_URL}/exchange?addr=${params.addr}&token=${intAmount}&type_from=${params.type_from}&type_to=${params.type_to}`

            const response = await fetch(url)
            const data = await response.json()

            // 处理响应
            if (data.msg === 'Done!' || data.code === '0') {
                return {
                    success: true,
                    data
                }
            } else {
                return {
                    success: false,
                    error: data.error || data.message || data.msg || '兑换失败',
                    ...data
                }
            }
        } catch (error) {
            console.error('兑换操作失败:', error)
            return {
                success: false,
                error: error instanceof Error ? error.message : '网络请求失败'
            }
        }
    }
} 
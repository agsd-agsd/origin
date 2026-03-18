<template>
  <v-container>
    <v-card class="pa-6 rounded-lg" elevation="1">
      <v-card-title class="text-h6 font-weight-bold d-flex align-center">
        <v-icon color="primary" class="mr-2">mdi-history</v-icon>
        交易历史
        <v-spacer></v-spacer>
        <v-chip-group v-model="selectedType" mandatory>
          <v-chip label size="small" value="all">全部</v-chip>
          <v-chip label size="small" value="swap">兑换</v-chip>
          <v-chip label size="small" value="send">发送</v-chip>
          <v-chip label size="small" value="receive">接收</v-chip>
        </v-chip-group>
      </v-card-title>
      
      <v-card-text class="pa-0">
        <v-list class="py-0">
          <template v-if="filteredTransactions.length > 0">
            <template v-for="(tx, index) in filteredTransactions" :key="tx.id">
              <!-- 兑换交易 -->
              <v-list-item v-if="tx.type === 'swap'" class="py-3">
                <template v-slot:prepend>
                  <v-avatar color="warning" variant="tonal" size="36">
                    <v-icon>mdi-swap-horizontal</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title class="font-weight-medium">
                  兑换 {{ tx.currency }} 换 {{ tx.toCurrency }}
                  <v-chip v-if="tx.status === 'pending'" size="x-small" color="warning" class="ml-2">待确认</v-chip>
                </v-list-item-title>
                <v-list-item-subtitle class="text-caption text-medium-emphasis">
                  {{ tx.amount }} {{ tx.currency }} → {{ tx.toAmount }} {{ tx.toCurrency }} | {{ formatDate(tx.timestamp) }}
                </v-list-item-subtitle>
                <template v-slot:append>
                  <div class="text-end">
                    <div class="font-weight-medium text-error">- {{ tx.amount }} {{ tx.currency }}</div>
                    <div class="text-caption text-success">+ {{ tx.toAmount }} {{ tx.toCurrency }}</div>
                  </div>
                </template>
              </v-list-item>
              
              <!-- 发送交易 -->
              <v-list-item v-else-if="tx.type === 'send'" class="py-3">
                <template v-slot:prepend>
                  <v-avatar color="error" variant="tonal" size="36">
                    <v-icon>mdi-arrow-top-right</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title class="font-weight-medium">
                  发送 {{ tx.currency }}
                  <v-chip v-if="tx.status === 'pending'" size="x-small" color="warning" class="ml-2">待确认</v-chip>
                </v-list-item-title>
                <v-list-item-subtitle class="text-caption text-medium-emphasis">
                  至 {{ tx.to }} | {{ formatDate(tx.timestamp) }}
                </v-list-item-subtitle>
                <template v-slot:append>
                  <div class="text-end">
                    <div class="font-weight-medium text-error">- {{ tx.amount }} {{ tx.currency }}</div>
                    <div class="text-caption text-medium-emphasis">
                      ≈ ${{ formatUsdValue(tx.currency, tx.amount) }} USD
                    </div>
                  </div>
                </template>
              </v-list-item>
              
              <!-- 接收交易 -->
              <v-list-item v-else-if="tx.type === 'receive'" class="py-3">
                <template v-slot:prepend>
                  <v-avatar color="success" variant="tonal" size="36">
                    <v-icon>mdi-arrow-bottom-left</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title class="font-weight-medium">
                  收到 {{ tx.currency }}
                  <v-chip v-if="tx.status === 'pending'" size="x-small" color="warning" class="ml-2">待确认</v-chip>
                </v-list-item-title>
                <v-list-item-subtitle class="text-caption text-medium-emphasis">
                  从 {{ tx.from }} | {{ formatDate(tx.timestamp) }}
                </v-list-item-subtitle>
                <template v-slot:append>
                  <div class="text-end">
                    <div class="font-weight-medium text-success">+ {{ tx.amount }} {{ tx.currency }}</div>
                    <div class="text-caption text-medium-emphasis">
                      ≈ ${{ formatUsdValue(tx.currency, tx.amount) }} USD
                    </div>
                  </div>
                </template>
              </v-list-item>
              
              <v-divider v-if="index < filteredTransactions.length - 1" inset></v-divider>
            </template>
          </template>
          
          <v-list-item v-else class="text-center py-4">
            <v-list-item-title class="text-medium-emphasis">
              暂无交易记录
            </v-list-item-title>
          </v-list-item>
        </v-list>
      </v-card-text>
      
      <v-card-actions class="pt-2">
        <v-pagination
          v-if="pages > 1"
          v-model="currentPage"
          :length="pages"
          :total-visible="5"
          rounded
        ></v-pagination>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useWalletStore } from '@/store/wallet'

const walletStore = useWalletStore()

// 筛选类型
const selectedType = ref('all')
const currentPage = ref(1)
const pageSize = 10

// 按类型筛选交易
const filteredTransactions = computed(() => {
  let transactions = walletStore.transactions || []
  
  // 按类型筛选
  if (selectedType.value !== 'all') {
    transactions = transactions.filter(tx => tx.type === selectedType.value)
  }
  
  // 计算分页
  const startIndex = (currentPage.value - 1) * pageSize
  const endIndex = startIndex + pageSize
  
  return transactions.slice(startIndex, endIndex)
})

// 总页数
const pages = computed(() => {
  if (!walletStore.transactions) return 1
  
  let filteredTx = walletStore.transactions
  if (selectedType.value !== 'all') {
    filteredTx = filteredTx.filter(tx => tx.type === selectedType.value)
  }
  
  return Math.max(1, Math.ceil(filteredTx.length / pageSize))
})

// 日期格式化
const formatDate = (timestamp) => {
  if (!timestamp) return ''
  
  const date = new Date(timestamp)
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) {
    return `今天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  } else if (diffDays === 1) {
    return `昨天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  } else {
    return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  }
}

// 计算USD价值
const formatUsdValue = (currency, amount) => {
  try {
    const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount
    if (isNaN(numAmount)) return '0.00'
    
    let usdValue = 0
    if (currency === 'wBKC') {
      // 1 wBKC = 0.1 USD
      usdValue = numAmount * 0.1
    } else if (currency === 'E20C') {
      // 1 E20C = 0.01 USD
      usdValue = numAmount * 0.01
    }
    
    return usdValue.toFixed(2)
  } catch {
    return '0.00'
  }
}
</script>

<style scoped>
/* 历史页面样式 */
</style> 
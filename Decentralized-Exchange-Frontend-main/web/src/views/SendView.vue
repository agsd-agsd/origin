<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" md="8" lg="6">
        <v-card class="rounded-lg" elevation="3">
          <v-card-title class="d-flex align-center px-4 py-3 bg-primary-lighten-5">
            <v-icon size="large" color="primary" class="mr-2">mdi-send</v-icon>
            <span class="text-h6 font-weight-bold">发送代币</span>
          </v-card-title>

          <v-card-text class="px-4 py-5">
            <!-- 发送表单 -->
            <v-form @submit.prevent="handleSend">
              <!-- 收款地址 -->
              <div class="mb-4">
                <label class="text-subtitle-2 font-weight-medium d-block mb-2">收款地址</label>
                <v-text-field
                  v-model="toAddress"
                  placeholder="输入有效的钱包地址"
                  variant="outlined"
                  density="comfortable"
                  :error-messages="addressError"
                  prepend-inner-icon="mdi-wallet-outline"
                  clearable
                  hide-details="auto"
                  class="mb-1"
                ></v-text-field>
                <div class="d-flex justify-end">
                  <v-btn size="small" variant="text" prepend-icon="mdi-history" @click="showRecipientHistory = true">
                    最近收款人
                  </v-btn>
                </div>
              </div>

              <!-- 代币类型选择 -->
              <div class="mb-4">
                <label class="text-subtitle-2 font-weight-medium d-block mb-2">选择代币</label>
                <v-select
                  v-model="selectedCurrency"
                  :items="currencies"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                >
                  <template v-slot:selection="{ item }">
                    <div class="d-flex align-center">
                      <v-avatar :color="getCurrencyColor(item.value)" size="28" class="mr-2">
                        <span class="text-caption font-weight-bold text-white">{{ getCurrencySymbol(item.value) }}</span>
                      </v-avatar>
                      <div>
                        <span class="font-weight-medium">{{ item.title }}</span>
                        <span class="text-caption text-medium-emphasis ml-2">
                          (可用: {{ formatBalance(getBalanceForCurrency(item.value)) }})
                        </span>
                      </div>
                    </div>
                  </template>
                  <template v-slot:item="{ item, props }">
                    <v-list-item v-bind="props">
                      <template v-slot:prepend>
                        <v-avatar :color="getCurrencyColor(item.value)" size="28">
                          <span class="text-caption font-weight-bold text-white">{{ getCurrencySymbol(item.value) }}</span>
                        </v-avatar>
                      </template>
                      <v-list-item-title>{{ item.title }}</v-list-item-title>
                      <v-list-item-subtitle>
                        可用: {{ formatBalance(getBalanceForCurrency(item.value)) }}
                      </v-list-item-subtitle>
                    </v-list-item>
                  </template>
                </v-select>
              </div>

              <!-- 发送金额 -->
              <div class="mb-5">
                <div class="d-flex justify-space-between align-center mb-2">
                  <label class="text-subtitle-2 font-weight-medium">发送金额</label>
                  <span class="text-caption text-medium-emphasis">
                    可用: {{ formatBalance(getBalanceForCurrency(selectedCurrency)) }} {{ selectedCurrency }}
                  </span>
                </div>
                <v-text-field
                  v-model="amount"
                  type="number"
                  placeholder="0.00"
                  variant="outlined"
                  density="comfortable"
                  :error-messages="amountError"
                  class="mb-1"
                  hide-details="auto"
                >
                  <template v-slot:append>
                    <v-btn
                      size="small"
                      variant="text"
                      color="primary"
                      @click="setMaxAmount"
                    >
                      最大
                    </v-btn>
                  </template>
                </v-text-field>
                <div class="text-caption text-medium-emphasis text-end" v-if="amount && !amountError">
                  ≈ ${{ calculateUsdValue() }} USD
                </div>
              </div>

              <!-- 备注信息 -->
              <div class="mb-5">
                <label class="text-subtitle-2 font-weight-medium d-block mb-2">备注信息 (可选)</label>
                <v-textarea
                  v-model="memo"
                  placeholder="添加交易备注..."
                  variant="outlined"
                  density="comfortable"
                  rows="2"
                  hide-details
                  counter="100"
                  maxlength="100"
                ></v-textarea>
              </div>

              <!-- 交易详情 -->
              <v-card class="mb-5 rounded-lg" variant="outlined">
                <v-list density="compact">
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon size="small" color="primary">mdi-information-outline</v-icon>
                    </template>
                    <v-list-item-title>交易详情</v-list-item-title>
                  </v-list-item>

                  <v-divider></v-divider>

                  <v-list-item>
                    <v-list-item-title class="text-caption">发送金额</v-list-item-title>
                    <v-list-item-subtitle class="text-end">
                      {{ amount || '0.00' }} {{ selectedCurrency }}
                    </v-list-item-subtitle>
                  </v-list-item>

                  <v-list-item>
                    <v-list-item-title class="text-caption">网络手续费</v-list-item-title>
                    <v-list-item-subtitle class="text-end">0.01 {{ selectedCurrency }}</v-list-item-subtitle>
                  </v-list-item>

                  <v-list-item>
                    <v-list-item-title class="text-caption text-primary font-weight-bold">总计</v-list-item-title>
                    <v-list-item-subtitle class="text-end text-primary font-weight-bold">
                      {{ calculateTotalAmount() }} {{ selectedCurrency }}
                    </v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-card>

              <v-btn
                block
                type="submit"
                color="primary"
                size="large"
                class="rounded-lg font-weight-bold"
                :loading="isLoading"
                :disabled="!isFormValid || isLoading"
                height="50"
              >
                {{ getSendButtonText() }}
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>

        <!-- 近期发送记录 -->
        <v-card class="mt-6 rounded-lg" elevation="2">
          <v-toolbar flat density="compact" color="background">
            <v-toolbar-title class="font-weight-bold">近期发送记录</v-toolbar-title>
            <v-spacer></v-spacer>
            <v-btn variant="text" size="small" to="/history" append-icon="mdi-chevron-right">
              查看全部
            </v-btn>
          </v-toolbar>

          <v-divider></v-divider>

          <v-list v-if="sendHistory.length > 0" class="py-0">
            <template v-for="(transaction, index) in sendHistory" :key="transaction.id">
              <v-list-item class="py-2">
                <template v-slot:prepend>
                  <v-avatar color="error" variant="tonal" size="38">
                    <v-icon size="small">mdi-arrow-top-right</v-icon>
                  </v-avatar>
                </template>

                <v-list-item-title>
                  发送 {{ transaction.amount }} {{ transaction.currency }}
                </v-list-item-title>
                
                <v-list-item-subtitle class="text-caption text-medium-emphasis">
                  至: {{ formatAddress(transaction.to) }} | {{ new Date(transaction.timestamp).toLocaleString() }}
                </v-list-item-subtitle>
                
                <template v-slot:append>
                  <v-chip
                    size="small"
                    :color="transaction.status === 'confirmed' ? 'success' : 'warning'"
                    variant="tonal"
                  >
                    {{ transaction.status === 'confirmed' ? '已确认' : '待确认' }}
                  </v-chip>
                </template>
              </v-list-item>
              <v-divider v-if="index < sendHistory.length - 1"></v-divider>
            </template>
          </v-list>

          <v-card-text v-else class="text-center py-8">
            <v-icon size="large" color="grey" class="mb-2">mdi-send</v-icon>
            <div class="text-body-1 text-medium-emphasis">暂无发送记录</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 收款人历史对话框 -->
    <v-dialog v-model="showRecipientHistory" max-width="400">
      <v-card>
        <v-toolbar color="primary" density="compact">
          <v-toolbar-title class="text-subtitle-1">最近收款人</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="showRecipientHistory = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-toolbar>
        <v-list density="compact">
          <v-list-item
            v-for="recipient in recentRecipients"
            :key="recipient.address"
            @click="selectRecipient(recipient.address)"
          >
            <template v-slot:prepend>
              <v-avatar color="primary" variant="tonal" size="36">
                <v-icon size="small">mdi-account</v-icon>
              </v-avatar>
            </template>
            <v-list-item-title>{{ formatAddress(recipient.address) }}</v-list-item-title>
            <v-list-item-subtitle>{{ recipient.date }}</v-list-item-subtitle>
          </v-list-item>
        </v-list>
      </v-card>
    </v-dialog>

    <!-- 交易确认对话框 -->
    <v-dialog v-model="showConfirmDialog" max-width="400">
      <v-card>
        <v-toolbar color="primary" density="compact">
          <v-toolbar-title class="text-subtitle-1">确认交易</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="showConfirmDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-toolbar>
        <v-card-text class="pa-4">
          <p class="text-body-1 mb-3">您即将发送以下交易:</p>
          
          <v-card variant="outlined" class="pa-3 mb-4">
            <div class="d-flex justify-space-between mb-2">
              <span class="text-caption text-medium-emphasis">发送金额</span>
              <span class="font-weight-medium">{{ amount }} {{ selectedCurrency }}</span>
            </div>
            <div class="d-flex justify-space-between mb-2">
              <span class="text-caption text-medium-emphasis">收款地址</span>
              <span class="font-weight-medium text-truncate" style="max-width: 200px;">{{ toAddress }}</span>
            </div>
            <div class="d-flex justify-space-between mb-2">
              <span class="text-caption text-medium-emphasis">手续费</span>
              <span class="font-weight-medium">0.01 {{ selectedCurrency }}</span>
            </div>
            <v-divider class="my-2"></v-divider>
            <div class="d-flex justify-space-between">
              <span class="text-body-2 font-weight-bold">总计</span>
              <span class="text-body-2 font-weight-bold">{{ calculateTotalAmount() }} {{ selectedCurrency }}</span>
            </div>
          </v-card>
          
          <p class="text-caption text-medium-emphasis">
            <v-icon size="x-small" class="mr-1">mdi-information-outline</v-icon>
            交易一旦发送将无法撤销，请确认交易详情正确。
          </p>
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="showConfirmDialog = false" class="mr-2">取消</v-btn>
          <v-btn color="primary" @click="confirmSend" :loading="isLoading">确认发送</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 交易结果对话框 -->
    <v-dialog v-model="showResultDialog" max-width="400">
      <v-card>
        <v-toolbar :color="sendSuccess ? 'success' : 'error'" density="compact">
          <v-toolbar-title class="text-white text-subtitle-1">
            {{ sendSuccess ? '交易已发送' : '交易失败' }}
          </v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="showResultDialog = false">
            <v-icon color="white">mdi-close</v-icon>
          </v-btn>
        </v-toolbar>
        <v-card-text class="pa-4 text-center">
          <v-avatar 
            :color="sendSuccess ? 'success' : 'error'" 
            size="64" 
            class="my-4"
          >
            <v-icon size="36" color="white">
              {{ sendSuccess ? 'mdi-check' : 'mdi-alert' }}
            </v-icon>
          </v-avatar>
          
          <h3 class="text-h6 mb-2">{{ sendSuccess ? '交易已发送成功' : '交易发送失败' }}</h3>
          <p class="text-body-2 text-medium-emphasis mb-4">
            {{ sendSuccess 
              ? `您已成功发送 ${amount} ${selectedCurrency} 至指定地址` 
              : (sendErrorMessage || '发送交易时遇到错误，请稍后重试') 
            }}
          </p>
          
          <v-btn 
            v-if="sendSuccess" 
            variant="text" 
            color="primary" 
            prepend-icon="mdi-eye" 
            size="small"
          >
            查看交易详情
          </v-btn>
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer></v-spacer>
          <v-btn 
            color="primary" 
            @click="closeResultDialog"
          >
            完成
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 成功提示 -->
    <v-snackbar v-model="showSuccess" color="success" location="top">
      交易已成功发送！
      <template v-slot:actions>
        <v-btn variant="text" @click="showSuccess = false">
          关闭
        </v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useWalletStore } from '@/store/wallet'

const walletStore = useWalletStore()

// 表单数据
const toAddress = ref('')
const selectedCurrency = ref('wBKC')
const amount = ref('')
const memo = ref('')

// 错误信息
const addressError = ref('')
const amountError = ref('')

// 界面状态
const isLoading = ref(false)
const showSuccess = ref(false)
const showRecipientHistory = ref(false)
const showConfirmDialog = ref(false)
const showResultDialog = ref(false)
const sendSuccess = ref(false)
const sendErrorMessage = ref('')

// 可选代币
const currencies = [
  { title: 'wBKC', value: 'wBKC' },
  { title: 'E20C', value: 'E20C' }
]

// 近期收款人列表
const recentRecipients = [
  { address: '0x1234567890abcdef1234567890abcdef12345678', date: '2023-05-15' },
  { address: '0xabcdef1234567890abcdef1234567890abcdef12', date: '2023-05-10' },
  { address: '0x7890abcdef1234567890abcdef1234567890abcd', date: '2023-05-05' }
]

// 表单验证
const isFormValid = computed(() => {
  return toAddress.value && 
         amount.value && 
         parseFloat(amount.value) > 0 && 
         parseFloat(amount.value) <= parseFloat(getBalanceForCurrency(selectedCurrency.value)) &&
         !addressError.value && 
         !amountError.value
})

// 近期发送记录
const sendHistory = computed(() => {
  if (!walletStore.transactions) return []
  return walletStore.transactions
    .filter(tx => tx.type === 'send')
    .slice(0, 5)
})

// 格式化余额
const formatBalance = (balance) => {
  try {
    const num = typeof balance === 'string' ? parseFloat(balance) : balance
    if (!isNaN(num)) {
      return num.toFixed(2)
    }
    return '0.00'
  } catch {
    return '0.00'
  }
}

// 获取所选代币的余额
const getBalanceForCurrency = (currency) => {
  if (currency === 'wBKC') {
    return walletStore.wbkcBalance
  } else if (currency === 'E20C') {
    return walletStore.e20cBalance
  }
  return '0.00'
}

// 格式化地址显示
const formatAddress = (address) => {
  if (!address) return ''
  if (address.length < 10) return address
  return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`
}

// 设置最大金额
const setMaxAmount = () => {
  amount.value = getBalanceForCurrency(selectedCurrency.value)
}

// 计算美元价值
const calculateUsdValue = () => {
  try {
    const numAmount = parseFloat(amount.value)
    if (isNaN(numAmount)) return '0.00'
    
    let usdValue = 0
    if (selectedCurrency.value === 'wBKC') {
      // 1 wBKC = 0.1 USD
      usdValue = numAmount * 0.1
    } else if (selectedCurrency.value === 'E20C') {
      // 1 E20C = 0.01 USD
      usdValue = numAmount * 0.01
    }
    
    return usdValue.toFixed(2)
  } catch {
    return '0.00'
  }
}

// 计算总金额（含手续费）
const calculateTotalAmount = () => {
  const numAmount = parseFloat(amount.value || '0')
  if (isNaN(numAmount)) return '0.00'
  
  // 手续费 0.01
  const total = numAmount + 0.01
  return total.toFixed(2)
}

// 获取按钮文本
const getSendButtonText = () => {
  if (!toAddress.value) {
    return '请输入收款地址'
  }
  
  if (!amount.value || parseFloat(amount.value) <= 0) {
    return '请输入金额'
  }
  
  if (parseFloat(amount.value) > parseFloat(getBalanceForCurrency(selectedCurrency.value))) {
    return '余额不足'
  }
  
  return '发送'
}

// 获取货币颜色
const getCurrencyColor = (currency) => {
  switch (currency) {
    case 'wBKC': return 'primary'
    case 'E20C': return 'amber'
    default: return 'grey'
  }
}

// 获取货币符号
const getCurrencySymbol = (currency) => {
  switch (currency) {
    case 'wBKC': return 'wBKC'
    case 'E20C': return 'E20C'
    default: return '?'
  }
}

// 选择收款人
const selectRecipient = (address) => {
  toAddress.value = address
  showRecipientHistory.value = false
}

// 处理发送
const handleSend = () => {
  // 验证地址
  if (!toAddress.value) {
    addressError.value = '请输入收款地址'
    return
  } else if (toAddress.value.length < 10) {
    addressError.value = '请输入有效的钱包地址'
    return
  } else {
    addressError.value = ''
  }
  
  // 验证金额
  const numAmount = parseFloat(amount.value)
  if (!amount.value || isNaN(numAmount) || numAmount <= 0) {
    amountError.value = '请输入有效金额'
    return
  } else if (numAmount > parseFloat(getBalanceForCurrency(selectedCurrency.value))) {
    amountError.value = `余额不足，最大可用: ${getBalanceForCurrency(selectedCurrency.value)} ${selectedCurrency.value}`
    return
  } else {
    amountError.value = ''
  }
  
  // 显示确认对话框
  showConfirmDialog.value = true
}

// 确认发送
const confirmSend = async () => {
  isLoading.value = true
  
  try {
    // 调用钱包store的发送方法
    const result = await walletStore.send({
      to: toAddress.value,
      amount: amount.value,
      currency: selectedCurrency.value,
      memo: memo.value
    })
    
    // 处理结果
    if (result.success) {
      sendSuccess.value = true
      sendErrorMessage.value = ''
      showSuccess.value = true
    } else {
      sendSuccess.value = false
      sendErrorMessage.value = result.error || '发送失败，请稍后再试'
    }
    
    // 关闭确认对话框，显示结果对话框
    showConfirmDialog.value = false
    showResultDialog.value = true
  } catch (error) {
    console.error('发送错误:', error)
    sendSuccess.value = false
    sendErrorMessage.value = error?.message || '发送过程中发生错误'
    
    showConfirmDialog.value = false
    showResultDialog.value = true
  } finally {
    isLoading.value = false
  }
}

// 关闭结果对话框并重置表单
const closeResultDialog = () => {
  showResultDialog.value = false
  
  if (sendSuccess.value) {
    // 重置表单
    toAddress.value = ''
    amount.value = ''
    memo.value = ''
    addressError.value = ''
    amountError.value = ''
  }
}

// 初始化
onMounted(() => {
  // 可以在这里加载数据或执行其他初始化操作
})
</script>

<style scoped>
/* 自定义样式 */
:deep(.v-field__input) {
  font-size: 1rem;
}

.fake-qr-code {
  width: 120px;
  height: 120px;
  background-color: #f5f5f5;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}
</style> 
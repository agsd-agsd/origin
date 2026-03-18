<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" md="8" lg="6">
        <v-card class="rounded-lg" elevation="3">
          <v-card-title class="d-flex align-center px-4 py-3 bg-primary-lighten-5">
            <v-icon size="large" color="primary" class="mr-2">mdi-qrcode</v-icon>
            <span class="text-h6 font-weight-bold">接收代币</span>
          </v-card-title>

          <v-card-text class="px-4 py-5">
            <!-- 地址和二维码展示 -->
            <div class="text-center">
              <div class="mb-4 text-body-1 text-medium-emphasis">
                分享您的钱包地址以接收付款
              </div>

              <!-- 二维码展示 -->
              <div class="qr-container mb-4">
                <div class="qr-code-wrapper">
                  <div v-if="walletStore.address" class="qr-code-actual">
                    <v-img
                      :src="`https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${walletStore.address}`"
                      alt="钱包地址二维码"
                      width="140"
                      height="140"
                      class="mx-auto"
                    ></v-img>
                  </div>
                  <div v-else class="no-wallet-placeholder">
                    <v-icon size="48" color="grey">mdi-wallet-outline</v-icon>
                    <p class="text-body-2 mt-2">钱包未连接</p>
                  </div>
                </div>
              </div>

              <!-- 地址显示和复制 -->
              <v-card class="mb-5 address-card" variant="outlined">
                <v-card-text class="pa-3">
                  <div class="text-caption text-medium-emphasis mb-1">您的钱包地址</div>
                  <div class="d-flex align-center">
                    <span class="text-body-2 text-truncate">{{ walletStore.address || '未连接钱包' }}</span>
                    <v-btn
                      icon
                      size="small"
                      variant="text"
                      class="ml-2" 
                      @click="copyAddress"
                      :disabled="!walletStore.address"
                    >
                      <v-icon size="small">mdi-content-copy</v-icon>
                    </v-btn>
                  </div>
                </v-card-text>
              </v-card>

              <!-- 代币选择 -->
              <div class="mb-5">
                <label class="text-subtitle-2 font-weight-medium d-block mb-3 text-start">选择想要接收的代币</label>
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
                          (余额: {{ formatBalance(getBalanceForCurrency(item.value)) }})
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
                        余额: {{ formatBalance(getBalanceForCurrency(item.value)) }}
                      </v-list-item-subtitle>
                    </v-list-item>
                  </template>
                </v-select>
              </div>

              <!-- 金额输入 (可选) -->
              <div class="mb-5">
                <label class="text-subtitle-2 font-weight-medium d-block mb-2 text-start">请求金额 (可选)</label>
                <v-text-field
                  v-model="amount"
                  type="number"
                  placeholder="0.00"
                  variant="outlined"
                  density="comfortable"
                  hide-details="auto"
                >
                  <template v-slot:append>
                    <span class="text-body-2 font-weight-medium">{{ selectedCurrency }}</span>
                  </template>
                </v-text-field>
                <div v-if="amount" class="text-caption text-medium-emphasis text-start mt-1">
                  ≈ ${{ calculateUsdValue() }} USD
                </div>
              </div>

              <!-- 备注信息 (可选) -->
              <div class="mb-5">
                <label class="text-subtitle-2 font-weight-medium d-block mb-2 text-start">备注信息 (可选)</label>
                <v-textarea
                  v-model="memo"
                  placeholder="添加备注信息..."
                  variant="outlined"
                  density="comfortable"
                  rows="2"
                  hide-details
                  counter="100"
                  maxlength="100"
                ></v-textarea>
              </div>

              <!-- 分享按钮 -->
              <div class="d-flex justify-center gap-2">
                <v-btn
                  color="primary"
                  prepend-icon="mdi-content-copy"
                  @click="copyFullInfo"
                  :disabled="!walletStore.address"
                >
                  复制接收信息
                </v-btn>
                <v-btn
                  variant="outlined"
                  prepend-icon="mdi-share-variant"
                  @click="shareAddress"
                  :disabled="!walletStore.address"
                >
                  分享地址
                </v-btn>
              </div>
            </div>
          </v-card-text>
        </v-card>

        <!-- 近期接收记录 -->
        <v-card class="mt-6 rounded-lg" elevation="2">
          <v-toolbar flat density="compact" color="background">
            <v-toolbar-title class="font-weight-bold">近期接收记录</v-toolbar-title>
            <v-spacer></v-spacer>
            <v-btn variant="text" size="small" to="/history" append-icon="mdi-chevron-right">
              查看全部
            </v-btn>
          </v-toolbar>

          <v-divider></v-divider>

          <v-list v-if="receiveHistory.length > 0" class="py-0">
            <template v-for="(transaction, index) in receiveHistory" :key="transaction.id">
              <v-list-item class="py-2">
                <template v-slot:prepend>
                  <v-avatar color="success" variant="tonal" size="38">
                    <v-icon size="small">mdi-arrow-bottom-left</v-icon>
                  </v-avatar>
                </template>

                <v-list-item-title>
                  收到 {{ transaction.amount }} {{ transaction.currency }}
                </v-list-item-title>
                
                <v-list-item-subtitle class="text-caption text-medium-emphasis">
                  来自: {{ formatAddress(transaction.from) }} | {{ new Date(transaction.timestamp).toLocaleString() }}
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
              <v-divider v-if="index < receiveHistory.length - 1"></v-divider>
            </template>
          </v-list>

          <v-card-text v-else class="text-center py-8">
            <v-icon size="large" color="grey" class="mb-2">mdi-tray-arrow-down</v-icon>
            <div class="text-body-1 text-medium-emphasis">暂无接收记录</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 复制成功提示 -->
    <v-snackbar
      v-model="showCopySuccessSnackbar"
      :timeout="2000"
      color="success"
      location="top"
    >
      <div class="d-flex align-center">
        <v-icon class="mr-2">mdi-check-circle</v-icon>
        {{ copySuccessMessage }}
      </div>
    </v-snackbar>

    <!-- 分享对话框 -->
    <v-dialog v-model="showShareDialog" max-width="500">
      <v-card>
        <v-toolbar color="primary">
          <v-toolbar-title>分享您的钱包地址</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="showShareDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-toolbar>
        <v-card-text class="pa-4">
          <div class="text-center mb-5">
            <div class="qr-container mb-4">
              <div class="qr-code-wrapper">
                <div class="qr-code-actual">
                  <v-img
                    :src="`https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${walletStore.address}`"
                    alt="钱包地址二维码"
                    width="140"
                    height="140"
                    class="mx-auto"
                  ></v-img>
                </div>
              </div>
            </div>
            
            <div class="mb-4">
              <div class="text-body-1 font-weight-medium mb-2">扫描二维码发送付款</div>
              <div class="text-caption text-medium-emphasis">
                您可以分享此二维码或钱包地址给其他人，以接收{{ selectedCurrency }}付款。
              </div>
            </div>
            
            <v-card variant="outlined" class="pa-3 mb-4">
              <div class="d-flex align-center justify-space-between">
                <span class="text-caption text-medium-emphasis">钱包地址</span>
                <v-btn
                  icon
                  size="x-small"
                  variant="text"
                  @click="copyAddress"
                >
                  <v-icon size="small">mdi-content-copy</v-icon>
                </v-btn>
              </div>
              <div class="text-body-2 font-weight-medium mt-1 text-truncate">
                {{ walletStore.address }}
              </div>
            </v-card>
            
            <div v-if="amount" class="mb-4">
              <div class="text-body-2 font-weight-medium">
                请求金额: {{ amount }} {{ selectedCurrency }}
              </div>
            </div>
          </div>
          
          <div class="d-flex justify-center">
            <v-btn
              color="primary"
              prepend-icon="mdi-content-copy"
              @click="copyFullInfo"
              class="mr-2"
            >
              复制信息
            </v-btn>
            <v-btn
              variant="outlined"
              prepend-icon="mdi-share-variant"
            >
              分享
            </v-btn>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useWalletStore } from '@/store/wallet'

const walletStore = useWalletStore()

// 表单数据
const selectedCurrency = ref('wBKC')
const amount = ref('')
const memo = ref('')

// 界面状态
const showShareDialog = ref(false)
const showCopySuccessSnackbar = ref(false)
const copySuccessMessage = ref('')

// 可选代币
const currencies = [
  { title: 'wBKC', value: 'wBKC' },
  { title: 'E20C', value: 'E20C' }
]

// 近期接收记录
const receiveHistory = computed(() => {
  if (!walletStore.transactions) return []
  return walletStore.transactions
    .filter(tx => tx.type === 'receive')
    .slice(0, 5)
})

// 获取所选代币的余额
const getBalanceForCurrency = (currency) => {
  if (currency === 'wBKC') {
    return walletStore.wbkcBalance
  } else if (currency === 'E20C') {
    return walletStore.e20cBalance
  }
  return '0.00'
}

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

// 格式化地址显示
const formatAddress = (address) => {
  if (!address) return ''
  if (address.length < 10) return address
  return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`
}

// 复制地址
const copyAddress = () => {
  if (walletStore.address) {
    navigator.clipboard.writeText(walletStore.address)
      .then(() => {
        showCopySuccessSnackbar.value = true
        copySuccessMessage.value = '地址已复制到剪贴板'
      })
      .catch(err => {
        console.error('复制失败：', err)
      })
  }
}

// 复制完整信息
const copyFullInfo = () => {
  if (walletStore.address) {
    let info = `钱包地址: ${walletStore.address}`
    
    if (amount.value) {
      info += `\n请求金额: ${amount.value} ${selectedCurrency.value}`
    }
    
    if (memo.value) {
      info += `\n备注: ${memo.value}`
    }
    
    navigator.clipboard.writeText(info)
      .then(() => {
        showCopySuccessSnackbar.value = true
        copySuccessMessage.value = '接收信息已复制到剪贴板'
      })
      .catch(err => {
        console.error('复制失败：', err)
      })
  }
}

// 分享地址
const shareAddress = () => {
  showShareDialog.value = true
}

// 初始化
onMounted(() => {
  // 可以在这里加载数据或执行其他初始化操作
})
</script>

<style scoped>
.qr-container {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.qr-code-wrapper {
  position: relative;
  width: 150px;
  height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 8px;
  padding: 5px;
  background-color: white;
}

.qr-code-actual {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.qr-code-actual > svg {
  /* width: 100% !important; */ /* Let options.width control size */
  /* height: 100% !important; */ /* Let options.width control size */
}

/* Added to target svg if vue-qr wraps it in a div when using v-html */
.qr-code-actual > div > svg {
    /* Let options.width control size */
}

.no-wallet-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  border-radius: 8px;
  border: 1px dashed rgba(0, 0, 0, 0.2);
}

.address-card {
  overflow: hidden;
}
</style> 
<template>
  <v-container>
    <v-row>
      <!-- 左侧兑换区域 -->
      <v-col cols="12" md="6">
        <v-card class="rounded-lg" elevation="1">
          <v-card-title class="font-weight-bold px-4 pt-4 pb-2">
            <div class="d-flex align-center">
              <v-icon color="primary" class="mr-2">mdi-swap-horizontal</v-icon>
              代币兑换
            </div>
          </v-card-title>
          
          <v-card-text class="px-4 pb-4">
            <!-- From Currency Card -->
            <v-card class="mb-4 rounded-lg" variant="outlined">
              <v-card-text class="pa-4">
                <div class="d-flex justify-space-between mb-2">
                  <span class="text-caption text-medium-emphasis">支付</span>
                  <span class="text-caption">
                    余额: {{ fromCurrency === 'wBKC' ? walletStore.formatBalance(walletStore.wbkcBalance) : walletStore.formatBalance(walletStore.e20cBalance) }} {{ fromCurrency }}
                    <v-btn density="compact" variant="text" size="x-small" class="ml-1" @click="setMaxAmount">最大</v-btn>
                  </span>
                </div>
                
                <div class="d-flex align-center">
                  <v-text-field
                    v-model="amount"
                    type="number"
                    min="0"
                    step="any"
                    density="compact"
                    variant="plain"
                    hide-details
                    class="text-h5 font-weight-bold"
                    :disabled="isLoading"
                    style="max-width: 70%"
                  ></v-text-field>
                  
                  <v-spacer></v-spacer>
                  
                  <v-select
                    v-model="fromCurrency"
                    :items="currencies"
                    variant="outlined"
                    density="compact"
                    hide-details
                    :disabled="isLoading"
                    class="max-width-select"
                  >
                    <template v-slot:selection="{ item }">
                      <div class="d-flex align-center">
                        <v-avatar 
                          size="28" 
                          :color="getCurrencyColor(item.value)" 
                          class="mr-2" 
                          variant="flat"
                        >
                          <span class="text-white font-weight-bold text-caption">{{ getCurrencySymbol(item.value) }}</span>
                        </v-avatar>
                        <span class="font-weight-medium">{{ item.title }}</span>
                      </div>
                    </template>
                    
                    <template v-slot:item="{ item, props }">
                      <v-list-item v-bind="props">
                        <template v-slot:prepend>
                          <v-avatar 
                            size="28" 
                            :color="getCurrencyColor(item.value)" 
                            variant="flat"
                          >
                            <span class="text-white font-weight-bold text-caption">{{ getCurrencySymbol(item.value) }}</span>
                          </v-avatar>
                        </template>
                        <v-list-item-title>{{ item.title }}</v-list-item-title>
                        <v-list-item-subtitle>{{ item.value === 'wBKC' ? '原生代币' : '平台代币' }}</v-list-item-subtitle>
                      </v-list-item>
                    </template>
                  </v-select>
                </div>
                
                <div class="text-right text-caption text-medium-emphasis" v-if="fromCurrency === 'wBKC'">
                  ≈ ${{ formatUsdValue(fromCurrency, amount) }} USD
                </div>
              </v-card-text>
            </v-card>
            
            <!-- Swap Button -->
            <div class="text-center my-2 position-relative">
              <v-btn
                color="primary"
                icon
                size="small"
                variant="flat"
                :disabled="isLoading"
                @click="swapDirections"
                class="swap-btn"
              >
                <v-icon size="small">mdi-swap-vertical</v-icon>
              </v-btn>
            </div>
            
            <!-- To Currency Card -->
            <v-card class="mb-4 rounded-lg" variant="outlined">
              <v-card-text class="pa-4">
                <div class="d-flex justify-space-between mb-2">
                  <span class="text-caption text-medium-emphasis">接收</span>
                  <span class="text-caption">
                    余额: {{ toCurrency === 'wBKC' ? walletStore.formatBalance(walletStore.wbkcBalance) : walletStore.formatBalance(walletStore.e20cBalance) }} {{ toCurrency }}
                  </span>
                </div>
                
                <div class="d-flex align-center">
                  <v-text-field
                    :model-value="outputAmount"
                    readonly
                    density="compact"
                    variant="plain"
                    hide-details
                    class="text-h5 font-weight-bold text-medium-emphasis"
                  ></v-text-field>
                  
                  <v-spacer></v-spacer>
                  
                  <v-select
                    v-model="toCurrency"
                    :items="currencies"
                    variant="outlined"
                    density="compact"
                    hide-details
                    :disabled="isLoading"
                    class="max-width-select"
                  >
                    <template v-slot:selection="{ item }">
                      <div class="d-flex align-center">
                        <v-avatar 
                          size="28" 
                          :color="getCurrencyColor(item.value)" 
                          class="mr-2" 
                          variant="flat"
                        >
                          <span class="text-white font-weight-bold text-caption">{{ getCurrencySymbol(item.value) }}</span>
                        </v-avatar>
                         <span class="font-weight-medium">{{ item.title }}</span>
                      </div>
                    </template>
                    
                    <template v-slot:item="{ item, props }">
                      <v-list-item v-bind="props">
                        <template v-slot:prepend>
                          <v-avatar 
                            size="28" 
                            :color="getCurrencyColor(item.value)" 
                            variant="flat"
                          >
                            <span class="text-white font-weight-bold text-caption">{{ getCurrencySymbol(item.value) }}</span>
                          </v-avatar>
                        </template>
                        <v-list-item-title>{{ item.title }}</v-list-item-title>
                        <v-list-item-subtitle>{{ item.value === 'wBKC' ? '原生代币' : '平台代币' }}</v-list-item-subtitle>
                      </v-list-item>
                    </template>
                  </v-select>
                </div>
                
                <div class="text-right text-caption text-medium-emphasis" v-if="toCurrency === 'wBKC'">
                  ≈ ${{ formatUsdValue(toCurrency, outputAmount) }} USD
                </div>
              </v-card-text>
            </v-card>
            
            <!-- Exchange Rate Card -->
            <v-card 
              class="mb-4 rounded-lg bg-surface-variant" 
              variant="flat"
              @click="showRateDetails = !showRateDetails"
            >
              <v-card-text class="pa-4">
                <div class="d-flex align-center justify-space-between">
                  <div class="d-flex align-center">
                    <v-icon size="small" class="mr-2 text-medium-emphasis">mdi-information-outline</v-icon>
                    <span class="text-caption text-medium-emphasis">当前汇率</span>
                  </div>
                  <div class="d-flex align-center">
                    <span class="text-body-2 font-weight-medium">
                      1 {{ fromCurrency }} = {{ getExchangeRate() }} {{ toCurrency }}
                    </span>
                    <v-icon size="small" class="ml-1">
                      {{ showRateDetails ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
                    </v-icon>
                  </div>
                </div>
                
                <v-expand-transition>
                  <div v-if="showRateDetails" class="mt-3 text-caption text-medium-emphasis">
                    <div class="d-flex justify-space-between">
                      <span>预计接收数量</span>
                      <span>{{ outputAmount }} {{ toCurrency }}</span>
                    </div>
                    <div class="d-flex justify-space-between mt-1">
                      <span>最低接收数量</span>
                      <span>{{ outputAmount }} {{ toCurrency }}</span>
                    </div>
                    <div class="d-flex justify-space-between mt-1">
                      <span>滑点容忍度</span>
                      <span>0.5%</span>
                    </div>
                    <div class="d-flex justify-space-between mt-1">
                      <span>交易费用</span>
                      <span>0.00 wBKC</span>
                    </div>
                  </div>
                </v-expand-transition>
              </v-card-text>
            </v-card>
            
            <!-- Error Alert -->
            <v-alert
              v-if="amountError"
              type="error"
              variant="tonal"
              class="mb-4 rounded-lg"
              closable
              @click:close="amountError = ''"
            >
              {{ amountError }}
            </v-alert>
            
            <!-- Submit Button -->
            <v-btn
              block
              color="primary"
              size="large"
              class="rounded-lg font-weight-bold"
              height="48"
              :disabled="!isSwapValid || isLoading"
              :loading="isLoading"
              @click="handleSwap"
            >
              {{ getSwapButtonText() }}
            </v-btn>
            
            <!-- 提供流动性链接 -->
            <div class="d-flex justify-center mt-3">
              <v-btn
                variant="text"
                color="primary"
                to="/liquidity"
                density="comfortable"
                prepend-icon="mdi-water"
                class="text-none"
              >
                添加流动性赚取收益
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <!-- 右侧市场信息和兑换历史 -->
      <v-col cols="12" md="6">
        <!-- 市场信息卡片 -->
        <v-card class="mb-6 rounded-lg" elevation="1">
          <v-card-title class="d-flex align-center px-4 pt-4 pb-2">
            <v-icon color="primary" class="mr-2">mdi-chart-line</v-icon>
            <span class="font-weight-bold">币对行情</span>
          </v-card-title>
          
          <v-card-text class="pb-0">
            <v-chip-group
              v-model="selectedPair"
              mandatory
              class="mb-3"
            >
              <v-chip label size="small" value="wBKC_BADGE">wBKC/E20C</v-chip>
              <v-chip label size="small" value="BADGE_wBKC">E20C/wBKC</v-chip>
            </v-chip-group>
          </v-card-text>
          
          <v-card-text class="pt-0">
            <div class="d-flex justify-space-between align-center mb-4">
              <div>
                <div class="text-h6 font-weight-bold">{{ selectedPair === 'wBKC_BADGE' ? '10.00' : '0.10' }}</div>
                <div class="text-caption text-medium-emphasis">
                  {{ selectedPair === 'wBKC_BADGE' ? '1 wBKC = 10 E20C' : '1 E20C = 0.1 wBKC' }}
                </div>
              </div>
              <v-chip color="success" size="small">
                <v-icon start size="x-small">mdi-trending-up</v-icon>
                0.00%
              </v-chip>
            </div>
            
            <div class="mb-4">
              <div class="d-flex justify-space-between mb-1 text-caption">
                <div class="text-medium-emphasis">24h最高</div>
                <div class="font-weight-medium">{{ selectedPair === 'wBKC_BADGE' ? '10.50' : '0.102' }}</div>
              </div>
              <div class="d-flex justify-space-between mb-1 text-caption">
                <div class="text-medium-emphasis">24h最低</div>
                <div class="font-weight-medium">{{ selectedPair === 'wBKC_BADGE' ? '9.80' : '0.095' }}</div>
              </div>
              <div class="d-flex justify-space-between text-caption">
                <div class="text-medium-emphasis">24h成交量</div>
                <div class="font-weight-medium">{{ selectedPair === 'wBKC_BADGE' ? '5,432.1 wBKC' : '54,321 E20C' }}</div>
              </div>
            </div>
            
            <!-- 真实图表 -->
            <div class="chart-container mb-4">
              <Line :data="chartData" :options="chartOptions" />
            </div>
          </v-card-text>
        </v-card>
        
        <!-- 最近兑换记录 -->
        <v-card class="rounded-lg" elevation="1">
          <v-card-title class="d-flex align-center px-4 pt-4 pb-2">
            <v-icon color="primary" class="mr-2">mdi-history</v-icon>
            <span class="font-weight-bold">最近兑换</span>
          </v-card-title>
          
          <v-list class="pa-0">
            <v-list-item v-for="(tx, index) in swapHistory.slice(0, 5)" :key="tx.id" density="compact">
              <v-list-item-title class="d-flex justify-space-between align-center text-body-2">
                <span>{{ tx.currency }} → {{ tx.toCurrency }}</span>
                <span class="text-caption">{{ formatDate(tx.timestamp) }}</span>
              </v-list-item-title>
              <v-list-item-subtitle class="d-flex justify-space-between">
                <span>{{ tx.amount }} {{ tx.currency }}</span>
                <span :class="tx.currency === 'wBKC' ? 'text-error' : 'text-success'">
                  {{ tx.currency === 'wBKC' ? '-' : '+' }}{{ tx.toAmount }} {{ tx.toCurrency }}
                </span>
              </v-list-item-subtitle>
            </v-list-item>
            
            <div v-if="swapHistory.length === 0" class="pa-4 text-center text-medium-emphasis text-caption">
              暂无兑换记录
            </div>
          </v-list>
          
          <v-card-actions class="px-4 pb-4">
            <v-spacer></v-spacer>
            <v-btn
              variant="text"
              color="primary"
              to="/history"
              size="small"
              append-icon="mdi-chevron-right"
            >
              查看全部历史
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- 交易确认对话框 -->
    <v-dialog v-model="showConfirmDialog" max-width="400" class="rounded-lg">
      <v-card class="rounded-lg">
        <v-card-title class="bg-primary-lighten-5 d-flex align-center px-4 py-3">
          <v-icon color="primary" class="mr-2">mdi-alert-circle-outline</v-icon>
          确认兑换
        </v-card-title>
        <v-card-text class="pa-4 pt-5">
          <p class="text-body-1 mb-4">您即将进行以下兑换交易：</p>
          
          <v-card variant="outlined" class="mb-4 rounded-lg pa-3">
            <div class="d-flex justify-space-between mb-3">
              <div>
                <div class="text-caption text-medium-emphasis mb-1">发送</div>
                <div class="d-flex align-center">
                  <v-avatar :color="getCurrencyColor(fromCurrency)" size="24" class="mr-2">
                    <span class="text-caption font-weight-bold text-white">{{ getCurrencySymbol(fromCurrency) }}</span>
                  </v-avatar>
                  <span class="font-weight-bold">{{ amount }} {{ fromCurrency }}</span>
                </div>
              </div>
              
              <v-icon>mdi-arrow-right</v-icon>
              
              <div class="text-end">
                <div class="text-caption text-medium-emphasis mb-1">接收</div>
                <div class="d-flex align-center justify-end">
                  <v-avatar :color="getCurrencyColor(toCurrency)" size="24" class="mr-2">
                    <span class="text-caption font-weight-bold text-white">{{ getCurrencySymbol(toCurrency) }}</span>
                  </v-avatar>
                  <span class="font-weight-bold">{{ outputAmount }} {{ toCurrency }}</span>
                </div>
              </div>
            </div>
            
            <v-divider class="mb-3"></v-divider>
            
            <div class="d-flex justify-space-between text-caption">
              <span class="text-medium-emphasis">汇率</span>
              <span>1 {{ fromCurrency }} = {{ getExchangeRate() }} {{ toCurrency }}</span>
            </div>
          </v-card>
          
          <p class="text-caption text-medium-emphasis mb-2">
            <v-icon size="x-small" class="mr-1">mdi-information-outline</v-icon>
            请注意，此交易一旦确认将无法撤销。
          </p>
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="showConfirmDialog = false" class="mr-2">取消</v-btn>
          <v-btn color="primary" @click="confirmSwap" :loading="isLoading">确认兑换</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 交易结果对话框 -->
    <v-dialog v-model="showResultDialog" max-width="400" class="rounded-lg">
      <v-card class="rounded-lg">
        <v-card-title :class="swapSuccess ? 'bg-success-lighten-5' : 'bg-error-lighten-5'" class="d-flex align-center px-4 py-3">
          <v-icon :color="swapSuccess ? 'success' : 'error'" class="mr-2">
            {{ swapSuccess ? 'mdi-check-circle-outline' : 'mdi-alert-circle-outline' }}
          </v-icon>
          {{ swapSuccess ? '兑换成功' : '兑换失败' }}
        </v-card-title>
        <v-card-text class="pa-4 pt-5">
          <div v-if="swapSuccess" class="text-center mb-4">
            <v-avatar class="mb-4" color="success" size="64">
              <v-icon size="36" color="white">mdi-check</v-icon>
            </v-avatar>
            <p class="text-h6 mb-2">兑换已完成</p>
            <p class="text-body-2 text-medium-emphasis">
              您已成功将 {{ amount }} {{ fromCurrency }} 兑换为 {{ outputAmount }} {{ toCurrency }}
            </p>
          </div>
          
          <div v-else class="text-center mb-4">
            <v-avatar class="mb-4" color="error" size="64">
              <v-icon size="36" color="white">mdi-close</v-icon>
            </v-avatar>
            <p class="text-h6 mb-2">兑换失败</p>
            <p class="text-body-2 text-medium-emphasis">
              {{ swapErrorMessage || '兑换过程中出现错误，请稍后再试' }}
            </p>
          </div>
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="closeResultDialog">完成</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 成功提示 -->
    <v-snackbar v-model="showSuccess" color="success">
      兑换成功！
      <template v-slot:actions>
        <v-btn variant="text" @click="showSuccess = false">
          关闭
        </v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useWalletStore } from '@/store/wallet'

// 导入Chart.js相关库
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

// 注册Chart.js组件
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

const walletStore = useWalletStore()

const amount = ref('')
const receivedAmount = ref('0');
const outputAmount = ref('0'); 
const exchangeRate = ref('0'); // 添加汇率响应式变量
const fromCurrency = ref('wBKC')
const toCurrency = ref('E20C')
const isLoading = ref(false)
const amountError = ref('')
const showRateDetails = ref(false)
const selectedPair = ref('wBKC_BADGE')
const showSuccess = ref(false)

const showConfirmDialog = ref(false)
const showResultDialog = ref(false)
const swapSuccess = ref(false)
const swapErrorMessage = ref('')

// 可兑换的货币列表
const currencies = [
  { title: 'wBKC', value: 'wBKC' },
  { title: 'E20C', value: 'E20C' }
]

// 图表数据 - wBKC/E20C
const wbkcE20CChartData = {
  labels: ['7天前', '6天前', '5天前', '4天前', '3天前', '2天前', '昨天', '今天'],
  datasets: [
    {
      label: 'wBKC/E20C 汇率',
      backgroundColor: 'rgba(66, 165, 245, 0.2)',
      borderColor: '#1976D2',
      pointBackgroundColor: '#1976D2',
      tension: 0.4,
      data: [10.2, 10.0, 10.3, 10.5, 10.2, 10.1, 10.4, 10.0]
    }
  ]
}

// 图表数据 - E20C/wBKC
const e20cBkcChartData = {
  labels: ['7天前', '6天前', '5天前', '4天前', '3天前', '2天前', '昨天', '今天'],
  datasets: [
    {
      label: 'E20C/wBKC 汇率',
      backgroundColor: 'rgba(255, 179, 0, 0.2)',
      borderColor: '#FB8C00',
      pointBackgroundColor: '#FB8C00',
      tension: 0.4,
      data: [0.098, 0.100, 0.097, 0.095, 0.098, 0.099, 0.096, 0.100]
    }
  ]
}

// 当前图表数据
const chartData = ref(wbkcE20CChartData)

// 图表配置
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false,
  },
  scales: {
    y: {
      beginAtZero: false,
      grid: {
        display: true,
        color: 'rgba(0, 0, 0, 0.05)'
      },
      ticks: {
        callback: function(value) {
          return selectedPair.value === 'wBKC_BADGE' 
            ? value.toFixed(2) + ' E20C' 
            : value.toFixed(3) + ' wBKC';
        }
      },
      title: {
        display: true,
        text: '价格'
      }
    },
    x: {
      grid: {
        display: false
      },
      title: {
        display: true,
        text: '时间'
      }
    }
  },
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      padding: 10,
      cornerRadius: 6,
      displayColors: false,
      callbacks: {
        label: function(context) {
          let label = context.dataset.label || '';
          if (label) {
            label += ': ';
          }
          if (context.parsed.y !== null) {
            label += selectedPair.value === 'wBKC_BADGE' 
              ? context.parsed.y.toFixed(2) + ' E20C' 
              : context.parsed.y.toFixed(3) + ' wBKC';
          }
          return label;
        }
      }
    }
  },
  elements: {
    point: {
      radius: 3,
      hoverRadius: 5
    }
  }
}

// 模拟交易历史数据
const generateSwapHistory = () => {
  const history = [];
  const now = Date.now();
  const day = 24 * 60 * 60 * 1000;
  const hour = 60 * 60 * 1000;
  
  // 生成20条兑换交易记录
  for (let i = 0; i < 20; i++) {
    const isBkcToE20C = i % 3 !== 0; // 2/3的交易是wBKC到E20C
    const randomTime = Math.floor(Math.random() * 14 * day); // 随机时间在过去两周内
    const timestamp = now - randomTime;
    const amount = (Math.random() * 10 + 1).toFixed(2);
    const toAmount = isBkcToE20C 
      ? (parseFloat(amount) * 10).toFixed(2)
      : (parseFloat(amount) * 0.1).toFixed(2);
    
    history.push({
      id: `swap-${100 + i}`,
      type: 'swap',
      status: Math.random() > 0.2 ? 'confirmed' : 'pending',
      amount: amount,
      currency: isBkcToE20C ? 'wBKC' : 'E20C',
      toAmount: toAmount,
      toCurrency: isBkcToE20C ? 'E20C' : 'wBKC',
      timestamp: timestamp,
      from: walletStore.address,
      to: walletStore.address
    });
  }
  
  // 生成20条发送交易记录
  for (let i = 0; i < 20; i++) {
    const useBkc = i % 2 === 0; // 一半wBKC，一半E20C
    const randomTime = Math.floor(Math.random() * 14 * day); // 随机时间在过去两周内
    const timestamp = now - randomTime;
    const amount = (Math.random() * 8 + 0.5).toFixed(2);
    
    history.push({
      id: `send-${200 + i}`,
      type: 'send',
      status: Math.random() > 0.1 ? 'confirmed' : 'pending',
      amount: amount,
      currency: useBkc ? 'wBKC' : 'E20C',
      timestamp: timestamp,
      from: walletStore.address,
      to: `0x${Math.random().toString(16).substring(2, 10)}...${Math.random().toString(16).substring(2, 6)}`
    });
  }
  
  // 生成20条接收交易记录
  for (let i = 0; i < 20; i++) {
    const useBkc = i % 2 === 0; // 一半wBKC，一半E20C
    const randomTime = Math.floor(Math.random() * 14 * day); // 随机时间在过去两周内
    const timestamp = now - randomTime;
    const amount = (Math.random() * 5 + 0.1).toFixed(2);
    
    history.push({
      id: `recv-${300 + i}`,
      type: 'receive',
      status: 'confirmed', // 接收的交易一般都是确认的
      amount: amount,
      currency: useBkc ? 'wBKC' : 'E20C',
      timestamp: timestamp,
      from: `0x${Math.random().toString(16).substring(2, 10)}...${Math.random().toString(16).substring(2, 6)}`,
      to: walletStore.address
    });
  }
  
  // 打乱交易记录顺序，按时间排序
  history.sort((a, b) => b.timestamp - a.timestamp);
  
  return history;
};

// 创建模拟数据
onMounted(() => {
  try {
    if (walletStore.address && (!walletStore.transactions || walletStore.transactions.length < 30)) {
      const txHistory = generateSwapHistory();
      if (txHistory && txHistory.length > 0) {
        walletStore.addDemoTransactions(txHistory);
      } else {
      }
    } else {
      if (!walletStore.address) {
      }
      if (walletStore.transactions && walletStore.transactions.length >= 30) {
      }
    }
  } catch (error) {
    console.error('Error in SwapView onMounted during demo transaction generation:', error);
  }
});

// 监听币对选择变化
watch(selectedPair, (newPair) => {
  if (newPair === 'wBKC_BADGE') {
    fromCurrency.value = 'wBKC'
    toCurrency.value = 'E20C'
    chartData.value = wbkcE20CChartData
  } else {
    fromCurrency.value = 'E20C'
    toCurrency.value = 'wBKC'
    chartData.value = e20cBkcChartData
  }
})

// 兑换历史（从wallet store获取）
const swapHistory = computed(() => {
  if (!walletStore.transactions) return []
  return walletStore.transactions.filter(tx => tx.type === 'swap')
})

// 根据当前选择获取余额
const fromBalance = computed(() => {
  return fromCurrency.value === 'wBKC' ? walletStore.wbkcBalance : walletStore.e20cBalance
})

const toBalance = computed(() => {
  return toCurrency.value === 'wBKC' ? walletStore.wbkcBalance : walletStore.e20cBalance
})

// 检查交换是否有效
const isSwapValid = computed(() => {
  if (!amount.value || parseFloat(amount.value) <= 0) return false
  if (fromCurrency.value === toCurrency.value) return false
  if (parseFloat(amount.value) > parseFloat(fromBalance.value)) return false
  return true
})

// 监听金额变化，验证输入
watch(amount, (newValue) => {
  if (!newValue) {
    amountError.value = ''
    return
  }
  
  const numValue = parseFloat(newValue)
  if (isNaN(numValue) || numValue <= 0) {
    amountError.value = '请输入有效金额'
    return
  }
  
  if (numValue > parseFloat(fromBalance.value)) {
    amountError.value = `余额不足，最大可用: ${fromBalance.value} ${fromCurrency.value}`
    return
  }
  
  amountError.value = ''
})

// 监听货币变化
watch([fromCurrency, toCurrency], ([newFrom, newTo]) => {
  // 防止选择相同的货币
  if (newFrom === newTo) {
    // 根据变化的是哪个下拉框来调整另一个
    if (newFrom !== fromCurrency.value) {
      toCurrency.value = fromCurrency.value
    } else {
      fromCurrency.value = toCurrency.value
    }
  }
  
  // 同步更新选择对
  if (newFrom === 'wBKC' && newTo === 'E20C') {
    selectedPair.value = 'wBKC_BADGE'
  } else if (newFrom === 'E20C' && newTo === 'wBKC') {
    selectedPair.value = 'BADGE_wBKC'
  }
  
  // 重新验证金额（因为余额可能变化）
  if (amount.value) {
    const numValue = parseFloat(amount.value)
    if (numValue > parseFloat(fromBalance.value)) {
      amountError.value = `余额不足，最大可用: ${fromBalance.value} ${fromCurrency.value}`
    } else {
      amountError.value = ''
    }
  }
})

// 监听影响输出金额计算的变量变化
watch([amount, fromCurrency, toCurrency], async () => {
  if (amount.value && parseFloat(amount.value) > 0) {
    try {
      // 正确调用getEstimatedOutput，它只接受fromCurrency和amount两个参数
      const result = await walletStore.getEstimatedOutput(
        fromCurrency.value, 
        amount.value
      );
      // 更新输出金额
      outputAmount.value = result;
    } catch (error) {
      console.error('计算兑换金额出错:', error);
      outputAmount.value = '0';
    }
  } else {
    outputAmount.value = '0';
  }
}, { immediate: true });

// 监听币种变化，更新汇率
watch([fromCurrency, toCurrency], async () => {
  try {
    // 调用wallet store或blockchain service获取真实汇率
    const rate = await walletStore.getExchangeRate(fromCurrency.value, toCurrency.value);
    exchangeRate.value = rate;
  } catch (error) {
    console.error('获取汇率出错:', error);
    // 设置默认值
    exchangeRate.value = fromCurrency.value === 'wBKC' ? '10.00' : '0.10';
  }
}, { immediate: true });

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

// 格式化日期
const formatDate = (timestamp) => {
  if (!timestamp) return ''
  
  const now = Date.now()
  const diff = now - timestamp
  
  if (diff < 60000) { // 1分钟内
    return '刚刚'
  } else if (diff < 3600000) { // 1小时内
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) { // 1天内
    return `${Math.floor(diff / 3600000)}小时前`
  } else {
    const date = new Date(timestamp)
    return `${date.getMonth() + 1}月${date.getDate()}日`
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

// 获取兑换汇率 (修改为返回响应式变量的值)
const getExchangeRate = () => {
  return exchangeRate.value;
}

// 设置最大金额
const setMaxAmount = () => {
  amount.value = fromCurrency.value === 'wBKC' 
    ? walletStore.wbkcBalance 
    : walletStore.e20cBalance
}

// 计算美元价值
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

// 交换方向
const swapDirections = () => {
  const temp = fromCurrency.value
  fromCurrency.value = toCurrency.value
  toCurrency.value = temp
  
  // 重置输入金额
  amount.value = ''
  amountError.value = ''
}

// 获取按钮文本
const getSwapButtonText = () => {
  if (!amount.value || amount.value === '0') {
    return '请输入金额'
  }
  
  if (parseFloat(amount.value) > parseFloat(fromBalance.value)) {
    return '余额不足'
  }
  
  if (fromCurrency.value === toCurrency.value) {
    return '选择不同的代币'
  }
  
  return '确认兑换'
}

// 处理兑换
const handleSwap = async () => {
  if (!isSwapValid.value) return
  
  // 显示确认对话框
  showConfirmDialog.value = true
}

// 确认兑换
const confirmSwap = async () => {
  if (!isSwapValid.value) return
    
  isLoading.value = true
  
  try {
    // 调用钱包store的兑换方法
    const result = await walletStore.swap({
        fromCurrency: fromCurrency.value,
        toCurrency: toCurrency.value,
        amount: amount.value
    });
    
    // 使用实际兑换金额
    if (result.success && result.outputAmount) {
      // 直接使用原始输出值，不进行单位转换
      outputAmount.value = result.outputAmount;
    }
    
    // 处理结果
    if (result.success) {
        swapSuccess.value = true;
        swapErrorMessage.value = '';
        showSuccess.value = true;
    } else {
      swapSuccess.value = false
      swapErrorMessage.value = result.error || '兑换失败，请稍后再试'
    }
    
    // 关闭确认对话框，显示结果对话框
    showConfirmDialog.value = false
    showResultDialog.value = true
  } catch (error) {
    console.error('兑换错误:', error)
    swapSuccess.value = false
    swapErrorMessage.value = error?.message || '兑换过程中发生错误'
    
    showConfirmDialog.value = false
    showResultDialog.value = true
  } finally {
    isLoading.value = false
  }
}

// 关闭结果对话框并重置表单
const closeResultDialog = () => {
  showResultDialog.value = false
  
  if (swapSuccess.value) {
    // 重置表单
    amount.value = ''
    amountError.value = ''
  }
}
</script>

<style scoped>
.max-width-select {
  max-width: 140px;
}

.swap-btn {
  background-color: var(--v-surface-variant);
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  z-index: 1;
}

.chart-container {
  height: 200px;
  border-radius: 8px;
  padding: 8px;
  background-color: rgba(0, 0, 0, 0.01);
}

/* 取消输入框上下按钮 */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
input[type=number] {
  -moz-appearance: textfield;
}
</style> 
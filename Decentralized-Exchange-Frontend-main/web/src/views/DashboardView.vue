<template>
  <v-container>
    <v-row>
      <!-- 左侧资产信息区域 -->
      <v-col cols="12" md="4" lg="3">
        <!-- 账户概览卡片 -->
        <v-card class="mb-6 rounded-lg" elevation="1">
          <v-card-text class="pa-4">
            <div class="text-overline text-medium-emphasis mb-1">总资产价值 (USD)</div>
            <div class="d-flex align-center">
              <h1 class="text-h5 font-weight-bold">${{ walletStore.usdValue }}</h1>
              <v-chip color="success" variant="elevated" size="small" class="ml-3">
                <v-icon start size="x-small">mdi-trending-up</v-icon>
                <span class="text-caption">+2.4%</span>
              </v-chip>
            </div>

            <!-- 刷新按钮和最后更新时间 -->
            <div class="d-flex align-center text-body-2 text-medium-emphasis mt-2">
              <span class="text-caption">最后更新: {{ lastUpdated }}</span>
              <v-btn icon size="small" variant="text" class="ml-2" @click="refreshBalances"
                :loading="walletStore.isLoading">
                <v-icon size="small">mdi-refresh</v-icon>
              </v-btn>
            </div>
          </v-card-text>
        </v-card>

        <!-- 快捷操作卡片 -->
        <v-card class="mb-6 rounded-lg" elevation="1">
          <v-card-text class="pa-4">
            <div class="text-subtitle-1 font-weight-bold mb-3">快捷操作</div>

            <v-list density="compact">
              <v-list-item to="/send" rounded="lg" class="mb-2" color="primary">
                <template v-slot:prepend>
                  <v-avatar color="primary" variant="tonal" size="36">
                    <v-icon>mdi-send</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title class="font-weight-medium">发送</v-list-item-title>
              </v-list-item>

              <v-list-item to="/receive" rounded="lg" class="mb-2" color="primary">
                <template v-slot:prepend>
                  <v-avatar color="primary" variant="tonal" size="36">
                    <v-icon>mdi-qrcode</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title class="font-weight-medium">接收</v-list-item-title>
              </v-list-item>

              <v-list-item to="/swap" rounded="lg" class="mb-2" color="primary">
                <template v-slot:prepend>
                  <v-avatar color="primary" variant="tonal" size="36">
                    <v-icon>mdi-swap-horizontal</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title class="font-weight-medium">兑换</v-list-item-title>
              </v-list-item>

              <v-list-item to="/history" rounded="lg" color="primary">
                <template v-slot:prepend>
                  <v-avatar color="primary" variant="tonal" size="36">
                    <v-icon>mdi-history</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title class="font-weight-medium">历史</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>

        <!-- 行情走势卡片 -->
        <v-card class="mb-6 rounded-lg" elevation="1">
          <v-card-text class="pa-4">
            <div class="d-flex align-center mb-4">
              <div class="text-subtitle-1 font-weight-bold">价格走势</div>
              <v-spacer></v-spacer>
              <v-chip-group v-model="selectedTimeframe" mandatory>
                <v-chip size="small" value="day">日</v-chip>
                <v-chip size="small" value="week">周</v-chip>
                <v-chip size="small" value="month">月</v-chip>
              </v-chip-group>
            </div>
            
            <!-- 图表 -->
            <div class="price-chart-container">
              <Line :data="currentChartData" :options="chartOptions" />
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- 右侧主内容区域 -->
      <v-col cols="12" md="8" lg="9">
        <!-- 资产列表卡片 -->
        <v-card class="mb-6 rounded-lg" elevation="1">
          <v-toolbar density="compact" flat color="background">
            <v-toolbar-title class="font-weight-bold">我的资产</v-toolbar-title>
            <v-spacer></v-spacer>
            <v-btn-toggle v-model="viewMode" mandatory rounded="xl" density="compact">
              <v-btn value="list" size="small">
                <v-icon size="small">mdi-format-list-bulleted</v-icon>
              </v-btn>
              <v-btn value="card" size="small">
                <v-icon size="small">mdi-view-grid</v-icon>
              </v-btn>
            </v-btn-toggle>
          </v-toolbar>

          <v-divider></v-divider>

          <v-list v-if="viewMode === 'list'" class="py-0">
            <!-- wBKC 币 -->
            <v-list-item class="py-3">
              <template v-slot:prepend>
                <v-avatar color="primary" variant="flat" size="40">
                  <span class="text-subtitle-2 font-weight-bold text-white">wBKC</span>
                </v-avatar>
              </template>

              <v-list-item-title class="font-weight-bold">wBKC</v-list-item-title>
              <v-list-item-subtitle>原生代币</v-list-item-subtitle>

              <template v-slot:append>
                <div class="text-end">
                  <div class="font-weight-bold">{{ walletStore.formatBalance(walletStore.wbkcBalance) }} wBKC</div>
                  <div class="text-caption text-medium-emphasis">${{ walletStore.usdValue }} USD</div>
                </div>
              </template>
            </v-list-item>

            <v-divider inset></v-divider>

            <!-- E20C 币 -->
            <v-list-item class="py-3">
              <template v-slot:prepend>
                <v-avatar color="amber" variant="flat" size="40">
                  <span class="text-subtitle-2 font-weight-bold text-white">E20C</span>
                </v-avatar>
              </template>

              <v-list-item-title class="font-weight-bold">E20C</v-list-item-title>
              <v-list-item-subtitle>平台代币</v-list-item-subtitle>

              <template v-slot:append>
                <div class="text-end">
                  <div class="font-weight-bold">{{ walletStore.formatBalance(walletStore.e20cBalance) }} E20C</div>
                  <div class="text-caption text-medium-emphasis">≈ ${{ e20cUsdValue }} USD</div>
                </div>
              </template>
            </v-list-item>
          </v-list>

          <div v-else class="pa-4">
            <v-row>
              <!-- wBKC 卡片 -->
              <v-col cols="12" sm="6">
                <v-card class="rounded-lg" elevation="0" variant="outlined">
                  <v-card-text>
                    <div class="d-flex align-center mb-3">
                      <v-avatar color="primary" variant="flat" size="38" class="mr-3">
                        <span class="text-subtitle-2 font-weight-bold text-white">wBKC</span>
                      </v-avatar>
                      <div>
                        <div class="font-weight-bold">wBKC</div>
                        <div class="text-caption text-medium-emphasis">原生代币</div>
                      </div>
                    </div>

                    <div class="text-h6 font-weight-bold mb-1">
                      {{ walletStore.formatBalance(walletStore.wbkcBalance) }} wBKC
                    </div>
                    <div class="text-caption text-medium-emphasis">
                      ≈ ${{ walletStore.usdValue }} USD
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>

              <!-- E20C 卡片 -->
              <v-col cols="12" sm="6">
                <v-card class="rounded-lg" elevation="0" variant="outlined">
                  <v-card-text>
                    <div class="d-flex align-center mb-3">
                      <v-avatar color="amber" variant="flat" size="38" class="mr-3">
                        <span class="text-subtitle-2 font-weight-bold text-white">E20C</span>
                      </v-avatar>
                      <div>
                        <div class="font-weight-bold">E20C</div>
                        <div class="text-caption text-medium-emphasis">平台代币</div>
                      </div>
                    </div>

                    <div class="text-h6 font-weight-bold mb-1">
                      {{ walletStore.formatBalance(walletStore.e20cBalance) }} E20C
                    </div>
                    <div class="text-caption text-medium-emphasis">
                      ≈ ${{ e20cUsdValue }} USD
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </div>
        </v-card>

        <!-- 市场行情卡片 -->
        <v-card class="mb-6 rounded-lg" elevation="1">
          <v-toolbar density="compact" flat color="background">
            <v-toolbar-title class="font-weight-bold">市场行情</v-toolbar-title>
            <v-spacer></v-spacer>
            <v-btn icon variant="text" size="small">
              <v-icon size="small">mdi-refresh</v-icon>
            </v-btn>
          </v-toolbar>

          <v-divider></v-divider>

          <v-table density="compact" class="market-table">
            <thead>
              <tr>
                <th class="text-left">代币</th>
                <th class="text-right">最新价格</th>
                <th class="text-right">24h涨跌</th>
                <th class="text-right">24h成交量</th>
                <th class="text-right">市值</th>
                <th class="text-right">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>
                  <div class="d-flex align-center">
                    <v-avatar color="primary" variant="flat" size="28" class="mr-2">
                      <span class="text-caption font-weight-bold text-white">wBKC</span>
                    </v-avatar>
                    <span class="font-weight-medium text-truncate" style="max-width: 100px;">wBKC</span>
                  </div>
                </td>
                <td class="text-right">$0.10</td>
                <td class="text-right text-success">+2.4%</td>
                <td class="text-right">$245,789</td>
                <td class="text-right">$10,000,000</td>
                <td class="text-right">
                  <v-btn color="primary" size="x-small" variant="text" to="/swap">兑换</v-btn>
                </td>
              </tr>
              <tr>
                <td>
                  <div class="d-flex align-center">
                    <v-avatar color="amber" variant="flat" size="28" class="mr-2">
                      <span class="text-caption font-weight-bold text-white">E20C</span>
                    </v-avatar>
                    <span class="font-weight-medium text-truncate" style="max-width: 100px;">E20C</span>
                  </div>
                </td>
                <td class="text-right">$0.01</td>
                <td class="text-right text-error">-1.2%</td>
                <td class="text-right">$124,567</td>
                <td class="text-right">$5,000,000</td>
                <td class="text-right">
                  <v-btn color="primary" size="x-small" variant="text" to="/swap">兑换</v-btn>
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card>

         <!-- 近期活动卡片 -->
         <v-card class="mb-6 rounded-lg" elevation="1">
            <v-toolbar density="compact" flat color="background">
               <v-toolbar-title class="font-weight-bold">近期活动</v-toolbar-title>
               <v-spacer></v-spacer>
               <v-btn variant="text" size="small" to="/history" append-icon="mdi-chevron-right">
                  查看全部
               </v-btn>
            </v-toolbar>
             <v-divider></v-divider>
            <v-list class="py-0">
               <v-list-item class="py-3">
                  <template v-slot:prepend>
                     <v-avatar color="success" variant="tonal" size="32">
                        <v-icon size="small">mdi-arrow-bottom-left</v-icon>
                     </v-avatar>
                  </template>
                  <v-list-item-title class="font-weight-medium">收到 wBKC</v-list-item-title>
                  <v-list-item-subtitle class="text-caption text-medium-emphasis">从 0xAbCd... | 2023-10-28 10:30</v-list-item-subtitle>
                   <template v-slot:append>
                     <div class="text-end">
                         <div class="font-weight-medium text-success">+ 5.00 wBKC</div>
                         <div class="text-caption text-medium-emphasis">≈ $0.50 USD</div>
                     </div>
                   </template>
               </v-list-item>
               <v-divider inset></v-divider>
                <v-list-item class="py-3">
                  <template v-slot:prepend>
                     <v-avatar color="error" variant="tonal" size="32">
                        <v-icon size="small">mdi-arrow-top-right</v-icon>
                     </v-avatar>
                  </template>
                  <v-list-item-title class="font-weight-medium">发送 E20C</v-list-item-title>
                  <v-list-item-subtitle class="text-caption text-medium-emphasis">至 0xEfGh... | 2023-10-27 15:00</v-list-item-subtitle>
                   <template v-slot:append>
                     <div class="text-end">
                         <div class="font-weight-medium text-error">- 100.00 E20C</div>
                         <div class="text-caption text-medium-emphasis">≈ $1.00 USD</div>
                     </div>
                   </template>
               </v-list-item>
                 <v-divider inset></v-divider>
                <v-list-item class="py-3">
                  <template v-slot:prepend>
                     <v-avatar color="warning" variant="tonal" size="32">
                        <v-icon size="small">mdi-swap-horizontal</v-icon>
                     </v-avatar>
                  </template>
                  <v-list-item-title class="font-weight-medium">兑换 wBKC 换 E20C</v-list-item-title>
                  <v-list-item-subtitle class="text-caption text-medium-emphasis">10 wBKC → 100 E20C | 2023-10-27 11:45</v-list-item-subtitle>
                   <template v-slot:append>
                     <div class="text-end">
                         <div class="font-weight-medium text-error">- 10 wBKC</div>
                         <div class="text-caption text-success">+ 100 E20C</div>
                     </div>
                   </template>
               </v-list-item>
               <v-divider inset></v-divider>
                <v-list-item class="py-3">
                  <template v-slot:prepend>
                     <v-avatar color="success" variant="tonal" size="32">
                        <v-icon size="small">mdi-arrow-bottom-left</v-icon>
                     </v-avatar>
                  </template>
                  <v-list-item-title class="font-weight-medium">收到 E20C</v-list-item-title>
                  <v-list-item-subtitle class="text-caption text-medium-emphasis">从 0x1a2b... | 2023-10-26 09:00</v-list-item-subtitle>
                   <template v-slot:append>
                     <div class="text-end">
                         <div class="font-weight-medium text-success">+ 200.00 E20C</div>
                         <div class="text-caption text-medium-emphasis">≈ $2.00 USD</div>
                     </div>
                   </template>
               </v-list-item>
                 <v-divider inset></v-divider>
                <v-list-item class="py-3">
                  <template v-slot:prepend>
                     <v-avatar color="error" variant="tonal" size="32">
                        <v-icon size="small">mdi-arrow-top-right</v-icon>
                     </v-avatar>
                  </template>
                  <v-list-item-title class="font-weight-medium">发送 wBKC</v-list-item-title>
                  <v-list-item-subtitle class="text-caption text-medium-emphasis">至 0x3c4d... | 2023-10-25 18:30</v-list-item-subtitle>
                   <template v-slot:append>
                     <div class="text-end">
                         <div class="font-weight-medium text-error">- 2.50 wBKC</div>
                         <div class="text-caption text-medium-emphasis">≈ $0.25 USD</div>
                     </div>
                   </template>
               </v-list-item>
            </v-list>
         </v-card>
      </v-col>
    </v-row>

    <!-- 错误提示 -->
    <v-snackbar v-model="showError" color="error">
      {{ walletStore.error }}
      <template v-slot:actions>
        <v-btn variant="text" @click="showError = false">
          关闭
        </v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useWalletStore } from '@/store/wallet'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { format } from 'date-fns' // 用于格式化日期

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const walletStore = useWalletStore()
const showError = ref(false)
const viewMode = ref('list')
const lastUpdated = ref('刚刚')

// 行情走势相关
const selectedTimeframe = ref('week') // 'day', 'week', 'month'
const chartStartDate = ref('')
const chartEndDate = ref('')

// 更新图表日期范围的函数
const updateChartDates = () => {
  const endDate = new Date()
  let startDate = new Date()
  
  switch (selectedTimeframe.value) {
    case 'day':
      startDate.setDate(endDate.getDate() - 1)
      break
    case 'week':
      startDate.setDate(endDate.getDate() - 7)
      break
    case 'month':
      startDate.setMonth(endDate.getMonth() - 1)
      break
  }
  chartStartDate.value = format(startDate, 'M/d')
  chartEndDate.value = format(endDate, 'M/d')
}

watch(selectedTimeframe, updateChartDates, { immediate: true })

// 计算 E20C 的美元价值 (E20C 到 wBKC 到 USD)
const e20cUsdValue = computed(() => {
  try {
    // E20C 到 wBKC 的汇率：1 E20C = 0.1 wBKC
    // wBKC 到 USD 的汇率：1 wBKC = 0.1 USD
    // 因此 1 E20C = 0.01 USD
    if (!walletStore.e20cBalance) return '0.00'; // 确保 e20cBalance 存在
    const balanceNum = parseFloat(walletStore.e20cBalance);
    if (isNaN(balanceNum)) return '0.00';
    return (balanceNum * 0.01).toFixed(2)
  } catch {
    return '0.00'
  }
})

// 监听错误状态
watch(() => walletStore.error, (newError) => {
  if (newError) {
    showError.value = true
  }
})

// 刷新余额
const refreshBalances = async () => {
  await walletStore.refreshBalances()
  lastUpdated.value = new Date().toLocaleTimeString()
}

// 组件挂载时刷新数据
onMounted(() => {
  refreshBalances()
})

const chartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: {
      beginAtZero: false,
      display: false, // 不显示y轴
    },
    x: {
      display: false, // 不显示x轴
    }
  },
  plugins: {
    legend: {
      display: false, // 不显示图例
    },
    tooltip: {
      enabled: true, // 启用工具提示
      mode: 'index',
      intersect: false,
      callbacks: {
        label: function(context) {
          return `价格: $${context.parsed.y.toFixed(2)}`;
        }
      }
    }
  },
  elements: {
    line: {
      tension: 0.3, // 线条平滑度
      borderColor: 'rgba(54, 162, 235, 0.8)', // 使用明确的蓝色
      borderWidth: 2,
      fill: true,
      backgroundColor: 'rgba(54, 162, 235, 0.1)', // 使用明确的浅蓝色作为区域填充色
    },
    point: {
      radius: 0, // 不显示数据点
      hoverRadius: 4,
    }
  }
});

// 模拟图表数据
const generatePriceData = (points, volatility = 0.2, startPrice = 100) => {
  const data = [];
  let price = startPrice;
  for (let i = 0; i < points; i++) {
    data.push(price);
    price += (Math.random() - 0.5) * volatility * price;
    if (price < 0) price = 0; // 防止价格为负
  }
  return data;
};

const dailyData = computed(() => ({
  labels: Array.from({ length: 24 }, (_, i) => `${i}:00`),
  datasets: [
    {
      label: '今日价格',
      data: generatePriceData(24, 0.05, Math.random() * 5 + 9.5), // 模拟0.05-0.2 USD范围波动
    }
  ]
}));

const weeklyData = computed(() => ({
  labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
  datasets: [
    {
      label: '本周价格',
      data: generatePriceData(7, 0.1, Math.random() * 10 + 90), // 模拟 90-110 USD范围波动
    }
  ]
}));

const monthlyData = computed(() => {
  const daysInMonth = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getDate();
  return {
    labels: Array.from({ length: daysInMonth }, (_, i) => `${i + 1}`),
    datasets: [
      {
        label: '本月价格',
        data: generatePriceData(daysInMonth, 0.15, Math.random() * 20 + 80), // 模拟 80-120 USD范围波动
      }
    ]
  };
});

const currentChartData = computed(() => {
  switch (selectedTimeframe.value) {
    case 'day':
      return dailyData.value;
    case 'week':
      return weeklyData.value;
    case 'month':
      return monthlyData.value;
    default:
      return weeklyData.value;
  }
});
</script>

<style scoped>
.market-table th,
.market-table td {
  white-space: nowrap;
}

.price-chart-container {
  height: 80px; /* 调整图表容器高度 */
  position: relative;
}

/* 移除旧的占位符样式 */
</style>
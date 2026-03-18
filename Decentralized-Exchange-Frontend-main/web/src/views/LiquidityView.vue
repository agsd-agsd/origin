<template>
    <v-container>
      <v-row>
        <!-- 左侧流动性操作区域 -->
        <v-col cols="12" md="6">
          <v-card class="rounded-lg" elevation="1">
            <v-card-title class="font-weight-bold px-4 pt-4 pb-2">
              <div class="d-flex align-center">
                <v-icon color="primary" class="mr-2">mdi-water</v-icon>
                流动性管理
              </div>
            </v-card-title>
            
            <v-card-text class="px-4 pb-4">
              <v-tabs v-model="activeTab" grow class="mb-4">
                <v-tab value="add">添加流动性</v-tab>
                <v-tab value="remove">移除流动性</v-tab>
              </v-tabs>
              
              <v-window v-model="activeTab">
                <!-- 添加流动性面板 -->
                <v-window-item value="add">
                  <!-- wBKC输入框 -->
                  <v-card class="mb-4 rounded-lg" variant="outlined">
                    <v-card-text class="pa-4">
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption text-medium-emphasis">Token A (wBKC)</span>
                        <span class="text-caption">
                          余额: {{ walletStore.formatBalance(walletStore.wbkcBalance) }} wBKC
                          <v-btn density="compact" variant="text" size="x-small" class="ml-1" @click="setMaxAmountA">最大</v-btn>
                        </span>
                      </div>
                      
                      <div class="d-flex align-center">
                        <v-text-field
                          v-model="amountA"
                          type="number"
                          min="0"
                          step="1"
                          density="compact"
                          variant="plain"
                          hide-details
                          class="text-h5 font-weight-bold"
                          :disabled="isLoading"
                          @input="calculateRatio('A')"
                        ></v-text-field>
                        
                        <v-spacer></v-spacer>
                        
                        <div class="d-flex align-center">
                          <v-avatar 
                            size="28" 
                            color="primary" 
                            class="mr-2" 
                            variant="flat"
                          >
                            <span class="text-white font-weight-bold text-caption">wBKC</span>
                          </v-avatar>
                           <span class="font-weight-medium">wBKC</span>
                        </div>
                      </div>
                    </v-card-text>
                  </v-card>
                  
                  <!-- 加号图标 -->
                  <div class="text-center my-2 position-relative">
                    <v-btn
                      color="primary"
                      icon
                      size="small"
                      variant="flat"
                      disabled
                    >
                      <v-icon size="small">mdi-plus</v-icon>
                    </v-btn>
                  </div>
                  
                  <!-- E20C输入框 -->
                  <v-card class="mb-4 rounded-lg" variant="outlined">
                    <v-card-text class="pa-4">
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption text-medium-emphasis">Token B (E20C)</span>
                        <span class="text-caption">
                          余额: {{ walletStore.formatBalance(walletStore.e20cBalance) }} E20C
                          <v-btn density="compact" variant="text" size="x-small" class="ml-1" @click="setMaxAmountB">最大</v-btn>
                        </span>
                      </div>
                      
                      <div class="d-flex align-center">
                        <v-text-field
                          v-model="amountB"
                          type="number"
                          min="0"
                          step="1"
                          density="compact"
                          variant="plain"
                          hide-details
                          class="text-h5 font-weight-bold"
                          :disabled="isLoading"
                          @input="calculateRatio('B')"
                        ></v-text-field>
                        
                        <v-spacer></v-spacer>
                        
                        <div class="d-flex align-center">
                          <v-avatar 
                            size="28" 
                            color="amber" 
                            class="mr-2" 
                            variant="flat"
                          >
                            <span class="text-white font-weight-bold text-caption">E20C</span>
                          </v-avatar>
                           <span class="font-weight-medium">E20C</span>
                        </div>
                      </div>
                    </v-card-text>
                  </v-card>
                  
                  <!-- 公告栏 -->
                  <v-alert
                    type="info"
                    variant="tonal"
                    class="mb-4 rounded-lg"
                    icon="mdi-information-outline"
                    density="compact"
                  >
                    <div class="text-caption">
                      <strong>流动性说明:</strong> 首次添加流动性将确定交易对的初始价格比率。系统会锁定最小流动性作为池子稳定性储备。
                    </div>
                  </v-alert>
                  
                  <!-- 价格信息 -->
                  <v-card class="mb-4 rounded-lg bg-surface-variant" variant="flat">
                    <v-card-text class="pa-4">
                      <div class="d-flex justify-space-between text-caption">
                        <span class="text-medium-emphasis">价格比率</span>
                        <span>1 wBKC = {{ priceBPerA }} E20C</span>
                      </div>
                      <div class="d-flex justify-space-between text-caption mt-1">
                        <span class="text-medium-emphasis">预计LP代币</span>
                        <span>{{ estimatedLPTokens }}</span>
                      </div>
                      <div class="d-flex justify-space-between text-caption mt-1">
                        <span class="text-medium-emphasis">池子份额</span>
                        <span>{{ poolShare }}%</span>
                      </div>
                    </v-card-text>
                  </v-card>
                  
                  <!-- 错误提示 -->
                  <v-alert
                    v-if="errorMessage"
                    type="error"
                    variant="tonal"
                    class="mb-4 rounded-lg"
                    closable
                    @click:close="errorMessage = ''"
                  >
                    {{ errorMessage }}
                  </v-alert>
                  
                  <!-- 添加流动性按钮 -->
                  <v-btn
                    block
                    color="primary"
                    size="large"
                    class="rounded-lg font-weight-bold"
                    height="48"
                    :disabled="!isAddLiquidityValid || isLoading"
                    :loading="isLoading"
                    @click="handleAddLiquidity"
                  >
                    {{ getAddLiquidityButtonText() }}
                  </v-btn>
                </v-window-item>
                
                <!-- 移除流动性面板 -->
                <v-window-item value="remove">
                  <!-- LP代币输入 -->
                  <v-card class="mb-4 rounded-lg" variant="outlined">
                    <v-card-text class="pa-4">
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption text-medium-emphasis">LP代币数量</span>
                        <span class="text-caption">
                          余额: {{ walletStore.formatBalance(lpBalance) }} LP
                          <v-btn density="compact" variant="text" size="x-small" class="ml-1" @click="setMaxLPAmount">最大</v-btn>
                        </span>
                      </div>
                      
                      <div class="d-flex align-center">
                        <v-text-field
                          v-model="lpAmount"
                          type="number"
                          min="0"
                          step="1"
                          density="compact"
                          variant="plain"
                          hide-details
                          class="text-h5 font-weight-bold"
                          :disabled="isLoading"
                          @input="calculateRemoveLiquidity"
                        ></v-text-field>
                        
                        <v-spacer></v-spacer>
                        
                        <div class="d-flex align-center">
                          <v-avatar 
                            size="28" 
                            color="deep-purple" 
                            class="mr-2" 
                            variant="flat"
                          >
                            <span class="text-white font-weight-bold text-caption">LP</span>
                          </v-avatar>
                           <span class="font-weight-medium">LP代币</span>
                        </div>
                      </div>
                    </v-card-text>
                  </v-card>
                  
                  <!-- 返回代币预览 -->
                  <v-card class="mb-4 rounded-lg bg-surface-variant" variant="flat">
                    <v-card-text class="pa-4">
                      <div class="text-subtitle-2 mb-3">您将收到:</div>
                      
                      <div class="d-flex justify-space-between align-center mb-2">
                        <div class="d-flex align-center">
                          <v-avatar size="24" color="primary" class="mr-2">
                            <span class="text-caption text-white">wBKC</span>
                          </v-avatar>
                          <span>wBKC</span>
                        </div>
                        <span class="font-weight-medium">{{ walletStore.formatBalance(expectedAmountA) }}</span>
                      </div>
                      
                      <div class="d-flex justify-space-between align-center">
                        <div class="d-flex align-center">
                          <v-avatar size="24" color="amber" class="mr-2">
                            <span class="text-caption text-white">E20C</span>
                          </v-avatar>
                          <span>E20C</span>
                        </div>
                        <span class="font-weight-medium">{{ walletStore.formatBalance(expectedAmountB) }}</span>
                      </div>
                    </v-card-text>
                  </v-card>
                  
                  <!-- 错误提示 -->
                  <v-alert
                    v-if="errorMessage"
                    type="error"
                    variant="tonal"
                    class="mb-4 rounded-lg"
                    closable
                    @click:close="errorMessage = ''"
                  >
                    {{ errorMessage }}
                  </v-alert>
                  
                  <!-- 移除流动性按钮 -->
                  <v-btn
                    block
                    color="error"
                    size="large"
                    class="rounded-lg font-weight-bold"
                    height="48"
                    :disabled="!isRemoveLiquidityValid || isLoading"
                    :loading="isLoading"
                    @click="handleRemoveLiquidity"
                  >
                    {{ getRemoveLiquidityButtonText() }}
                  </v-btn>
                </v-window-item>
              </v-window>
            </v-card-text>
          </v-card>
        </v-col>
        
        <!-- 右侧流动性信息和统计 -->
        <v-col cols="12" md="6">
          <!-- 池子信息卡片 -->
          <v-card class="mb-6 rounded-lg" elevation="1">
            <v-card-title class="font-weight-bold px-4 pt-4 pb-2">
              <div class="d-flex align-center">
                <v-icon color="primary" class="mr-2">mdi-chart-pie</v-icon>
                流动性池数据
              </div>
            </v-card-title>
            
            <v-card-text>
              <v-list>
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon color="primary">mdi-water-percent</v-icon>
                  </template>
                  <v-list-item-title>总流动性 (TVL)</v-list-item-title>
                  <v-list-item-subtitle>≈ ${{ formatUsdValue(totalLiquidityValue) }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon color="primary">mdi-bank</v-icon>
                  </template>
                  <v-list-item-title>Pool Token A (wBKC)</v-list-item-title>
                  <v-list-item-subtitle>{{ walletStore.formatBalance(poolInfo.tokenABalance) }} wBKC</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon color="amber">mdi-bank</v-icon>
                  </template>
                  <v-list-item-title>Pool Token B (E20C)</v-list-item-title>
                  <v-list-item-subtitle>{{ walletStore.formatBalance(poolInfo.tokenBBalance) }} E20C</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon color="deep-purple">mdi-ticket-confirmation</v-icon>
                  </template>
                  <v-list-item-title>LP代币总供应量</v-list-item-title>
                  <v-list-item-subtitle>{{ walletStore.formatBalance(poolInfo.totalLPSupply) }} LP</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon color="info">mdi-swap-horizontal</v-icon>
                  </template>
                  <v-list-item-title>当前汇率</v-list-item-title>
                  <v-list-item-subtitle>1 wBKC = {{ priceBPerA }} E20C</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
          
          <!-- 用户流动性卡片 -->
          <v-card class="rounded-lg" elevation="1">
            <v-card-title class="font-weight-bold px-4 pt-4 pb-2">
              <div class="d-flex align-center">
                <v-icon color="deep-purple" class="mr-2">mdi-account-cash</v-icon>
                您的流动性
              </div>
            </v-card-title>
            
            <v-card-text>
              <v-list v-if="Number(lpBalance) > 0">
                <v-list-item>
                  <template v-slot:prepend>
                    <v-avatar size="36" color="deep-purple" class="mr-2">
                      <span class="text-caption text-white">LP</span>
                    </v-avatar>
                  </template>
                  <v-list-item-title class="font-weight-medium">{{ walletStore.formatBalance(lpBalance) }} LP代币</v-list-item-title>
                  <v-list-item-subtitle>
                    占池子份额: {{ formatSharePercentage(lpBalance, poolInfo.totalLPSupply) }}%
                  </v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <v-list-item-title>您提供的资产</v-list-item-title>
                  <v-list-item-subtitle>
                    <div class="d-flex align-center mt-1">
                      <v-avatar size="20" color="primary" class="mr-1">
                        <span class="text-caption text-white">w</span>
                      </v-avatar>
                      <span>{{ walletStore.formatBalance(userTokenA) }} wBKC</span>
                    </div>
                    <div class="d-flex align-center mt-1">
                      <v-avatar size="20" color="amber" class="mr-1">
                        <span class="text-caption text-white">E</span>
                      </v-avatar>
                      <span>{{ walletStore.formatBalance(userTokenB) }} E20C</span>
                    </div>
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
              
              <div v-else class="text-center py-8">
                <v-icon size="64" color="grey lighten-2" class="mb-4">mdi-water-off</v-icon>
                <div class="text-h6 text-grey">您还没有提供流动性</div>
                <div class="text-body-2 text-grey">添加代币到池子，赚取手续费收益</div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
      
      <!-- 操作结果对话框 -->
      <v-dialog v-model="showResultDialog" max-width="400" class="rounded-lg">
        <v-card class="rounded-lg">
          <v-card-title :class="operationSuccess ? 'bg-success-lighten-5' : 'bg-error-lighten-5'" class="d-flex align-center px-4 py-3">
            <v-icon :color="operationSuccess ? 'success' : 'error'" class="mr-2">
              {{ operationSuccess ? 'mdi-check-circle-outline' : 'mdi-alert-circle-outline' }}
            </v-icon>
            {{ operationSuccess ? '操作成功' : '操作失败' }}
          </v-card-title>
          <v-card-text class="pa-4 pt-5">
            <div v-if="operationSuccess" class="text-center mb-4">
              <v-avatar class="mb-4" color="success" size="64">
                <v-icon size="36" color="white">mdi-check</v-icon>
              </v-avatar>
              <p class="text-h6 mb-2">{{ activeTab === 'add' ? '添加流动性成功' : '移除流动性成功' }}</p>
              <p class="text-body-2 text-medium-emphasis" v-if="activeTab === 'add'">
                您已成功添加 {{ amountA }} wBKC 和 {{ amountB }} E20C 到流动性池
              </p>
              <p class="text-body-2 text-medium-emphasis" v-else>
                您已成功移除流动性并收到 {{ expectedAmountA }} wBKC 和 {{ expectedAmountB }} E20C
              </p>
            </div>
            
            <div v-else class="text-center mb-4">
              <v-avatar class="mb-4" color="error" size="64">
                <v-icon size="36" color="white">mdi-close</v-icon>
              </v-avatar>
              <p class="text-h6 mb-2">{{ activeTab === 'add' ? '添加流动性失败' : '移除流动性失败' }}</p>
              <p class="text-body-2 text-medium-emphasis">
                {{ errorMessage || '操作处理过程中出现错误，请稍后再试' }}
              </p>
            </div>
          </v-card-text>
          <v-card-actions class="pa-4 pt-0">
            <v-spacer></v-spacer>
            <v-btn color="primary" @click="closeResultDialog">完成</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-container>
  </template>
  
  <script setup>
  import { ref, computed, onMounted, watch } from 'vue';
  import { useWalletStore } from '@/store/wallet';
  import blockchainService from '@/services/blockchain';
  
  const walletStore = useWalletStore();
  
  // 流动性操作页面状态
  const activeTab = ref('add');
  const isLoading = ref(false);
  const errorMessage = ref('');
  const showResultDialog = ref(false);
  const operationSuccess = ref(false);
  
  // 添加流动性数据
  const amountA = ref('');
  const amountB = ref('');
  const priceBPerA = ref('10.00'); // 默认比率
  const estimatedLPTokens = ref('0.00');
  const poolShare = ref('0.00');
  
  // 移除流动性数据
  const lpBalance = ref('0');
  const lpAmount = ref('');
  const expectedAmountA = ref('0.00');
  const expectedAmountB = ref('0.00');
  
  // 池子信息
  const poolInfo = ref({
    tokenABalance: '0',
    tokenBBalance: '0',
    totalLPSupply: '0',
    k: '0'
  });
  
  // 用户信息
  const userTokenA = ref('0');
  const userTokenB = ref('0');
  const totalLiquidityValue = ref('0');
  
  // 计算属性
  const isAddLiquidityValid = computed(() => {
    try {
      // 确保所有金额都是有效的
      if (!amountA.value || !amountB.value) {
        return false;
      }
      
      // 检查数值是否有效 - 兼容Mock模式的小数
      const amountANum = parseFloat(amountA.value);
      const amountBNum = parseFloat(amountB.value);
      if (amountANum <= 0 || amountBNum <= 0) {
        return false;
      }
      
      // 检查余额是否足够 - 兼容Mock模式
      const wbkcBalanceNum = parseFloat(walletStore.wbkcBalance);
      const e20cBalanceNum = parseFloat(walletStore.e20cBalance);
      
      // 如果余额是整数格式，尝试使用BigInt比较，否则使用parseFloat
      let amountAValid, amountBValid;
      try {
        // 尝试BigInt比较（真实模式）
        if (Number.isInteger(amountANum) && Number.isInteger(amountBNum) && 
            Number.isInteger(wbkcBalanceNum) && Number.isInteger(e20cBalanceNum)) {
          amountAValid = BigInt(amountA.value) <= BigInt(walletStore.wbkcBalance);
          amountBValid = BigInt(amountB.value) <= BigInt(walletStore.e20cBalance);
        } else {
          // 使用浮点数比较（Mock模式）
          amountAValid = amountANum <= wbkcBalanceNum;
          amountBValid = amountBNum <= e20cBalanceNum;
        }
      } catch {
        // BigInt转换失败，使用浮点数比较
        amountAValid = amountANum <= wbkcBalanceNum;
        amountBValid = amountBNum <= e20cBalanceNum;
      }
      
      return amountAValid && amountBValid;
    } catch (error) {
      console.error('验证输入时出错:', error);
      return false;
    }
  });
  
  const isRemoveLiquidityValid = computed(() => {
    return lpAmount.value && 
           parseInt(lpAmount.value) > 0 && 
           parseInt(lpAmount.value) <= parseInt(lpBalance.value);
  });
  
  // 初始化
  onMounted(async () => {
    try {
      isLoading.value = true;
      await refreshPoolInfo();
      await refreshUserLPBalance();
      
      // 计算当前池子价格比例 - 修正映射关系
      if (parseInt(poolInfo.value.tokenABalance) > 0 && parseInt(poolInfo.value.tokenBBalance) > 0) {
        // A是E20C，B是wBKC，但在UI中显示相反
        const ratio = parseInt(poolInfo.value.tokenABalance) / parseInt(poolInfo.value.tokenBBalance);
        priceBPerA.value = (1 / ratio).toFixed(4); // 在UI中显示为wBKC/E20C
      }
      
      isLoading.value = false;
    } catch (error) {
      console.error('初始化流动性页面失败:', error);
      isLoading.value = false;
      errorMessage.value = '加载数据失败';
    }
  });
  
  // 监听输入变化
  watch([amountA, amountB], () => {
    if (amountA.value && amountB.value && parseInt(amountA.value) > 0 && parseInt(amountB.value) > 0) {
      estimateLP();
    } else {
      estimatedLPTokens.value = '0.00';
      poolShare.value = '0.00';
    }
  });
  
  watch(lpAmount, () => {
    if (lpAmount.value && parseInt(lpAmount.value) > 0) {
      calculateRemoveLiquidity();
    } else {
      expectedAmountA.value = '0.00';
      expectedAmountB.value = '0.00';
    }
  });
  
  // 方法
  const refreshPoolInfo = async () => {
    try {
      const info = await blockchainService.getPoolInfo();
      
      // 直接使用合约返回的原始数值，不进行任何转换
      poolInfo.value = {
        tokenABalance: info.tokenABalance,
        tokenBBalance: info.tokenBBalance,
        totalLPSupply: info.totalLPSupply,
        k: info.k
      };
      
      // 计算总流动性价值 (假设 1 wBKC = $0.1, 1 E20C = $0.01)
      const wbkcValue = parseInt(info.tokenABalance) * 0.1;
      const e20cValue = parseInt(info.tokenBBalance) * 0.01;
      totalLiquidityValue.value = (wbkcValue + e20cValue).toFixed(2);
      
    } catch (error) {
      console.error('获取池子信息失败:', error);
      throw error;
    }
  };
  
  // 刷新用户LP余额
  const refreshUserLPBalance = async () => {
    try {
      const balance = await blockchainService.getUserLPBalance(walletStore.address);
      // 直接使用合约返回的原始数值，不进行任何转换
      lpBalance.value = balance;
      
      // 计算用户提供的代币数量 - 修正映射关系
      if (parseInt(lpBalance.value) > 0 && parseInt(poolInfo.value.totalLPSupply) > 0) {
        const userShare = parseInt(lpBalance.value) / parseInt(poolInfo.value.totalLPSupply);
        // 修正映射：tokenA是E20C，tokenB是wBKC
        userTokenB.value = Math.floor(userShare * parseInt(poolInfo.value.tokenABalance)).toString(); // E20C显示为B
        userTokenA.value = Math.floor(userShare * parseInt(poolInfo.value.tokenBBalance)).toString(); // wBKC显示为A
      } else {
        userTokenA.value = '0';
        userTokenB.value = '0';
      }
      
    } catch (error) {
      console.error('获取LP余额失败:', error);
      throw error;
    }
  };
  
  const setMaxAmountA = () => {
    amountA.value = walletStore.wbkcBalance;
    calculateRatio('A');
  };
  
  const setMaxAmountB = () => {
    amountB.value = walletStore.e20cBalance;
    calculateRatio('B');
  };
  
  const setMaxLPAmount = () => {
    lpAmount.value = lpBalance.value;
    calculateRemoveLiquidity();
  };
  
  const calculateRatio = async () => {
    try {
      // 在AMM模型中，价格由池子中的资产比例决定
      // 使用getAmountBOut和getAmountAOut来计算预期输出

      if (poolInfo.value.tokenABalance === '0' || poolInfo.value.tokenBBalance === '0') {
        // 首次添加流动性时，自由设置比例
        return;
      }
      
      // 根据当前池子比例自动计算另一个代币数量
      if (amountA.value && parseInt(amountA.value) > 0) {
        // 修正映射关系：amountA.value是wBKC(对应合约B)
        // 如果用户输入了A代币数量(wBKC)，计算出相应的B代币数量(E20C)
        // 使用getAmountAOut来计算wBKC兑换E20C的数量
        const amountBOut = await blockchainService.getAmountAOut(amountA.value);
        amountB.value = amountBOut;
        
        // 显示当前比例
        if (parseInt(amountA.value) > 0 && parseInt(amountBOut) > 0) {
          const ratio = parseInt(amountBOut) / parseInt(amountA.value);
          priceBPerA.value = ratio.toFixed(4);
        }
      } else if (amountB.value && parseInt(amountB.value) > 0) {
        // 修正映射关系：amountB.value是E20C(对应合约A)
        // 如果用户输入了B代币数量(E20C)，计算出相应的A代币数量(wBKC)
        // 使用getAmountBOut来计算E20C兑换wBKC的数量
        const amountAOut = await blockchainService.getAmountBOut(amountB.value);
        amountA.value = amountAOut;
        
        // 显示当前比例
        if (parseInt(amountB.value) > 0 && parseInt(amountAOut) > 0) {
          const ratio = parseInt(amountB.value) / parseInt(amountAOut);
          priceBPerA.value = ratio.toFixed(4);
        }
      }
    } catch (error) {
      console.error('计算比例失败:', error);
    }
  };
  
  const estimateLP = () => {
    try {
      if (!amountA.value || !amountB.value || 
          parseInt(amountA.value) <= 0 || parseInt(amountB.value) <= 0) {
        return;
      }
      
      const amountANum = parseInt(amountA.value); // wBKC
      const amountBNum = parseInt(amountB.value); // E20C
      const totalLPSupply = parseInt(poolInfo.value.totalLPSupply);
      // 修正映射关系
      const poolTokenANum = parseInt(poolInfo.value.tokenBBalance); // tokenB=wBKC对应UI中的A
      const poolTokenBNum = parseInt(poolInfo.value.tokenABalance); // tokenA=E20C对应UI中的B
      
      let lpAmount;
      if (totalLPSupply === 0 || poolTokenANum === 0 || poolTokenBNum === 0) {
        // 首次添加流动性，使用几何平均数
        lpAmount = Math.floor(Math.sqrt(amountANum * amountBNum));
      } else {
        // 后续添加流动性，按比例计算
        const lpFromA = Math.floor((amountANum * totalLPSupply) / poolTokenANum);
        const lpFromB = Math.floor((amountBNum * totalLPSupply) / poolTokenBNum);
        lpAmount = Math.min(lpFromA, lpFromB);
      }
      
      estimatedLPTokens.value = lpAmount.toString();
      
      // 计算池子份额
      if (totalLPSupply > 0) {
        const newShare = (lpAmount / (totalLPSupply + lpAmount)) * 100;
        poolShare.value = newShare.toFixed(2);
      } else {
        poolShare.value = '100.00';
      }
    } catch (error) {
      console.error('估算LP代币失败:', error);
    }
  };
  
  // 计算移除流动性得到的代币数量
  const calculateRemoveLiquidity = () => {
    try {
      if (!lpAmount.value || parseInt(lpAmount.value) <= 0) {
        return;
      }
      
      const lpAmountNum = parseInt(lpAmount.value);
      const totalLPSupply = parseInt(poolInfo.value.totalLPSupply);
      const poolTokenANum = parseInt(poolInfo.value.tokenABalance);
      const poolTokenBNum = parseInt(poolInfo.value.tokenBBalance);
      
      if (totalLPSupply > 0 && lpAmountNum <= totalLPSupply) {
        const shareRatio = lpAmountNum / totalLPSupply;
        const amountA = Math.floor(poolTokenANum * shareRatio); // E20C
        const amountB = Math.floor(poolTokenBNum * shareRatio); // wBKC
        
        // 修正代币A(E20C)和B(wBKC)的映射
        expectedAmountB.value = amountA.toString(); // E20C在UI中显示为B
        expectedAmountA.value = amountB.toString(); // wBKC在UI中显示为A
      } else {
        expectedAmountA.value = '0';
        expectedAmountB.value = '0';
      }
    } catch (error) {
      console.error('计算移除流动性失败:', error);
    }
  };
  
  const formatUsdValue = (amount) => {
    try {
      const num = typeof amount === 'string' ? parseFloat(amount) : amount;
      if (!isNaN(num)) {
        return num.toFixed(2);
      }
      return '0.00';
    } catch {
      return '0.00';
    }
  };
  
  const formatSharePercentage = (lpAmount, totalSupply) => {
    try {
      if (!lpAmount || !totalSupply) return '0.00';
      
      const lpNum = parseInt(lpAmount);
      const totalNum = parseInt(totalSupply);
      
      if (isNaN(lpNum) || isNaN(totalNum) || totalNum === 0) {
        return '0.00';
      }
      
      return ((lpNum / totalNum) * 100).toFixed(2);
    } catch {
      return '0.00';
    }
  };

  const getAddLiquidityButtonText = () => {
    if (!amountA.value || !amountB.value) {
      return '请输入金额';
    }
    
    if (parseInt(amountA.value) > parseInt(walletStore.wbkcBalance)) {
      return 'wBKC余额不足';
    }
    
    if (parseInt(amountB.value) > parseInt(walletStore.e20cBalance)) {
      return 'E20C余额不足';
    }
    
    return '确认添加流动性';
  };
  
  const getRemoveLiquidityButtonText = () => {
    if (!lpAmount.value) {
      return '请输入LP代币数量';
    }
    
    if (parseInt(lpAmount.value) > parseInt(lpBalance.value)) {
      return 'LP代币余额不足';
    }
    
    return '确认移除流动性';
  };
  
  // 处理兑换
  const handleAddLiquidity = async () => {
    if (!isAddLiquidityValid.value) return;
    
    isLoading.value = true;
    errorMessage.value = '';
    
    try {
      // 这里使用原始数值，不需要任何转换
      const amountAValue = amountB.value;  // E20C对应代币A
      const amountBValue = amountA.value;  // wBKC对应代币B
      
      
      // 调用blockchain.js的添加流动性方法，参数顺序修正
      const result = await blockchainService.addLiquidity(amountAValue, amountBValue);
      
      
      // 刷新数据
      await refreshPoolInfo();
      await refreshUserLPBalance();
      await walletStore.refreshBalances();
      
      // 显示成功对话框
      operationSuccess.value = true;
      showResultDialog.value = true;
    } catch (error) {
      console.error('添加流动性失败:', error);
      errorMessage.value = error.message || '添加流动性失败，请稍后再试';
      operationSuccess.value = false;
      showResultDialog.value = true;
    } finally {
      isLoading.value = false;
    }
  };
  
  // 处理移除流动性
  const handleRemoveLiquidity = async () => {
    if (!isRemoveLiquidityValid.value) return;
    
    isLoading.value = true;
    errorMessage.value = '';
    
    try {
      // 这里使用原始数值，不需要任何转换
      const lpAmountValue = lpAmount.value;
      
      
      // 调用blockchain.js的移除流动性方法
      const result = await blockchainService.removeLiquidity(lpAmountValue);
      
      
      // 刷新数据
      await refreshPoolInfo();
      await refreshUserLPBalance();
      await walletStore.refreshBalances();
      
      // 显示成功对话框
      operationSuccess.value = true;
      showResultDialog.value = true;
    } catch (error) {
      console.error('移除流动性失败:', error);
      errorMessage.value = error.message || '移除流动性失败，请稍后再试';
      operationSuccess.value = false;
      showResultDialog.value = true;
    } finally {
      isLoading.value = false;
    }
  };
  
  const closeResultDialog = () => {
    showResultDialog.value = false;
    
    if (operationSuccess.value) {
      // 重置表单
      if (activeTab.value === 'add') {
        amountA.value = '';
        amountB.value = '';
      } else {
        lpAmount.value = '';
        expectedAmountA.value = '0.00';
        expectedAmountB.value = '0.00';
      }
    }
  };
  </script>
  
  <style scoped>
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
<template>
  <v-container fluid class="d-flex align-center justify-center" style="min-height: 100vh;">
    <v-card class="pa-10" elevation="8" style="width: 400px;">
      <v-card-title class="text-h5 font-weight-bold text-center mb-6">解锁你的钱包</v-card-title>

      <v-card-text>
        <v-alert
          type="info"
          variant="tonal"
          class="mb-4 rounded-lg"
        >
          正在自动使用演示账户登录...
        </v-alert>
        
        <v-form @submit.prevent="login">
          <v-text-field
            v-model="password"
            label="输入密码"
            type="password"
            prepend-inner-icon="mdi-lock-outline"
            variant="outlined"
            density="compact"
            class="mb-4"
            required
          ></v-text-field>

          <v-alert
            v-if="error"
            type="error"
            variant="tonal"
            class="mb-4 rounded-lg"
          >
            {{ error }}
          </v-alert>

          <v-btn
            type="submit"
            color="primary"
            size="large"
            block
            class="rounded-lg font-weight-bold"
            :loading="isLoading"
            :disabled="isLoading"
          >
            解锁
          </v-btn>
          
          <v-btn
            color="success"
            size="large"
            block
            class="rounded-lg font-weight-bold mt-2"
            @click="useDemo"
            :loading="isLoading"
            :disabled="isLoading"
          >
            使用演示账户
          </v-btn>
        </v-form>
      </v-card-text>

      <v-card-actions class="text-center d-block">
        <router-link to="/register" class="text-body-2 text-primary text-decoration-none">
          没有钱包？创建新钱包 <v-icon size="small">mdi-chevron-right</v-icon>
        </router-link>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWalletStore } from '@/store/wallet'
import walletService from '@/services/walletService'
import CONFIG from '@/config'

const router = useRouter()
const walletStore = useWalletStore()

const password = ref('')
const isLoading = ref(false)
const error = ref('')

onMounted(async () => {
  // 自动使用演示账户
  await useDemo()
})

// 使用演示账户
const useDemo = async () => {
  isLoading.value = true
  error.value = ''
  
  try {
    walletStore.setAddress(CONFIG.DEMO_ACCOUNT)
    await walletStore.refreshBalances()
    router.replace('/dashboard')
  } catch (err) {
    console.error('演示账户登录失败:', err)
    error.value = '演示账户登录失败，请尝试手动登录'
  } finally {
    isLoading.value = false
  }
}

const login = async () => {
  if (!password.value) {
    error.value = '请输入密码'
    return
  }

  isLoading.value = true
  error.value = ''
  
  try {
    // 使用钱包服务解锁钱包
    const wallet = walletService.unlockWallet(password.value)
    
    if (wallet) {
      
      // 更新钱包状态
      walletStore.setAddress(wallet.address)
      
      // 刷新余额
      await walletStore.refreshBalances()
      
      // 跳转到仪表盘
      router.push('/dashboard')
    } else {
      error.value = '密码错误或钱包数据损坏'
    }
  } catch (err) {
    console.error('登录错误:', err)
    error.value = '登录过程中发生错误'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
/* 可以添加一些样式来进一步美化 */
</style> 
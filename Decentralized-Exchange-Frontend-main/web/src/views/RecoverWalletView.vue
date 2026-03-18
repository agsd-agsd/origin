<template>
  <v-container fluid class="d-flex align-center justify-center" style="min-height: 100vh;">
    <v-card class="pa-8" elevation="8" style="width: 500px;">
      <v-card-title class="text-h5 font-weight-bold text-center mb-6">恢复钱包</v-card-title>

      <v-card-text>
        <v-form @submit.prevent="recoverWallet">
          <div class="text-body-2 mb-4">
            请输入您的助记词（通常为12个单词，用空格分隔）：
          </div>
          
          <v-textarea
            v-model="mnemonic"
            label="助记词"
            variant="outlined"
            rows="3"
            placeholder="例如: apple banana cat dog elephant fish goat horse igloo jacket kite lion"
            class="mb-4"
            hide-details
            required
          ></v-textarea>
          
          <v-text-field
            v-model="password"
            label="设置新密码"
            type="password"
            prepend-inner-icon="mdi-lock-outline"
            variant="outlined"
            density="compact"
            class="mb-2"
            :error-messages="passwordError"
            required
          ></v-text-field>
          
          <v-text-field
            v-model="confirmPassword"
            label="确认密码"
            type="password"
            prepend-inner-icon="mdi-lock-check-outline"
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
            恢复钱包
          </v-btn>
        </v-form>
      </v-card-text>

      <v-card-actions class="text-center d-block">
        <router-link to="/login" class="text-body-2 text-primary text-decoration-none">
          返回登录 <v-icon size="small">mdi-chevron-right</v-icon>
        </router-link>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useWalletStore } from '@/store/wallet'
import walletService from '@/services/walletService'

const router = useRouter()
const walletStore = useWalletStore()

// 表单数据
const mnemonic = ref('')
const password = ref('')
const confirmPassword = ref('')
const isLoading = ref(false)
const error = ref('')

// 密码错误信息
const passwordError = computed(() => {
  if (!password.value) return null
  return walletService.validatePassword(password.value)
})

// 恢复钱包
const recoverWallet = async () => {
  // 验证助记词
  if (!mnemonic.value.trim()) {
    error.value = '请输入助记词'
    return
  }
  
  // 简单验证助记词格式
  const words = mnemonic.value.trim().split(/\s+/)
  if (words.length < 12) {
    error.value = '助记词应至少包含12个单词'
    return
  }
  
  // 验证密码
  const pwdError = walletService.validatePassword(password.value)
  if (pwdError) {
    error.value = pwdError
    return
  }
  
  if (password.value !== confirmPassword.value) {
    error.value = '密码和确认密码不同！'
    return
  }
  
  isLoading.value = true
  error.value = ''
  
  try {
    // 从助记词恢复钱包
    const wallet = walletService.recoverFromMnemonic(mnemonic.value.trim())
    
    if (wallet) {
      
      // 加密并存储钱包数据
      walletService.secureStore(wallet, password.value)
      
      // 设置钱包地址到状态管理
      walletStore.setAddress(wallet.address)
      
      // 提示用户
      alert('钱包恢复成功！')
      
      // 跳转到仪表盘
      router.push('/dashboard')
    } else {
      error.value = '无法从提供的助记词恢复钱包'
    }
  } catch (err) {
    console.error('恢复钱包错误:', err)
    error.value = '恢复钱包过程中发生错误'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
/* 可以添加一些样式来进一步美化 */
</style> 
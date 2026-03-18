<template>
  <v-container fluid class="d-flex align-center justify-center" style="min-height: 100vh;">
    <v-card class="pa-8" elevation="8" style="width: 500px;">
      <v-card-title class="text-h5 font-weight-bold text-center mb-6">{{ currentStep === 'create' ? '创建新钱包' : '备份助记词' }}</v-card-title>

      <v-card-text v-if="currentStep === 'create'">
        <v-form @submit.prevent="createWallet">
          <v-text-field
            v-model="password"
            label="设置密码"
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
          
          <div class="text-caption mb-6">
            <v-icon size="small" color="info" class="mr-1">mdi-information-outline</v-icon>
            密码用于加密您的钱包数据，至少8个字符，建议包含大小写字母、数字和特殊符号
          </div>

          <v-checkbox
            v-model="agreedToTerms"
            label="我已阅读并同意《服务条款》"
            density="compact"
            class="mb-4"
            hide-details
          ></v-checkbox>

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
            :disabled="isLoading || !agreedToTerms"
          >
            创建钱包
          </v-btn>
        </v-form>
      </v-card-text>

      <!-- 助记词备份步骤 -->
      <v-card-text v-if="currentStep === 'backup'">
        <v-alert
          type="warning"
          variant="tonal"
          class="mb-4 rounded-lg"
        >
          <div class="font-weight-bold mb-1">重要安全提示</div>
          <div class="text-body-2">
            请将这些助记词抄写在纸上并妥善保管。这是恢复钱包的唯一方式，任何人获得这些单词都能控制您的资产。
          </div>
        </v-alert>

        <v-card variant="outlined" class="mb-6 pa-4">
          <div class="d-flex flex-wrap">
            <v-chip
              v-for="(word, index) in mnemonicWords"
              :key="index"
              class="ma-1"
              color="primary"
              variant="outlined"
            >
              <span class="text-caption mr-1">{{ index + 1 }}.</span> {{ word }}
            </v-chip>
          </div>
        </v-card>

        <v-checkbox
          v-model="confirmedBackup"
          label="我已安全备份好这些助记词"
          density="compact"
          class="mb-4"
          hide-details
        ></v-checkbox>

        <v-btn
          color="primary"
          size="large"
          block
          class="rounded-lg font-weight-bold"
          :disabled="!confirmedBackup"
          @click="finishSetup"
        >
          完成设置
        </v-btn>
      </v-card-text>

      <v-card-actions class="text-center d-block" v-if="currentStep === 'create'">
        <router-link to="/login" class="text-body-2 text-primary text-decoration-none">
          已有钱包？前往登录 <v-icon size="small">mdi-chevron-right</v-icon>
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
const password = ref('')
const confirmPassword = ref('')
const agreedToTerms = ref(false)
const isLoading = ref(false)
const error = ref('')

// 步骤控制
const currentStep = ref('create') // create, backup
const confirmedBackup = ref(false)

// 钱包数据
const walletData = ref(null)
const mnemonicWords = ref<string[]>([])

// 密码错误信息
const passwordError = computed(() => {
  if (!password.value) return null
  return walletService.validatePassword(password.value)
})

// 创建钱包
const createWallet = async () => {
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
  
  if (!agreedToTerms.value) {
    error.value = '请同意服务条款！'
    return
  }
  
  isLoading.value = true
  error.value = ''
  
  try {
    // 创建新钱包
    walletData.value = walletService.createWallet()
    
    // 分割助记词用于显示
    mnemonicWords.value = walletData.value.mnemonic.split(' ')
    
    // 进入备份步骤
    currentStep.value = 'backup'
  } catch (err) {
    console.error('创建钱包错误:', err)
    error.value = '创建钱包过程中发生错误'
  } finally {
    isLoading.value = false
  }
}

// 完成设置
const finishSetup = () => {
  // 加密并存储钱包数据
  walletService.secureStore(walletData.value, password.value)
  
  // 设置钱包地址到状态管理
  walletStore.setAddress(walletData.value.address)
  
  // 提示用户
  alert('钱包创建成功！请妥善保管您的助记词，它是恢复钱包的唯一方式。')
  
  // 跳转到登录页面
  router.push('/login')
}
</script>

<style scoped>
/* 可以添加一些样式来进一步美化 */
</style> 
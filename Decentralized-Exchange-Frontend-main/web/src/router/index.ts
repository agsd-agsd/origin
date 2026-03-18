import { createRouter, createWebHistory } from 'vue-router'
import { useWalletStore } from '@/store/wallet'
import CONFIG from '@/config'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            redirect: '/dashboard'
        },
        {
            path: '/register',
            name: 'Register',
            component: () => import('@/views/RegisterView.vue')
        },
        {
            path: '/login',
            name: 'Login',
            component: () => import('@/views/LoginView.vue')
        },
        {
            path: '/recover-wallet',
            name: 'RecoverWallet',
            component: () => import('@/views/RecoverWalletView.vue')
        },
        {
            path: '/dashboard',
            name: 'Dashboard',
            component: () => import('@/views/DashboardView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/swap',
            name: 'Swap',
            component: () => import('@/views/SwapView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/send',
            name: 'Send',
            component: () => import('@/views/SendView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/receive',
            name: 'Receive',
            component: () => import('@/views/ReceiveView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/history',
            name: 'History',
            component: () => import('@/views/HistoryView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/liquidity',
            name: 'Liquidity',
            component: () => import('@/views/LiquidityView.vue'),
            meta: { requiresAuth: true }
        }
    ]
})

// 路由守卫 - 自动使用演示账户
router.beforeEach(async (to, from, next) => {
    const walletStore = useWalletStore()

    // 自动使用演示账户登录
    if (!walletStore.isLoggedIn) {
        walletStore.setAddress(CONFIG.DEMO_ACCOUNT)
        try {
            await walletStore.refreshBalances()
        } catch (error) {
            console.error('自动登录刷新余额失败:', error)
        }
    }
    
    // 如果目标是登录或注册页，但已经登录了演示账户，则重定向到仪表板
    if ((to.path === '/login' || to.path === '/register') && walletStore.isLoggedIn) {
        next('/dashboard')
    } else {
        next()
    }
})

export default router 
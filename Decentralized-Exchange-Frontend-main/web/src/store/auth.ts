import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
    state: () => ({
        isAuthenticated: true, // 暂时设置为 true 以便测试
        user: null
    }),

    actions: {
        login() {
            this.isAuthenticated = true
        },
        logout() {
            this.isAuthenticated = false
        }
    }
}) 
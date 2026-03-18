import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import '@mdi/font/css/materialdesignicons.css'

export default createVuetify({
    components,
    directives,
    icons: {
        defaultSet: 'mdi',
        aliases,
        sets: {
            mdi,
        },
    },
    theme: {
        defaultTheme: 'dark',
        themes: {
            light: {
                dark: false,
                colors: {
                    primary: '#3B82F6', // Tailwind blue-500
                    secondary: '#10B981', // Tailwind emerald-500
                    accent: '#8B5CF6', // Tailwind purple-500
                    error: '#EF4444', // Tailwind red-500
                    warning: '#F59E0B', // Tailwind amber-500
                    info: '#3B82F6', // Tailwind blue-500
                    success: '#10B981', // Tailwind emerald-500
                    background: '#F9FAFB', // Tailwind gray-50
                    surface: '#FFFFFF', // White
                }
            },
            dark: {
                dark: true,
                colors: {
                    primary: '#3B82F6', // Tailwind blue-500
                    secondary: '#10B981', // Tailwind emerald-500 
                    accent: '#8B5CF6', // Tailwind purple-500
                    error: '#EF4444', // Tailwind red-500
                    warning: '#F59E0B', // Tailwind amber-500
                    info: '#3B82F6', // Tailwind blue-500
                    success: '#10B981', // Tailwind emerald-500
                    background: '#111827', // Tailwind gray-900
                    surface: '#1F2937', // Tailwind gray-800
                }
            }
        }
    }
}) 
import { createApp } from 'vue'

import App from './App.vue'
import { initializeLocale } from './locales'
import router from './router'
import './styles/main.css'

await initializeLocale()
createApp(App).use(router).mount('#app')

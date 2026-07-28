import { createApp } from 'vue'

import App from './App.vue'
import { initializeLocale } from './locales'
import router from './router'
import './styles/global/index.js'

await initializeLocale()
createApp(App).use(router).mount('#app')

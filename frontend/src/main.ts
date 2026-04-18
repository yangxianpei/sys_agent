import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './style.css'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import persistState from 'pinia-plugin-persistedstate';
const pinia = createPinia();
pinia.use(persistState)
createApp(App).use(router).use(ElementPlus).use(pinia).mount('#app')

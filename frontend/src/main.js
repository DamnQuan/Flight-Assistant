import { createApp } from 'vue'
import App from './App.vue'
import './style.css'

createApp(App).mount('#app')

// 注册 Service Worker（PWA），开发模式下跳过以避免缓存干扰 HMR
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  // 监听 SW 发来的更新通知，自动刷新页面
  navigator.serviceWorker.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'update') {
      console.log('[PWA] 检测到新版本，自动刷新...')
      window.location.reload()
    }
  })

  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(reg => {
        console.log('[PWA] Service Worker 已注册:', reg.scope)
      })
      .catch(err => {
        console.warn('[PWA] Service Worker 注册失败:', err)
      })
  })
}

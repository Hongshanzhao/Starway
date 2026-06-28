import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src') // 保留，没问题
    }
  },
  server: {
    port: 3000, // 保留，即使启动时被占用，vite 会自动换端口（如 3001/3002），不影响代理
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000', // 关键：用 IPv4 地址，避免 localhost 解析问题
        changeOrigin: true, // 保留，解决跨域
        secure: false, // 新增：兼容本地 http 服务，避免 ssl 校验
        withCredentials: true, // 新增：保留 Cookie/Session，解决验证码刷新问题
        // 删掉冗余的 rewrite 配置
      }
    }
  }
})
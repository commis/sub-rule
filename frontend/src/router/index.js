import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/components/Login.vue'
import Channels from '@/views/Channels.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/channels',
    name: 'Channels',
    component: Channels,
    beforeEnter: (to, from, next) => {
      // 路由守卫，检查用户是否已登录
      const isLoggedIn = localStorage.getItem('isLoggedIn')
      if (isLoggedIn) {
        next()
      } else {
        next('/login')
      }
    }
  },
  {
    path: '/',
    redirect: '/login'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router  
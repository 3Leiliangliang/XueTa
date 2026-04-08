import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/home.vue'
import Translate from '../views/translate.vue'
import Qa from '../views/qa.vue'
import Note from '../views/note.vue'
import Desktop from '../views/desktop.vue'
import Planning from '../views/planning.vue'
import Login from '../views/auth/login.vue'
import Register from '../views/auth/register.vue'
import ResetPassword from '@/views/auth/reset-password.vue'
import About from '../views/about.vue'
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home,
      meta: {
        showHeader: true,
        showFooter: true
      }
    },
    {
      path: '/translate',
      name: 'Translate',
      component: Translate,
      meta: {
        showHeader: true,
        showFooter: true
      }
    },
    {
      path: '/qa',
      name: 'Qa',
      component: Qa,
      meta: {
        showHeader: true,
        showFooter: true
      }
    },
    {
      path: '/note',
      name: 'Note',
      component: Note,
      meta: {
        showHeader: true,
        showFooter: true
      }
    },
    {
      path: '/desktop',
      name: 'Desktop',
      component: Desktop,
      meta: {
        showHeader: true,
        showFooter: false
      }
    },
    {
      path: '/planning',
      name: 'Planning',
      component: Planning,
      meta: {
        showHeader: true,
        showFooter: true
      }
    },
    // 认证模块（无Header/Footer）
    {
      path: '/auth',
      meta: { 
        showHeader: false,
        showFooter: false
       },
      children: [
        {
          path: 'login',
          name: 'Login',
          component: Login
        },
        {
          path: 'register',
          name: 'Register',
          component: Register
        },
        {
          path: 'resetPassword',
          name: 'ResetPassword',
          component: ResetPassword
        }
      ]
    },
    {
      path: '/about',
      name: 'About',
      component: About,
      meta: {
        showHeader: true,
        showFooter: true
      }
    }
  ],
})

export default router

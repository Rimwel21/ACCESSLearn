import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  { path: '/', name: 'Home', component: () => import('@/pages/LandingPage.vue') },
  { path: '/portal', name: 'Portal', component: () => import('@/pages/auth/PortalPage.vue') },
  { path: '/login',    name: 'Login',    component: () => import('@/pages/auth/LoginPage.vue') },
  { path: '/register', name: 'Register', component: () => import('@/pages/auth/RegisterPage.vue') },
  { path: '/admin/login', name: 'AdminLogin', component: () => import('@/pages/admin/AdminLoginPage.vue') },
  { path: '/profile/setup', name: 'ProfileSetup', component: () => import('@/pages/auth/ProfileSetupPage.vue'), meta: { requiresAuth: true } },
  { path: '/forbidden', name: 'Forbidden', component: () => import('@/pages/auth/ForbiddenPage.vue') },

  {
    path: '/teacher',
    component: () => import('@/components/layout/TeacherLayout.vue'),
    meta: { requiresAuth: true, role: 'teacher' },
    children: [
      { path: '',            redirect: '/teacher/dashboard' },
      { path: 'dashboard',   name: 'TeacherDashboard', component: () => import('@/pages/teacher/DashboardPage.vue') },
      { path: 'class',       name: 'ClassManagement',  component: () => import('@/pages/teacher/ClassManagementPage.vue') },
      { path: 'modules',     name: 'Modules',          component: () => import('@/pages/teacher/ModulesPage.vue') },
      { path: 'modules/:moduleId/preview', name: 'ModulePreview', component: () => import('@/pages/teacher/ModulePreviewPage.vue') },
      { path: 'activities',  name: 'TeacherActivities', component: () => import('@/pages/teacher/ActivitiesPage.vue') },
      { path: 'quizzes',     name: 'Quizzes',          component: () => import('@/pages/teacher/QuizzesPage.vue') },
    ],
  },

  // Dashboard keeps the student sidebar layout
  {
    path: '/student',
    component: () => import('@/components/layout/StudentLayout.vue'),
    meta: { requiresAuth: true, role: 'student' },
    children: [
      { path: '',           redirect: '/student/dashboard' },
      { path: 'dashboard',  name: 'StudentDashboard', component: () => import('@/pages/student/DashboardPage.vue') },
      { path: 'quiz',       name: 'StudentQuiz',      component: () => import('@/pages/student/QuizPage.vue') },
      { path: 'activities', name: 'Activities',       component: () => import('@/pages/student/ActivitiesPage.vue') },
      { path: 'activities/handsign', name: 'HandSignLanguage', component: () => import('@/pages/student/HandSignLanguagePage.vue') },
    ],
  },

  {
    path: '/admin',
    component: () => import('@/components/layout/AdminLayout.vue'),
    meta: { requiresAuth: true, role: 'admin' },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', name: 'AdminDashboard', component: () => import('@/pages/admin/DashboardPage.vue') },
    ],
  },

  // Topic viewer renders full-screen, no sidebar; only its own Go Back button.
  {
    path: '/student/modules/:moduleId',
    name: 'TopicViewer',
    component: () => import('@/pages/student/TopicViewerPage.vue'),
    meta: { requiresAuth: true, role: 'student' },
  },

  { path: '/:pathMatch(.*)*', redirect: '/' },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { path: '/forbidden' }
  }

  if (to.meta.role && auth.role && to.meta.role !== auth.role) {
    return auth.role === 'teacher'
      ? { path: '/teacher/class' }
      : auth.role === 'admin'
        ? { path: '/admin/dashboard' }
        : { path: '/student/dashboard' }
  }

  if ((to.name === 'Login' || to.name === 'Register' || to.name === 'Portal' || to.name === 'AdminLogin') && auth.isAuthenticated) {
    return auth.role === 'teacher'
      ? { path: '/teacher/class' }
      : auth.role === 'admin'
        ? { path: '/admin/dashboard' }
        : { path: '/student/dashboard' }
  }

  return true
})

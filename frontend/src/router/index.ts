import { createRouter, createWebHistory } from 'vue-router'
import { ElLoading } from 'element-plus'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            redirect: '/workspace',
            component: () => import('../components/home/index.vue'),
            children: [
                {
                    path: '/conversation',
                    name: 'conversation',
                    component: () => import('../components/conversation/conversation.vue'),
                    meta: {
                        current: 'conversation'
                    },
                    children: [
                        {
                            path: '/conversation/',
                            name: 'defaultPage',
                            component: () => import('../components/conversation/defaultPage.vue'),
                        },
                        {
                            path: '/conversation/chatPage',
                            name: 'chatPage',
                            component: () => import('../components/conversation/chatPage.vue'),
                        }
                    ]
                },
                {
                    path: '/dashboard',
                    name: 'dashboard',
                    component: () => import('../components/dashboard/dashboard.vue'),
                    meta: {
                        current: 'dashboard'
                    }
                },
                {
                    path: '/homepage',
                    name: 'homepage',
                    component: () => import('../components/homepage/homepage.vue'),
                    meta: {
                        current: 'homepage'
                    }
                },
                {
                    path: '/mars',
                    name: 'mars',
                    meta: {
                        current: 'mars'
                    },
                    component: () => import('../components/homepage/mars-chat.vue'),
                },
                {
                    path: '/agent-skill',
                    name: 'agent-skill',
                    component: () => import('../components/skill/agent-skill.vue'),
                    meta: {
                        current: 'agent-skill'
                    }
                },
                {
                    path: '/mcp-server',
                    name: 'mcp-server',
                    component: () => import('../components/mcp/index.vue'),
                    meta: {
                        current: 'mcp-server'
                    }
                },
                {
                    path: '/agent',
                    name: 'agent',
                    component: () => import('../components/agent/agent.vue'),
                    meta: {
                        current: 'agent'
                    }
                },
                {
                    path: '/agent/editor',
                    name: 'agent-editor',
                    meta: {
                        current: 'agent'
                    },
                    component: () => import('../components/agent/agent-editor.vue'),
                },
                {
                    path: '/knowledge',
                    name: 'knowledge',
                    meta: {
                        current: 'knowledge'
                    },
                    component: () => import('../components/knowledge/knowledge.vue'),
                },
                {
                    path: '/knowledge/:knowledgeId/files',
                    name: 'knowledge-file',
                    meta: {
                        current: 'knowledge'
                    },
                    component: () => import('../components/knowledge/knowledge-file.vue'),
                },
                {
                    path: '/tool',
                    name: 'tool',
                    component: () => import('../components/tool/index.vue'),
                    meta: {
                        current: 'tool'
                    }
                },
                {
                    path: '/model',
                    name: 'model',
                    component: () => import('../components/model/index.vue'),
                    meta: {
                        current: 'model'
                    }
                },

            ]
        },
        {
            path: '/workspace',
            name: 'workspace',
            component: () => import('../components/workspace/index.vue'),
            meta: {
                current: 'workspace'
            },
            children: [
                {
                    path: '',
                    name: 'workspaceDefaultPage',
                    component: () => import('../components/workspace/defaultPage.vue'),
                },
                {
                    path: 'workspacePage',
                    name: 'workspacePage',
                    component: () => import('../components/workspace/workspacePage.vue'),
                },
            ]
        },
        {
            path: '/',
            redirect: '/workspace',
        },
        {
            path: '/workspace/taskGraph',
            name: 'taskGraphPage',
            component: () => import('../components/workspace/taskGraphPage.vue'),
            meta: {
                requiresAuth: true
            }
        },
        {
            path: '/login',
            name: 'login',
            component: () => import('../components/login/login.vue'),
        },
        {
            path: '/register',
            name: 'register',
            component: () => import('../components/login/register.vue'),
        },
        // {
        //   path: '/about',
        //   name: 'about',
        //   component: () => import('../views/AboutView.vue'),
        // },
    ],
})

let routeLoading: ReturnType<typeof ElLoading.service> | null = null

const closeRouteLoading = () => {
    if (routeLoading) {
        routeLoading.close()
        routeLoading = null
    }
}

router.beforeEach((to, from, next) => {
    if (to.fullPath !== from.fullPath) {
        closeRouteLoading()
        routeLoading = ElLoading.service({
            lock: true,
            text: '页面加载中...',
            background: 'rgba(255, 255, 255, 0.35)',
        })
    }
    next()
})

router.afterEach(() => {
    closeRouteLoading()
})

router.onError(() => {
    closeRouteLoading()
})

export default router

import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../components/home/index.vue'
import Login from '../components/login/login.vue'
import Register from '../components/login/register.vue'
import Mcp from "../components/mcp/index.vue"
import Tool from "../components/tool/index.vue"
import Model from "../components/model/index.vue"
import Workspace from "../components/workspace/index.vue"
import WorkspaceDefaultPage from "../components/workspace/defaultPage.vue"
import WorkspacePage from "../components/workspace/workspacePage.vue"
import TaskGraphPage from '../components/workspace/taskGraphPage.vue'
import Agent from '../components/agent/agent.vue'
import AgentEditor from '../components/agent/agent-editor.vue'
import Knowledge from '../components/knowledge/knowledge.vue'
import KnowledgeFile from '../components/knowledge/knowledge-file.vue'
import Conversation from '../components/conversation/conversation.vue'
import ChatPage from '../components/conversation/chatPage.vue'
import DefaultPage from '../components/conversation/defaultPage.vue'
import AgentSkill from '../components/skill/agent-skill.vue'
import Homepage from '../components/homepage/homepage.vue'
import MarsChat from '../components/homepage/mars-chat.vue'
import Dashboard from '../components/dashboard/dashboard.vue'
const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            redirect: '/workspace',
            component: HomeView,
            children: [
                {
                    path: '/conversation',
                    name: 'conversation',
                    component: Conversation,
                    meta: {
                        current: 'conversation'
                    },
                    children: [
                        {
                            path: '/conversation/',
                            name: 'defaultPage',
                            component: DefaultPage,
                        },
                        {
                            path: '/conversation/chatPage',
                            name: 'chatPage',
                            component: ChatPage,
                        }
                    ]
                },
                {
                    path: '/dashboard',
                    name: 'dashboard',
                    component: Dashboard,
                    meta: {
                        current: 'dashboard'
                    }
                },
                {
                    path: '/homepage',
                    name: 'homepage',
                    component: Homepage,
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
                    component: MarsChat,
                },
                {
                    path: '/agent-skill',
                    name: 'agent-skill',
                    component: AgentSkill,
                    meta: {
                        current: 'agent-skill'
                    }
                },
                {
                    path: '/mcp-server',
                    name: 'mcp-server',
                    component: Mcp,
                    meta: {
                        current: 'mcp-server'
                    }
                },
                {
                    path: '/agent',
                    name: 'agent',
                    component: Agent,
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
                    component: AgentEditor,
                },
                {
                    path: '/knowledge',
                    name: 'knowledge',
                    meta: {
                        current: 'knowledge'
                    },
                    component: Knowledge,
                },
                {
                    path: '/knowledge/:knowledgeId/files',
                    name: 'knowledge-file',
                    meta: {
                        current: 'knowledge'
                    },
                    component: KnowledgeFile,
                },
                {
                    path: '/tool',
                    name: 'tool',
                    component: Tool,
                    meta: {
                        current: 'tool'
                    }
                },
                {
                    path: '/model',
                    name: 'model',
                    component: Model,
                    meta: {
                        current: 'model'
                    }
                },

            ]
        },
        {
            path: '/workspace',
            name: 'workspace',
            component: Workspace,
            meta: {
                current: 'workspace'
            },
            children: [
                {
                    path: '',
                    name: 'workspaceDefaultPage',
                    component: WorkspaceDefaultPage,
                },
                {
                    path: 'workspacePage',
                    name: 'workspacePage',
                    component: WorkspacePage,
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
            component: TaskGraphPage,
            meta: {
                requiresAuth: true
            }
        },
        {
            path: '/login',
            name: 'login',
            component: Login,
        },
        {
            path: '/register',
            name: 'register',
            component: Register,
        },
        // {
        //   path: '/about',
        //   name: 'about',
        //   component: () => import('../views/AboutView.vue'),
        // },
    ],
})

export default router

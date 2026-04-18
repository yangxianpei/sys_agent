<script setup lang="ts">
import { useUserStore } from './store/user'

const userStore = useUserStore()
/** 刷新后把 localStorage 里的 token / userInfo 同步进 Pinia（与 request 拦截器用的键一致） */
userStore.initUserState()
</script>

<template>
       <router-view></router-view>
</template>

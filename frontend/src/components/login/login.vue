<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { loginAPI } from '../../api/login'
import { useUserStore } from '../../store/user'

const router = useRouter()
const userStore = useUserStore()

const loginForm = reactive({
  username: '',
  password: ''
})

// const loading = ref(false)

// const handleLogin = async () => {
//   if (!loginForm.username || !loginForm.password) {
//     ElMessage.warning('请输入用户名和密码')
//     return
//   }

//   try {
//     loading.value = true
//     const response = await loginAPI(loginForm)
    
//     // response.data结构可能是{status_code: number, data: {...}}
//     const responseData = response.data
//     if (responseData.status_code === 200) {
//       ElMessage.success('登录成功')
      
//       // 使用store管理用户状态
//       const userData = responseData.data || {}
//       if (userData.access_token && userData.user_id) {
//         // 先保存基础用户信息
//         userStore.setUserInfo(userData.access_token, {
//           id: userData.user_id,
//           username: loginForm.username
//         })
        
//         // 立即获取完整的用户信息（包括头像等）
//         try {
//           const userInfoResponse = await getUserInfoAPI(userData.user_id)
//           const userInfoData = userInfoResponse.data
//           if (userInfoData.status_code === 200) {
//             const completeUserData = userInfoData.data || {}
//             // 更新用户信息，包含头像
//             userStore.updateUserInfo({
//               avatar: completeUserData.user_avatar || completeUserData.avatar,
//               description: completeUserData.user_description || completeUserData.description
//             })
//           }
//         } catch (error) {
//           console.error('获取用户详细信息失败:', error)
//         }
//       }
      
//       // 跳转到主页
//       router.push('/')
//     } else {
//       ElMessage.error(responseData.status_message || '登录失败')
//     }
//   } catch (error: any) {
//     console.error('登录错误:', error)
//     if (error.response?.data?.message) {
//       ElMessage.error(error.response.data.status_message)
//     } else if (error.response?.data?.detail) {
//       ElMessage.error(error.response.data.detail)
//     } else {
//       ElMessage.error('登录失败，请检查网络连接')
//     }
//   } finally {
//     loading.value = false
//   }
// }

const goToRegister = () => {
  router.push('/register')
}

const handleLogin=(e:any)=>{
  console.log(e)
}
const login_handle= async ()=>{
  const d=await loginAPI(loginForm)
  debugger
  if(d.code ==200){
    ElMessage.success('登录成功')
    userStore.setUserInfo(d.data)
    router.push('/')
  }else{
    ElMessage.error('登录失败')
  }

}

</script>

<template>
  <div class="login-container">
    <!-- 左侧3D图形区域 -->
    <div class="left-section">
      <div class="graphic-container">
        <div class="mesh-blobs" aria-hidden="true">
          <span class="blob blob-a"></span>
          <span class="blob blob-b"></span>
          <span class="blob blob-c"></span>
        </div>
        <div class="grid-floor" aria-hidden="true" />
        <div class="scene-3d">
          <div class="hub">
            <div class="hub-glow" />
            <div class="hub-sphere" />
            <div class="hub-ring ring-1" />
            <div class="hub-ring ring-2" />
            <div class="hub-ring ring-3" />
          </div>
          <div class="orbit-cube">
            <div class="mini-cube">
              <span class="mc f"></span><span class="mc b"></span><span class="mc r"></span>
              <span class="mc l"></span><span class="mc t"></span><span class="mc bo"></span>
            </div>
          </div>
          <div class="float-orb orb-1" />
          <div class="float-orb orb-2" />
        </div>
      </div>
    </div>

    <!-- 右侧登录表单区域 -->
    <div class="right-section">
      <div class="login-form-container">
        <!-- Logo和标题 -->
        <div class="header">
          <div class="logo">
            <span class="logo-text">HelloAgent</span>
          </div>
          <p class="subtitle">更智能、更多元的大模型应用开发平台</p>
        </div>

        <!-- 登录表单 -->
        <div class="login-form">
          <div class="form-group">
            <label class="form-label">账号</label>
            <el-input
              v-model="loginForm.username"
              placeholder="请输入账号"
              size="large"
              class="login-input"
              @change="handleLogin"
            />
          </div>

          <div class="form-group">
            <label class="form-label">密码</label>
            <el-input
             v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              class="login-input"
              show-password
            />
          </div>

          <div class="form-actions">
            <div class="register-link">
              <span>没有账号？</span>
              <a href="#" @click="goToRegister" >注册</a>
            </div>
          </div>

          <el-button
            type="primary"
            size="large"
            class="login-button"
            @click="login_handle"
          >
            登录
          </el-button>
        </div>

      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.login-container {
  display: flex;
  height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.left-section {
  flex: 1;
  position: relative;
  overflow: hidden;
  min-height: 100%;

  .graphic-container {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(
        ellipse 130% 90% at 45% 15%,
        rgba(79, 129, 255, 0.18) 0%,
        transparent 58%
      ),
      radial-gradient(ellipse 80% 60% at 80% 70%, rgba(139, 92, 246, 0.1) 0%, transparent 50%),
      linear-gradient(165deg, #e4ebf6 0%, #d0ddf0 42%, #c4d4ea 100%);

    .mesh-blobs {
      position: absolute;
      inset: -15%;
      pointer-events: none;
      overflow: visible;

      .blob {
        position: absolute;
        border-radius: 50%;
        filter: blur(64px);
        opacity: 0.5;
        animation: blobDrift 22s ease-in-out infinite;

        &.blob-a {
          width: min(52vmin, 520px);
          height: min(52vmin, 520px);
          top: -18%;
          left: -22%;
          background: linear-gradient(135deg, #7ba3ff, #4f81ff);
          animation-delay: 0s;
        }

        &.blob-b {
          width: min(44vmin, 440px);
          height: min(44vmin, 440px);
          bottom: -12%;
          right: -18%;
          background: linear-gradient(135deg, #9b7dff, #5b7cff);
          animation-delay: -7s;
        }

        &.blob-c {
          width: min(32vmin, 320px);
          height: min(32vmin, 320px);
          top: 38%;
          left: 28%;
          background: linear-gradient(135deg, #5ecfff, #6366f1);
          opacity: 0.32;
          animation-delay: -14s;
        }
      }
    }

    .grid-floor {
      position: absolute;
      left: 50%;
      bottom: 8%;
      width: 180%;
      height: 62%;
      transform: translateX(-50%) rotateX(72deg);
      transform-origin: 50% 100%;
      background-image: linear-gradient(
          rgba(79, 129, 255, 0.07) 1px,
          transparent 1px
        ),
        linear-gradient(90deg, rgba(79, 129, 255, 0.07) 1px, transparent 1px);
      background-size: 42px 42px;
      mask-image: radial-gradient(ellipse 75% 58% at 50% 100%, black 18%, transparent 78%);
      pointer-events: none;
    }

    .scene-3d {
      position: relative;
      width: min(88vmin, 520px);
      height: min(88vmin, 520px);
      max-width: 100%;
      max-height: 100%;
      perspective: 1100px;
      perspective-origin: 50% 42%;
      flex-shrink: 0;
    }

    .hub {
      position: absolute;
      left: 50%;
      top: 50%;
      width: 1px;
      height: 1px;
      transform-style: preserve-3d;
      transform: translate(-50%, -50%);
    }

    .hub-glow {
      position: absolute;
      left: 50%;
      top: 50%;
      width: 360px;
      height: 360px;
      margin: -180px 0 0 -180px;
      background: radial-gradient(
        circle,
        rgba(160, 198, 255, 0.5) 0%,
        rgba(79, 129, 255, 0.14) 48%,
        transparent 72%
      );
      animation: pulseGlow 4.5s ease-in-out infinite;
    }

    .hub-sphere {
      position: absolute;
      left: 50%;
      top: 50%;
      width: 124px;
      height: 124px;
      margin: -62px 0 0 -62px;
      border-radius: 50%;
      background: radial-gradient(circle at 32% 28%, #e8f0ff 0%, #6b9eff 38%, #3b66db 88%);
      box-shadow: 0 0 56px rgba(79, 129, 255, 0.55), inset 0 -14px 28px rgba(30, 58, 138, 0.35);
      animation: hubFloat 5s ease-in-out infinite;
    }

    .hub-ring {
      position: absolute;
      left: 50%;
      top: 50%;
      border-radius: 50%;
      border: 1px solid rgba(255, 255, 255, 0.38);
      box-shadow: 0 0 0 1px rgba(79, 129, 255, 0.12);
      transform-style: preserve-3d;

      &.ring-1 {
        width: 280px;
        height: 280px;
        margin: -140px 0 0 -140px;
        transform: rotateX(76deg);
        animation: spinRing 22s linear infinite;
      }

      &.ring-2 {
        width: 364px;
        height: 364px;
        margin: -182px 0 0 -182px;
        border-color: rgba(255, 255, 255, 0.22);
        transform: rotateX(76deg) rotateZ(18deg);
        animation: spinRingReverse 16s linear infinite;
      }

      &.ring-3 {
        width: 448px;
        height: 448px;
        margin: -224px 0 0 -224px;
        border-color: rgba(255, 255, 255, 0.14);
        transform: rotateX(76deg) rotateZ(-24deg);
        animation: spinRingTilt 28s linear infinite;
      }
    }

    .orbit-cube {
      position: absolute;
      left: 50%;
      top: 50%;
      width: 1px;
      height: 1px;
      transform-style: preserve-3d;
      animation: orbitSpin 14s linear infinite;
    }

    .mini-cube {
      position: absolute;
      width: 76px;
      height: 76px;
      left: 0;
      top: 0;
      margin: -38px 0 0 -38px;
      transform-style: preserve-3d;
      transform: translateX(226px) rotateX(-12deg) rotateY(24deg);
      animation: cubeSelfSpin 6s linear infinite;

      .mc {
        position: absolute;
        width: 76px;
        height: 76px;
        border: 1px solid rgba(255, 255, 255, 0.38);
        background: linear-gradient(145deg, rgba(79, 129, 255, 0.42), rgba(59, 102, 219, 0.22));
        backdrop-filter: blur(6px);

        &.f {
          transform: rotateY(0deg) translateZ(38px);
        }
        &.b {
          transform: rotateY(180deg) translateZ(38px);
        }
        &.r {
          transform: rotateY(90deg) translateZ(38px);
        }
        &.l {
          transform: rotateY(-90deg) translateZ(38px);
        }
        &.t {
          transform: rotateX(90deg) translateZ(38px);
        }
        &.bo {
          transform: rotateX(-90deg) translateZ(38px);
        }
      }
    }

    .float-orb {
      position: absolute;
      border-radius: 50%;
      background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.88), rgba(79, 129, 255, 0.48));
      box-shadow: 0 10px 28px rgba(79, 129, 255, 0.28);

      &.orb-1 {
        width: 22px;
        height: 22px;
        left: 6%;
        top: 18%;
        animation: floatOrbA 7s ease-in-out infinite;
      }

      &.orb-2 {
        width: 16px;
        height: 16px;
        right: 8%;
        bottom: 22%;
        animation: floatOrbB 9s ease-in-out infinite;
      }
    }
  }
}

.right-section {
  width: 450px;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: -2px 0 20px rgba(0, 0, 0, 0.1);

  .login-form-container {
    width: 320px;
    padding: 40px 0;

    .header {
      text-align: center;
      margin-bottom: 40px;

      .logo {
        margin-bottom: 16px;

        .logo-text {
          display: inline-block;
          background: linear-gradient(45deg, #4f81ff, #3b66db);
          color: white;
          padding: 12px 24px;
          border-radius: 8px;
          font-size: 20px;
          font-weight: 700;
          letter-spacing: 2px;
          font-family: 'SF Pro Display', 'Helvetica Neue', 'Arial', sans-serif;
          box-shadow: 0 4px 12px rgba(79, 129, 255, 0.3);
        }
      }

      .subtitle {
        color: #555;
        font-size: 16px;
        margin: 0;
        line-height: 1.6;
        font-weight: 400;
        font-family: 'PingFang SC', 'Helvetica Neue', 'Arial', sans-serif;
      }
    }

    .login-form {
      .form-group {
        margin-bottom: 20px;

        .form-label {
          display: block;
          font-size: 16px;
          font-weight: 600;
          color: #2c3e50;
          margin-bottom: 10px;
          font-family: 'PingFang SC', 'Helvetica Neue', 'Arial', sans-serif;
          letter-spacing: 0.5px;
        }

        .login-input {
          :deep(.el-input__wrapper) {
            background: #f8f9fc;
            border: 1px solid #e1e5e9;
            border-radius: 8px;
            padding: 12px 16px;
            box-shadow: none;

            &:hover {
              border-color: #4f81ff;
            }

            &.is-focus {
              border-color: #4f81ff;
              box-shadow: 0 0 0 3px rgba(79, 129, 255, 0.1);
            }
          }

          :deep(.el-input__inner) {
            color: #2c3e50;
            font-size: 16px;
            font-family: 'PingFang SC', 'Helvetica Neue', 'Arial', sans-serif;
            font-weight: 400;

            &::placeholder {
              color: #a0a0a0;
              font-size: 15px;
            }
          }
        }
      }

      .form-actions {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 24px;

        .register-link {
          font-size: 15px;
          color: #666;
          font-family: 'PingFang SC', 'Helvetica Neue', 'Arial', sans-serif;

          a {
            color: #4f81ff;
            text-decoration: none;
            margin-left: 6px;
            font-weight: 500;
            transition: all 0.2s ease;

            &:hover {
              text-decoration: underline;
              color: #3b66db;
            }
          }
        }
      }

      .login-button {
        width: 100%;
        height: 52px;
        background: linear-gradient(45deg, #4f81ff, #3b66db);
        border: none;
        border-radius: 10px;
        font-size: 18px;
        font-weight: 600;
        font-family: 'PingFang SC', 'Helvetica Neue', 'Arial', sans-serif;
        letter-spacing: 1px;
        transition: all 0.3s ease;

        &:hover {
          transform: translateY(-1px);
          box-shadow: 0 8px 25px rgba(79, 129, 255, 0.3);
        }

        &:active {
          transform: translateY(0);
        }
      }
    }

    .footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 36px;
      color: #667084;
      font-size: 13px;
      font-family: 'PingFang SC', 'Helvetica Neue', 'Arial', sans-serif;
      font-weight: 400;
      border-top: 1px solid #eef2f7;
      padding-top: 16px;

      .version-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 999px;
        background: #f2f8ff;
        color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.25);
        font-weight: 600;
        letter-spacing: 0.3px;
      }

      .footer-icons {
        display: flex;
        gap: 10px;

        a {
          width: 28px;
          height: 28px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f8fafc;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          transition: all 0.2s ease;
          overflow: hidden;

          &:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(59, 130, 246, 0.2);
            border-color: rgba(59, 130, 246, 0.4);
          }

          .icon-img {
            width: 18px;
            height: 18px;
            object-fit: contain;
            filter: saturate(0.9) contrast(1.05);
          }
        }
      }
    }
  }
}

@keyframes blobDrift {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(6%, -4%) scale(1.05);
  }
  66% {
    transform: translate(-4%, 5%) scale(0.96);
  }
}

@keyframes pulseGlow {
  0%,
  100% {
    opacity: 0.85;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.08);
  }
}

@keyframes hubFloat {
  0%,
  100% {
    transform: translateZ(0);
  }
  50% {
    transform: translateZ(12px);
  }
}

@keyframes spinRing {
  from {
    transform: rotateX(76deg) rotateZ(0deg);
  }
  to {
    transform: rotateX(76deg) rotateZ(360deg);
  }
}

@keyframes spinRingTilt {
  from {
    transform: rotateX(76deg) rotateZ(-24deg);
  }
  to {
    transform: rotateX(76deg) rotateZ(336deg);
  }
}

@keyframes spinRingReverse {
  from {
    transform: rotateX(76deg) rotateZ(18deg);
  }
  to {
    transform: rotateX(76deg) rotateZ(-342deg);
  }
}

@keyframes orbitSpin {
  from {
    transform: translate(-50%, -50%) rotateY(0deg);
  }
  to {
    transform: translate(-50%, -50%) rotateY(360deg);
  }
}

@keyframes cubeSelfSpin {
  from {
    transform: translateX(226px) rotateX(-12deg) rotateY(0deg);
  }
  to {
    transform: translateX(226px) rotateX(-12deg) rotateY(360deg);
  }
}

@keyframes floatOrbA {
  0%,
  100% {
    transform: translate(0, 0);
    opacity: 0.9;
  }
  50% {
    transform: translate(12px, -18px);
    opacity: 1;
  }
}

@keyframes floatOrbB {
  0%,
  100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-10px, 14px);
  }
}
</style>
<template>
  <main class="auth-page">
    <div class="auth-bg" aria-hidden="true">
      <span v-for="n in 18" :key="`spark-${n}`" class="spark"></span>
      <span v-for="n in 7" :key="`veil-${n}`" class="wind-veil"></span>
    </div>

    <RouterLink class="brand" to="/">
      <img :src="wordmark" alt="Starway" />
    </RouterLink>

    <section class="brand-side">
      <el-tag effect="plain">Starway Access</el-tag>
      <h1>从这里进入你的星图</h1>
      <p>登录之后，画像、岗位、测评与 AI 建议会重新汇合，继续把模糊的前途整理成可抵达的航线。</p>
    </section>

    <section class="form-side">
      <RouterView />
    </section>
  </main>
</template>

<script setup>
import { RouterLink, RouterView } from 'vue-router'
import wordmark from '@/assets/starway-wordmark-transparent.png'
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  display: grid;
  grid-template-columns: minmax(320px, .95fr) minmax(360px, 1fr);
  color: white;
  background:
    linear-gradient(90deg, rgba(4,16,20,.82), rgba(13,33,30,.54) 42%, rgba(4,12,14,.42)),
    radial-gradient(circle at 76% 46%, rgba(220,234,223,.18), transparent 30%),
    linear-gradient(180deg, rgba(5,14,18,.08), rgba(7,18,18,.78)),
    url('/1.jpg') center / cover no-repeat;
  animation: authBgBreath 18s ease-in-out infinite alternate;
}

.auth-page::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(120deg, transparent 0 34%, rgba(255,255,255,.12) 46%, transparent 58%),
    radial-gradient(circle at 20% 78%, rgba(120,160,131,.2), transparent 28%);
  opacity: .75;
}

.auth-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
  perspective: 1200px;
}

.brand {
  position: absolute;
  top: 34px;
  left: 44px;
  z-index: 3;
  width: clamp(150px, 16vw, 230px);
  border-radius: 18px;
  padding: 0;
  background: transparent;
  line-height: 0;
}

.brand img {
  width: 100%;
  max-width: 100%;
  height: auto;
  display: block;
  filter: saturate(1.25) brightness(1.22) contrast(1.04) drop-shadow(0 12px 26px rgba(151,231,185,.24));
}

.brand-side {
  min-height: 100vh;
  padding: 148px 56px 70px;
  display: grid;
  align-content: center;
  position: relative;
  z-index: 2;
}

.brand-side :deep(.el-tag) {
  width: fit-content;
  color: rgba(236,250,241,.88);
  border-color: rgba(255,255,255,.38);
  background: rgba(255,255,255,.12);
}

.brand-side h1 {
  max-width: 500px;
  margin: 22px 0 0;
  font-size: clamp(38px, 5.2vw, 68px);
  font-weight: 520;
  line-height: 1.04;
  text-shadow: 0 18px 54px rgba(0,0,0,.32);
}

.brand-side p {
  max-width: 520px;
  margin: 24px 0 0;
  color: rgba(239,250,244,.76);
  line-height: 1.95;
  font-size: 17px;
}

.form-side {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 96px 38px 42px;
  position: relative;
  isolation: isolate;
  z-index: 2;
}

.form-side::before {
  content: "";
  position: absolute;
  inset: 12% 8% 10%;
  z-index: -1;
  border-radius: 34px;
  pointer-events: none;
  background:
    radial-gradient(circle at 36% 20%, rgba(165,181,178,.18), transparent 32%),
    linear-gradient(145deg, rgba(3,13,15,.88), rgba(7,24,25,.76));
  border: 1px solid rgba(255,255,255,.18);
  box-shadow: 0 42px 120px rgba(0,0,0,.48);
  backdrop-filter: blur(8px) saturate(1.08);
  -webkit-backdrop-filter: blur(8px) saturate(1.08);
}

.spark,
.wind-veil {
  position: absolute;
}

.spark {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(220,234,223,.88);
  box-shadow: 0 0 18px rgba(220,234,223,.86);
  animation: sparkFloat 10s ease-in-out infinite;
}

.spark:nth-of-type(1) { left: 16%; top: 20%; animation-delay: -.2s; }
.spark:nth-of-type(2) { left: 34%; top: 32%; animation-delay: -1.1s; }
.spark:nth-of-type(3) { left: 55%; top: 18%; animation-delay: -2s; }
.spark:nth-of-type(4) { left: 72%; top: 28%; animation-delay: -2.9s; }
.spark:nth-of-type(5) { left: 88%; top: 44%; animation-delay: -3.8s; }
.spark:nth-of-type(6) { left: 68%; top: 66%; animation-delay: -4.7s; }
.spark:nth-of-type(7) { left: 42%; top: 78%; animation-delay: -5.6s; }
.spark:nth-of-type(8) { left: 20%; top: 62%; animation-delay: -6.5s; }
.spark:nth-of-type(9) { left: 82%; top: 78%; animation-delay: -7.4s; }
.spark:nth-of-type(10) { left: 8%; top: 42%; animation-delay: -8.3s; }
.spark:nth-of-type(11) { left: 60%; top: 48%; animation-delay: -9.2s; }
.spark:nth-of-type(12) { left: 48%; top: 8%; animation-delay: -10.1s; }
.spark:nth-of-type(13) { left: 92%; top: 16%; animation-delay: -11s; }
.spark:nth-of-type(14) { left: 30%; top: 88%; animation-delay: -11.9s; }
.spark:nth-of-type(15) { left: 74%; top: 8%; animation-delay: -12.8s; }
.spark:nth-of-type(16) { left: 52%; top: 84%; animation-delay: -13.7s; }
.spark:nth-of-type(17) { left: 12%; top: 76%; animation-delay: -14.6s; }
.spark:nth-of-type(18) { left: 38%; top: 14%; animation-delay: -15.5s; }

.wind-veil {
  width: 56vw;
  height: 120px;
  border-radius: 999px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.28), rgba(220,234,223,.16), transparent);
  filter: blur(4px);
  opacity: .45;
  transform: rotate(-16deg);
  animation: veilRun 16s ease-in-out infinite;
}

.wind-veil:nth-of-type(19) { left: -10%; top: 22%; animation-delay: -1s; }
.wind-veil:nth-of-type(20) { left: 22%; top: 40%; animation-delay: -4s; animation-duration: 19s; }
.wind-veil:nth-of-type(21) { left: 50%; top: 18%; animation-delay: -7s; animation-duration: 21s; }
.wind-veil:nth-of-type(22) { left: 4%; top: 70%; animation-delay: -10s; animation-duration: 18s; }
.wind-veil:nth-of-type(23) { left: 58%; top: 64%; animation-delay: -13s; animation-duration: 23s; }
.wind-veil:nth-of-type(24) { left: 38%; top: 84%; animation-delay: -16s; animation-duration: 20s; }
.wind-veil:nth-of-type(25) { left: 72%; top: 38%; animation-delay: -19s; animation-duration: 24s; }

@keyframes authBgBreath {
  to { background-position: 48.8% 49.2%, center, center, 49% 50%; }
}

@keyframes sparkFloat {
  0%, 100% { transform: translate3d(0, 0, 60px) scale(.7); opacity: .2; }
  50% { transform: translate3d(44px, -40px, 180px) scale(1.25); opacity: .86; }
}

@keyframes veilRun {
  0%, 100% { transform: translate3d(-5%, 0, 80px) rotate(-16deg); opacity: .12; }
  50% { transform: translate3d(12%, -26px, 160px) rotate(-16deg); opacity: .48; }
}

@media (max-width: 900px) {
  .auth-page {
    grid-template-columns: 1fr;
  }

  .brand {
    left: 24px;
    top: 22px;
    width: min(220px, 62vw);
  }

  .brand-side {
    min-height: auto;
    padding: 112px 24px 20px;
  }

  .form-side {
    min-height: auto;
    padding: 26px 24px 40px;
  }

  .form-side::before {
    inset: 0 12px 20px;
  }
}
</style>

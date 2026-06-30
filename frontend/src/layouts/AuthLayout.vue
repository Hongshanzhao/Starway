<template>
  <main class="auth-page">
    <section class="brand-side">
      <RouterLink class="brand" to="/">Starway</RouterLink>
      <div class="living-layers" aria-hidden="true">
        <span v-for="n in 18" :key="n"></span>
      </div>
      <h1>把模糊的前途，整理成可抵达的航线</h1>
      <p>用岗位数据、学生画像和 AI 推演，让每一次选择都有证据，也有下一步。</p>
    </section>
    <section class="form-side">
      <RouterView />
    </section>
  </main>
</template>

<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(320px, 0.95fr) minmax(360px, 1fr);
}

.brand-side {
  position: relative;
  overflow: hidden;
  padding: 56px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background:
    radial-gradient(circle at 22% 18%, rgba(120, 160, 131, 0.36), transparent 28%),
    radial-gradient(circle at 76% 80%, rgba(220, 234, 223, 0.56), transparent 30%),
    linear-gradient(135deg, #edf5eb, #d9e7d8 48%, #d9cec2);
}

.brand {
  position: absolute;
  top: 34px;
  left: 56px;
  z-index: 2;
  font-size: 22px;
  font-weight: 500;
}

.living-layers {
  position: absolute;
  inset: 0;
  perspective: 900px;
}

.living-layers span {
  position: absolute;
  width: 38px;
  height: 16px;
  border-radius: 999px 999px 999px 4px;
  background: linear-gradient(135deg, rgba(79,124,99,.68), rgba(220,234,223,.82));
  filter: blur(.1px);
  opacity: .72;
  transform: translateZ(var(--z, 0)) rotate(var(--r, -12deg));
  animation: flock 10s linear infinite;
}

.living-layers span:nth-child(1) { left: 10%; top: 18%; --z: 80px; --r: -18deg; animation-duration: 9s; }
.living-layers span:nth-child(2) { left: 18%; top: 28%; --z: 20px; --r: 12deg; animation-duration: 12s; }
.living-layers span:nth-child(3) { left: 34%; top: 16%; --z: 120px; --r: -8deg; animation-duration: 8s; }
.living-layers span:nth-child(4) { left: 58%; top: 24%; --z: 40px; --r: 18deg; animation-duration: 13s; }
.living-layers span:nth-child(5) { left: 74%; top: 18%; --z: 100px; --r: -20deg; animation-duration: 10s; }
.living-layers span:nth-child(6) { left: 82%; top: 42%; --z: 30px; --r: 8deg; animation-duration: 14s; }
.living-layers span:nth-child(7) { left: 64%; top: 68%; --z: 90px; --r: -16deg; animation-duration: 9.5s; }
.living-layers span:nth-child(8) { left: 22%; top: 72%; --z: 30px; --r: 20deg; animation-duration: 12.5s; }
.living-layers span:nth-child(n + 9) {
  width: 18px;
  height: 48px;
  border-radius: 999px 4px 999px 4px;
  opacity: .34;
  animation-name: leafDrift;
}

h1 {
  max-width: 520px;
  margin: 0;
  position: relative;
  z-index: 1;
  font-size: clamp(34px, 5vw, 62px);
  font-weight: 500;
  line-height: 1.12;
}

p {
  max-width: 520px;
  margin: 22px 0 0;
  position: relative;
  z-index: 1;
  color: #5d656e;
  line-height: 1.9;
  font-size: 17px;
}

.form-side {
  background: rgba(255,255,255,.2);
  backdrop-filter: blur(18px);
  display: grid;
  place-items: center;
  padding: 32px;
}

@keyframes flock {
  0% { transform: translate3d(-14px, 10px, 0) translateZ(var(--z, 0)) rotate(var(--r, -12deg)); }
  50% { transform: translate3d(24px, -12px, 0) translateZ(calc(var(--z, 0) + 30px)) rotate(calc(var(--r, -12deg) + 8deg)); }
  100% { transform: translate3d(-14px, 10px, 0) translateZ(var(--z, 0)) rotate(var(--r, -12deg)); }
}

@keyframes leafDrift {
  50% { transform: translate3d(18px, -28px, 0) rotate(22deg); opacity: .55; }
}

@media (max-width: 860px) {
  .auth-page {
    grid-template-columns: 1fr;
  }

  .brand-side {
    min-height: 280px;
    padding: 86px 28px 38px;
  }

  .brand {
    left: 28px;
  }
}
</style>

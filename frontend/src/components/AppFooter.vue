<template>
  <footer class="footer">
    <div class="page-shell footer-inner">
      <span>Starway 职业规划系统</span>
      <span>基于真实岗位数据、画像、测评与匹配报告</span>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  padding: 34px 0 42px;
  color: var(--muted);
}

.footer-inner {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 14px;
}

@media (max-width: 640px) {
  .footer-inner {
    flex-direction: column;
  }
}
</style>

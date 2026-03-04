<template>
  <div class="layout">
    <header class="header">
      <div class="header-inner">
        <NuxtLink to="/carousels" class="logo">
          <span class="logo-icon">&#9632;</span>
          Генератор каруселей
        </NuxtLink>
      </div>
    </header>
    <main class="main">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: var(--card);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 14px 20px;
  display: flex;
  align-items: center;
}

.logo {
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-icon {
  color: var(--accent);
  font-size: 22px;
}

.main {
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 20px;
  width: 100%;
}
</style>

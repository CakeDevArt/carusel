<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>

<style>
:root {
  --bg: #f5f5f7;
  --card: #ffffff;
  --text: #1d1d1f;
  --text-secondary: #6e6e73;
  --accent: #0071e3;
  --accent-hover: #0077ED;
  --success: #34c759;
  --warning: #ff9f0a;
  --danger: #ff3b30;
  --border: #d2d2d7;
  --radius: 12px;
  --shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
  --shadow-lg: 0 10px 25px rgba(0,0,0,0.1);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

a {
  color: var(--accent);
  text-decoration: none;
}

button {
  cursor: pointer;
  font-family: inherit;
}
</style>

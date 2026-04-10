<template>
  <RouterView />
</template>

<style>
:root {
  --bg: #020716;
  --panel: rgba(8, 23, 52, 0.52);
  --panel-strong: rgba(10, 31, 70, 0.66);
  --line: rgba(96, 165, 250, 0.28);
  --line-strong: rgba(56, 189, 248, 0.58);
  --text: #dcecff;
  --muted: #91acd0;
  --green: #38bdf8;
  --cyan: #7dd3fc;
  --amber: #facc15;
  --orange: #fb923c;
  --red: #eb5757;
  --blue: #2563eb;
  --shadow: rgba(0, 0, 0, 0.42) 0 24px 70px;
  --font: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif;
  font-family: var(--font);
  font-size: 16px;
  line-height: 1.45;
  letter-spacing: 0;
  color: var(--text);
  background: var(--bg);
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-width: 1280px;
  min-height: 100vh;
  overflow: auto;
  background:
    linear-gradient(90deg, rgba(56, 189, 248, 0.08) 1px, transparent 1px),
    linear-gradient(0deg, rgba(96, 165, 250, 0.07) 1px, transparent 1px),
    radial-gradient(circle at 12% 18%, rgba(37, 99, 235, 0.28), transparent 32%),
    radial-gradient(circle at 82% 12%, rgba(56, 189, 248, 0.2), transparent 28%),
    #020716;
  background-size: 64px 64px, 64px 64px, auto, auto, auto;
}

button {
  font: inherit;
}

#app {
  min-height: 100vh;
}
</style>

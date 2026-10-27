<template>
  <main class="platform">
    <header>
      <h1>PLATFORM</h1>
      <p>Operating system for organizing work</p>
    </header>

    <section>
      <h2>Current Context</h2>
      <p>Создание первого интерфейса Platform</p>
    </section>

    <section>
      <h2>Decisions</h2>
      <ul>
        <li>Архитектура должна рождаться из сущности Platform</li>
        <li>Interface отделён от Core и Memory</li>
      </ul>
    </section>

    <section>
      <h2>Next Actions</h2>
      <ol>
        <li>Создать первый рабочий экран</li>
        <li>Проверить модель Platform</li>
        <li>Развивать систему итерациями</li>
      </ol>
    </section>

    <section>
      <h2>Memory</h2>
      <p>
        Context · Sessions · Decisions · Capture · Snapshots
      </p>
    </section>
  </main>
</template>

<style scoped>
.platform {
  max-width: 900px;
  margin: 40px auto;
  padding: 24px;
  font-family: system-ui, sans-serif;
}

section {
  margin-top: 30px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 12px;
}

h1 {
  font-size: 42px;
}

h2 {
  margin-bottom: 10px;
}
</style>

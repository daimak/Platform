# Platform HELP
# Platform HELP

## 📌 ROOT RULE
Все команды выполняются относительно:

C:\Work\Platform

---

## 📂 Перейти в корень проекта

cd C:\Work\Platform

---

## 🌳 Посмотреть структуру проекта

tree /F /A

---

## 📁 Проверить RFC папку

dir RFC

---

## 💾 Сохранить структуру в файл

tree /F /A > structure.txt

---

## 🚨 RULE: Root Drift

Если в структуре есть:
- C:\Work\RFC
- любые другие диски (D:\, E:\)
- папки вне Platform

→ это ошибка системы

---

## 🧠 RULE: Source of Truth

- файловая структура: C:\Work\Platform
- изменения: CHANGELOG.md
- изменения дизайна: RFC/
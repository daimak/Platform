rem Пинг-сторожка витрины: скрытый запуск ping-vitrina.cmd (окно 0 = невидимо) — фикс «чёрного окна cmd», 15.11
CreateObject("WScript.Shell").Run """C:\Work\Platform\Workspace\sales-lane\ping-vitrina.cmd""", 0, False

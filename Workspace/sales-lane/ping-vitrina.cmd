@echo off
rem Ping vitriny: raz v 15 min (schtasks VitrinaPing). Log = sales-lane\ping-vitrina.log
curl -s -o NUL -m 20 -w "%date% %time% code=%%{http_code} %URL%" http://158.160.152.181/ >> "C:\Work\Platform\Workspace\sales-lane\ping-vitrina.log"
echo. >> "C:\Work\Platform\Workspace\sales-lane\ping-vitrina.log"

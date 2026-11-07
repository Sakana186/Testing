@echo off
title Supermarket Offline Payment Simulator (SOPRCS)
echo ======================================================================
echo  HE THONG THANH TOAN NGOAI TUYEN SIEU THI (SOPRCS DEMO)
echo  Chu de 7: Di sieu thi khong mang tien mat va mat mang 4G / Wi-Fi
echo ======================================================================
echo.
echo Dang chuyen vao thu muc ma nguon (src)...
cd /d "%~dp0src"
echo Dang khoi dong cum Microservices (Port 8080 - 8084)...
start "SOPRCS_Microservices" python run_microservices.py
echo Cho 2 giay de cac services hoan tat khoi tao...
timeout /t 2 /nobreak >nul
echo Dang mo trinh duyet http://localhost:8080...
start http://localhost:8080
echo.
echo ======================================================================
echo  Server dang chay on dinh trong cua so [SOPRCS_Microservices].
echo  Trinh duyet web da duoc mo tai http://localhost:8080
echo  De dung he thong, dong cua so [SOPRCS_Microservices].
echo ======================================================================
pause

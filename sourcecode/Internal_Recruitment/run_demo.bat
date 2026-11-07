@echo off
title He Thong Tuyen Dung & Dieu Chuyen Noi Bo (Internal Recruitment Portal)
echo ======================================================================
echo  HE THONG TUYEN DUNG NOI BO MINH BACH (INTERNAL RECRUITMENT DEMO)
echo  Chu de 6: So hoa quy trinh tuyen dung noi bo doanh nghiep
echo ======================================================================
echo.
echo Dang chuyen vao thu muc ma nguon (src)...
cd /d "%~dp0src"
echo Dang khoi dong cum 5 Microservices (Port 8090 - 8094)...
start "IRTMP_Microservices" python run_microservices.py
echo Cho 2 giay de cac services hoan tat khoi tao...
timeout /t 2 /nobreak >nul
echo Dang mo trinh duyet http://localhost:8090...
start http://localhost:8090
echo.
echo ======================================================================
echo  Server dang chay on dinh trong cua so [IRTMP_Microservices].
echo  Trinh duyet web da duoc mo tai http://localhost:8090
echo  De dung he thong, dong cua so [IRTMP_Microservices].
echo ======================================================================
pause

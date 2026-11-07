@echo off
title He Thong Tuyen Dung & Dieu Chuyen Noi Bo (Internal Recruitment Portal)
echo ======================================================================
echo  HE THONG TUYEN DUNG NOI BO MINH BACH (INTERNAL RECRUITMENT DEMO)
echo  Chu de 6: So hoa quy trinh tuyen dung noi bo doanh nghiep
echo ======================================================================
echo.
echo Dang khoi dong cum 5 Microservices (Port 8090 - 8094)...
start http://localhost:8090
python run_microservices.py
pause


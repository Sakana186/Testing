@echo off
title Supermarket Offline Payment Simulator (SOPRCS)
echo ======================================================================
echo  HE THONG THANH TOAN NGOAI TUYEN SIEU THI (SOPRCS DEMO)
echo  Chu de 7: Di sieu thi khong mang tien mat va mat mang 4G / Wi-Fi
echo ======================================================================
echo.
echo Dang khoi dong cum Microservices (Gateway, POS, Payment, Token, Customer)...
start http://localhost:8080
python run_microservices.py
pause


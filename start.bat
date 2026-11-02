@echo off
title Smart Parking System - Dashboard
cls
echo ======================================================================
echo    SMART VEHICLE PARKING AND BILLING SYSTEM
echo    Core Data Structure : Doubly Linked List (C++ & Python Engine)
echo    Storage File        : parking_records.txt
echo ======================================================================
echo.
echo [1/2] Opening dashboard in your default browser...
timeout /t 1 /nobreak >nul
start http://localhost:8000

echo [2/2] Starting local Python API bridge...
echo.
echo Press Ctrl+C anytime to stop the server.
echo.
python server.py 8000
pause

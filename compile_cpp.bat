@echo off
title Compile C++ Parking System
cls
echo ======================================================================
echo    Compiling parking_system.cpp
echo ======================================================================
echo.
echo Running: g++ -std=c++11 parking_system.cpp -o parking_system.exe
g++ -std=c++11 parking_system.cpp -o parking_system.exe
if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] parking_system.exe compiled successfully!
    echo Both C++ and the Web UI share the exact same 'parking_records.txt'.
    echo You can now run 'parking_system.exe' in your terminal or IDE.
) else (
    echo.
    echo [NOTE] If your system has Windows Defender Application Control (WDAC)
    echo or MinGW path restrictions, you can compile and run this C++ file
    echo inside VS Code, Code::Blocks, Dev-C++, or Visual Studio.
)
echo.
pause

@echo off
rem bangaio-nx: tools\build_switch.bat with its output in a log, for unattended builds.
rem Usage: tools\switch_build_bg.bat <log> [extra cmake --build args]   (BUILD_DIR / JOBS / EXTRA_CMAKE as for build_switch.bat)
set "HERE=%~dp0"
set "LOG=%~1"
call "%HERE%build_switch.bat" %2 %3 %4 %5 > "%LOG%" 2>&1
echo exit=%ERRORLEVEL% >> "%LOG%"

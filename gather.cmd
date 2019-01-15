@echo off
SETLOCAL ENABLEEXTENSIONS
set file=output.txt
set rep=10
REM Print the date
echo Date: %date% > %file%
for /F "tokens=*" %%A IN (targets.txt) DO (
  echo %%A
  echo %%A >> %file%
  echo Time: %time% >> %file%
  for /F "tokens=1 delims=," %%G IN ("%%A") DO (
  	ping -n %rep% %%G >> %file%
  	tracert %%G >> %file%
  	echo --------------- >> %file%
  )
)


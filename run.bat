
python colorMapping.py

@echo off
set /p NAME="Image Name: "
echo %NAME% > selection.txt



echo "Move screen to right size"
pause
python photoSlicerColorHSL.py
PrettyConsole.exe
pause
python photoSlicerColor.py
PrettyConsole.exe
pause
python photoSlicer.py
PrettyConsoleBW.exe
pause

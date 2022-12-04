python colorMapping.py
echo moon.jpg > selection.txt
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

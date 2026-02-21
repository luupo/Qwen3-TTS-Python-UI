@echo off
cd /d "%~dp0"
echo Larger window (1320px), bigger text areas; push.ps1> .msg
git commit --amend -F .msg
git push --force origin master
del .msg 2>nul
pause

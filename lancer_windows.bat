@echo off
rem Lanceur Windows : double-clic = mise a jour du classeur du mois, puis ouverture dans Excel.
rem 1. se place dans le dossier du projet ; 2. trouve Python (conda "rush2", sinon .venv) ;
rem 3. lance main.py --offline ; 4. ouvre le classeur le plus recent de deliverables\.
chcp 65001 >nul
setlocal

rem Le double-clic peut demarrer ailleurs : on revient dans le dossier de ce fichier
cd /d "%~dp0"

rem --- 1. Python de l'environnement conda "rush2" (emplacements habituels de conda) -----------
set "PYTHON="
if defined CONDA_EXE for %%I in ("%CONDA_EXE%\..\..") do if exist "%%~fI\envs\rush2\python.exe" set "PYTHON=%%~fI\envs\rush2\python.exe"
for %%B in ("%USERPROFILE%\miniconda3" "%USERPROFILE%\anaconda3" "%LOCALAPPDATA%\miniconda3" "%LOCALAPPDATA%\anaconda3" "%ProgramData%\miniconda3" "%ProgramData%\anaconda3") do (
    if not defined PYTHON if exist "%%~B\envs\rush2\python.exe" set "PYTHON=%%~B\envs\rush2\python.exe"
)

rem --- 2. Sinon, le Python du dossier .venv -------------------------------------------------
if not defined PYTHON if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"

if not defined PYTHON (
    echo Aucun environnement Python trouvé ^(ni conda "rush2", ni dossier .venv^).
    echo Suivre la partie « Installation » du README, puis relancer.
    pause
    exit /b 1
)
echo Python utilisé : %PYTHON%
echo.

rem --- 3. Mise a jour du classeur -------------------------------------------------------------
"%PYTHON%" main.py --offline
if errorlevel 1 (
    echo.
    echo ERREUR : la mise à jour a échoué ^(message ci-dessus^). Aucun classeur n'a été ouvert.
    pause
    exit /b 1
)

rem --- 4. Ouverture du classeur le plus recent (dir /o-d = du plus recent au plus ancien) ------
set "CLASSEUR="
for /f "delims=" %%F in ('dir /b /o-d "deliverables\analyse_ventes_*.xlsx" 2^>nul') do if not defined CLASSEUR set "CLASSEUR=%%F"
if defined CLASSEUR (
    echo.
    echo Ouverture de deliverables\%CLASSEUR%
    start "" "deliverables\%CLASSEUR%"
) else (
    echo Aucun classeur trouvé dans deliverables\.
)
echo.
pause

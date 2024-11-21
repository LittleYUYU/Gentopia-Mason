@echo off
setlocal

REM Get the base agent name from the first argument
set "base_agent=%~1"

REM Get the clone agent name from the second argument
set "clone_agent=%~2"

REM Check if base agent directory exists
if not exist ".\gentpool\pool\%base_agent%" (
    echo Base agent directory .\gentpool\pool\%base_agent% does not exist. Exiting...
    exit /b 1
)

REM Check if clone agent directory already exists
if exist ".\gentpool\pool\%clone_agent%" (
    echo Clone agent directory .\gentpool\pool\%clone_agent% already exists. Exiting...
    exit /b 1
)

REM Directory paths
set "base_dir_path=.\gentpool\pool\%base_agent%"
set "clone_dir_path=.\gentpool\pool\%clone_agent%"

REM Prompt user to confirm cloning
set /p answer=Cloning agent %base_agent% to %clone_agent%, continue? (y/n): 
if /i not "%answer%"=="y" (
    echo Exiting...
    exit /b 1
)

REM Copy the entire base agent directory to the clone agent directory
xcopy /e /i /h "%base_dir_path%" "%clone_dir_path%"

REM Register the clone agent in the pool by appending to __init__.py
echo from .%clone_agent% import * >> ".\gentpool\pool\__init__.py"

REM Update the agent names in the clone agent directory
REM Use PowerShell for text replacements
powershell -Command "(Get-Content '.\gentpool\pool\%clone_agent%\__init__.py').replace('%base_agent%', '%clone_agent%') | Set-Content '.\gentpool\pool\%clone_agent%\__init__.py'"
powershell -Command "(Get-Content '.\gentpool\pool\%clone_agent%\agent.yaml').replace('name: %base_agent%', 'name: %clone_agent%') | Set-Content '.\gentpool\pool\%clone_agent%\agent.yaml'"

echo Agent %clone_agent% has been cloned from %base_agent%.
endlocal

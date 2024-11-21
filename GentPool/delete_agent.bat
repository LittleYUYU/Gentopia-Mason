@echo off

REM Get the agent name from the first argument
set agent_name=%1

REM Directory path
set dir_path=.\gentpool\pool\%agent_name%

REM Ask for user confirmation
echo Deleting agent %agent_name% in folder %dir_path%, this is irreversible, are you sure? (y/n)
set /p answer=

if /i "%answer%"=="y" (
    REM Check if directory exists before trying to delete it
    if exist "%dir_path%" (
        REM Remove the directory
        rmdir /s /q "%dir_path%" 

        REM Unregister the agent from the pool
        powershell -command "(Get-Content './gentpool/pool/__init__.py') -replace 'from .%agent_name% import .*', '' | Set-Content './gentpool/pool/__init__.py'"

        echo Agent %agent_name% has been deleted.
    ) else (
        echo Agent %agent_name% does not exist.
    )
) else (
    echo Agent deletion cancelled.
)

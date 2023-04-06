:<<BATCH
    @echo off
    :: Just an entry point for installer
    python --version 2>NUL
    if errorlevel 1 goto errorNoPython

    echo Python found, executing install
    python installer.py

    goto:eof

    :errorNoPython
    echo.
    echo Error^: Python was not found
BATCH
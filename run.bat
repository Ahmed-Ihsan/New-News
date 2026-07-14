@echo off
chcp 65001 >nul 2>&1
title Tech News Aggregator

echo.
echo   ============================================
echo     Tech News Aggregator - Quick Launcher
echo   ============================================
echo.
echo   [1] CLI - Collect news + Markdown report
echo   [2] CLI + PDF export
echo   [3] CLI + Telegram post
echo   [4] CLI + Card image
echo   [5] CLI + All (PDF + Post + Image)
echo   [6] TUI - Terminal interface
echo   [7] GUI - Desktop interface
echo   [8] Exit
echo.
set /p choice="  Select option (1-8): "

if "%choice%"=="1" goto cli
if "%choice%"=="2" goto cli_pdf
if "%choice%"=="3" goto cli_post
if "%choice%"=="4" goto cli_image
if "%choice%"=="5" goto cli_all
if "%choice%"=="6" goto tui
if "%choice%"=="7" goto gui
if "%choice%"=="8" exit
echo   Invalid option.
pause
exit /b

:cli
py -3.10 -m tech_news_aggregator
pause
exit /b

:cli_pdf
py -3.10 -m tech_news_aggregator --pdf
pause
exit /b

:cli_post
py -3.10 -m tech_news_aggregator --post
pause
exit /b

:cli_image
py -3.10 -m tech_news_aggregator --post --image
pause
exit /b

:cli_all
py -3.10 -m tech_news_aggregator --pdf --post --image
pause
exit /b

:tui
py -3.10 -m tech_news_aggregator --tui
exit /b

:gui
py -3.10 -m tech_news_aggregator --gui
exit /b

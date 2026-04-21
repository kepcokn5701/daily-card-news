@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

REM ============================================================
REM  regen_today.bat — 카드뉴스 HTML 재생성 (휘발성 뷰 복구용)
REM
REM  사용법:
REM    regen_today.bat              ← 오늘 날짜로 재생성
REM    regen_today.bat 2026-04-19   ← 지정일로 재생성
REM
REM  배치: daily-card-news\scripts\ 에 위치
REM  역할: 결과물\scraps\YYYY-MM-DD.json 을 입력으로
REM        결과물\cardnews\YYYY-MM-DD.html 생성 후 브라우저 오픈
REM ============================================================

REM 스크립트 위치의 상위 폴더 (daily-card-news 루트) 로 이동
cd /d "%~dp0\.."

REM 1) 날짜 인자 처리
set DATE_ARG=%~1
if "%DATE_ARG%"=="" (
    for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set DATE_ARG=%%i
)

set INPUT=결과물\scraps\%DATE_ARG%.json
set OUTPUT=결과물\cardnews\%DATE_ARG%.html

echo.
echo ===========================================
echo  daily-card-news : regen_today
echo  날짜 : %DATE_ARG%
echo ===========================================
echo.

REM 2) 입력 JSON 존재 확인
if not exist "%INPUT%" (
    echo [err] 입력 JSON 이 없습니다: %INPUT%
    echo.
    echo 다음 중 하나로 해결:
    echo   A. 해당 날짜 수집 안 됐다면 먼저 수집:
    echo      python scripts\collect_aitimes.py --date %DATE_ARG%
    echo      그 다음 카드용 JSON 을 Cowork 에서 생성한 뒤 이 배치 재실행
    echo   B. 날짜 오타라면 올바른 날짜로 재호출:
    echo      regen_today.bat 2026-04-19
    echo.
    pause
    exit /b 1
)

REM 3) 출력 폴더 준비
if not exist "결과물\cardnews" mkdir "결과물\cardnews"

REM 4) 카드뉴스 생성
echo [regen] 입력: %INPUT%
echo [regen] 출력: %OUTPUT%
echo.
python scripts\generate_cards.py --input "%INPUT%" --output "%OUTPUT%" --theme modern-light

if errorlevel 1 (
    echo.
    echo [err] 생성 실패. 위 에러 로그 확인 필요.
    pause
    exit /b 1
)

echo.
echo [done] 재생성 완료.
echo.

REM 5) 브라우저 자동 오픈 (더블클릭 사용성 고려)
set /p OPEN_BROWSER="지금 브라우저로 열까요? [Y/n]: "
if /i "%OPEN_BROWSER%"=="n" goto :skipopen
start "" "%OUTPUT%"
:skipopen

endlocal

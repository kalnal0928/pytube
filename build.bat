@echo off
echo YouTube Downloader 빌드 시작...

REM 이전 빌드 파일 정리
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM yt-dlp.exe 존재 확인
if not exist "yt-dlp.exe" (
    echo 오류: yt-dlp.exe 파일이 없습니다!
    echo https://github.com/yt-dlp/yt-dlp/releases/latest 에서 다운로드하세요.
    pause
    exit /b 1
)

REM PyInstaller 실행
echo PyInstaller로 빌드 중...
pyinstaller --clean youtube_downloader_ui.spec

REM 빌드 결과 확인
if exist "dist\youtube_downloader_ui\youtube_downloader_ui.exe" (
    echo.
    echo ✅ 빌드 성공!
    echo 📁 실행 파일 위치: dist\youtube_downloader_ui\youtube_downloader_ui.exe
    echo.
    echo 배포용 폴더: dist\youtube_downloader_ui\
    echo 이 폴더 전체를 압축해서 배포하세요.
) else (
    echo ❌ 빌드 실패!
    echo 오류 로그를 확인하세요.
)

pause
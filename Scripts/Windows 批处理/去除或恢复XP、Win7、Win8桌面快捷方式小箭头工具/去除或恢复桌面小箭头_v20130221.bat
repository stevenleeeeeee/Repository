@echo off
setlocal enabledelayedexpansion
title ȥ����ָ������ݷ�ʽС��ͷ����(by���԰�)
color 0A
mode con: cols=50 lines=25


cls::����
call :admintest::����Ƿ��ǹ���Ա�������
call :vercheck::��鵱ǰϵͳ�Ƿ���Win7��Win8


:menu
set Line===================================================
echo %Line%
echo 	��ʾ��������ͬʱ֧��XP��Win7��Win8ϵͳ
echo.
echo		[A]	ȥ����ͷ
echo		[B]	�ָ���ͷ
echo		[C]	����
echo.
echo		[X]	�˳�
echo %Line%


choice /c ABCX /M ��ѡ��
if %errorlevel%==1 call :remove
if %errorlevel%==2 call :add
if %errorlevel%==3 call :about
if %errorlevel%==4 exit
goto :menu

:remove
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Icons" /v 29 /d "%systemroot%\system32\%value%" /t reg_sz /f
taskkill /f /im explorer.exe
start explorer
goto :EOF


:add
reg delete "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Icons" /v 29 /f
taskkill /f /im explorer.exe
start explorer
goto :EOF


:admintest::�����Ƿ����Թ���Ա�������
set rnd=_%random%
md %windir%\%rnd% >nul 2>nul
if %errorlevel%==1 (echo.&echo ���Ҽ����ļ���ѡ���Թ���Ա������С���&echo.&echo �����԰�������˳�����&pause>nul 2>nul &exit)
rd /q %windir%\%rnd%
goto :EOF


:vercheck::ϵͳ�汾���
ver | find "5.1" >nul 2>nul && (echo ���ĵ�ǰϵͳ��WinXP������Ҫ��&set value=shell32.dll,49&echo.&goto :EOF)
ver | find "6.1" >nul 2>nul && (echo ���ĵ�ǰϵͳ��Win7������Ҫ��&set value=imageres.dll,196&echo.&goto :EOF)
ver | find "6.2" >nul 2>nul && (echo ���ĵ�ǰϵͳ��Win8������Ҫ��&set value=imageres.dll,197&echo.&goto :EOF)
ver | find "6.3" >nul 2>nul && (echo ���ĵ�ǰϵͳ��Win8.1������Ҫ��&set value=imageres.dll,197&echo.&goto :EOF)
echo.&echo ��Ǹ����������ֻ����Win7��Win8ϵͳ��ʹ�ã�
echo.&echo �밴������˳��ɡ���
pause>nul
exit


:about::����
echo.
echo ��ȥ����ָ������ݷ�ʽС��ͷ���ߡ�
echo ���ߣ����԰�
echo ΢����http://weibo.com/liuxianan
echo QQ��937925941
echo ���ڣ�2013��2��11��
echo.
goto :EOF


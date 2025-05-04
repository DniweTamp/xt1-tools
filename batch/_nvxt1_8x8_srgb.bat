@echo off
title Any texture to bc7 DDS Conversion

set NEWNVTT="C:\Program Files\NVIDIA Corporation\NVIDIA Texture Tools\nvtt_export.exe"
set dds_to_xt1="%~dp0\dds_to_xt1.exe"
set "fileCount=0"
for %%A in (%*) do set /a "fileCount+=1"

setlocal EnableDelayedExpansion
FOR %%a IN (%*) DO (
    set /a "currentFile+=1"
    
    :: Calculate the progress
    set /a "progress=currentFile*20/fileCount"
    
    :: Create the progress bar
    set "progressBar="
    for /L %%B in (1,1,!progress!) do set "progressBar=!progressBar!#"
    for /L %%B in (!progress!,1,19) do set "progressBar=!progressBar!-"
    
    echo File !currentFile!/!fileCount! [!progressBar!]: %%~na%%~xa

    %NEWNVTT% %%a -f astc-ldr-8x8 -q highest --dx10 --export-transfer-function srgb -o "%%~da%%~pa%%~na.dds"
    %dds_to_xt1% "%%~da%%~pa%%~na.dds"
    del "%%~da%%~pa%%~na.dds"
    cls
)

::pause
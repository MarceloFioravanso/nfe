@echo off
echo.
echo ================================================
echo  VERIFICADOR DE NOTAS FISCAIS PENDENTES NO EXCEL
echo ================================================
echo.
echo Este script mostrará todas as notas pendentes
echo para emissão encontradas no arquivo Excel.
echo.

python verificar_notas_pendentes.py

echo.
echo Se quiser processar as notas, execute:
echo   processa_notas.bat
echo.
pause

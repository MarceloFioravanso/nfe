@echo off
echo.
echo ================================================
echo  PROCESSADOR DE MÚLTIPLAS NOTAS FISCAIS NO EXCEL
echo ================================================
echo.
echo Este script processará as notas pendentes
echo encontradas no arquivo Excel.
echo.
echo IMPORTANTE: Certifique-se de fechar o arquivo Excel
echo antes de continuar para evitar conflitos de acesso.
echo.
pause

python processa_multiplas_notas.py

echo.
pause

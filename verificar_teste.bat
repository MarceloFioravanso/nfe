@echo off
echo.
echo ================================================
echo  VERIFICADOR DE NOTAS PENDENTES (MODO TESTE)
echo ================================================
echo.
echo Este script executará o modo de teste do processa_multiplas_notas.py
echo para verificar quantas notas pendentes existem sem iniciar o processamento.
echo.

python processa_multiplas_notas.py --teste

echo.
pause

@echo off
echo.
echo ================================================
echo  INSTALACAO DO SISTEMA DE AUTOMACAO DE NOTAS
echo ================================================
echo.
echo Este script vai instalar todas as dependencias
echo necessarias para o sistema funcionar corretamente.
echo.
echo IMPORTANTE: E necessario ter o Python instalado.
echo.
echo Pressione CTRL+C para cancelar ou 
pause

echo.
echo Instalando dependencias...
pip install -r requirements.txt

echo.
echo Testando a instalacao...
python -c "import pandas; import selenium; import openpyxl; print('Bibliotecas instaladas com sucesso!')"

echo.
echo ================================================
echo  INSTALACAO CONCLUIDA!
echo ================================================
echo.
echo Para verificar notas pendentes, execute:
echo   verificar_rapido.bat
echo.
echo Para processar notas pendentes, execute:
echo   processa_notas.bat
echo.
pause

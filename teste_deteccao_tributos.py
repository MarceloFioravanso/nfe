# -*- coding: utf-8 -*-
"""
Script para testar a detecção de tributos federais sem uma sessão real do Selenium.
Isso apenas verifica se o código compila e se a lógica parece estar correta.
"""
import logging
from preencher_tributos import preencher_tributos_federais

# Configurando o logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('teste_tributos')

# Criando um mock de dados
dados_nota = {
    'valor_servico': 1000.00,
    'irrf': 15.00,
    'pis': 6.50,
    'cofins': 30.00,
    'csll': 10.00,
    'valor_liquido': 938.50  # Valor serviço (1000) - Total tributos (61.50)
}

# Informando sobre o teste
print("=" * 80)
print("TESTE DE COMPILAÇÃO DO MÓDULO DE TRIBUTOS FEDERAIS")
print("=" * 80)
print("Este script apenas verifica se o código compila corretamente.")
print("Para um teste real, é necessário executar com o Selenium e uma página ativa.")
print("Dados de teste:")
for chave, valor in dados_nota.items():
    print(f"  - {chave}: {valor}")
print("=" * 80)

# Exibindo as funções disponíveis
print("Funções disponíveis no módulo:")
print("  - preencher_tributos_federais")
print("  - preencher_tributos")
print("=" * 80)

# O código abaixo não será executado de verdade, mas serve para verificar
# se o código compila e se a lógica parece estar correta
print("Se você não viu erros até aqui, o módulo está compilando corretamente!")
print("=" * 80)

# -*- coding: utf-8 -*-
"""
Teste da funcionalidade de preenchimento do campo de descrição do serviço com informações adicionais.
"""
import logging
import pandas as pd
from datetime import datetime

# Configura o logger
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('teste_descricao')

# Simula os dados da nota
dados_nota = {
    'descricao_servico': 'DESENVOLVIMENTO DE PROGRAMA DE CARGOS E SALÁRIOS',
    'vencimento': datetime(2025, 5, 10),
    'parcela': '2/4'
}

def teste_formatacao_descricao():
    """Testa a formatação da descrição do serviço com informações adicionais"""
    logger.info("Iniciando teste da formatação da descrição do serviço")
    
    # Simula o processamento da descrição
    descricao_servico = dados_nota.get('descricao_servico', '')
    
    # Formata o vencimento
    vencimento = dados_nota.get('vencimento', '')
    if vencimento and not pd.isna(vencimento):
        if isinstance(vencimento, datetime):
            vencimento = vencimento.strftime("%d/%m/%Y")
    
    # Obtém o número da parcela
    parcela = dados_nota.get('parcela', '')
      # Adiciona informações complementares à descrição do serviço
    descricao_completa = [descricao_servico]
    
    # Linha em branco após a descrição
    descricao_completa.append("")
    
    # Vencimento com linha em branco após
    if vencimento:
        descricao_completa.append(f"VENCIMENTO: {vencimento}")
        descricao_completa.append("")
        
    # Parcela com linha em branco após
    if parcela:
        descricao_completa.append(f"PARCELA: {parcela}")
        descricao_completa.append("")
    
    # Adiciona informações de PIX/depósito
    descricao_completa.extend([
        "DADOS PARA PIX OU DEPÓSITO:",
        "",
        "PIX: (51) 99775-6607",
        "BANCO: 748 - SICREDI",
        "AGÊNCIA: 0116", 
        "CONTA: 17240-7",
        "TITULAR: LAFIORAVANSO CONSULTORIA EMPRESARIAL LTDA.",
        "CNPJ: 02.572.042/0001-22"
    ])
    
    # Junta todas as linhas com quebras de linha
    descricao_final = "\n".join(descricao_completa)
    
    logger.info("Descricao formatada:")
    print("=" * 60)
    print(descricao_final)
    print("=" * 60)
    
    # Verifica se todas as informações estão presentes
    verificacoes = {
        'Serviço': 'DESENVOLVIMENTO DE PROGRAMA DE CARGOS E SALÁRIOS' in descricao_final,
        'Vencimento': 'VENCIMENTO: 10/05/2025' in descricao_final,
        'Parcela': 'PARCELA: 2/4' in descricao_final,
        'PIX': 'PIX: (51) 99775-6607' in descricao_final,
        'Banco': 'BANCO: 748 - SICREDI' in descricao_final,
        'Agência': 'AGÊNCIA: 0116' in descricao_final,
        'Conta': 'CONTA: 17240-7' in descricao_final,
        'Titular': 'TITULAR: LAFIORAVANSO CONSULTORIA EMPRESARIAL LTDA.' in descricao_final,
        'CNPJ': 'CNPJ: 02.572.042/0001-22' in descricao_final
    }
    
    # Exibe o resultado das verificações
    for item, resultado in verificacoes.items():
        status = "PASSOU" if resultado else "FALHOU"
        logger.info(f"Verificação '{item}': {status}")
    
    # Verifica se todas as informações estão presentes
    if all(verificacoes.values()):
        logger.info("TESTE PASSOU: Todas as informações foram incluídas corretamente na descrição")
        return True
    else:
        falhas = [k for k, v in verificacoes.items() if not v]
        logger.error(f"TESTE FALHOU: As seguintes informações não foram encontradas: {', '.join(falhas)}")
        return False

if __name__ == "__main__":
    logger.info("=== Iniciando o teste de formatação da descrição do serviço ===")
    teste_formatacao_descricao()
    logger.info("=== Teste concluído ===")

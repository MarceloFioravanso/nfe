# -*- coding: utf-8 -*-
"""
Teste da funcionalidade de preenchimento do campo de descrição do serviço
usando os componentes de vencimento das colunas X, Y, Z e parcela da coluna AL.
"""
import logging
import pandas as pd

# Configura o logger
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('teste_vencimento_parcela')

# Simula os dados da nota com os componentes de vencimento e parcela
dados_nota = {
    'descricao_servico': 'CONSULTORIA EM GESTÃO DE PESSOAS',
    'vencimento_dia': 15,
    'vencimento_mes': 6,
    'vencimento_ano': 2025,
    'parcela': '3/5'
}

def teste_componentes_vencimento():
    """Testa a formatação da descrição do serviço com vencimento composto por componentes"""
    logger.info("Iniciando teste dos componentes de vencimento e parcela")
    
    # Simula o processamento da descrição
    descricao_servico = dados_nota.get('descricao_servico', '')
    
    # Compõe a data de vencimento a partir dos campos separados
    vencimento_dia = dados_nota.get('vencimento_dia', '')
    vencimento_mes = dados_nota.get('vencimento_mes', '')
    vencimento_ano = dados_nota.get('vencimento_ano', '')
    
    # Formata o vencimento se os componentes existirem
    vencimento = ''
    if vencimento_dia and vencimento_mes and vencimento_ano:
        try:
            dia = str(int(vencimento_dia)).zfill(2)
            mes = str(int(vencimento_mes)).zfill(2)
            ano = str(int(vencimento_ano))
            
            # Formata como DD/MM/AAAA
            vencimento = f"{dia}/{mes}/{ano}"
            logger.info(f"Data de vencimento composta: {vencimento}")
        except (ValueError, TypeError) as e:
            logger.warning(f"Erro ao formatar componentes de data: {e}")
    
    # Obtém o número da parcela
    parcela = dados_nota.get('parcela', '')
    
    # Adiciona informações complementares à descrição do serviço
    descricao_completa = [descricao_servico]
      # Adiciona linha em branco após a descrição principal
    descricao_completa.append("")
    
    # Adiciona informações de vencimento (com linha em branco após)
    if vencimento:
        descricao_completa.append(f"VENCIMENTO: {vencimento}")
        descricao_completa.append("")
        
    # Adiciona informações de parcela (com linha em branco após)
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
    
    logger.info("Descrição formatada:")
    print("=" * 60)
    print(descricao_final)
    print("=" * 60)
    
    # Verifica se todas as informações estão presentes
    verificacoes = {
        'Serviço': 'CONSULTORIA EM GESTÃO DE PESSOAS' in descricao_final,
        'Vencimento': 'VENCIMENTO: 15/06/2025' in descricao_final,
        'Parcela': 'PARCELA: 3/5' in descricao_final,
        'Linha em branco após descrição': '\n\n' in descricao_final,
        'Linha em branco antes de PIX': 'PARCELA: 3/5\n\n' in descricao_final,
        'Linha em branco após título PIX': 'DADOS PARA PIX OU DEPÓSITO:\n\n' in descricao_final,
        'PIX': 'PIX: (51) 99775-6607' in descricao_final,
    }
    
    # Exibe os resultados das verificações
    for item, resultado in verificacoes.items():
        logger.info(f"Verificação {item}: {'✓' if resultado else '✗'}")
    
    # Retorna sucesso se todas as verificações passaram
    return all(verificacoes.values())

if __name__ == "__main__":
    sucesso = teste_componentes_vencimento()
    print(f"\nTeste {'bem-sucedido' if sucesso else 'falhou'}!")

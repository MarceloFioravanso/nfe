# -*- coding: utf-8 -*-
"""
Teste da formatação exata da descrição do serviço conforme o exemplo fornecido.
"""
import logging

# Configura o logger
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('teste_formatacao_exemplo')

def teste_formatacao_exemplo():
    """
    Verifica se a formatação da descrição segue exatamente o exemplo fornecido.
    
    Exemplo esperado:
    SPÉCIALITÉ - PESQUISA DE REMUNERAÇÃO

    VENCIMENTO: 30/06/2025

    PARCELA: 1/6

    DADOS PARA PIX OU DEPÓSITO:

    PIX: (51) 99775-6607
    BANCO: 748 - SICREDI
    AGÊNCIA: 0116
    CONTA: 17240-7
    TITULAR: LAFIORAVANSO CONSULTORIA EMPRESARIAL LTDA.
    CNPJ: 02.572.042/0001-22
    """
    logger.info("Iniciando teste da formatação conforme exemplo fornecido")
    
    # Dados de exemplo
    dados_nota = {
        'descricao_servico': 'SPÉCIALITÉ - PESQUISA DE REMUNERAÇÃO',
        'vencimento_dia': 30,
        'vencimento_mes': 6,
        'vencimento_ano': 2025,
        'parcela': '1/6'
    }
    
    # Processamento similar à função preencher_descricao_servico
    descricao_servico = dados_nota.get('descricao_servico', '')
    
    # Compõe a data de vencimento
    vencimento = ''
    vencimento_dia = dados_nota.get('vencimento_dia', '')
    vencimento_mes = dados_nota.get('vencimento_mes', '')
    vencimento_ano = dados_nota.get('vencimento_ano', '')
    
    if vencimento_dia and vencimento_mes and vencimento_ano:
        dia = str(int(vencimento_dia)).zfill(2)
        mes = str(int(vencimento_mes)).zfill(2)
        ano = str(int(vencimento_ano))
        vencimento = f"{dia}/{mes}/{ano}"
    
    # Obtém a parcela
    parcela = dados_nota.get('parcela', '')
    
    # Constrói a descrição completa
    descricao_completa = [descricao_servico]
      # Adiciona linha em branco após a descrição principal
    descricao_completa.append("")
    
    # Adiciona vencimento (com linha em branco após)
    if vencimento:
        descricao_completa.append(f"VENCIMENTO: {vencimento}")
        descricao_completa.append("")
    
    # Adiciona parcela (com linha em branco após)
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
    
    # Exemplo esperado
    exemplo_esperado = """SPÉCIALITÉ - PESQUISA DE REMUNERAÇÃO

VENCIMENTO: 30/06/2025

PARCELA: 1/6

DADOS PARA PIX OU DEPÓSITO:

PIX: (51) 99775-6607
BANCO: 748 - SICREDI
AGÊNCIA: 0116
CONTA: 17240-7
TITULAR: LAFIORAVANSO CONSULTORIA EMPRESARIAL LTDA.
CNPJ: 02.572.042/0001-22"""
      # Compara com o exemplo esperado
    logger.info("Descrição gerada:")
    print("=" * 60)
    print(descricao_final)
    print("=" * 60)
    
    # Mostra as linhas individuais para diagnóstico
    logger.info("Linhas da descrição gerada (com marcadores):")
    for i, linha in enumerate(descricao_final.split('\n')):
        logger.info(f"Linha {i+1}: '{linha}'")
    
    logger.info("Exemplo esperado:")
    print("=" * 60)
    print(exemplo_esperado)
    print("=" * 60)
    
    # Mostra as linhas do exemplo esperado
    logger.info("Linhas do exemplo esperado (com marcadores):")
    for i, linha in enumerate(exemplo_esperado.split('\n')):
        logger.info(f"Linha {i+1}: '{linha}'")
    
    # Verifica as linhas em branco
    linhas_geradas = descricao_final.split('\n')
    linhas_esperadas = exemplo_esperado.split('\n')
    
    logger.info("\nVerificação de linhas em branco:")
    for i in range(len(linhas_esperadas)):
        if i >= len(linhas_geradas):
            logger.info(f"Linha {i+1}: Esperado linha em branco? {linhas_esperadas[i] == ''}, mas está ausente na descrição gerada")
        elif linhas_esperadas[i] == '':
            logger.info(f"Linha {i+1}: Esperado linha em branco, Gerado: '{linhas_geradas[i]}' - Corresponde: {linhas_geradas[i] == ''}")
    
    # Verifica se a formatação está exatamente como esperado
    if descricao_final == exemplo_esperado:
        logger.info("✓ SUCESSO: A formatação corresponde EXATAMENTE ao exemplo fornecido")
        return True
    else:
        logger.error("✗ FALHA: A formatação NÃO corresponde ao exemplo fornecido")
        
        # Exibe diferenças linha a linha para facilitar diagnóstico
        descricao_linhas = descricao_final.split("\n")
        exemplo_linhas = exemplo_esperado.split("\n")
        
        max_linhas = max(len(descricao_linhas), len(exemplo_linhas))
        
        for i in range(max_linhas):
            linha_desc = descricao_linhas[i] if i < len(descricao_linhas) else "(linha ausente)"
            linha_exemplo = exemplo_linhas[i] if i < len(exemplo_linhas) else "(linha ausente)"
            
            if linha_desc != linha_exemplo:
                logger.error(f"Linha {i+1} - Atual: '{linha_desc}' | Esperado: '{linha_exemplo}'")
        
        return False

if __name__ == "__main__":
    sucesso = teste_formatacao_exemplo()
    print(f"\nResultado do teste: {'SUCESSO' if sucesso else 'FALHA'}")

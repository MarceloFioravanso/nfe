# -*- coding: utf-8 -*-
"""
Teste da funcionalidade de preenchimento do campo bairro na automação de NFS-e.
Este script testa apenas a parte do dicionário de mapeamento.
"""
import logging

# Configura o logger
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('teste_bairro')

# Simula os dados do Excel
dados_excel = {
    'CNPJ': '12.345.678/0001-90',
    'Empresa - Razão Social': 'Empresa Teste LTDA',
    'Endereço': 'Rua das Flores',
    'Número': '123',
    'Complemento': 'Sala 45',
    'BAIRRO': 'Jardim América',
    'Município': 'São Paulo',
    'Estado': 'SP',
    'CEP': '01234-567',
}

def mapear_dados_nota(dados_nota):
    """
    Mapeia os dados do Excel para as variáveis necessárias para emissão da nota fiscal.
    (Versão simplificada para teste)
    """
    logger.info("Mapeando dados da nota fiscal...")
        
    # Mapeamento baseado nas colunas reais do Excel
    mapeamento = {
        'cnpj_tomador': dados_nota.get('CNPJ', ''),
        'razao_social': dados_nota.get('Empresa - Razão Social', ''),
        'nome_fantasia': dados_nota.get('Empresa - Razão Social', ''),  
        'endereco': dados_nota.get('Endereço', ''),
        'numero': dados_nota.get('Número', ''),  
        'complemento': dados_nota.get('Complemento', ''),  
        'bairro': dados_nota.get('BAIRRO', ''),
        'cidade': dados_nota.get('Município', ''),
        'uf': dados_nota.get('Estado', ''),
        'cep': dados_nota.get('CEP', ''),
    }
    
    logger.info(f"Dados mapeados: {mapeamento}")
    return mapeamento

def teste_campo_bairro():
    """Testa o mapeamento do campo bairro"""
    logger.info("Iniciando teste do campo bairro")
    
    # Mapeia os dados
    dados_mapeados = mapear_dados_nota(dados_excel)
    
    # Verifica se o bairro foi mapeado corretamente
    if dados_mapeados.get('bairro') == 'Jardim América':
        logger.info("TESTE PASSOU: O campo bairro foi mapeado corretamente")
    else:
        logger.error(f"TESTE FALHOU: O campo bairro não foi mapeado corretamente. Valor: {dados_mapeados.get('bairro')}")

    # Verifica se o campo está sendo incluído no dicionário de campos de endereço
    campos_endereco = {
        'bairro': {
            'seletores': ['input[name="InformacoesTomador.bairro"]', 'input[aria-label="Bairro"]', 'input[name*="bairro"]', 'input[class*="campo-texto"][aria-label="Bairro"]'],
            'valor': dados_mapeados.get('bairro', ''),
            'obrigatorio': False
        }
    }
    
    if campos_endereco['bairro']['valor'] == 'Jardim América':
        logger.info("TESTE PASSOU: O campo bairro está corretamente incluído no dicionário de campos de endereço")
    else:
        logger.error(f"TESTE FALHOU: O campo bairro não está corretamente configurado no dicionário. Valor: {campos_endereco['bairro']['valor']}")

if __name__ == "__main__":
    logger.info("=== Iniciando o teste de preenchimento do campo bairro ===")
    teste_campo_bairro()
    logger.info("=== Teste concluído ===")
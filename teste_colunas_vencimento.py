# -*- coding: utf-8 -*-
"""
Teste para verificar se as colunas de vencimento e parcela existem na planilha Excel
e se contêm os dados esperados.
"""
import os
import pandas as pd
import logging

# Configura o logger
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('teste_colunas_vencimento')

# Define o caminho do arquivo Excel usado na automação
EXCEL_PATH = r"C:\Users\pesqu\OneDrive\LAF\Adm_Fioravanso\Planejamentos_Controles\Financeiro\_Controle NotaFiscal.xlsx"

def verificar_colunas_excel():
    """
    Verifica se as colunas de vencimento e parcela existem na planilha Excel.
    """
    logger.info(f"Verificando colunas no arquivo Excel: {EXCEL_PATH}")
    
    # Verifica se o arquivo existe
    if not os.path.exists(EXCEL_PATH):
        logger.error(f"Arquivo Excel não encontrado: {EXCEL_PATH}")
        return False
    
    try:
        # Carrega o arquivo Excel
        df = pd.read_excel(EXCEL_PATH, sheet_name=0, header=2)
        
        logger.info(f"Arquivo Excel carregado com sucesso. {len(df)} linhas encontradas.")
        logger.info(f"Colunas disponíveis: {list(df.columns)}")
        
        # Verifica se as colunas necessárias estão presentes
        colunas_necessarias = ['Dia Venc.', 'Mês Venc.', 'Ano Venc.', 'Parcela']
        colunas_presentes = []
        colunas_ausentes = []
        
        for coluna in colunas_necessarias:
            if coluna in df.columns:
                colunas_presentes.append(coluna)
                # Verifica se há dados nesta coluna
                valores_validos = df[coluna].notna().sum()
                logger.info(f"Coluna '{coluna}' encontrada com {valores_validos} valores válidos")
            else:
                colunas_ausentes.append(coluna)
                logger.error(f"Coluna '{coluna}' NÃO encontrada na planilha")
        
        if colunas_ausentes:
            logger.error(f"As seguintes colunas estão ausentes: {', '.join(colunas_ausentes)}")
            
            # Sugestão para verificar nomes de coluna alternativos
            logger.info("Verificando possíveis nomes alternativos para as colunas...")
            
            # Para vencimento
            for nome_alternativo in ['Dia Venc', 'Dia', 'Vencimento Dia']:
                if nome_alternativo in df.columns:
                    logger.info(f"Possível alternativa para 'Dia Venc.': '{nome_alternativo}'")
            
            for nome_alternativo in ['Mês Venc', 'Mês', 'Vencimento Mês']:
                if nome_alternativo in df.columns:
                    logger.info(f"Possível alternativa para 'Mês Venc.': '{nome_alternativo}'")
                    
            for nome_alternativo in ['Ano Venc', 'Ano', 'Vencimento Ano']:
                if nome_alternativo in df.columns:
                    logger.info(f"Possível alternativa para 'Ano Venc.': '{nome_alternativo}'")
                    
            # Para parcela
            for nome_alternativo in ['Parc', 'Nº Parcela', 'Número Parcela']:
                if nome_alternativo in df.columns:
                    logger.info(f"Possível alternativa para 'Parcela': '{nome_alternativo}'")
        
        return len(colunas_ausentes) == 0
        
    except Exception as e:
        logger.error(f"Erro ao verificar colunas no Excel: {e}")
        return False

def verificar_dados_exemplo():
    """
    Verifica os valores de algumas linhas para demonstrar os dados presentes.
    """
    try:
        # Carrega o arquivo Excel
        df = pd.read_excel(EXCEL_PATH, sheet_name=0, header=2)
        
        # Verifica se há linhas válidas
        if len(df) == 0:
            logger.warning("A planilha não contém linhas de dados")
            return
        
        # Mostra os dados das últimas 3 linhas da planilha (potenciais notas pendentes)
        logger.info("Exibindo dados das últimas 3 linhas da planilha:")
        for i in range(min(3, len(df))):
            idx = len(df) - i - 1
            linha = df.iloc[idx]
            
            # Verifica se esta linha tem dados de vencimento e parcela
            dia_venc = linha.get('Dia Venc.', 'N/A') if 'Dia Venc.' in df.columns else 'N/A'
            mes_venc = linha.get('Mês Venc.', 'N/A') if 'Mês Venc.' in df.columns else 'N/A'
            ano_venc = linha.get('Ano Venc.', 'N/A') if 'Ano Venc.' in df.columns else 'N/A'
            parcela = linha.get('Parcela', 'N/A') if 'Parcela' in df.columns else 'N/A'
            
            logger.info(f"Linha {idx + 3} do Excel (Razão Social: {linha.get('Empresa - Razão Social', 'N/A')}):")
            logger.info(f"  - Dia vencimento (Dia Venc.): {dia_venc}")
            logger.info(f"  - Mês vencimento (Mês Venc.): {mes_venc}")
            logger.info(f"  - Ano vencimento (Ano Venc.): {ano_venc}")
            logger.info(f"  - Parcela: {parcela}")
            
            # Exemplo de como os valores seriam formatados
            try:
                if pd.notna(dia_venc) and pd.notna(mes_venc) and pd.notna(ano_venc) and dia_venc != 'N/A':
                    dia = str(int(dia_venc)).zfill(2)
                    mes = str(int(mes_venc)).zfill(2)
                    ano = str(int(ano_venc))
                    vencimento = f"{dia}/{mes}/{ano}"
                    logger.info(f"  → Data de vencimento formatada: {vencimento}")
                else:
                    logger.warning("  → Dados de vencimento incompletos")
            except (ValueError, TypeError) as e:
                logger.warning(f"  → Erro ao formatar data: {e}")
            
    except Exception as e:
        logger.error(f"Erro ao verificar dados de exemplo: {e}")

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("TESTANDO ACESSO ÀS COLUNAS DE VENCIMENTO E PARCELA NO EXCEL")
    logger.info("=" * 60)
    
    # Verifica se as colunas existem
    colunas_ok = verificar_colunas_excel()
    
    # Mostra exemplos de dados
    logger.info("\nVerificando dados de exemplo:")
    verificar_dados_exemplo()
    
    # Sugestão para resolver problemas
    if not colunas_ok:
        logger.info("\nSUGESTÕES DE SOLUÇÃO:")
        logger.info("1. Verifique se o arquivo Excel está aberto. Feche-o e tente novamente.")
        logger.info("2. Verifique se as colunas existem com nomes diferentes e ajuste o mapeamento.")
        logger.info("3. Para ajustar o mapeamento em nfs_emissao_auto.py, modifique as linhas:")
        logger.info("   'vencimento_dia': dados_nota.get('Dia Venc.', ''),  # Coluna para dia do vencimento")
        logger.info("   'vencimento_mes': dados_nota.get('Mês Venc.', ''),  # Coluna para mês do vencimento")
        logger.info("   'vencimento_ano': dados_nota.get('Ano Venc.', ''),  # Coluna para ano do vencimento")
        logger.info("   'parcela': dados_nota.get('Parcela', '')            # Coluna para número da parcela")
    else:
        logger.info("\nTodas as colunas necessárias foram encontradas!")

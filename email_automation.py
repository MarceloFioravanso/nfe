#!/usr/bin/env python3
import os
import pandas as pd
import logging
from dotenv import load_dotenv
import re
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from exchange_manager import ExchangeEmailManager
import argparse
from PyPDF2 import PdfReader  # para extrair número interno de PDFs

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('email_automation')

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
PASTA_ENTRADA = './entrada'
LAYOUT_EMAIL_FILE = './layout_email.txt'
ARQUIVO_EXCEL_INFO = 'C:\\Users\\pesqu\\OneDrive\\LAF\\Adm_Fioravanso\\Planejamentos_Controles\\Financeiro\\_Controle NotaFiscal.xlsx'

# Funções auxiliares
def renomear_arquivos(pasta, empresa_map=None):
    """Renomeia arquivos PDF e XML na pasta de entrada com prefixo 2025 e sufixo empresa."""
    # Listar arquivos XML e PDF
    from datetime import datetime as _dt
    current_year = _dt.now().year
    xml_entries = []
    pdf_entries = []
    for entry in os.scandir(pasta):
        if not entry.is_file():
            continue
        ext = os.path.splitext(entry.name)[1].lower()
        if ext == '.xml':
            xml_entries.append(entry)
        elif ext == '.pdf':
            pdf_entries.append(entry)

    arquivos_por_nota = {}
    # Processar XML primeiro: extrair número do nome via prefixo ou do conteúdo
    for entry in xml_entries:
        name = entry.name
        # Tenta primeiro extrair via nome no formato 2025_<numero>
        m = re.match(r"2025_(\d+)", name)
        if m:
            numero = m.group(1)
        else:
            # Fallback: extrair número do conteúdo do XML (tag numero_nfse)
            numero = None
            try:
                tree = ET.parse(entry.path)
                num_text = tree.findtext('.//numero_nfse')
                if num_text and num_text.isdigit():
                    numero = num_text
                else:
                    raise ValueError('Tag numero_nfse inválida')
            except Exception as e:
                logger.warning(f"Falha ao extrair número de XML ({name}): {e}")
                continue
        # Obter sufixo de empresa
        empresa = empresa_map.get(int(numero)) if empresa_map else None
        sufixo = f" - {empresa}" if empresa else ''
        novo_nome = f"{current_year}_{numero}{sufixo}.xml"
        novo_caminho = os.path.join(pasta, novo_nome)
        os.rename(entry.path, novo_caminho)
        arquivos_por_nota[int(numero)] = [novo_caminho]

    # Processar PDFs: extrair número via prefixo ou fallback regex
    for entry in pdf_entries:
        numero = None
        try:
            # Extrai texto completo do PDF
            reader = PdfReader(entry.path)
            text = ''.join(page.extract_text() or '' for page in reader.pages)
            # Procura número interno após 'Número da NFS-e' (flexível, sem acento e ignore case)
            m = re.search(r'n[uú]mero da nfs-?e[:\s]*([0-9]+)', text, re.IGNORECASE)
            if m:
                numero = m.group(1)
            else:
                logger.warning(f"Regex não encontrou número no PDF {entry.name}")
                # Segunda tentativa com expressão mais abrangente
                m = re.search(r'nfs-?e[\s\:]*([0-9]+)', text, re.IGNORECASE)
                if m:
                    numero = m.group(1)
                    logger.info(f"Número encontrado com regex alternativo: {numero}")
                else:
                    raise ValueError('número interno não encontrado')
        except Exception as e:
            logger.warning(f"Não foi possível extrair número interno do PDF {entry.name}: {e}")
            # Salvando conteúdo para debug em caso de falha
            try:
                with open(f"/tmp/pdf_content_{entry.name.replace('.pdf', '.txt')}", "w", encoding="utf-8") as f:
                    f.write(text[:2000])  # Salvando os primeiros 2000 caracteres para debug
                logger.info(f"Primeiros 2000 caracteres do PDF salvos para debug")
            except:
                pass
            continue
            
        # Dado que encontramos o número, renomeamos o arquivo
        empresa = empresa_map.get(int(numero)) if empresa_map else None
        sufixo = f" - {empresa}" if empresa else ''
        novo_nome = f"{current_year}_{numero}{sufixo}.pdf"
        novo_caminho = os.path.join(pasta, novo_nome)
        
        # Importante: realmente renomear o arquivo fisicamente
        os.rename(entry.path, novo_caminho)
        logger.info(f"PDF renomeado: {entry.name} -> {novo_nome}")
        
        # Adicionar à lista de arquivos para essa nota
        arquivos_por_nota.setdefault(int(numero), []).append(novo_caminho)
    
    logger.info(f"Arquivos renomeados e mapeados por nota: {arquivos_por_nota}")
    return arquivos_por_nota


def ler_informacoes_excel(arquivo_excel):
    try:
        df = pd.read_excel(arquivo_excel, engine='openpyxl')
        logger.info(f"Arquivo Excel lido com sucesso. Colunas encontradas: {df.columns.tolist()}")
        
        # Verifica colunas necessárias - usando os nomes exatos das colunas como aparecem no Excel
        expected = ['NÚMERO DAS NOTAS', 'E-MAIL\nResponsável', 'Nome Reduzido']
        logger.info(f"Procurando pelas colunas: {expected}")
        
        for col in expected:
            if col not in df.columns:
                logger.error(f"Coluna '{col}' não encontrada no Excel. Colunas encontradas: {df.columns.tolist()}")
                return []
        
        logger.info("Todas as colunas necessárias foram encontradas.")
        
        # Tratar e converter
        df['NÚMERO DAS NOTAS'] = pd.to_numeric(df['NÚMERO DAS NOTAS'], errors='coerce')
        df = df.dropna(subset=['NÚMERO DAS NOTAS'])
        df['NÚMERO DAS NOTAS'] = df['NÚMERO DAS NOTAS'].astype(int)
        
        # Construir lista de dicionários - mapeando as colunas para os campos esperados pelo código
        informacoes = []
        for _, row in df.iterrows():
            informacoes.append({
                'Numero': int(row['NÚMERO DAS NOTAS']),
                'Email': str(row['E-MAIL\nResponsável']).strip() if pd.notna(row['E-MAIL\nResponsável']) else '',
                'Empresa_reduzido': str(row['Nome Reduzido']).strip() if pd.notna(row['Nome Reduzido']) else ''
            })
        
        logger.info(f"Processadas {len(informacoes)} linhas do Excel.")
        return informacoes
        
    except Exception as e:
        logger.error(f"Erro ao ler arquivo Excel: {e}")
        return []


def ler_layout_email(arquivo_layout):
    try:
        return open(arquivo_layout, 'r', encoding='utf-8').read()
    except Exception as e:
        logger.error(f'Erro ao ler layout de e-mail: {e}')
        return ''

def ler_historico_envio(account, empresas_validas):
    """Lê os e-mails enviados nos últimos 3 anos, filtra pelo padrão de anexo e empresas válidas."""
    historico = []
    data_limite = datetime.now(ZoneInfo("America/Sao_Paulo")) - timedelta(days=3*365)
    padrao = re.compile(r'(\d{4})_(\d+) - (.+)\.pdf')
    vistos = set()
    try:
        mails = account.sent.filter(datetime_sent__gte=data_limite).order_by('-datetime_sent')
        for msg in mails:
            if msg.subject in vistos:
                continue
            vistos.add(msg.subject)
            for att in msg.attachments or []:
                nome = getattr(att, 'name', '')
                m = padrao.match(nome)
                if m and m.group(3) in empresas_validas:
                    destinatarios = [r.email_address for r in msg.to_recipients or []]
                    historico.append({
                        'assunto': msg.subject,
                        'data_envio': msg.datetime_sent,
                        'empresa': m.group(3),
                        'destinatarios': destinatarios
                    })
                    break
    except Exception as e:
        logger.error(f"Erro ao ler histórico de envio: {e}")
    return historico

# Script principal
if __name__ == '__main__':
    logger.info('Iniciando automação de e-mails...')
    # Parse de argumentos
    parser = argparse.ArgumentParser(description='Automação de e-mails NFSE')
    parser.add_argument('--historico', action='store_true', help='Gerar relatório de histórico de envios')
    args = parser.parse_args()

    # 1. Ler Excel para obter mapeamento empresa
    informacoes = ler_informacoes_excel(ARQUIVO_EXCEL_INFO)
    empresa_map = {info['Numero']: info['Empresa_reduzido'] for info in informacoes}
    # 2. Renomear e mapear arquivos na pasta de entrada com base no mapeamento
    arquivos_por_nota = renomear_arquivos(PASTA_ENTRADA, empresa_map)
    if not arquivos_por_nota:
        logger.warning('Nenhum arquivo PDF ou XML encontrado na pasta de entrada.')

    # 3. Layout
    layout = ler_layout_email(LAYOUT_EMAIL_FILE)
    if not layout:
        logger.error('Layout de e-mail vazio.')
        exit(1)

    # 4. Conectar Exchange
    manager = ExchangeEmailManager()
    setup = manager.connect()
    if not setup:
        logger.error('Falha ao conectar ao Exchange.')
        exit(1)

    # Se solicitou só histórico, gera e sai
    if args.historico:
        empresas_validas = set(info['Empresa_reduzido'] for info in informacoes)
        historico = ler_historico_envio(manager.account, empresas_validas)
        if historico:
            df_hist = pd.DataFrame(historico)
            arquivo_hist = 'historico_envios.xlsx'
            df_hist.to_excel(arquivo_hist, index=False)
            logger.info(f"Histórico de envios salvo em {arquivo_hist}")
        else:
            logger.warning('Nenhum histórico de envios encontrado.')
        exit(0)

    # 5. Criar rascunhos
    count_sucesso = 0
    count_sem_arquivos = 0
    count_email_invalido = 0
    
    for info in informacoes:
        numero = int(info['Numero'])
        email_dest = info['Email']
        # Ignorar email inválido
        if not isinstance(email_dest, str) or not email_dest.strip():
            logger.debug(f"Email inválido ou ausente para nota {numero}: '{email_dest}'")
            count_email_invalido += 1
            continue

        # Obter arquivos já mapeados por número da nota
        arquivos = arquivos_por_nota.get(numero, [])
        if not arquivos:
            logger.debug(f'Nenhum arquivo encontrado para nota {numero} (provavelmente já enviada).')
            count_sem_arquivos += 1
            continue

        # Definir assunto
        assunto = "Nota Fiscal La'Fioravanso Consultoria Empresarial"
        # Calcular saudação de acordo com horário de Brasília (GMT-3)
        sp_tz = ZoneInfo("America/Sao_Paulo")
        hora = datetime.now(sp_tz).hour
        if hora < 12:
            saudacao = "Bom dia"
        elif hora < 18:
            saudacao = "Boa tarde"
        else:
            saudacao = "Boa noite"
        # Substituir placeholders no layout
        corpo = layout
        corpo = corpo.replace('{{SAUDACAO}}', saudacao)
        corpo = corpo.replace('{{ARQUIVO}}', ', '.join(os.path.basename(a) for a in arquivos))
        corpo = corpo.replace('{{NUMERO_NOTA}}', str(numero))

        # Remover assinatura fixa (se houver) para permitir assinatura padrão do Outlook
        # Exemplo: se houver uma assinatura fixa no layout, remova-a ou comente a linha abaixo
        # corpo = corpo.replace('{{ASSINATURA}}', 'Assinatura fixa aqui')  # Remova esta linha se existir

        success = manager.create_draft_with_attachments(
            to_email=email_dest,
            subject=assunto,
            body_html=corpo,
            attachment_paths=arquivos
        )
        if success:
            count_sucesso += 1
            logger.info(f"Rascunho criado com sucesso para nota {numero}")
        else:
            logger.error(f"Falha ao criar rascunho para nota {numero}")
            count_email_invalido += 1

    # Relatório final mais detalhado
    total_notas = len(informacoes)
    logger.info(f'=== RESUMO DA EXECUÇÃO ===')
    logger.info(f'Total de notas processadas: {total_notas}')
    logger.info(f'Rascunhos criados com sucesso: {count_sucesso}')
    logger.info(f'Notas sem arquivos (provavelmente já enviadas): {count_sem_arquivos}')
    logger.info(f'Notas com email inválido ou erro de criação: {count_email_invalido}')
    logger.info(f'Percentual de sucesso (notas com arquivos): {(count_sucesso / (count_sucesso + count_email_invalido) * 100):.1f}%' if (count_sucesso + count_email_invalido) > 0 else 'N/A')
#!/usr/bin/env python3
"""
exchange_manager.py
Classe para gerenciar conexões e e-mails do Exchange
"""
import os
import logging
from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv

# Importações para o Exchange Email
from exchangelib import Credentials, Account, DELEGATE, HTMLBody, Message, Mailbox, Configuration, FileAttachment
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
from exchangelib import EWSTimeZone

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('exchange_manager')

class ExchangeEmailManager:
    """Gerencia operações de e-mail usando a API Exchange"""

    def __init__(self):
        """Inicializa o gerenciador de e-mail Exchange"""
        load_dotenv()  # Carregar variáveis de ambiente do .env
        self.email = os.getenv("EMAIL_USUARIO")
        self.password = os.getenv("EMAIL_SENHA")
        self.server = os.getenv("EXCHANGE_SERVER")  # Corrigido nome da variável
        self.service_endpoint = os.getenv("EMAIL_SERVICE_ENDPOINT") # Endpoint EWS
        self.account = None
        self.tz = EWSTimeZone.localzone()

        if not all([self.email, self.password]):
             raise ValueError("EMAIL_USUARIO e EMAIL_SENHA devem ser definidos no arquivo .env")

        # Desabilitar verificação SSL se necessário (manter comentado se não usar cert auto-assinado)
        # BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter

        logger.info(f"ExchangeEmailManager inicializado para {self.email}")

    def connect(self) -> bool:
        """Estabelece conexão com a conta Exchange"""
        try:
            logger.info(f"Conectando à conta Exchange: {self.email}")
            credentials = Credentials(username=self.email, password=self.password)

            # Priorizar a conexão direta via endpoint EWS para maior velocidade
            if self.service_endpoint:
                logger.info(f"Conectando via endpoint EWS direto: {self.service_endpoint}")
                config = Configuration(service_endpoint=self.service_endpoint, credentials=credentials)
                self.account = Account(
                    primary_smtp_address=self.email,
                    config=config,
                    autodiscover=False,
                    access_type=DELEGATE
                )
            # Usar configuração de servidor sem autodiscover se endpoint não estiver disponível
            elif self.server:
                logger.info(f"Usando servidor Exchange configurado: {self.server}")
                config = Configuration(server=self.server, credentials=credentials)
                self.account = Account(
                    primary_smtp_address=self.email,
                    config=config,
                    autodiscover=False,
                    access_type=DELEGATE
                )
            # Última opção: usar autodiscover padrão (mais lento)
            else:
                logger.info("Nenhum endpoint ou servidor configurado. Tentando autodiscover padrão...")
                self.account = Account(
                    primary_smtp_address=self.email,
                    credentials=credentials,
                    autodiscover=True,
                    access_type=DELEGATE
                )

            # Testa a conexão
            logger.info(f"Pasta raiz: {self.account.root}")
            logger.info(f"Conexão com a conta Exchange estabelecida com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao conectar à conta Exchange: {str(e)}", exc_info=True)
            return False

    def create_draft_with_attachments(self, to_email: str, subject: str, body_html: str, attachment_paths: List[str]) -> bool:
        """
        Cria um e-mail de rascunho com anexos e corpo em HTML.

        Args:
            to_email: E-mail do destinatário.
            subject: Assunto do e-mail.
            body_html: Corpo do e-mail em HTML.
            attachment_paths: Lista de caminhos para os arquivos a serem anexados.

        Returns:
            bool: True se o rascunho foi criado com sucesso, False caso contrário.
        """
        try:
            if not self.account:
                logger.warning("Conta não conectada. Tentando conectar...")
                if not self.connect():
                    return False

            # Preparar lista de destinatários, suportando string com emails separados por ';' ou lista de emails
            if isinstance(to_email, str):
                emails = [e.strip() for e in to_email.split(';') if e.strip()]
            else:
                emails = list(to_email)
            recipients = [Mailbox(email_address=addr) for addr in emails]

            # Construir mensagem usando body_html
            message = Message(
                account=self.account,
                folder=self.account.drafts,
                subject=subject,
                body=HTMLBody(body_html),
                to_recipients=recipients
            )

            # Anexar arquivos
            for file_path in attachment_paths:
                try:
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    file_name = os.path.basename(file_path)
                    attachment = FileAttachment(name=file_name, content=file_content)
                    message.attach(attachment)
                    logger.info(f"Anexado arquivo: {file_name}")
                except FileNotFoundError:
                    logger.error(f"Erro: Arquivo de anexo não encontrado em {file_path}")
                    # Decide se continua sem o anexo ou retorna False
                    # return False # Descomente para falhar se um anexo não for encontrado
                except Exception as e:
                    logger.error(f"Erro ao anexar arquivo {file_path}: {str(e)}")
                    # return False # Descomente para falhar em qualquer erro de anexo

            # Salvar como rascunho
            message.save()

            logger.info(f"Rascunho de e-mail criado para {to_email} - Assunto: {subject}")
            return True

        except Exception as e:
            logger.error(f"Erro ao criar rascunho de e-mail para {to_email}: {str(e)}", exc_info=True)
            return False

    # Você pode adicionar aqui o método para ler e-mails enviados se necessário
    # def read_sent_emails(self, years=3): ...

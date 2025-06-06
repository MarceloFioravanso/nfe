# Automação NFSe - Projeto Limpo e Organizado

Este projeto contém dois sistemas principais:
1. **Automação de Emissão de NFSe** - Para emitir notas fiscais automaticamente
2. **Automação de E-mails** - Para enviar e-mails com notas fiscais anexadas

## 📁 Estrutura do Projeto (Após Limpeza - 06/06/2025)

### Scripts Principais
- `nfs_emissao_auto.py`: Automação completa de emissão de NFSe
- `email_automation.py`: Automação de envio de e-mails com anexos

### Módulos Core
- `exchange_manager.py`: Gerenciador de conexões Exchange
- `preencher_dados_servico.py`: Preenchimento de dados de serviço
- `busca_empresa.py`: Busca de empresas por CNPJ
- `preencher_tributos.py`: Preenchimento de tributos

### Configuração e Dados
- `requirements.txt`: Dependências do projeto
- `.env`: Variáveis de ambiente (credenciais)
- `layout_email.txt`: Template de e-mail
- `informacoes_notas.xlsx`: Dados das notas fiscais
- `entrada/`: Pasta para arquivos PDF e XML
- `logs/`: Logs e capturas de tela

### Arquivo
- `_archive/`: Arquivos antigos organizados por categoria
- `LIMPEZA_PROJETO.md`: Documentação da limpeza realizada

## Configuração
1. Crie um arquivo `.env` com as seguintes variáveis de ambiente:
   ```dotenv
   EMAIL_USUARIO=seu_email@exemplo.com
   EMAIL_SENHA=sua_senha
   # Opcional, caso use ews sem autodiscover:
   EMAIL_SERVER=servidor_ews.exemplo.com
   # Ou, se usar endpoint EWS:
   EMAIL_SERVICE_ENDPOINT=https://ews.exemplo.com/EWS/Exchange.asmx
   ```

2. Preencha o arquivo `informacoes_notas.xlsx` com as colunas:
   - `Numero`: Número da nota fiscal.
   - `Email`: E-mail do(s) destinatário(s). Para múltiplos, separe por `;`.
   - `Empresa (reduzido)`: Código ou nome reduzido da empresa (usado no sufixo de arquivos).

3. Coloque os arquivos PDF e XML na pasta `entrada/` antes de executar.

## Execução
1. Instale as dependências:
   ```bash
   pip install exchangelib python-dotenv pandas openpyxl PyPDF2
   ```

2. Execute o script principal:
   ```bash
   python email_automation.py
   ```

## Funcionalidades
- Renomeia arquivos PDF/XML adicionando prefixo `ANO_Numero - Empresa` usando o número interno do PDF (próximo a “Número da NFS-e”) ou do XML.
- Lê informações de `informacoes_notas.xlsx` (Número, Email, Empresa) para gerar rascunhos no Exchange.
- Suporta múltiplos destinatários separados por `;`.
- Gera rascunhos de e-mail com assunto, corpo via template (`layout_email.txt`) e anexos.
- (Opcional) Com `--historico`, gera relatório `historico_envios.xlsx` com envios dos últimos 3 anos.

# Automação de Emissão de Notas Fiscais (NFSe)

Este projeto também inclui um sistema para automatizar o processo de emissão de notas fiscais no sistema NFSe de Cachoeirinha.

## Automação NFSe - Principais Arquivos
- `nfs_emissao_auto.py`: Script principal para automação da emissão de NFSe.
- `busca_empresa.py`: Módulo especializado para busca e seleção de empresas por CNPJ.
- `.env`: Arquivo com as credenciais de acesso ao sistema NFSe (não incluído no repositório).
- `logs/`: Pasta onde são armazenados os logs e screenshots do processo.

## Novas Funcionalidades (Junho/2025)

### Integração com Excel
- Carrega dados do arquivo Excel para preenchimento automático do formulário
- Identifica a próxima nota a ser emitida (linha sem número de nota, mas com dados válidos)
- Atualiza automaticamente o Excel após emissão bem-sucedida da nota

### Busca de Empresas Otimizada
- Sistema robusto para busca de empresas por CNPJ ou nome
- Múltiplas estratégias para encontrar e selecionar empresas nos resultados
- Tratamento avançado de erros com interação manual quando necessário

### Captura de Número da Nota
- Extração automática do número da nota emitida
- Atualização do arquivo Excel com o número da nota recém emitida
- Criação automática de backups do Excel antes de qualquer modificação

## Configuração da Automação NFSe

1. Crie um arquivo `.env` com suas credenciais:
   ```dotenv
   NFS_URL=https://nfse-cachoeirinha.atende.net/autoatendimento/servicos/nfse?redirected=1
   CPF_CNPJ=seu_cpf_ou_cnpj
   SENHA=sua_senha
   ```

2. Instale as dependências necessárias:
   ```bash
   pip install -r requirements.txt
   ```

3. Execute o script principal:
   ```bash
   python nfs_emissao_auto.py
   ```

## Fluxo de Automação
1. Carregamento dos dados do Excel
2. Identificação da próxima nota a emitir
3. Login no sistema NFSe
4. Navegação até a página de emissão
5. Preenchimento automático com dados do Excel
6. Emissão da nota fiscal
7. Extração do número da nota emitida
8. Atualização do Excel com o número da nota

## Observações
- O sistema requer interação manual apenas para solucionar CAPTCHAs
- Screenshots são salvos em cada etapa do processo para facilitar o diagnóstico
- Logs detalhados são gerados para acompanhamento e depuração

## Script de Emissão Automática (nfs_emissao_auto.py)

### Funcionalidades
- Login automático no sistema NFSe
- Navegação pela área fiscal
- Emissão de nota fiscal
- Capturas de tela em cada etapa para monitoramento
- Tratamento de erros e situações inesperadas

### Fluxo de Automação
1. Inicialização e configuração do navegador
2. Acesso à página inicial do sistema NFSe
3. Login no sistema com CPF/CNPJ e senha
4. Clicar no botão "Acessar" para entrar na área fiscal
5. Aguardar redirecionamento para a página de destino
6. Fechar o aviso na página de destino, se houver
7. Clicar no botão "Emitir Nota Fiscal" para iniciar o processo de emissão
8. Clicar no botão "Próximo" para avançar no fluxo de emissão
9. Selecionar "Pessoa Jurídica" como tipo do tomador

### Configuração
1. Certifique-se de que o arquivo `.env` tenha as seguintes variáveis adicionais:
   ```dotenv
   NFS_URL=https://nfse-cachoeirinha.atende.net/autoatendimento/servicos/nfse?redirected=1
   CPF_CNPJ=seu_cpf_ou_cnpj
   SENHA=sua_senha
   ```

2. Certifique-se de ter as pastas necessárias:
   - `logs/`
   - `logs/imagens/`
   - `logs/html/`

### Execução
Execute o script de emissão automática:
```bash
python nfs_emissao_auto.py
```

**Nota:** O script requer interação manual para resolver CAPTCHAs quando apresentados.

## Logs e Monitoramento
O script gera logs detalhados e capturas de tela em cada etapa crítica, facilitando o diagnóstico de problemas. Os logs são salvos em:
- `logs/nfse_emissao_[DATA]_[HORA].log` - Log textual detalhado
- `logs/imagens/` - Capturas de tela do processo
- `logs/html/` - Código HTML das páginas para análise
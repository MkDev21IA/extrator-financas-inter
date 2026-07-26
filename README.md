# 🏦 Extrator de Finanças Inter (Local Data Pipeline)

> **Pipeline de extração local para automação de extratos do Banco Inter. Desenvolvido para garantir privacidade total dos dados financeiros, sem depender de APIs de terceiros, planilhas manuais ou plataformas em nuvem.**

Nenhuma empresa terceirizada precisa ter acesso ao seu extrato bancário. Este projeto utiliza Engenharia de Dados local para acessar sua conta (via QR Code seguro), extrair os dados, processá-los e disponibilizá-los em um painel de Business Intelligence (Metabase) rodando inteiramente na sua máquina.

## ⚙️ Arquitetura do Projeto

1. **Camada de Extração (Playwright):** Um robô com navegação isolada acessa o Internet Banking de forma segura, contornando a ausência de APIs abertas e exibindo uma interface de status enquanto extrai o CSV em background.
2. **Camada ETL (Pandas):** Limpeza dos dados brutos do banco, normalização de datas e geração de Hashes MD5 para garantir que transações não sejam duplicadas no banco de dados (Idempotência).
3. **Motor de Regras Relacional (SQLite) & Parcelamento:** 
* Sistema interativo via terminal (CLI) para categorização automática.
* Módulo isolado (manage_portions.py com suporte a loop) para desmembrar compras parceladas avulsas no banco.
4. **Camada Analítica (Metabase via Docker):** Painel de BI plugado no banco de dados local para geração de insights orçamentários avançados.

## 🚀 Como usar

### Pré-requisitos
* Python 3.10+
* Windows Subsystem for Linux (WSL) ou ambiente Linux/macOS nativo
* Docker (para subir o painel analítico do Metabase)

### 1. Instalação
Clone este repositório e acesse a pasta:
```bash
git clone [https://github.com/seu-usuario/extrator-financas-inter.git](https://github.com/seu-usuario/extrator-financas-inter.git)
cd extrator-financas-inter
```

Crie e ative um ambiente virtual: 
```bash
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
```

Instale as dependências e os binários do navegador para automação: 
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Execução do Pipeline
Basta rodar o orquestrador principal. Ele guiará você por todo o processo (Extração, ETL e Treinamento) no terminal:
```bash
python main.py
```
*(Dica: Se estiver utilizando o Windows com WSL, você pode criar um arquivo `.bat` apontando para o script de inicialização local para automatizar a chamada — Tem exemplos na pasta exemplos_execucao).*

### 3. Gerenciamento de Parcelamentos Manuais
Caso precise desmembrar uma compra parcelada:

1. Pegue o `id_hash` da transação no Metabase.
2. Execute o atalho correspondente: `parcelar.bat` (Windows) ou `./parcelar.sh` (Linux/macOS).
3. Cole o hash e informe o número de parcelas (o script aceita múltiplos hashes em sequência).


### 4. Visualização (Metabase)
Com o banco de dados (`meu_dinheiro.db`) alimentado pelo script, suba o container do Metabase mapeando a pasta atual do seu projeto:

```bash
docker run -d -p 3000:3000 \
  -v "$(pwd)":/dados_projeto \
  --name metabase_financas \
  metabase/metabase:latest
```

1. Abra o navegador e acesse `http://localhost:3000`.
2. Crie sua conta de administrador local (funciona offline).
3. Adicione o seu banco de dados selecionando o tipo **SQLite**.
4. No campo **Caminho do Arquivo (Filename)**, digite o caminho interno mapeado no container: `/dados_projeto/meu_dinheiro.db`.

## 🔒 Segurança e Privacidade
O projeto roda **100% offline** (exceto pela conexão estrita com o site do banco para o download). Seus dados nunca saem da sua máquina. O Metabase é conteinerizado para ler exclusivamente o arquivo SQLite local gerado na sua pasta.
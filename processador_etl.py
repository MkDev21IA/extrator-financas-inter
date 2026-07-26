import pandas as pd
import hashlib
import sqlite3
import os
import glob
import numpy as np

def setup_database_com_regras(db_path="meu_dinheiro.db"):
    print("[*] Verificando estrutura do banco e motor de regras...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabela de Transações OFICIAL (Agora com a coluna categoria)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transacoes (
        id_hash TEXT PRIMARY KEY,
        data_transacao DATE,
        descricao TEXT,
        valor NUMERIC,
        saldo_conta NUMERIC,
        categoria TEXT,
        tipo_conta TEXT
    )
    """)
    
    # Tabela de Regras
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS regras_categorizacao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        palavra_chave TEXT NOT NULL UNIQUE, -- Unique evita duplicar a mesma regra
        categoria_destino TEXT NOT NULL,
        tipo_fluxo TEXT NOT NULL CHECK(tipo_fluxo IN ('ENTRADA', 'SAIDA'))
    )
    """)
    
    # Inserindo regras semente
    regras_iniciais = [
        # SAÍDAS (valor negativo)
        ('IFOOD', 'Alimentação', 'SAIDA'),
        ('UBER', 'Transporte', 'SAIDA'),
        ('99APP', 'Transporte', 'SAIDA'),
        ('AMAZON', 'Assinaturas/Compras', 'SAIDA'),
        ('PAG*MERCADOPAGO', 'Serviços', 'SAIDA'),
        ('FATURA','Transferência Interna', 'SAIDA'),
        # ENTRADAS (valor positivo)
        ('RESGATE','Resgate de Investimento','ENTRADA'),
        ('PROV', 'Rendimentos B3', 'ENTRADA'),
        ('RENDIMENTO', 'Rendimentos', 'ENTRADA'),
        ('CASHBACK', 'Estorno/Cashback', 'ENTRADA')
    ]
    
    cursor.executemany("""
    INSERT OR IGNORE INTO regras_categorizacao (palavra_chave, categoria_destino, tipo_fluxo)
    VALUES (?, ?, ?)
    """, regras_iniciais)
    
    conn.commit()
    conn.close()

def processar_todos_csvs(diretorio="./downloads"):
    arquivos = glob.glob(os.path.join(diretorio, "*.csv"))
    if not arquivos: return None
    lista_df = []

    for arq in arquivos:
        with open(arq, 'r', encoding='utf-8', errors='ignore') as f:
            primeira_linha = f.readline().strip()

        if "Extrato" in primeira_linha or "Conta" in primeira_linha:
            df = pd.read_csv(arq, sep=';', skiprows=6, header=None, names=['data_transacao', 'descricao', 'valor', 'saldo_conta'], encoding='utf-8')
            df['tipo_conta'] = 'CONTA'
            df['valor'] = df['valor'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
            
        elif '"Data"' in primeira_linha or 'Data' in primeira_linha:
            df = pd.read_csv(arq, sep=',', encoding='utf-8')
            df = df.rename(columns={'Data': 'data_transacao', 'Lançamento': 'descricao', 'Valor': 'valor'})
            df['saldo_conta'] = np.nan
            df['tipo_conta'] = 'CARTAO'
            df['valor'] = df['valor'].astype(str).str.replace('R$ ', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float) * -1
            df = df[['data_transacao', 'descricao', 'valor', 'saldo_conta', 'tipo_conta']]
        else:
            continue

        df['data_transacao'] = pd.to_datetime(df['data_transacao'], format='%d/%m/%Y', errors='coerce').dt.strftime('%Y-%m-%d')
        df = df.dropna(subset=['data_transacao', 'valor'])
        df['id_hash'] = df.apply(lambda row: hashlib.md5(f"{row['data_transacao']}{row['descricao']}{row['valor']}".encode('utf-8')).hexdigest(), axis=1)
        lista_df.append(df)

    return pd.concat(lista_df, ignore_index=True) if lista_df else None

def aplicar_regras_categorizacao(df, db_path="meu_dinheiro.db"):
    print("[*] Aplicando motor de categorização...")
    conn = sqlite3.connect(db_path)
    
    # Carrega as regras do banco para o Pandas
    df_regras = pd.read_sql("SELECT palavra_chave, categoria_destino, tipo_fluxo FROM regras_categorizacao", conn)
    conn.close()
    
    # Cria a coluna categoria com valor padrão
    df['categoria'] = 'Não Categorizado'
    
    # Separa as regras por fluxo para evitar cruzamentos errados
    regras_saida = df_regras[df_regras['tipo_fluxo'] == 'SAIDA']
    regras_entrada = df_regras[df_regras['tipo_fluxo'] == 'ENTRADA']
    
    # Aplica regras de SAÍDA (Apenas onde valor < 0)
    for _, regra in regras_saida.iterrows():
        mascara_saida = (df['valor'] < 0) & (df['descricao'].str.contains(regra['palavra_chave'], case=False, na=False))
        df.loc[mascara_saida, 'categoria'] = regra['categoria_destino']
        
    # Aplica regras de ENTRADA (Apenas onde valor > 0)
    for _, regra in regras_entrada.iterrows():
        mascara_entrada = (df['valor'] > 0) & (df['descricao'].str.contains(regra['palavra_chave'], case=False, na=False))
        df.loc[mascara_entrada, 'categoria'] = regra['categoria_destino']
        
    print("[+] Categorização concluída. Amostra dos dados:")
    print(df[['descricao', 'valor', 'categoria']].head())
    return df

def carregar_dados_sqlite(df, db_path="meu_dinheiro.db"):
    print("[*] Iniciando conexão com o banco de dados SQLite...")
    conn = sqlite3.connect(db_path)
    
    # 1. Garantir que a tabela oficial existe com o Hash como Chave Primária
    conn.execute("""
    CREATE TABLE IF NOT EXISTS transacoes (
        id_hash TEXT PRIMARY KEY,
        data_transacao DATE,
        descricao TEXT,
        valor NUMERIC,
        saldo_conta NUMERIC,
        categoria TEXT,
        tipo_conta TEXT
    )
    """)
    
    # 2. Carregar o DataFrame limpo em uma tabela temporária (Staging)
    # if_exists='replace' garante que a staging table seja limpa a cada execução
    df.to_sql('staging_transacoes', conn, if_exists='replace', index=False)
    
    # 3. O Upsert: Inserir na tabela oficial apenas os hashes inéditos
    query_insert = """
    INSERT OR IGNORE INTO transacoes (id_hash, data_transacao, descricao, valor, saldo_conta, categoria, tipo_conta)
    SELECT id_hash, data_transacao, descricao, valor, saldo_conta, categoria, tipo_conta
    FROM staging_transacoes;
    """
    
    cursor = conn.cursor()
    cursor.execute(query_insert)
    linhas_inseridas = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"[+] Carga concluída com sucesso! {linhas_inseridas} transações inéditas adicionadas.")

if __name__ == "__main__":
    
    # Prepara a infraestrutura (Tabelas e Regras)
    setup_database_com_regras()

    # Processa os csvs
    df_bruto = processar_todos_csvs("./downloads")
    
    if df_bruto is None:
        print("[X] Erro: Nenhum CSV válido encontrado.")
    else:
        try:
            # Categorização
            df_categorizado = aplicar_regras_categorizacao(df_bruto)
            carregar_dados_sqlite(df_categorizado)
            
        except Exception as e:
            print(f"[X] Erro crítico na carga: {e}")
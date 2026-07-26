import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta  # Para somar meses facilmente
import hashlib

def parcelar_transacao_manual(id_hash_original, num_parcelas):
    conn = sqlite3.connect("meu_dinheiro.db")
    cursor = conn.cursor()
    
    # 1. Busca a transação original
    cursor.execute("SELECT data_transacao, descricao, valor, tipo_conta, categoria FROM transacoes WHERE id_hash = ?", (id_hash_original,))
    transacao = cursor.fetchone()
    
    if not transacao:
        print("[X] Transação não encontrada!")
        conn.close()
        return

    data_str, desc, valor_total, tipo_conta, categoria = transacao
    
    # 2. Calcula o valor de cada parcela
    valor_parcela = valor_total / num_parcelas
    data_base = datetime.strptime(data_str, "%Y-%m-%d") # Ajuste para o formato da sua data no banco
    
    print(f"[*] Parcelando '{desc}' de R$ {valor_total:.2f} em {num_parcelas}x de R$ {valor_parcela:.2f}...")

    # 3. Atualiza a primeira parcela na transação original (adicionando (1/X) na descrição)
    desc_parcelada_1 = f"{desc} (1/{num_parcelas})"
    cursor.execute("""
        UPDATE transacoes 
        SET valor = ?, descricao = ? 
        WHERE id_hash = ?
    """, (valor_parcela, desc_parcelada_1, id_hash_original))

    # 4. Cria as transações futuras para os próximos meses
    for i in range(2, num_parcelas + 1):
        nova_data = data_base + relativedelta(months=(i - 1))
        nova_data_str = nova_data.strftime("%Y-%m-%d")
        nova_desc = f"{desc} ({i}/{num_parcelas})"
        
        # Gera um hash único para a parcela futura
        novo_hash = hashlib.sha256(f"{nova_data_str}{nova_desc}{valor_parcela}{tipo_conta}".encode()).hexdigest()
        
        cursor.execute("""
            INSERT OR IGNORE INTO transacoes (id_hash, data_transacao, descricao, valor, tipo_conta, categoria, saldo_conta)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (novo_hash, nova_data_str, nova_desc, valor_parcela, tipo_conta, categoria))

    conn.commit()
    conn.close()
    print("[+] Parcelamento aplicado com sucesso no banco de dados!")

if __name__ == "__main__":
    conn = sqlite3.connect("meu_dinheiro.db")
    cursor = conn.cursor()
    
    print("===================================================")
    print("         GERENCIADOR DE PARCELAMENTOS")
    print("===================================================\n")
    
    # Lista as últimas 15 transações para facilitar a visualização do ID Hash
    cursor.execute("""
        SELECT id_hash, data_transacao, descricao, valor 
        FROM transacoes 
        ORDER BY data_transacao DESC 
        LIMIT 15
    """)
    transacoes = cursor.fetchall()
    conn.close()
    
    if not transacoes:
        print("[!] Nenhuma transação encontrada no banco de dados.")
    else:
        print("Últimas transações registradas:")
        print("-" * 65)
        for t in transacoes:
            h, data, desc, val = t
            print(f"Data: {data} | Valor: R$ {val:.2f} | Desc: {desc}")
            print(f"ID (hash): {h}")
            print("-" * 65)
        
        try:
            escolha_hash = input("\nCole o ID_HASH completo da transação que deseja parcelar (ou 'S' para sair): ").strip()
            if escolha_hash.upper() == 'S':
                exit()
            
            num = int(input("Informe o número total de parcelas (ex: 5): ").strip())
            
            parcelar_transacao_manual(escolha_hash, num)
            
        except Exception as e:
            print(f"\n[X] Erro ao processar o parcelamento: {e}")
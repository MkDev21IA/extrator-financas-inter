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
    print("===================================================")
    print("         GERENCIADOR DE PARCELAMENTOS")
    print("===================================================\n")
    print("Dica: Obtenha o id_hash diretamente pelo Metabase.\n")
    
    while True:
        escolha_hash = input("Cole o ID_HASH da transação (ou 'S' para sair): ").strip()
        
        if escolha_hash.upper() == 'S':
            print("\n[*] Encerrando o gerenciador de parcelamentos...")
            break
        
        if not escolha_hash:
            print("[!] O ID_HASH não pode estar vazio. Tente novamente.\n")
            continue
            
        try:
            num = int(input("Informe o número total de parcelas (ex: 5): ").strip())
            if num <= 1:
                print("[!] O número de parcelas deve ser maior que 1.\n")
                continue
                
            parcelar_transacao_manual(escolha_hash, num)
            print("-" * 50)
            
        except ValueError:
            print("[X] Entrada inválida. Digite um número inteiro para as parcelas.\n")
        except Exception as e:
            print(f"\n[X] Erro ao processar o parcelamento: {e}\n")
        
        print() # Espaço para a próxima interação do loop
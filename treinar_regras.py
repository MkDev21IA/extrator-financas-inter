import sqlite3
import pandas as pd

def treinar_motor():
    conn = sqlite3.connect("meu_dinheiro.db")
    cursor = conn.cursor()
    
    # Agora buscamos o id_hash para poder fazer classificações cirúrgicas
    query = """
    SELECT id_hash, data_transacao, descricao, valor, tipo_conta 
    FROM transacoes 
    WHERE categoria = 'Não Categorizado'
    ORDER BY data_transacao DESC
    """
    df_orfaos = pd.read_sql(query, conn)
    
    if df_orfaos.empty:
        print("[+] Excelente! Zero transações órfãs. O motor está 100% treinado.")
        conn.close()
        return

    print(f"\n[*] Encontradas {len(df_orfaos)} transações órfãs.")
    print("Ações: [R]egra universal | [M]anual (só esta) | [I]gnorar (Avulso) | [P]ular")
    print("-" * 65)
    
    for _, row in df_orfaos.iterrows():
        cursor.execute("SELECT categoria FROM transacoes WHERE id_hash = ?", (row['id_hash'],))
        status_atual = cursor.fetchone()[0]
        if status_atual != 'Não Categorizado':
            continue
        print(f"\n[{row['tipo_conta']}] Data: {row['data_transacao']} | Valor: R$ {row['valor']:.2f}")
        print(f"Desc: {row['descricao']}")
        
        acao = input("Escolha [R/M/I/P] ou [S] para Sair: ").strip().upper()
        
        # 0. SAIR (Fecha o banco de forma limpa e encerra o script)
        if acao == 'S':
            print("[*] Saindo e salvando alterações...")
            break

        # 1. PULAR (Não faz nada, vai perguntar de novo na próxima)
        if acao == 'P' or acao == '':
            continue
            
        # 2. IGNORAR (Marca como Avulso para sair da fila de órfãos)
        elif acao == 'I':
            cursor.execute("UPDATE transacoes SET categoria = 'Avulso' WHERE id_hash = ?", (row['id_hash'],))
            conn.commit()
            print(" -> Marcado como 'Avulso'.")
            
        # 3. MANUAL (Você digita a categoria, mas NÃO cria uma regra futura)
        elif acao == 'M':
            cat = input("  Digite a categoria (APENAS para esta transação): ").strip()
            cursor.execute("UPDATE transacoes SET categoria = ? WHERE id_hash = ?", (cat, row['id_hash']))
            conn.commit()
            print(f" -> Classificado pontualmente como '{cat}'.")
            
        # 4. REGRA (Cria a palavra-chave e atualiza todo o histórico passado e futuro)
        elif acao == 'R':
            palavra = input("  Palavra-chave (ex: UBER, PAGARME): ").strip().upper()
            cat = input("  Categoria destino: ").strip()
            fluxo = 'ENTRADA' if row['valor'] > 0 else 'SAIDA'
            
            # Insere a regra no motor
            cursor.execute("""
            INSERT OR IGNORE INTO regras_categorizacao (palavra_chave, categoria_destino, tipo_fluxo)
            VALUES (?, ?, ?)
            """, (palavra, cat, fluxo))
            
            # Atualiza o banco (essa transação e qualquer outra antiga que bata com a regra)
            operador = ">" if fluxo == "ENTRADA" else "<"
            cursor.execute(f"""
                UPDATE transacoes 
                SET categoria = ? 
                WHERE categoria = 'Não Categorizado' 
                AND valor {operador} 0 
                AND descricao LIKE ?
            """, (cat, f"%{palavra}%"))
            
            conn.commit()
            print(f" -> Regra '{palavra}' criada e aplicada no banco de dados!")
            
        else:
            print(" -> Comando não reconhecido. Pulando...")
            
    conn.close()
    print("\n[*] Sessão de treinamento finalizada!")

if __name__ == "__main__":
    treinar_motor()
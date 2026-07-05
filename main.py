import subprocess
import sys
import os

def rodar_script_com_input(nome_script, entrada_usuario=None):
    """Executa um script python interativo passando dados para o stdin se necessário."""
    try:
        if entrada_usuario:
            # Injeta a escolha do usuário diretamente no fluxo do terminal do script filho
            resultado = subprocess.run(
                [sys.executable, nome_script],
                input=entrada_usuario,
                text=True,
                check=True
            )
        else:
            resultado = subprocess.run(
                [sys.executable, nome_script],
                check=True
            )
        return resultado.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"[X] Erro ao executar {nome_script}: {e}")
        return False

def pipeline_principal():
    print("=" * 60)
    print("      INICIANDO PIPELINE DE AUTOMAÇÃO FINANCEIRA")
    print("=" * 60)
    
    # 1. O novo menu blindado contra erros de digitação
    print("\nEscolha o período de extração:")
    print("[ A ] 7 dias")
    print("[ B ] 15 dias")
    print("[ C ] 30 dias")
    print("[ D ] 90 dias")
    
    opcao = input("\nDigite a letra correspondente: ").strip().upper()
    
    # Dicionário que traduz a letra do usuário para o texto exato que o site do Inter exige
    mapa_periodos = {
        'A': '7 dias',
        'B': '15 dias',
        'C': '30 dias',
        'D': '90 dias'
    }
    
    # Se digitar uma letra inválida, o sistema assume '7 dias' por segurança para não quebrar
    periodo = mapa_periodos.get(opcao, '7 dias')
    print(f"\n[*] Período validado: {periodo}")
    
    # 2. Executa o Crawler (passando o período já formatado perfeitamente)
    print("\n[PASSO 1/3] Ativando Crawler do Banco Inter...")
    if not rodar_script_com_input("crawler_inter.py", entrada_usuario=f"{periodo}\n"):
        print("[X] Pipeline abortado devido a falha no Crawler.")
        return

    # 3. Executa o Processador ETL
    print("\n[PASSO 2/3] Iniciando Processamento ETL e Categorização...")
    if not rodar_script_com_input("processador_etl.py"):
        print("[X] Pipeline abortado devido a falha na ETL.")
        return

    # 4. Pergunta se deseja realizar o treinamento de regras agora
    print("\n[PASSO 3/3] Validação de Transações Órfãs")
    treinar = input("Deseja rodar o motor de treinamento de regras agora? (S/N): ").strip().upper()
    
    if treinar == 'S':
        rodar_script_com_input("treinar_regras.py")
    else:
        print("[*] Treinamento pulado. O banco está pronto para consulta no Metabase.")
        
    print("\n" + "=" * 60)
    print("            PIPELINE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)

if __name__ == "__main__":
    # Garante que o ambiente virtual está ativo ou usa o interpretador corrente
    pipeline_principal()
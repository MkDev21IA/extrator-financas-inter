import os
from playwright.sync_api import sync_playwright

def rodar_crawler(periodo_escolhido):
    os.makedirs("./downloads", exist_ok=True)
    with sync_playwright() as p:
        print("[*] Iniciando o modo Widget (Apenas QR Code)...")
        
        # 1. Configurando o Chromium para parecer um app flutuante
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--app=https://contadigital.inter.co',  # Remove abas e barra de URL
                '--window-size=500,750',                # Tamanho da janela
                '--window-position=500,150'             # Tenta centralizar na tela
            ]
        )
        
        # 2. Forçando o site a respeitar o tamanho do nosso widget
        context = browser.new_context(
            viewport={'width': 500, 'height': 750}
        )
        page = context.new_page()

        # Como usamos o --app, o site já deve carregar, mas o goto garante o fluxo
        page.goto("https://contadigital.inter.co")
        
        print("\n[!] Aponte a câmera para o QR Code na janela flutuante.")
        
        try:
            # Espera carregar a área logada
            page.wait_for_selector('text="Conta Digital"', timeout=90000) 
            print("[*] Login detectado com sucesso!")
            
            # 3. Esconde a interface visual pro usuário
            print("[*] Ocultando a interface. O robô assumiu em background...")
            page.evaluate("document.body.style.visibility = 'hidden';")
            page.evaluate("document.body.style.backgroundColor = '#121212';") # Fundo escuro
            
        except Exception as e:
            print("[X] Tempo esgotado ou erro:", e)
            browser.close()
            return

        # 1. Navegação via Menu Superior (Hover)
        page.hover("text='Conta Digital'")
        page.click("text='Extrato'")

        # 2. Abrindo o filtro de período
        print(f"[*] Configurando filtro para: {periodo_escolhido}...")
        page.get_by_test_id("filterChipsDates").click()

        # 3. Selecionando os 7 dias na mini-guia lateral
        page.click(f"text='{periodo_escolhido}'") 

        # 4. Aplicando o filtro
        page.click("text='Filtrar'")

        # Timeout para aguardar a página buscar os dados
        page.wait_for_timeout(2000)
        
        print("[*] Clicando em Exportar...")
        page.click("text='Exportar'") 

        print("[*] Selecionando o formato CSV...")
        
        # Marca a opção correspondente ao CSV.
        page.click("text='CSV'")

        print("[*] Confirmando e iniciando o download...")
        # Captura o download que será disparado ao clicar em "Continuar"
        with page.expect_download() as download_info:
            page.click("text='Continuar'")
            
        download = download_info.value

        # Define o caminho onde o arquivo bruto será salvo localmente
        nome_arquivo = periodo_escolhido.replace(' ', '')
        caminho_salvar = f"./downloads/extrato_ultimos_{nome_arquivo}.csv"
        download.save_as(caminho_salvar)

        print(f"[+] Sucesso absoluto! Extrato bruto salvo em: {caminho_salvar}")

        # Fechando o navegador após a conclusão
        print("[*] Finalizando a sessão do navegador local...")
        browser.close()

if __name__ == "__main__":
    print("\n--- Opções de Filtro do Inter ---")
    print("Opções válidas: '7 dias', '15 dias', '30 dias', '90 dias'")

    # Define qual período baixar antes de abrir o navegador
    escolha = input("Digite o período exato que deseja extrair: ")

    rodar_crawler(escolha)
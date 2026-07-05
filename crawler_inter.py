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
                '--window-size=1280,800',                # Tamanho da janela
                '--window-position=300,100'             # Tenta centralizar na tela
            ]
        )
        
        # 2. Forçando o site a respeitar o tamanho do nosso widget
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()

        # Como usamos o --app, o site já deve carregar, mas o goto garante o fluxo
        page.goto("https://contadigital.inter.co")
        
        print("\n[!] Aponte a câmera para o QR Code na janela flutuante.")
        
        try:
            # Espera carregar a área logada
            page.wait_for_selector('text="Conta Digital"', timeout=90000) 
            print("[*] Login detectado com sucesso!")

            # Levantando a cortina de privacidade animada.
            print("[*] Ocultando a interface visual. Iniciando animação de carregamento...")
            cortina_js = """
            // Passo 1: Injeta as regras de animação (CSS)
            let style = document.createElement('style');
            style.innerHTML = `
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
            `;
            document.head.appendChild(style);

            // Passo 2: Cria a tela preta de bloqueio
            let overlay = document.createElement('div');
            overlay.style.position = 'fixed';
            overlay.style.top = '0';
            overlay.style.left = '0';
            overlay.style.width = '100vw';
            overlay.style.height = '100vh';
            overlay.style.backgroundColor = '#0a0a0a'; 
            overlay.style.zIndex = '99999999';
            overlay.style.display = 'flex';
            overlay.style.alignItems = 'center';
            overlay.style.justifyContent = 'center';
            overlay.style.color = '#00FF00';
            overlay.style.fontFamily = 'monospace';
            overlay.style.pointerEvents = 'none'; // A mágica que deixa o robô clicar por baixo
            
            // Passo 3: Adiciona o anel giratório e o texto com efeito de pulso
            overlay.innerHTML = `
                <div style="display:flex; flex-direction:column; align-items:center;">
                    <div style="width: 60px; height: 60px; border: 5px solid #1a1a1a; border-top: 5px solid #00FF00; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 25px;"></div>
                    <div style="font-size: 24px; animation: pulse 2s infinite;">[ STATUS: EXTRAINDO DADOS ]</div>
                    <div style="font-size: 14px; color: #555; margin-top: 15px;">Operação em andamento pelo robô. Não feche a janela...</div>
                </div>
            `;
            document.body.appendChild(overlay);
            """
            page.evaluate(cortina_js)

            # Fôlego para o carregamento dos componentes assíncronos do dashboard
            print("[*] Aguardando renderização completa (5s)...")
            page.wait_for_timeout(5000)

            print("[*] Navegando para o extrato...")

            # Tenta focar apenas no elemento que está de fato VISÍVEL na tela
            menu_conta = page.locator("text='Conta Digital'").locator("visible=true").first
            menu_conta.hover()

            # 1. Navegação via Menu Superior (Hover)
            page.click("text='Extrato'")

            # 2. Abrindo o filtro de período
            print(f"[*] Configurando filtro para: {periodo_escolhido}...")
            page.get_by_test_id("filterChipsDates").click()

            # 3. Selecionando o período na mini-guia lateral
            page.click(f"text='{periodo_escolhido}'") 

            # 4. Aplicando o filtro
            page.click("text='Filtrar'")

            # Timeout para aguardar a página buscar os dados
            page.wait_for_timeout(3000)
            
            print("[*] Clicando em Exportar...")
            page.click("text='Exportar'") 

            print("[*] Selecionando o formato CSV...")
            page.click("text='CSV'")

            print("[*] Confirmando e iniciando o download...")
            # Captura o download que será disparado ao clicar em "Continuar"
            with page.expect_download() as download_info:
                page.click("text='Continuar'")
                
            download = download_info.value

            # Define o caminho onde o arquivo bruto será salvo localmente
            nome_arquivo = periodo_escolhido.replace(' ', '')
            caminho_salvar = f"./downloads/extrato_{nome_arquivo}.csv"
            download.save_as(caminho_salvar)
            
            print(f"[+] Sucesso absoluto! Extrato salvo em: {caminho_salvar}")
        
        except Exception as e:
            print(f"\n[X] Falha crítica durante a automação do navegador: {e}")

        finally:
            # O bloco finally garante que o navegador feche mesmo se o script cair no except
            print("[*] Finalizando a sessão do navegador com segurança...")
            browser.close()

if __name__ == "__main__":
    # O crawler não exibe mais menus próprios. 
    # Ele apenas aguarda o "main.py" injetar silenciosamente o período validado.
    escolha = input()

    rodar_crawler(escolha)
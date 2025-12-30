# ==============================================================================
# Autora: Bruna Ferreira | GitHub: @brunafdev
# Projeto: Bot de Download Automático de Notas Fiscais (Selenium)
# Descrição: Acessa portal de terceiros, realiza login, filtra prestadores e baixa faturas/espelhos.
# ==============================================================================

import os
import time
import shutil
import glob
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÕES GERAIS ---
# URLs genéricas (Substitua pelas reais em variáveis de ambiente se for rodar localmente)
LOGIN_URL = os.getenv("URL_PORTAL_LOGIN", "https://portal-exemplo.com/login")
APROVACAO_URL = os.getenv("URL_PORTAL_BUSCA", "https://portal-exemplo.com/aprovacao")

# Credenciais via Variáveis de Ambiente (Segurança)
# Nunca deixe senhas fixas no código!
SEU_LOGIN = os.getenv("PORTAL_USER", "USUARIO_DEMO")
SUA_SENHA = os.getenv("PORTAL_PASS", "SENHA_DEMO")

# Caminhos Relativos (Funciona em qualquer computador)
BASE_PATH = os.path.join(os.getcwd(), "Arquivos_Download")
PASTA_ESPELHO = os.path.join(BASE_PATH, "Relatorios_Espelho")
PASTA_NOTAS = os.path.join(BASE_PATH, "Notas_PDF")

EXCEL_FILE_NAME = "lista_prestadores.xlsx"
EXCEL_FILE_PATH = os.path.join(os.getcwd(), EXCEL_FILE_NAME)
# -----------------------------

def limpar_string_arquivo(texto):
    """Remove caracteres proibidos do Windows para nomear arquivos"""
    return re.sub(r'[|*?:"<>/]', "", texto).strip()

def limpar_mes(texto_data):
    """Recebe 'Outubro/202X' e retorna apenas 'Outubro'"""
    if "/" in texto_data:
        return texto_data.split('/')[0].strip()
    return texto_data.strip()

def garantir_foco_janela(driver):
    """Garante que o navegador esteja ativo para receber comandos"""
    try:
        driver.minimize_window()
        driver.maximize_window()
    except: pass

def pressionar_esc_robusto(driver):
    """Fecha modais ou popups indesejados"""
    try:
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE)
        actions.perform()
    except: pass

def esperar_novo_arquivo(pasta, qtd_antes, ext=".pdf", timeout=60):
    """Aguarda o download terminar verificando a pasta"""
    inicio = time.time()
    while time.time() - inicio < timeout:
        arquivos = glob.glob(os.path.join(pasta, "*"))
        # Ignora arquivos temporários de download (.crdownload, .tmp)
        validos = [f for f in arquivos if os.path.isfile(f) and not f.endswith(('.crdownload', '.tmp'))]
        
        if len(validos) > qtd_antes:
            novo = max(validos, key=os.path.getmtime)
            # Verifica se o download terminou totalmente (extensão correta)
            if not novo.lower().endswith(ext):
                time.sleep(0.5)
                continue
            return novo
        time.sleep(1)
    return None

def mover_arquivo(origem, pasta_dest, nome_arquivo_final):
    """Move e renomeia o arquivo baixado para a pasta organizada"""
    if not os.path.exists(origem): return False
    
    if not os.path.exists(pasta_dest):
        os.makedirs(pasta_dest)
        
    destino_final = os.path.join(pasta_dest, nome_arquivo_final)
    
    # Evita sobrescrever arquivos com mesmo nome
    if os.path.exists(destino_final):
        base, ext = os.path.splitext(nome_arquivo_final)
        destino_final = os.path.join(pasta_dest, f"{base}_COPY_{int(time.time())}{ext}")

    try:
        shutil.move(origem, destino_final)
        print(f" -> Arquivo Organizado: {os.path.basename(destino_final)}")
        return True
    except Exception as e:
        print(f"Erro ao mover: {e}")
        return False

def configurar_driver(download_path):
    """Configurações do Chrome Driver (Headless opcional, Downloads automáticos)"""
    if not os.path.exists(download_path): os.makedirs(download_path)
    
    opts = Options()
    prefs = {
        "download.default_directory": download_path,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True,
        "pdfjs.disabled": True
    }
    opts.add_experimental_option("prefs", prefs)
    opts.add_argument("--start-maximized")
    # opts.add_argument("--headless") # Descomente para rodar sem abrir janela
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)

def main():
    # Verifica se a planilha de input existe
    if not os.path.exists(EXCEL_FILE_PATH):
        print(f"Erro: Arquivo '{EXCEL_FILE_NAME}' não encontrado na pasta do script.")
        return

    # Lê lista de prestadores a buscar
    try:
        df = pd.read_excel(EXCEL_FILE_PATH, header=None)
        lista_prestadores = df.iloc[:, 0].dropna().astype(str).tolist()
    except Exception as e:
        print(f"Erro ao ler Excel: {e}")
        return

    driver = configurar_driver(BASE_PATH)
    wait = WebDriverWait(driver, 20) 

    try:
        print(f">>> Iniciando automação no portal...")
        driver.get(LOGIN_URL)
        
        # Login (IDs genéricos, adapte conforme o HTML real)
        wait.until(EC.element_to_be_clickable((By.ID, "Login"))).send_keys(SEU_LOGIN)
        driver.find_element(By.ID, "Senha").send_keys(SUA_SENHA)
        driver.find_element(By.XPATH, "//button[contains(text(), 'Entrar')]").click()
        time.sleep(3)

        for prestador in lista_prestadores:
            print(f"\n--- Processando Fornecedor: {prestador} ---")
            
            try:
                driver.get(APROVACAO_URL)
                # Filtro na tabela (Select2)
                wait.until(EC.element_to_be_clickable((By.ID, "s2id_sel2_lPrestador"))).click()
                search = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='select2-drop']//input")))
                search.clear()
                search.send_keys(str(prestador))
                time.sleep(1)
                search.send_keys(Keys.ENTER)
                
                # Pausa para interação humana (Captcha ou filtros visuais)
                print(">>> PAUSA: Aplique os filtros de data e clique em BUSCAR na tela.")
                time.sleep(5) # Simulação de espera
                
                # Varredura da Tabela de Resultados
                btns_download = driver.find_elements(By.CSS_SELECTOR, "a.btnDown")
                print(f" -> Encontrados {len(btns_download)} documentos.")

                for i, btn in enumerate(btns_download, 1):
                    # Captura dados da linha para renomear o arquivo corretamente
                    linha = btn.find_element(By.XPATH, "./ancestor::tr")
                    cols = linha.find_elements(By.TAG_NAME, "td")
                    
                    nome_empresa = cols[1].text.strip()
                    data_ref = limpar_mes(cols[2].text.strip())
                    nome_arquivo = f"{limpar_string_arquivo(nome_empresa)}_{data_ref}.pdf"

                    # Download
                    qtd_antes = len(glob.glob(os.path.join(BASE_PATH, "*")))
                    driver.execute_script("arguments[0].click();", btn)
                    
                    novo_arquivo = esperar_novo_arquivo(BASE_PATH, qtd_antes)
                    if novo_arquivo:
                        mover_arquivo(novo_arquivo, PASTA_ESPELHO, nome_arquivo)
                    else:
                        print(f"Timeout no download {i}")

            except Exception as e:
                print(f"Erro ao processar {prestador}: {e}")

    finally:
        print("Encerrando driver...")
        driver.quit()

if __name__ == "__main__":
    main()

    #bfdev
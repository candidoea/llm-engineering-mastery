import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import sys 
from selenium.webdriver.common.action_chains import ActionChains 
from selenium.webdriver.chrome.service import Service
# ==========================================
# CREDENCIAIS DE LOGIN
# ==========================================
USER_EMAIL = "thomas.souto@tpbrazil"
USER_PASSWORD = "Manaus@92262231"

# ==========================================
# CONFIGURAÇÕES INICIAIS (MODO HEADLESS HABILITADO)
# ==========================================
# Força a saída do console (stdout) para UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Definindo o diretório de download
DOWNLOAD_DIR = r"\\AZTBR-VM-ETL01\bulkinsert\Wyndham\Bases\AdherenceAudit" 
print(f"Iniciando automação Five9 em MODO HEADLESS. O download será salvo em: {DOWNLOAD_DIR}")

# === Caminhos Chrome/Driver ===
chrome_driver_path = r"F:\chrome-test\chromedriver-win64\chromedriver.exe"
chrome_binary_path = r"F:\chrome-test\chrome-win64\chrome.exe"
service = Service(executable_path=chrome_driver_path)

# Configurações do Chrome
options = webdriver.ChromeOptions()
options.binary_location = chrome_binary_path

# ➡️ HABILITA O MODO HEADLESS (SEM JANELA)
options.add_argument("--headless=new") 
options.add_argument("--disable-blink-features=AutomationControlled")

# Configuração para forçar o download para o diretório especificado
prefs = {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False, # Desativa a caixa de diálogo de download
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True 
}
options.add_experimental_option("prefs", prefs)


# === Inicializar navegador ===
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 60)

print(f"✅ Versão ChromeDriver: {driver.capabilities['chrome']['chromedriverVersion']}")
print(f"✅ Versão Navegador: {driver.capabilities['browserVersion']}")

try:
    # ==========================================
    # LOGIN
    # ==========================================
    print("Navegando para https://us6.five9.com/login")
    driver.get("https://us6.five9.com/login")

    print(f"Realizando Login com o usuário: {USER_EMAIL}...")
    
    wait.until(EC.presence_of_element_located((By.ID, "input_username"))).send_keys(USER_EMAIL)
    driver.find_element(By.ID, "input_password").send_keys(USER_PASSWORD)
    driver.find_element(By.ID, "input_login_submit").click()

    print("Login efetuado. Aguardando carregamento da página inicial...")
    time.sleep(6) 
    
    # ==========================================
    # ACESSO AO MENU DE RELATÓRIOS
    # ==========================================
    print("Navegando para a seção de Relatórios (Dashboard & Reports)...")
    reports_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Dashboard & Reports')]")))
    reports_link.click()

    print("Aguardando carregamento da página de relatórios...")
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "yui-navset-top")))
    
    # ==========================================
    # CLIQUE EM 'CANNED REPORTS'
    # ==========================================
    print("➡️ Clicando em 'Canned Reports' para garantir o carregamento da lista...")
    canned_reports_link = wait.until(
        EC.element_to_be_clickable((By.ID, "tab1"))
    )
    driver.execute_script("arguments[0].click();", canned_reports_link) # Uso do JS click é mais robusto em Headless
    
    wait.until(EC.presence_of_element_located((By.ID, "cannedReports")))
    time.sleep(5) 

    # ==========================================
    # SELEÇÃO E EXECUÇÃO DO RELATÓRIO
    # ==========================================
    print("Selecionando e executando o relatório 'Adherence Audit - TP Brazil'...")

    report_link_xpath = "//a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'adherence audit')]"
    run_button_xpath = "//tr[td/a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'adherence audit')]]//a[contains(text(), 'Run')]"
    
    run_button = wait.until(EC.element_to_be_clickable((By.XPATH, run_button_xpath)))
    driver.execute_script("arguments[0].click();", run_button)
    print("Botão 'Run' clicado. Aguardando tela de configuração...")
    time.sleep(10) 
    
    # ==========================================
    # CONFIGURAR O PERÍODO
    # ==========================================
    print("Configurando o período para 'This week'...")
    
    interval_select_element = wait.until(EC.presence_of_element_located((By.ID, "rdw_tf_interval")))
    interval_select = Select(interval_select_element)
    interval_select.select_by_value("THIS_WEEK")
    
    time.sleep(5) 

    # ==========================================
    # GERAR RELATÓRIO
    # ==========================================
    print("Executando o relatório...")
    
    # Botão 'Run Report' (ID: rw_run_btn)
    run_report_button = wait.until(EC.element_to_be_clickable(
        (By.ID, "rw_run_btn")
    ))
    driver.execute_script("arguments[0].click();", run_report_button)
    
    print("Relatório em execução. Aguardando o botão de Exportação...")
    
    # Espera o carregamento total, aguardando o botão 'Export Details'
    wait.until(EC.element_to_be_clickable(
        (By.ID, "rw_export_btn")
    ))
    time.sleep(20)
    
    # Botão 'Export Details' (ID: rw_export_btn)
    print("Clicando em 'Export Details'...")
    export_details_button = driver.find_element(By.ID, "rw_export_btn")
    driver.execute_script("arguments[0].click();", export_details_button)
    time.sleep(5) # Pausa para o pop-up carregar
    
    # ==========================================
    # EXPORTAR PARA CSV (Windows)
    # ==========================================
    print("Selecionando o formato CSV...")
    
    # 1. Seleciona a opção CSV (ID: rr_output_format_CSV)
    csv_radio = wait.until(EC.element_to_be_clickable(
        (By.ID, "rr_output_format_CSV")
    ))
    csv_radio.click()
    time.sleep(5)

    # 2. Clica em OK para iniciar a geração do relatório (ID: rr_output_format_apply)
    print("Clicando em 'OK' para iniciar a geração...")
    ok_button = wait.until(EC.element_to_be_clickable(
        (By.ID, "rr_output_format_apply")
    ))
    driver.execute_script("arguments[0].click();", ok_button)

    # 3. PAUSA LONGA AQUI PARA O RELATÓRIO SER GERADO
    print("Aguardando 15 segundos para o relatório ser gerado...")
    time.sleep(20) 

    # ==========================================
    # DOWNLOAD DO RELATÓRIO
    # ==========================================
    # 4. Espera o botão 'Download' ficar visível e clicável (ID: pd_btn_download)
    download_button = wait.until(EC.element_to_be_clickable(
        (By.ID, "pd_btn_download")
    ))
    
    # 5. Clica no botão 'Download'
    print("➡️ Clicando em 'Download' para baixar o arquivo...")
    driver.execute_script("arguments[0].click();", download_button)
    
    # Pausa para o arquivo iniciar/completar o download.
    time.sleep(10) 

    print(f"✅ Processo de automação concluído. O arquivo deve estar em: {DOWNLOAD_DIR}")

except Exception as e:
    print(f"[ERRO] Ocorreu um erro durante a automação: {e}")
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"error_page_{timestamp}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"HTML da página de erro salvo em 'error_page_{timestamp}.html'")
    except:
        print("Não foi possível salvar a página de erro.")
finally:
    # Este 'quit' é crucial no modo headless para fechar o processo do Chrome em segundo plano
    driver.quit() 
    print("Navegador fechado.")
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

def get_gost_page_selenium(gost_number):
    # Настройка опций браузера
    options = Options()
    # Отключаем автоматизацию (чтобы сайт не думал, что это бот)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    # Опционально: запуск в фоне (headless) – раскомментируйте, если не нужен видимый браузер
    # options.add_argument("--headless")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Исполняем скрипт для изменения свойства navigator.webdriver
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    url_part = gost_number.lower().replace(' ', '-').replace('–', '-')
    url = f"https://gostexpert.ru/gost/{url_part}"
    print(f"Перехожу на: {url}")

    try:
        driver.get(url)
        
        # Ждём появления тега body (до 10 секунд)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Даём дополнительное время на динамическую загрузку
        time.sleep(3)
        
        # Пробуем получить заголовок и часть исходного кода
        print(f"Заголовок страницы: {driver.title}")
        print(f"URL после загрузки: {driver.current_url}")
        
        # Проверим, есть ли на странице что-то похожее на контент ГОСТа
        page_source = driver.page_source[:500]
        print("Первые 500 символов page_source:")
        print(page_source)
        
        # Оставляем браузер открытым для осмотра
        time.sleep(10)
        
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    get_gost_page_selenium("ГОСТ 60731-2001")
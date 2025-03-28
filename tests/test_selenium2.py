from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time

WAITING_VALUE = 'PICCO R-MFT60 6-4 L08'

# Настройка Chrome
options = Options()
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--start-maximized')
options.add_experimental_option('excludeSwitches', ['enable-automation'])

def login(driver, username, password):
    try:
        # Переходим на страницу входа
        driver.get('http://127.0.0.1:5000/admin_login')
        
        # Ожидаем появления полей формы входа
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        
        # Заполняем форму
        driver.find_element(By.NAME, 'username').send_keys(username)
        driver.find_element(By.NAME, 'password').send_keys(password)
        time.sleep(1)
        
        # Нажимаем кнопку входа
        driver.find_element(By.NAME, 'submit').click()
        print("✓ Успешный вход в систему")
    except Exception as e:
        print(f"✗ Ошибка при входе: {e}")
        return False
    return True

def main():
    try:
        # Создаем драйвер
        driver = webdriver.Chrome(options=options)
        
        # Выполняем вход
        login(driver, 'user3', '123')
        time.sleep(1)

        
        # Переходим на страницу деталей
        driver.get('http://127.0.0.1:5000/details')
        print("✓ Страница деталей загружена")
        time.sleep(1)

        driver.find_element(By.CLASS_NAME, 'selected-deal').click()
        time.sleep(1)
        driver.find_element(By.NAME, 'apply_select_deal').click()
        
        # Нажимаем на ссылку продукта
        driver.find_element(By.CLASS_NAME, 'product-link').click()
        print("✓ Ссылка продукта нажата")
        time.sleep(1)

        # Вводим новое значение
        driver.find_element(By.NAME, 'add_to_deal').click()
        print("✓ Инструмент добавлен в сделку")

        # Перезагружаем страницу
        driver.get('http://127.0.0.1:5000/deals')
        time.sleep(1)

        # Нажимаем на ссылку продукта
        driver.find_element(By.CLASS_NAME, 'product-link').click()
        print("✓ Ссылка сделки нажата")
        time.sleep(1)
        
        # Получаем значение из detail_item
        detail_item = driver.find_element(By.CLASS_NAME, 'related-tools').get_attribute('outerHTML')
        text_content = detail_item.strip()
        
        # Проверяем результат
        if WAITING_VALUE in text_content:
            print("\n🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
            print(f"Сделка содержит ожидаемое значение: {WAITING_VALUE}")
        else:
            print("\n❌ ТЕСТ НЕ ПРОЙДЕН!")
            print(f"Сделка не содержит ожидаемое значение: {WAITING_VALUE}")

            
    except Exception as e:
        print(f"\n❌ Произошла ошибка при выполнении теста: {e}")
    finally:
        time.sleep(3)
        driver.quit()

if __name__ == "__main__":
    main()
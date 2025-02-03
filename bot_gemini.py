import random
from selenium import webdriver 
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import google.generativeai as genai
from google.api_core import retry
from google.api_core import exceptions
import time
import re

# 使用 Gemini 生成答案，加入重試機制
def generate_answer(question, options, max_retries=3):
    prompt = f"""問題: {question}
選項: {', '.join(options)}
只返回最合適的選項的內容，沒有其他描述。"""
    
    model = genai.GenerativeModel('gemini-pro')
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except exceptions.ResourceExhausted:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # 逐漸增加等待時間
                print(f"API 配額已達上限，等待 {wait_time} 秒後重試...")
                time.sleep(wait_time)
            else:
                print("達到最大重試次數，隨機選擇一個答案")
                return random.choice(options)
        except Exception as e:
            print(f"生成答案時發生錯誤: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return random.choice(options)

# 初始化瀏覽器
def init_browser():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("user-data-dir=C:/temp/chrome-profile")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

# 標準化文本
def standardize_text(text):
    return re.sub(r'\s+', '', text).strip()

# 進行答題操作
def complete_assessment(driver):
    driver.get('https://isafeevent.moe.edu.tw/exam/')
    
    wait = WebDriverWait(driver, 20)

    try:
        start_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.btnStartExam')))
        start_button.click()
    except Exception as e:
        print(f"錯誤: {e}")
        return

    time.sleep(3)

    questions = []
    options = []

    # 收集所有問題和選項
    for i in range(1, 11):
        try:
            question_div = driver.find_element(By.ID, f'div_q_{i}')
            question_text = question_div.find_element(By.TAG_NAME, 'h4').text
            questions.append(question_text)

            option_elements = question_div.find_elements(By.CLASS_NAME, 'form-check-label')
            question_options = [option.text.strip() for option in option_elements]
            options.append(question_options)
        except Exception as e:
            print(f"錯誤在第 {i} 題: {e}")
            continue

    if len(questions) != len(options):
        print("問題和選項的數量不一致，請檢查網頁結構。")
        return

    # 回答問題
    for i, question in enumerate(questions):
        try:
            answer = generate_answer(question, options[i])
            print(f"問題: {question}, 選擇答案: {answer}")

            formatted_answer = answer.strip()
            found = False

            for option in options[i]:
                if standardize_text(formatted_answer) in standardize_text(option):
                    option_elements = driver.find_elements(By.XPATH, f"//div[@id='div_q_{i + 1}']//label[contains(text(), '{option}')]")
                    if option_elements:
                        option_elements[0].click()
                        found = True
                        break

            if not found:
                print(f"未找到對應的答案: {formatted_answer}，隨機選擇一個選項。")
                random_option = random.choice(options[i])
                option_elements = driver.find_elements(By.XPATH, f"//div[@id='div_q_{i + 1}']//label[contains(text(), '{random_option}')]")
                if option_elements:
                    option_elements[0].click()
                print(f"隨機選擇的選項: {random_option}")

        except Exception as e:
            print(f"處理第 {i+1} 題時發生錯誤: {e}")
            # 發生錯誤時隨機選擇一個答案
            random_option = random.choice(options[i])
            option_elements = driver.find_elements(By.XPATH, f"//div[@id='div_q_{i + 1}']//label[contains(text(), '{random_option}')]")
            if option_elements:
                option_elements[0].click()
            print(f"錯誤處理：隨機選擇的選項: {random_option}")

    # 提交答案
    try:
        submit_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'btnSendExam')))
        submit_button.click()
        print("答案提交成功！")
    except Exception as e:
        print(f"提交答案時發生錯誤: {e}")

# 主函數
def main():
    driver = init_browser()
    driver.get("https://isafeevent.moe.edu.tw/")
    
    print("請在瀏覽器中完成登入操作，完成後按下 Enter 鍵繼續...")
    input()
    
    api_key = str(input("輸入 Gemini API 金鑰:"))
    genai.configure(api_key=api_key)
    
    num_attempts = int(input("輸入要重複答題的次數:"))
    answerDelay = int(input("輸入答題間隔秒數:"))

    for attempt in range(num_attempts):
        try:
            print(f"開始第 {attempt + 1} 次答題...")
            complete_assessment(driver)
            print(f"等待{answerDelay}秒後重新開始...")
            time.sleep(answerDelay)
        except Exception as e:
            print(f"第 {attempt + 1} 次答題過程中發生錯誤: {e}")
            print("等待30秒後繼續...")
            time.sleep(30)

if __name__ == "__main__":
    main()
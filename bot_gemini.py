import random
from selenium import webdriver 
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import google.generativeai as genai
import time

def generate_answer(question, options):
    """使用 Gemini 生成答案"""
    try:
        prompt = f"問題: {question}\n選項: {', '.join(options)}\n只返回最合適的選項的內容，沒有其他描述。"
        response = genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"API錯誤: {e}")
        return random.choice(options)

def click_element(driver, xpath):
    """點擊元素的通用函數"""
    try:
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        element.click()
        return True
    except Exception:
        return False

def answer_question(driver, question, options, question_number):
    """處理單個問題"""
    answer = generate_answer(question, options)
    print(f"問題 {question_number}: {question}\n選擇答案: {answer}")
    
    # 嘗試點擊對應答案
    for option in options:
        if answer.replace(' ', '') in option.replace(' ', ''):
            if click_element(driver, f"//div[@id='div_q_{question_number}']//label[contains(text(), '{option}')]"):
                return
    
    # 如果找不到匹配的答案，隨機選擇
    random_option = random.choice(options)
    click_element(driver, f"//div[@id='div_q_{question_number}']//label[contains(text(), '{random_option}')]")
    print(f"使用隨機答案: {random_option}")

def complete_quiz(driver):
    """完成一次測驗"""
    driver.get('https://isafeevent.moe.edu.tw/exam/')
    
    # 點擊開始按鈕
    if not click_element(driver, "//button[contains(@class, 'btnStartExam')]"):
        return False
    
    time.sleep(2)
    
    # 處理每個問題
    for i in range(1, 11):
        try:
            div = driver.find_element(By.ID, f'div_q_{i}')
            question = div.find_element(By.TAG_NAME, 'h4').text
            options = [opt.text.strip() for opt in div.find_elements(By.CLASS_NAME, 'form-check-label')]
            answer_question(driver, question, options, i)
        except Exception as e:
            print(f"處理第 {i} 題時出錯: {e}")
    
    # 提交答案
    click_element(driver, "//button[contains(@class, 'btnSendExam')]")
    return True

def main():
    # 初始化
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=webdriver.ChromeOptions().add_argument("user-data-dir=C:/temp/chrome-profile")
    )
    driver.get("https://isafeevent.moe.edu.tw/")
    
    # 設定
    print("請在瀏覽器中完成登入操作，完成後按下 Enter 鍵繼續...")
    input()
    
    genai.configure(api_key=input("輸入 Gemini API 金鑰: "))
    attempts = int(input("輸入要重複答題的次數: "))
    delay = int(input("輸入答題間隔秒數: "))
    
    # 主循環
    for i in range(attempts):
        try:
            print(f"\n開始第 {i + 1} 次答題...")
            if complete_quiz(driver):
                print("答題完成!")
            time.sleep(delay)
        except Exception as e:
            print(f"錯誤: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
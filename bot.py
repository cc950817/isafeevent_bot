import random
from selenium import webdriver 
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import openai
import time
import re

# 使用 OpenAI 生成答案
def generate_answer(question, options):
    # 更直接和簡單的 Prompt，避免過多描述干擾
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是一個幫助人們快速選擇正確答案的AI助手。"},
            {"role": "user", "content": f"問題: {question}\n選項: {', '.join(options)}\n只返回最合適的選項的內容，沒有其他描述。"}
        ],
        max_tokens=200,
        temperature=0.5
    )
    return response['choices'][0]['message']['content'].strip()

# 初始化瀏覽器
def init_browser():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("user-data-dir=C:/temp/chrome-profile")  # 自定義的路徑
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

# 標準化文本的功能，用於移除多餘空格或格式問題
def standardize_text(text):
    return re.sub(r'\s+', '', text).strip()  # 移除所有空格並去除首尾空格

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

    time.sleep(3) #等待網頁加載完畢

    questions = []
    options = []

    for i in range(1, 11):
        try:
            question_div = driver.find_element(By.ID, f'div_q_{i}')
            question_text = question_div.find_element(By.TAG_NAME, 'h4').text
            questions.append(question_text)

            # 提取選項
            option_elements = question_div.find_elements(By.CLASS_NAME, 'form-check-label')
            question_options = [option.text.strip() for option in option_elements]
            options.append(question_options)
        except Exception as e:
            print(f"錯誤在第 {i} 題: {e}")
            continue

    if len(questions) != len(options):
        print("問題和選項的數量不一致，請檢查網頁結構。")
        return

    # 使用 OpenAI 來回答每個問題
    answers = []
    for i, question in enumerate(questions):
        answer = generate_answer(question, options[i])
        print(f"問題: {question}, 選擇答案: {answer}")
        answers.append(answer)

        formatted_answer = answer.strip()

        # 增強匹配邏輯：使用標準化後的文本進行匹配
        found = False
        for option in options[i]:
            if standardize_text(formatted_answer) in standardize_text(option):
                # 定位到匹配的選項，並點擊
                option_elements = driver.find_elements(By.XPATH, f"//div[@id='div_q_{i + 1}']//label[contains(text(), '{option}')]")
                if option_elements:
                    option_elements[0].click()
                    found = True
                    break

        # 如果沒有找到AI的答案，隨機選擇一個選項
        if not found:
            print(f"未找到對應的答案: {formatted_answer}，隨機選擇一個選項。")
            random_option = random.choice(options[i])  # 隨機選擇一個選項
            option_elements = driver.find_elements(By.XPATH, f"//div[@id='div_q_{i + 1}']//label[contains(text(), '{random_option}')]")
            if option_elements:
                option_elements[0].click()
            print(f"隨機選擇的選項: {random_option}")

    # 提交答案
    submit_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'btnSendExam')))
    submit_button.click()

    print("答案提交成功！")

# 主函數
def main():
    driver = init_browser()
    driver.get("https://isafeevent.moe.edu.tw/")
    
    print("請在瀏覽器中完成登入操作，完成後按下 Enter 鍵繼續...")
    input()
    
    openai.api_key = str(input("輸入OpenAI金鑰:"))
    num_attempts = int(input("輸入要重複答題的次數:"))
    answerDelay = int(input("輸入答題間隔秒數"))


    for attempt in range(num_attempts):
        print(f"開始第 {attempt + 1} 次答題...")
        complete_assessment(driver)
        print(f"等待{answerDelay}秒後重新開始...")
        time.sleep(answerDelay)  # 每次答題間隔秒數

if __name__ == "__main__":
    main()
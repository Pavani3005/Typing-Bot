from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import easyocr
import pyautogui
import time
import keyboard
from PIL import Image
#from transformers import TrOCRProcessor, VisionEncoderDecoderModel
#import pytesseract
import io
import requests
import base64

#pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# def no_captcha(driver):
#     processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
#     model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")
#     wait = WebDriverWait(driver, 10)
#     captcha_img = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "challengeImg")))
#     img_src = captcha_img.get_attribute('src')
#     response = requests.get(img_src)
#     image = Image.open(io.BytesIO(response.content))
#     image.save('captcha.png')
#     image = Image.open('captcha.png').convert("RGB")
#     pixel_values = processor(image, return_tensors="pt").pixel_values
#     generated_ids = model.generate(pixel_values)
#     text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
#     print("captcha text: ",text)




def bypass_captcha(driver):
    try:
        print("Waiting for captcha...")
        wait = WebDriverWait(driver, 10)
        captcha_img = wait.until(
            EC.visibility_of_element_located((By.CLASS_NAME, "challengeImg"))
        )
        time.sleep(1)  # Ensure image is fully loaded
        print("Captcha image found.")
        # Get the image source (handle both base64 and URL)
        img_src = captcha_img.get_attribute('src')
        
        response = requests.get(img_src)
        image = Image.open(io.BytesIO(response.content))
        print("Captcha image loaded successfully.")
        # Enhanced image processing
        image = image.convert('L')  # Grayscale
        image = image.point(lambda x: 0 if x < 140 else 255)  # Adjust threshold
        image = image.resize((int(image.width*2), int(image.height*2)), Image.LANCZOS)  # Upscale
        
        # Save for debugging
        image.save('captcha_processed.png')
        
        reader = easyocr.Reader(['pt'])
        results = reader.readtext('captcha_processed.png')  # Change to processed image
        if results:
            captcha_text = results[0][1]  # Get text from first result
            print(f"Using captcha text: {captcha_text}")
            
            # Find and fill the captcha input field
            captcha_input = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "challengeTextArea")))
            captcha_input.clear()
            
            # Type the captcha text
            driver.execute_script(f"arguments[0].value='{captcha_text}';", captcha_input)
        
        # Submit the form
        captcha_input.send_keys(Keys.RETURN)
        
        # Check if captcha was successful
        time.sleep(2)
        if "challengeImg" in driver.page_source:
            print("Captcha failed, retrying...")
            return False
        return True
        
    except Exception as e:
        print(f"Error in bypass_captcha: {str(e)}")
        return False
    

def type_text(text):
    for word in text:
            pyautogui.typewrite(word + " ", interval=0)  # Type each word with a small delay

def scrape_and_type(driver):
    try:
        # Wait for the Enter a Typing Race button and click it
        wait = WebDriverWait(driver, 10)
        enter_race_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Enter a Typing Race')]")))
        enter_race_button.click()
        time.sleep(3)  # Wait for animation and text to load
        
        # Get the page source after JavaScript has loaded
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find the specific span with text content
        target_elements = soup.find_all("span")
        
        scraped_data = ""
        for element in target_elements:
            if "unselectable" in str(element):
                text = element.text
                if text:  # Only append non-empty strings
                    scraped_data += text
        
        scraped_data = scraped_data.split()  # Split the text into words
        
        # Wait for the typing input to be ready
        wait = WebDriverWait(driver, 10)
        input_field = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "txtInput")))
        input_field.click()  # Focus the input field
        
        return scraped_data
        
    except Exception as e:
        print(f"Error occurred: {e}")
        return []

def human_benchmark(driver):
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    
    # Find all spans with class="incomplete"
    target_elements = soup.find_all("span", class_="incomplete")
    
    scraped_data = ""
    for element in target_elements:
        text = element.text
        scraped_data += text  # Add space between words
    
    return scraped_data.strip()

def monkey_type(driver):
    try:
        wait = WebDriverWait(driver, 10)
        
        # Attempt to find and click the cookie prompt button
        try:
            accept_cookies = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'accept all')]")))
            accept_cookies.click()
        except Exception as e:
            print(f"Failed to find or click the Accept button: {e}")
        
        # Wait for the JavaScript to load
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.word")))
        
        # Ensure the page has finished loading
        time.sleep(2)  # Optional delay
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        scraped_data = ""
        # Find all divs with class "word"
        divs = soup.find_all("div", class_="word")
        
        if not divs:
            print("No divs with class 'word' found.")
            return ""
        
        for div in divs:
            target_elements = div.find_all("letter")
            if not target_elements:
                print("No letter tags found within divs.")
                return ""
            
            for i in target_elements:
                scraped_data += i.text
            scraped_data += " "
        
        return scraped_data.strip()
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return ""


def main():
    ch = int(input("Choose a website:\n1. Type Racer\n2. Human Benchmark\n3. Monkey Type\nEnter your choice: "))
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('--disable-gpu')
    #chrome_options.add_argument("--disable-notifications")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(options=chrome_options)
    website_url1 = "https://play.typeracer.com/"
    website_url2 = "https://humanbenchmark.com/tests/typing"
    website_url3 = "https://monkeytype.com/"
    if ch == 1:
        driver.get(website_url1)
        data = scrape_and_type(driver)
        #print("Scraped data:", data)
        keyboard.wait('enter')
        type_text(data) # Wait for Enter key to be pressed
        time.sleep(2)
        bypass_captcha(driver)  # Call the function to bypass captcha
    elif ch == 2:
        driver.get(website_url2)
        data = human_benchmark(driver)
        pyautogui.typewrite(data, interval=0)  # Call the function to bypass captcha
    elif ch == 3:
        driver.get(website_url3)
        data = monkey_type(driver)
        print("Scraped data:", data)
        keyboard.wait('enter')
        pyautogui.typewrite(data, interval=0)

    else:
        print("Invalid choice. Exiting...")
        return
    print("Press 'q' to quit...")
    keyboard.wait('q')
    driver.quit()  # Properly close the browser

if __name__ == "__main__":
    main()
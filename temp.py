from flask import Flask, request, jsonify, Response
import undetected_chromedriver as uc
import json
import time
import uuid
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from threading import Lock
import re
import os
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

app = Flask(__name__)

class LambdaChatManager:
    def __init__(self):
        self.driver = None
        self.base_url = "https://lambda.chat"
        self.conversation_id = None
        self.message_id = None
        self.lock = Lock()
        self.setup_driver()
        # Configure settings first
        self.open_settings()
        # Then start initial conversation
        print("Starting initial conversation...")
        initial_response = self.create_conversation("1")
        print("Initial bot response:", initial_response)
        print("Initial conversation started")

    def setup_driver(self):
        options = uc.ChromeOptions()
        # Enable clipboard permissions
        options.add_experimental_option("prefs", {
            "profile.content_settings.exceptions.clipboard": {
                "*": {"setting": 1}
            }
        })
        
        # Create a persistent user data directory
        user_data_dir = os.path.join(os.path.expanduser("~"), "wincommander_chrome_profile")
        os.makedirs(user_data_dir, exist_ok=True)
        print(f"Using Chrome profile at: {user_data_dir}")
        
        # Use persistent profile
        self.driver = uc.Chrome(options=options, user_data_dir=user_data_dir)
        self.driver.get(f"{self.base_url}/models/hermes3-405b-fp8-128k")
        time.sleep(3)

    def open_settings(self):
        try:
            # Navigate to settings page
            self.driver.get(f"{self.base_url}/settings")
            time.sleep(2)  # Wait for settings page to load
            
            # Wait for and find the direct paste toggle button
            direct_paste_toggle = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='directPaste']"))
            )
            
            # Find the parent label element that's clickable
            toggle_label = direct_paste_toggle.find_element(By.XPATH, "./..")
            
            # Click the toggle
            toggle_label.click()
            time.sleep(1)  # Wait for toggle to take effect
            
            # Find and click the Hermes model link
            hermes_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/settings/hermes3-405b-fp8-128k']"))
            )
            hermes_link.click()
            time.sleep(2)  # Wait for model settings to load
            
            # Find and clear the system prompt textarea
            system_prompt_textarea = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[aria-label='Custom system prompt']"))
            )
            
            # Clear textarea like a human would - select all and delete
            self.driver.execute_script("arguments[0].focus();", system_prompt_textarea)
            # ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).send_keys(Keys.BACKSPACE).perform()
            time.sleep(1)  # Wait for clearing to take effect
            
            # Navigate directly to the model page instead of clicking close
            self.driver.get(f"{self.base_url}/models/hermes3-405b-fp8-128k")
            time.sleep(2)  # Wait for page to load
            
            print("Settings configured and returned to chat")
            
        except Exception as e:
            print(f"Error configuring settings: {e}")

    def create_conversation(self, initial_message):
        with self.lock:
            try:
                # Create conversation using UI
                textarea = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "textarea"))
                )
                textarea.clear()
                textarea.send_keys(initial_message)
                
                send_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                send_button.click()
                
                # Wait for response and get conversation ID from URL
                time.sleep(0)
                current_url = self.driver.current_url
                self.conversation_id = current_url.split("/")[-1]
                
                # Get message ID from the last message element
                message_elements = self.driver.find_elements(By.CSS_SELECTOR, ".group[role='presentation']")
                if message_elements:
                    self.message_id = message_elements[-1].get_attribute("id")
                
                response = self.wait_for_response()
                return response
            except Exception as e:
                print(f"Error creating conversation: {e}")
                return None

    def edit_message(self, new_message):
        with self.lock:
            try:
                # Find all message divs
                message_divs = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".group[role='presentation']"))
                )
                
                # Find and click edit button using updated selector
                edit_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[title='Branch']"))
                )
                edit_button.click()
                
                # Wait for and fill edit textarea
                edit_textarea = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "textarea.w-full"))
                )
                edit_textarea.clear()
                self.driver.execute_script("arguments[0].value = arguments[1]", edit_textarea, new_message)
                
                # Click submit button
                submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                submit_button.click()
                
                # Wait for new response to load
                time.sleep(2)
                
                # Get updated message ID
                message_elements = self.driver.find_elements(By.CSS_SELECTOR, ".group[role='presentation']")
                if message_elements:
                    self.message_id = message_elements[-1].get_attribute("id")
                
                return self.wait_for_response()
            except Exception as e:
                print(f"Error editing message: {e}")
                return None

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((Exception)),
        reraise=True
    )
    def find_and_click_copy_button(self):
        """Retry mechanism for finding and clicking copy button with exponential backoff"""
        copy_button = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 
                "button.btn[title='Copy to clipboard']:not(.rounded-lg):not(.border-gray-200)"
            ))
        )
        
        # Click rapidly 3 times with minimal delay
        for _ in range(3):
            copy_button.click()
            time.sleep(0.05)  # Reduced from 0.2 to 0.05 seconds
        
        return True

    def wait_for_response(self):
        try:
            # First wait for the stop button to appear (meaning generation has started)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 
                    "button.btn:has(svg path[d='M24 6H8a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2'])"
                ))
            )
            
            # Then wait for the stop button to disappear (meaning generation is complete)
            WebDriverWait(self.driver, 600).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, 
                    "button.btn:has(svg path[d='M24 6H8a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2'])"
                ))
            )

            # Scroll to bottom instantly using JavaScript
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            try:
                # Find all AI message boxes
                ai_messages = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 
                        "div.relative.min-h-\\[calc\\(2rem\\+theme\\(spacing\\[3\\.5\\]\\)\\*2\\)\\].min-w-\\[60px\\].break-words.rounded-2xl.border.border-gray-100.bg-gradient-to-br.from-gray-50.px-5.py-3\\.5.text-gray-600.prose-pre\\:my-2.dark\\:border-gray-800.dark\\:from-gray-800\\/40.dark\\:text-gray-300"
                    ))
                )
                
                try:
                    # Use the retry-enabled method to find and click copy button
                    copy_success = self.find_and_click_copy_button()
                    
                    # Get text from clipboard without delay
                    clipboard_text = self.driver.execute_script(
                        "return navigator.clipboard.readText()"
                    )
                    
                    return clipboard_text
                    
                except Exception as e:
                    print(f"Failed to copy response after all retries: {e}")
                    return "Error copying response"
                
            except Exception as e:
                print(f"Error getting response text: {e}")
                return "Error getting response"
            
        except Exception as e:
            print(f"Error in wait_for_response: {e}")
            return "Error getting response"

# Initialize chat manager before starting server
chat_manager = LambdaChatManager()

@app.route('/api/chat/edit', methods=['POST'])
def edit_message():
    data = request.json
    new_message = data.get('message')
    
    if not new_message:
        return jsonify({'error': 'No message provided'}), 400
    
    response = chat_manager.edit_message(new_message)
    if response:
        return jsonify({
            'message_id': chat_manager.message_id,
            'response': response
        })
    return jsonify({'error': 'Failed to edit message'}), 500

def cleanup():
    if chat_manager.driver:
        chat_manager.driver.quit()

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        cleanup()
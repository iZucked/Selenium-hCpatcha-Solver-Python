import json
import random
import time
from typing import Dict, List
import requests
from time import sleep
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
import base64


def human_click(browser: webdriver, element: WebElement):
    """
    Clicks an element on a web page in a 'human like' way to avoid bot detection
    :param browser: The web driver
    :param element: The element to click
    """
    action_chains = ActionChains(browser)
    wait_time = random.uniform(0, 0.5)
    action_chains.pause(wait_time).move_to_element(element).pause(wait_time).click().perform()


class CaptchaSolver:
    def __init__(self, key: str, max_element_wait_time=60, request_timeout_length=120, solving_timeout_length=300):
        self.api_key = key
        self.max_element_wait_time = max_element_wait_time
        self.request_timeout_length = request_timeout_length
        self.solving_timeout_length = solving_timeout_length

    def solve_captcha_selenium(self, browser: webdriver) -> bool:
        wait = WebDriverWait(browser, self.max_element_wait_time)
        # Go to clicking iframe
        try:
            wait.until(EC.frame_to_be_available_and_switch_to_it(
                (By.XPATH, "//iframe[@title='widget containing checkbox for hCaptcha security challenge']")))
        except TimeoutException:
            print("[ERROR] : Can't find captcha!")
            return False

        # Click Start button
        start_button = wait.until(EC.element_to_be_clickable((By.ID, "anchor")))
        human_click(browser, start_button)

        time.sleep(10)

        # Go to form iframe
        browser.switch_to.default_content()
        try:
            # Check if frame can be found (if not an exception is thrown and the captcha is solved)
            WebDriverWait(browser, 5).until(EC.frame_to_be_available_and_switch_to_it(
                (By.XPATH, "//iframe[@title='Main content of the hCaptcha challenge']")))
        except TimeoutException:
            return True

        # Go through different screens until finished
        time_out_time = time.time() + self.solving_timeout_length
        while time.time() < time_out_time:
            prompt_text: str = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "prompt-text"))).text

            # Get images
            images: List[WebElement] = []
            for i in range(1, 10):
                element_xpath = f"/html/body/div[1]/div/div/div[2]/div[{i}]/div[2]/div"
                wait.until(EC.text_to_be_present_in_element_attribute(
                    (By.XPATH, element_xpath), "style", "url"))
                images.append(wait.until(EC.presence_of_element_located(
                    (By.XPATH, element_xpath))))

            base64_images = CaptchaSolver.get_base64_images_from_captcha(images)
            try:
                actions = self.get_captcha_solution(base64_images, prompt_text)
            except Exception as e:
                print(f"Got exception: {e} when trying to get solution")
                return False

            # Check if it is making us click all squares (normally means it has no clue what it's doing)
            click_count = sum(map(lambda x: 1 if x == 'CLICK' else 0, actions))
            if click_count == 9:
                # Remove some random clicks
                for _ in range(random.randint(1, 4)):
                    actions[random.randint(0, len(actions) - 1)] = "NOPE"

            # Click on images
            for i in range(9):
                if actions[i] == "CLICK":
                    image = wait.until(
                        EC.element_to_be_clickable((By.XPATH, f"/html/body/div[1]/div/div/div[2]/div[{i + 1}]")))
                    human_click(browser, image)

            # Submit
            submit_button = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "button-submit")))
            human_click(browser, submit_button)

            # Leave iframe and go back to start iframe
            browser.switch_to.default_content()
            wait.until(EC.frame_to_be_available_and_switch_to_it(
                (By.XPATH, "//iframe[@title='widget containing checkbox for hCaptcha security challenge']")))

            # Check if finished
            try:
                if WebDriverWait(browser, 5).until(EC.text_to_be_present_in_element_attribute(
                        (By.CLASS_NAME, "check"), "style", "display: block")
                ):
                    return True
            except TimeoutException:
                # Exit iframe and go back to captcha iframe
                browser.switch_to.default_content()
                wait.until(EC.frame_to_be_available_and_switch_to_it(
                    (By.XPATH, "//iframe[@title='Main content of the hCaptcha challenge']")))

            """
            # Use this code for a check if the captcha is removed from the page or you're redirected once it is finished
            try:
                WebDriverWait(browser, 15).until(EC.frame_to_be_available_and_switch_to_it(
                    (By.XPATH, "//iframe[@title='Main content of the hCaptcha challenge']")))
            except TimeoutException:
                return True
            """

        return False

    @staticmethod
    def get_base64_images_from_captcha(images: List[WebElement]) -> List[str]:
        results = []

        for image in images:
            # Get url of each image
            style = image.get_attribute("style")
            url = style.split("url")[1].split(')')[0][1:].replace('"', '')

            # Get image encoding
            results.append(base64.b64encode(requests.get(url).content).decode('ascii'))
            time.sleep(0.01)

        return results

    def get_captcha_solution(self, base64_images: List[str], prompt_text: str) -> List[str]:
        create_task_endpoint = "https://api.anycaptcha.com/createTask"

        headers = {
            "Host": "api.anycaptcha.com",
            "Content-Type": "application/json"
        }

        body = {
            "clientKey": self.api_key,
            "task": {
                "type": "HCaptchaClickTask",
                "ChallengeCaption": prompt_text,
                "ImageIndex1": base64_images[0],
                "ImageIndex2": base64_images[1],
                "ImageIndex3": base64_images[2],
                "ImageIndex4": base64_images[3],
                "ImageIndex5": base64_images[4],
                "ImageIndex6": base64_images[5],
                "ImageIndex7": base64_images[6],
                "ImageIndex8": base64_images[7],
                "ImageIndex9": base64_images[8]
            }
        }

        response = requests.post(create_task_endpoint, json=body, headers=headers)
        json_response = json.loads(response.content)
        if json_response['errorId'] == 0:
            print("[SUCCESS] : Created captcha task")
        else:
            raise Exception(f"[ERROR]: Couldn't create task, reason {json_response['errorCode']}")

        get_task_endpoint = "https://api.anycaptcha.com/getTaskResult"
        body = {
            "clientKey": self.api_key,
            "taskId": json_response['taskId']
        }

        time_out = time.time() + self.request_timeout_length

        while time.time() < time_out:
            response = requests.post(get_task_endpoint, json=body, headers=headers)
            json_response: Dict = json.loads(response.content)

            if json_response['errorId'] > 0:
                # If captcha can't be solved then click random images
                if "NotSupportChallenge" in json_response['errorDescription']:
                    return ["CLICK" if random.randint(1, 3) == 3 else "NO" for _ in range(9)]
                else:
                    raise Exception(
                        f"[ERROR] : Couldn't get response from task, reason {json_response['errorDescription']}")
            elif json_response['errorId'] == 0 and json_response['status'] == "ready":
                return list(json_response['solution'].values())
            else:
                sleep(1)  # Is processing

        raise Exception("[ERROR] : Captcha solver timed out")

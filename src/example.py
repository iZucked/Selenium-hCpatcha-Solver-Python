import os
from json import loads
from CaptchaSolver import CaptchaSolver
from selenium.webdriver import Chrome


def get_anycaptcha_api_key() -> str:
    file_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(file_path, 'r') as file:
        json_data = loads(file.read())
        return json_data['api_keys']['anycaptcha']


def main():
    solver = CaptchaSolver(get_anycaptcha_api_key())

    # Go to Site
    driver = Chrome()
    driver.get("https://maximedrn.github.io/hcaptcha-solver-python-selenium/")

    # Solve Captcha
    if solver.solve_captcha_selenium(driver):
        print("Captcha Solved")
    else:
        print("Failed Solving Captcha")


if __name__ == "__main__":
    main()

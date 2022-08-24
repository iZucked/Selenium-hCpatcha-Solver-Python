# Selenium-hCpatcha-Solver-Python

<center>
    <img src="logo.png" width="640" height="320">
</center>

### What Is This Project?
This is a 'human like' hCaptcha solver for selenium written in python, it utilises the api provided by [anycaptcha](https://anycaptcha.com?referral=13256) and is mainly focused for people who can't solve a captcha through a callback function and need to stay as undetected as possible.

### How Can I Run The Example?
1. Install the dependencies of the project
```vim
pip3 install -r requirements.txt 
```

2. Create an [anycaptcha](https://anycaptcha.com?referral=13256) account, add balance to the account (minimum $1) and then get your API key from the ["User Dashboard"](https://anycaptcha.com/account) page


3. Place your [anycaptcha](https://anycaptcha.com?referral=13256) api key in the sr/config.json file
```vim
{
  "api_keys" : {
    "anycaptcha" : "ENTER_YOU_API_KEY_HERE"
  }
}
```

4. Change the webdriver in src/example.py if you're running Firefox rather than Chrome


5. Run The example.py file and configure the driver if there are any errors which occur
```vim
python3 src/example.py
```
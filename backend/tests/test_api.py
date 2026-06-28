import requests

BASE = 'http://127.0.0.1:5000'

def test_register_login():
    print('开始注册用户')
    r = requests.post(BASE + '/api/register', json={'username': 'testuser', 'password': 'pass123', 'captcha': 'ABCD'})
    print(r.json())
    # login (bypass captcha by first requesting /api/captcha to get one but session required)

if __name__ == '__main__':
    test_register_login()

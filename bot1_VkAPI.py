import requests

getServer = 'https://api.vk.com/method/groups.getLongPollServer?group_id=166256214&v=5.50&access_token=ba777fbd7831e6fc3da8613dd838e2d14b76d8352e5f4aaf1693ccde23c1ee2f347f35d8a33d8291c701d'

response = requests.get(getServer)

key = response.json()['response']['key']


##
url = 'https://lp.vk.com/wh166256214?act=a_check&key=' + key + '&ts=1&wait=25'

response = requests.get(url)

for update in response.json()['updates']: # Проверка каждого элемента списка
	print(update['object']['body'])
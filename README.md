# Telegram boost media stream (PublicLink Bot)

Downloading/Streaming media files from telegram is too slow.
To overcome this this bot will download media forwarded/sent to it and upload it to aws s3 bucket.
So you will get public link or sharable link of media content.

# Workflow of bot:

- User forward/send media to bot.
- Bot will forward message to private telegram account.(There is size limit for bot to download content so we need to forward media from bot to private telegram account)
- Using telegram api private telegram account will download content, upload content and return aws s3 key url to bot.
- Bot reply this url to the user.

# Why need to use telegram bot api?, while we can use telegram api only:
- Here we using heroku and specially i am using heroku free dynamo account so thing is for telegram api  we need to keep listening or we need to keep connection with telegram api server to read new incomming message. 
- In case of telegram bot api there is webhook so on new incomming message telegram bot api will ping our heroku api. If my dynamo free account got sleep so due to this ping it will wake up again and my dynamo hours will not waste.
- Then we will forward whatever message we got from bot to private telegram account after forwarding message we will call telegram api for recent messages with bot and start downloading and uploading media files.

# To run this bot:
- First run this script on local host and login with telegram api to generate telegram session file.
- Then push script on heroku with telegram session file.
- Make random conversation between your private telegram account and bot to grab chat_id of your private account and assign it's value to account_id variable name in script. 
- update all token, keys etc credential in script to make bot working.




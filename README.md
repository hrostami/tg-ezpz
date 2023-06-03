# tg-ezpz
Using reality-ezpz(Reality with sing-box/xray) with a telegram bot!

first run reality-ezpz script for the first time:
```bash
bash <(curl -sL https://raw.githubusercontent.com/aleskxyz/reality-ezpz/master/reality-ezpz.sh)
```
Then setup the telegram bot using commands below
```bash
mkdir tg-ezpz 
curl -Lo /root/tg-ezpz/bot.py https://raw.githubusercontent.com/hrostami/tg-ezpz/master/bot.py
python3 /root/tg-ezpz/bot.py admin_id bot_token domain(optional)
```

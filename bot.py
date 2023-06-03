import subprocess
import logging
import os
import re
import sys
import pickle
try:
    import qrcode
    from PIL import Image
    from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
except ImportError:
    print('\n --> Installing requirements\n')
    requirements = ['Pillow', 'qrcode', 'python-telegram-bot==13.5']
    for library in requirements:
        process = subprocess.run(f'pip3 install {library}'.split(' '))
        if process.returncode != 0:
            print(f"Error occured while installing {library}\nPlease install it manually using:\npip install {library}")
            sys.exit(1)
    import qrcode
    from PIL import Image
    from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters

logging.basicConfig(filename='bot.log', filemode='w', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

if not os.path.exists('/etc/systemd/system/tg-ezpz.service'):
    print('--------> Setting up startup \n\n')
    os.system('curl -Lo /etc/systemd/system/tg-ezpz.service https://raw.githubusercontent.com/hrostami/tg-ezpz/master/tg-ezpz.service')
    os.system('systemctl daemon-reload')
    os.system('sleep 0.2')
    os.system('systemctl enable tg-ezpz.service')

try:
    with open('user_data.pkl', 'rb') as f:
        user_data = pickle.load(f)
except FileNotFoundError:
    user_data = {'ADMIN_ID':int(sys.argv[1]), 'BOT_TOKEN':sys.argv[2]}
    if sys.argv[3] :
        user_data['DOMAIN'] = sys.argv[3]
        domain = sys.argv[3]
    with open('user_data.pkl', 'wb') as f:
        pickle.dump(user_data, f)
bot_token = user_data['BOT_TOKEN']
admin_id = user_data['ADMIN_ID']
if not bot_token:
    logging.error('Telegram bot token is not set ---> exiting')
    sys.exit(1)
else:
    admin_id = int(admin_id)   



ezpz_link = 'https://raw.githubusercontent.com/aleskxyz/reality-ezpz/master/reality-ezpz.sh'


commands_guide = ("Add one of the following commands after /run :\n\n"
                    "transport <tcp|h2|grpc> --> Transport protocol (h2, grpc, tcp, default: tcp)\n\n"
                    "domain <domain.com> -->Domain to use as SNI (default: www.google.com)\n\n"
                    "regenerate -->Regenerate public and private keys\n\n"
                    "default -->Restore default configuration\n\n"
                    "restart -->Restart services\n\n"
                    "enable-safenet -->Enable blocking malware and adult content\n\n"
                    "disable-safenet -->Enable blocking malware and adult content\n\n"
                    "port <port> -->Server port (default: 443)\n\n"
                    "enable-natvps -->Enable natvps.net support\n\n"
                    "disable-natvps -->Disable natvps.net support\n\n"
                    "warp-license <warp-license> -->Add Cloudflare warp+ license\n\n"
                    "enable-warp -->Enable Cloudflare warp\n\n"
                    "disable-warp -->Disable Cloudflare warp\n\n"
                    "core <singbox|xray> -->Select core (xray, singbox, default: singbox)\n\n"
                    "add-user <username> -->Add new user\n\n"
                    "list-users -->List all users\n\n"
                    "show-config <username> -->Shows the config and QR code of the user\n\n"
                    "delete-user <username> -->Delete the user\n\n"
                    )

def check_environment_variable(variable_name):
    if variable_name in os.environ:
        value = os.environ[variable_name]
        logging.info(f"The environment variable '{variable_name}' is set to {value}.")
        return True
    else:
        logging.error(f"The environment variable '{variable_name}' is not set.")
        return False

def generate_command(message):
    parts = message.split()
    if len(parts) >= 2 and parts[0] == "/run":
        command = parts[1]
        arg = None
        command_map = {
            "transport": "<tcp|h2|grpc>",
            "domain": "<domain>",
            "regenerate": None,
            "default": None,
            "restart": None,
            "enable-safenet": None,
            "disable-safenet": None,
            "port": "<port>",
            "enable-natvps": None,
            "disable-natvps": None,
            "warp-license": "<warp-license>",
            "enable-warp": None,
            "disable-warp": None,
            "core": "<singbox|xray>",
            "add-user": "<username>",
            "list-users": None,
            "show-config": "<username>",
            "delete-user": "<username>"
        }

        if command in command_map:
            arg_placeholder = command_map[command]
            if arg_placeholder is not None:
                if len(parts) >= 3:
                    arg = parts[2]
                else:
                    return ""  # Invalid command, missing argument
            command = f"bash <(curl -sL {ezpz_link}) --{command} {arg}" if arg else f"bash <(curl -sL https://bit.ly/realityez) --{command}"
            return command

    return ""

# Command handler
def command_handler(update, context):
    chat_id = update.message.chat_id
    command = generate_command(update.message.text)

    if chat_id == admin_id:
        if command:
            output = subprocess.run(command, shell=True, capture_output=True, text=True, executable="/bin/bash")
            if output.returncode != 0:
                logging.info(f"Command {command} execution failed.")
                logging.info("Error output:", output.stderr)
            else:
                output = output.stdout.strip()
                if output:
                    # Extract the "vless://" part using regex
                    
                    if "vless" in output:
                        vless_part = re.search(r"vless://(.+)", output).group(0)
                        if domain and os.path.exists(f"/var/www/{domain}/html/index.html"):
                            with open(f"/var/www/{domain}/html/index.html", "w") as file:
                                file.write(vless_part)
                        # Create a QR code from the "vless://" part
                        qr = qrcode.QRCode()
                        qr.add_data(vless_part)
                        qr.make(fit=True)
                        qr_img = qr.make_image(fill="black", back_color="white")

                        # Save the QR code image
                        qr_img.save("qrcode.png")
                        update.message.reply_photo(
                            photo=open("qrcode.png", "rb"),
                            caption=vless_part)
                    else:
                        if 0 < len(output) < 50 :
                            update.message.reply_text(output)
                        else:
                            with open("output.txt", "w") as file:
                                file.write(output)
                            update.message.reply_document(
                                document=open("output.txt", "r"),
                                filename="output.txt",
                                caption="Here's the output"
                            )
                else:
                    update.message.reply_text("Command ran successfully")
        else:
            update.message.reply_text(f"Invalid command!\n{commands_guide}")

# Define a handler to send log
def log_handler(update, context):
    chat_id = update.message.chat_id
    if chat_id == admin_id:
        update.message.reply_document(
        document=open("bot.log", "r"),
        filename="bot.log",
        caption="Here's the Log! "
                            )
        
# Define start handler
def start_handler(update, context):
    chat_id = update.message.chat_id
    if not check_environment_variable('ADMIN_ID') :
        os.environ['ADMIN_ID'] = f'{chat_id}'
        context.bot.send_message(chat_id=chat_id, text='Your Id is saved.\nPlease wait 1 minute then try again')
        os.system('reboot')
    elif chat_id == admin_id:
        context.bot.send_message(chat_id=chat_id, text=commands_guide)
    else:
        context.bot.send_message(chat_id=chat_id, text='You are not allowed to send messages to this bot')
 
# Function to handle errors
def error(bot, context):
    logging.info(f" {bot} caused error {context.error}")

# Define the main function
def main():
    # Create a telegram bot and add a command handler for /replace command
    updater = Updater(bot_token)
    updater.dispatcher.add_handler(CommandHandler('run', command_handler))
    updater.dispatcher.add_handler(CommandHandler('start', start_handler))
    updater.dispatcher.add_handler(CommandHandler('log', log_handler))
    updater.dispatcher.add_error_handler(MessageHandler(Filters.all, error))
    updater.bot.send_message(chat_id=admin_id, text="EZPZ bot started")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
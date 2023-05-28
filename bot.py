import subprocess
import logging
import os
import re
import sys

try:
    import qrcode
    from PIL import Image
    from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
except ImportError:
    print('\n --> Installing requirements\n')
    requirements = ['Pillow', 'qrcode', 'python-telegram-bot==13.5']
    for library in requirements:
        subprocess.run(f'pip3 install {library}'.split(' '))
    import qrcode
    from PIL import Image
    from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters

if not os.path.exists('/etc/systemd/system/tg-ezpz.service'):
    print('--------> Setting up startup \n\n')
    os.system('curl -Lo /etc/systemd/system/tg-ezpz.service https://raw.githubusercontent.com/hrostami/tg-ezpz/master/tg-ezpz.service')
    os.system('systemctl daemon-reload')
    os.system('sleep 0.2')
    os.system('systemctl enable tg-ezpz.service')

bot_token = os.environ.get('BOT_TOKEN')
admin_id = os.environ.get('ADMIN_ID')
if not bot_token:
    logging.error('Telegram bot token is not set ---> exiting')
    sys.exit(1)
else:
    admin_id = int(admin_id)   

logging.basicConfig(filename='bot.log', filemode='w', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

ezpz_link = 'https://raw.githubusercontent.com/aleskxyz/reality-ezpz/master/reality-ezpz.sh'

commands_guide = ("Add one of the following commands after /run :\n"
                    "transport <tcp|h2|grpc> --> Transport protocol (h2, grpc, tcp, default: tcp)\n"
                    "domain <domain.com> -->Domain to use as SNI (default: www.google.com)\n"
                    "regenerate -->Regenerate public and private keys\n"
                    "default -->Restore default configuration\n"
                    "restart -->Restart services\n"
                    "enable-safenet -->Enable blocking malware and adult content\n"
                    "disable-safenet -->Enable blocking malware and adult content\n"
                    "port <port> -->Server port (default: 443)\n"
                    "enable-natvps -->Enable natvps.net support\n"
                    "disable-natvps -->Disable natvps.net support\n"
                    "warp-license <warp-license> -->Add Cloudflare warp+ license\n"
                    "enable-warp -->Enable Cloudflare warp\n"
                    "disable-warp -->Disable Cloudflare warp\n"
                    "core <singbox|xray> -->Select core (xray, singbox, default: singbox)\n"
                    "add-user <username> -->Add new user\n"
                    "list-users -->List all users\n"
                    "show-config <username> -->Shows the config and QR code of the user\n"
                    "delete-user <username> -->Delete the user\n"
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
    if not check_environment_variable('ADMIN_ID') :
        logging.error("ADMIN_ID hasn't been set---> exiting")
        print("ADMIN_ID hasn't been set---> exiting")
        sys.exit(1)
    updater.bot.send_message(chat_id=admin_id, text="EZPZ bot started")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
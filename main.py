import logging
import configparser
import urllib.request, json

import telegram.error
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

def stop(update, context):
    updater.stop()

def echo(update, context):
    logging.log(logging.INFO, update.message.chat.username + " " + update.message.text)
    if update.message.chat.username in config['BotConfig']['AdminUsers']:
        # ToDo: Check incoming message -> status, restart <component>, etc.
        status = {
            "data_provider": {
                "status": "N/A",
                "parent_fetched_block": -1,
                "parent_processed_block": -1
            }
        }
        with urllib.request.urlopen("http://"+config['PoolConfig']['MonitorIP']+":3000/ptp/proxy/"+config['PoolConfig']['DataProviderPubKey']+"/GetDataProviderInfo") as url:
            data = json.loads(url.read().decode())
            status["data_provider"]["status"] = data["data"]["status"]
            status["data_provider"]["parent_fetched_block"] = data["data"]["parentFetchedHeight"]
            status["data_provider"]["parent_processed_block"] = data["data"]["parentProcessedHeight"]
            # ToDo: Check if delta is too big and show warning or something
        # ToDo: Fetch Lifecycle manager status
        # ToDo: Format output nicely
        context.bot.send_message(chat_id=update.effective_chat.id, text=status)
        

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')

    updater = Updater(token=config['BotConfig']['TelegramToken'])
    dispatcher = updater.dispatcher
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    stop_handler = CommandHandler('stop', stop)
    dispatcher.add_handler(stop_handler)
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)
    updater.start_polling()
    updater.idle()
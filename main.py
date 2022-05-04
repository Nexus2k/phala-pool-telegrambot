import logging
import configparser
import urllib.request, json
from telegram import BotCommand

import telegram.error
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from natsort import natsorted


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to the Phala/Khala Pool status bot!")
    context.bot.set_my_commands([BotCommand("/status","Show pool status")])

def stop(update, context):
    updater.stop()

def status(update, context):
    logging.log(logging.INFO, update.message.chat.username + " " + update.message.text)
    if update.message.chat.username not in config['BotConfig']['AdminUsers']:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You're not an Admin for this bot!")
        return
    # ToDo: Check incoming message -> status, restart <component>, etc.
    status = {
        "data_provider": {
            "status": "N/A",
            "parent_fetched_block": -1,
            "parent_processed_block": -1,
            "fetched_block": -1,
            "processed_block": -1
        },
        "lifecycle_manager": {
            "workers": []
        }
    }
    with urllib.request.urlopen("http://"+config['PoolConfig']['MonitorIP']+":3000/ptp/proxy/"+config['PoolConfig']['DataProviderPubKey']+"/GetDataProviderInfo") as url:
        data = json.loads(url.read().decode())
        status["data_provider"]["status"] = data["data"]["status"].replace("S_","")
        status["data_provider"]["parent_fetched_block"] = data["data"]["parentFetchedHeight"]
        status["data_provider"]["parent_processed_block"] = data["data"]["parentProcessedHeight"]
        status["data_provider"]["parent_status"] = "✅" if data["data"]["parentFetchedHeight"]-100 < data["data"]["parentProcessedHeight"] else "❎"
        status["data_provider"]["fetched_block"] = data["data"]["paraFetchedHeight"]
        status["data_provider"]["processed_block"] = data["data"]["paraProcessedHeight"]
        status["data_provider"]["para_status"] = "✅" if data["data"]["paraFetchedHeight"]-50 < data["data"]["paraProcessedHeight"] else "❎"
    with urllib.request.urlopen("http://"+config['PoolConfig']['MonitorIP']+":3000/ptp/proxy/"+config['PoolConfig']['LifecycleManagerPubKey']+"/GetWorkerStatus") as url:
        worker_output = []
        data = json.loads(url.read().decode())
        for worker_state in data["data"]["workerStates"]:
            status["lifecycle_manager"]["workers"].append({
                "name": worker_state["worker"]["name"],
                "status": worker_state["status"]
            })
            worker_status = "✅"
            if worker_state["status"] not in ["S_MINING", "S_SYNCHED"]:
                worker_status = "❎"
            if (worker_state["paraHeaderSynchedTo"] < status["data_provider"]["processed_block"]-10):
                worker_status = "❎"
            if worker_state["paraHeaderSynchedTo"] == -1:
                worker_status = "❎"
            worker_output.append("<strong>- {}:</strong> State: {} / Last block: {} {}".format(
                worker_state["worker"]["name"], 
                worker_state["status"].replace("S_",""),
                worker_state["paraHeaderSynchedTo"],worker_status))
    output = """
<strong>DataProvider:</strong>
    <strong>Status:</strong> {status}
    <strong>Parent Chain:</strong> {parent_processed_block}/{parent_fetched_block} {parent_status}
    <strong>Para Chain:</strong> {processed_block}/{fetched_block} {para_status}
<strong>LifecycleManager:</strong>
{}
    """.format("\n".join(natsorted(worker_output)), **status["data_provider"])
    context.bot.send_message(chat_id=update.effective_chat.id, parse_mode="HTML", text=output)


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')

    updater = Updater(token=config['BotConfig']['TelegramToken'])
    dispatcher = updater.dispatcher
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    stop_handler = CommandHandler('stop', stop)
    dispatcher.add_handler(stop_handler)
    status_handler = CommandHandler('status', status)
    dispatcher.add_handler(status_handler)
    updater.start_polling()
    updater.idle()
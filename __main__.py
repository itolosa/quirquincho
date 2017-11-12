from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from config import *
from bitcoinrpc.authproxy import AuthServiceProxy
import hashlib, logging

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Hashing de (string + salt) en algoritmo sha256
def hash(string):
	sha = hashlib.sha256()
	template = (str(string) + salt).encode('utf-8')
	sha.update(template)

	return sha.hexdigest()

# Enviar CHA
def send(bot, update):
	user = update.message.from_user
	userHash = hash(user.id)
	balance = float(rpc.getbalance(userHash))

	try:
		msgSplit = update.message.text.split(" ")

		amount = float(msgSplit[1])
		receptor = msgSplit[2]

		if not len(receptor) == 34 and receptor[0] == 'c':
			sending = "Address inválida"
		else:
			if not balance > amount:
				sending = "Balance insuficiente"
			else:
				if not amount > 0:
					sending	= "Monto inválido"
				else:
					sending = rpc.sendfrom(userHash, receptor, float(amount))
					sending = "txid: " + sending

	except:
		amount = 0.0
		receptor = "invalid"
		sending = "syntax error\nUSO: /send monto address"

	logger.info("send(%i, %f, %s) => %s" % (user.id, amount, receptor, sending))
	update.message.reply_text("%s" % sending)		


# Generar solo 1 address por usuario (user.id)
def address(bot, update):
	user = update.message.from_user
	userHash = hash(user.id)

	addressList = rpc.getaddressesbyaccount(userHash)

	if len(addressList) == 0:
		address = rpc.getnewaddress(userHash)
	else:
		address = addressList[0]

	logger.info("address(%i) => %s" % (user.id, address))
	update.message.reply_text("%s" % address)


# Mostrar balance de usuario
def balance(bot, update):
	user = update.message.from_user
	userHash = hash(user.id)

	balance = float(rpc.getbalance(userHash))

	logger.info("balance(%i) => %f" % (user.id, balance))
	update.message.reply_text("{0:.8f} CHA".format(balance))


# Información de la red
def red(bot, update):
	info = rpc.getmininginfo()

	difficulty = float(info['difficulty'])
	blocks = info['blocks']
	power = info['networkhashps'] / 1000000.0

	delta = difficulty * 2**32 / float(info['networkhashps']) / 60 / 60.0

	logger.info("red() => (%i, %f, %f, %i)" % (blocks, difficulty, power, delta))

	msg = "Bloques: %i\nDificultad: %f\nHashing Power: %f Mh/s" +
		+ "\n\nEl siguiente bloque se creará en %f horas"

	update.message.reply_text(msg % (blocks, difficulty, power, delta))

def error(bot, update, error):
	logger.warning('Update: "%s" - Error: "%s"', update, error)


def main():
	global rpc

	rpc = AuthServiceProxy("http://%s:%s@127.0.0.1:%i"%(RPCuser, RPCpassword, RPCport))
	updater = Updater(token)

	# Get the dispatcher to register handlers
	dp = updater.dispatcher

	dp.add_handler(CommandHandler("address", address))
	dp.add_handler(CommandHandler("balance", balance))
	dp.add_handler(CommandHandler("send", send))
	dp.add_handler(CommandHandler("red", red))

	# log all errors
	dp.add_error_handler(error)

	# Start the Bot
	updater.start_polling()

	logger.info("Init")

	updater.idle()


if __name__ == '__main__':
	main()

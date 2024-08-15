import json
import os
import logging
from os.path import join, dirname
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio
import boto3
import time


# Carregar o TOKEN e instance_id
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
TOKEN = os.environ.get("TOKEN")
instance_id = os.environ.get("INSTANCE_ID")
grupo_id = int(os.environ.get("GRUPO_ID"))

# Configurar o Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


#'State': 'disabled'|'disabling'|'enabled'|'pending'

async def get_state():
	loop = asyncio.get_event_loop()
	return await loop.run_in_executor(None, _get_state)

async def get_ip():
	loop = asyncio.get_event_loop()
	return await loop.run_in_executor(None, _get_ip)

# Função síncrona que realiza a operação real
def _get_state():
	ec2 = boto3.client('ec2')
	response = ec2.describe_instances(InstanceIds=[instance_id])
	instance_state = response['Reservations'][0]['Instances'][0]['State']['Name']
	return instance_state

def _get_ip():
	ec2 = boto3.client('ec2')
	response = ec2.describe_instances(InstanceIds=[instance_id])
	try:

		return response['Reservations'][0]['Instances'][0]['PublicIpAddress']

	except Exception:
		return None


	
# Funções - Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	if update.message.chat_id != grupo_id:
		await update.message.reply_text("O grupo não tem permissão de executar esse comando!!")
		return None
		

	if await get_state() == 'running':
		await update.message.reply_text(f"Instancia já iniciada! Verifique o IP: {await get_ip()}")
		return None
	try:
	
		await update.message.reply_text("Inicializando computador...")
		ec2 = boto3.client('ec2')
		response = ec2.start_instances(InstanceIds=[instance_id])
	
		await update.message.reply_text("Computador Inicialiado! Por favor, espere 60segundos e digite */status* para saber o IP", parse_mode = "Markdown")
	
	
	except Exception as e:
		await update.message.reply_text("Computador *não* iniciado.", parse_mode = "Markdown")
		await update.message.reply_text(f"Error: {e}")


		
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
	if update.message.chat_id != grupo_id:
		await update.message.reply_text("O grupo não tem permissão de executar esse comando!!")
		return None
		
	status = await get_state()
	if status == 'running':
		ip = await get_ip()
		await update.message.reply_text(f"*SERVIDOR RODANDO!!*\nIP: {ip}", parse_mode = "Markdown")
		
	elif  status == 'pending':
		await update.message.reply_text("Computador inicializando. Espere um tempo para digitar novamente */status*", parse_mode = "Markdown")
		
	else:
		await update.message.reply_text("Computador desligado. Inicie ele utilizando */start*", parse_mode = "Markdown")
	
		
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
	if update.message.chat_id != grupo_id:
		await update.message.reply_text("O grupo não tem permissão de executar esse comando!!")
		return None
		
	ec2 = boto3.client('ec2')

	try:
		response = ec2.stop_instances(InstanceIds=[instance_id])
		await update.message.reply_text("Computador desligado com sucesso.")
	except Exception as e:
		await update.message.reply_text("Computador *não* desligado.", parse_mode = "Markdown")
		await update.message.reply_text(f"Error: {e}")
		

async def vitin(update: Update, context: ContextTypes.DEFAULT_TYPE):
	if update.message.chat_id != grupo_id:
		await update.message.reply_text("O grupo não tem permissão de executar esse comando!!")
		return None
	await update.message.reply_text(f"Vitin viadinho da o butico caladinho :O")
		


# Função principal para criar e inicializar a aplicação
application = None
async def initialize_application():
	global application
	if application is None:

		application = ApplicationBuilder().token(TOKEN).build()
		application.add_handler(CommandHandler("start", start))
		application.add_handler(CommandHandler("status", status))
		application.add_handler(CommandHandler("stop", stop))
		application.add_handler(CommandHandler("vitin", vitin))

		await application.initialize()
		await application.start()

# Função que vai cuidar de realizar a comunicação com o webhook
async def handle_request(event):
	try:
		logging.info("Processing request")
		update = Update.de_json(json.loads(event['body']), application.bot)
		await application.process_update(update)
		logging.info("Request processed successfully")
	except Exception as e:
		logging.error(f"Error processing update: {e}")
		raise
		
def lambda_handler(event, context):
	# Inicializar nossa aplicação caso não tenha
	loop = asyncio.get_event_loop()
	if loop.is_closed():
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)

	loop.run_until_complete(initialize_application())
	loop.run_until_complete(handle_request(event))

	# Retornar uma mensagem de sucesso.
	return {
		'statusCode': 200,
		'body': json.dumps('Request processed successfully')
	}

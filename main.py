import json
import requests
import uuid
import discord
from discord.ext import commands
import pysftp
from paramiko import SSHException
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

FTP_HOST = os.getenv('FTP_HOST')
FTP_PORT = int(os.getenv('FTP_PORT'))
FTP_USER = os.getenv('FTP_USER')
FTP_PASS = os.getenv('FTP_PASS')
FTP_FILENAME = 'whitelist.json'

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')

# Conexão com o FTP
def modificar_arquivo_sftp(hostname, port, username, password, caminho_remoto, novo_conteudo):
    try:
        # Desabilitar a verificação da chave do host
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None

        with pysftp.Connection(hostname, port=port, username=username, password=password, cnopts=cnopts) as sftp:
            # Lendo o conteúdo atual do arquivo
            with sftp.open(caminho_remoto, 'r') as arquivo_remoto:
                conteudo_atual = arquivo_remoto.read().decode('utf-8').replace('\n', '')

            # Modificando o conteúdo
            novo_conteudo_completo = conteudo_atual[:-1] + ', ' + str(novo_conteudo) + ']'

            # Escrevendo o novo conteúdo no arquivo
            with sftp.open(caminho_remoto, 'w') as arquivo_remoto:
                arquivo_remoto.write(novo_conteudo_completo)

            print("Arquivo modificado com sucesso!")
    except SSHException as e:
        print(f"Erro SSH: {str(e)}")
    except Exception as e:
        print(f"Ocorreu um erro: {str(e)}")

def request_user_json(nickname):
    import requests
    url = f"https://api.mojang.com/users/profiles/minecraft/{nickname}"
    response = requests.get(url)

    if response.status_code == 200:
        dic = json.loads(response.text)
        uuid_str = dic.pop("id")
        formatted_uuid = str(uuid.UUID(uuid_str))
        dic = {"uuid": formatted_uuid, **dic}
        return json.dumps(dic)
    else:
        return None

# Conexão com o MySQL/MariaDB
# def insert_to_database(nickname):
#     connection = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)
#     try:
#         with connection.cursor() as cursor:
#             sql = "INSERT INTO nicks (nickname) VALUES (%s)"
#             cursor.execute(sql, (nickname,))
#         connection.commit()
#     finally:
#         connection.close()

# Adicionar um nickname ao whitelist
def add_to_whitelist(nickname):
    user_content = request_user_json(nickname)

    if user_content is not None:
        modificar_arquivo_sftp(FTP_HOST, FTP_PORT, FTP_USER, FTP_PASS, FTP_FILENAME, user_content)



intents = discord.Intents.all()
intents.members = True  # Isso é necessário para receber eventos de membros, como quando alguém entra no servidor
intents.messages = True  # Isso é necessário para permitir que o bot leia as mensagens dos usuários
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.command()

@bot.event
# async def on_message(message):
#     print(f"Mensagem recebida: {message.content}")
#     await bot.process_commands(message)

async def apresentar(ctx):
    await ctx.send("Por favor, digite seu nickname do Minecraft:")

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        nickname = await bot.wait_for('message', check=check, timeout=60)
        nickname = nickname.content.strip()
        add_to_whitelist(nickname)

        await ctx.send(f"Nickname '{nickname}' adicionado à whitelist do servidor com sucesso! Lembre-se que para essa alteração ser reconhecida o servidor precisa reiniciar, isso acontece automaticamente às 13h e as 5h\n Bom jogo!")
    except TimeoutError:
        await ctx.send("Tempo esgotado. Por favor, tente novamente.")


# Rodar o bot
bot.run(os.getenv('DISCORD_TOKEN'))
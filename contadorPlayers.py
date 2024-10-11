from mcstatus import JavaServer
import time
import subprocess

# Configurações do servidor
server_address = "localhost"  # IP do servidor Minecraft
server_port = 25565            # Porta do servidor Minecraft

try:
    tempoMAX = 2
    i = tempoMAX
    while i != 0:
        # Conectando ao servidor Minecraft usando o Query
        server = JavaServer(server_address, server_port)
        query = server.query()

        # Obtendo a lista de jogadores
        players_online = query.players.names
        if len(players_online) == 0:
            i -= 1
        else:
            i = tempoMAX
        print(players_online)
    if i == 0:
        subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
        
    time.sleep(60)
except Exception as e:
    print(f"Erro ao conectar ao servidor: {e}")

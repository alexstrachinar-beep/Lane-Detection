import socket

server_address = ('127.0.0.1', 5000)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_socket.connect(server_address)

message = "Hello from sender!"
client_socket.sendall(message.encode('utf-8'))

response = client_socket.recv(1024).decode('utf-8')
print(f"[SENDER] Raspuns primit de la receiver: {response}")

client_socket.close()

import socket

ip = '127.0.0.1'
port = 5001

conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

conn.connect((ip, port))
print('Connected.')

msg = conn.recv(128)
print(f'Received message [{msg}]')

conn.close()

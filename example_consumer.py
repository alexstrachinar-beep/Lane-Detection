import cv2
import object_socket

# Creăm socket-ul de trimitere
s = object_socket.ObjectSenderSocket('127.0.0.1', 5000, 
                                     print_when_awaiting_receiver=True, 
                                     print_when_sending_object=True)

# Deschidem fișierul video
video = cv2.VideoCapture('.\\data\\Venice_10.mp4')

while True:
    ret, frame = video.read()
    
    # Trimitem starea citirii (ret) și cadrul (frame)
    s.send_object((ret, frame))

    # Dacă clipul s-a terminat, oprim bucla
    if not ret:
        break

    # Opțiune de oprire manuală cu 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video.release()
s.close()

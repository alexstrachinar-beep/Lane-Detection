import cv2
import numpy as np
import object_socket

# Conectare la socket-ul sender-ului
s = object_socket.ObjectReceiverSocket('127.0.0.1', 5000, 
                                       print_when_connecting_to_sender=True, 
                                       print_when_receiving_object=True)

while True:
    ret, frame = s.recv_object()
    
    # Dacă nu mai sunt cadre primite, oprim bucla
    if not ret or frame is None:
        break

    # ---------------------------------------------------------------------
    # ALGORITM LANE DETECTION
    # ---------------------------------------------------------------------
    height, width = frame.shape[:2]

    # 1. Convertire în grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 2. Regiunea de Interes (ROI) - Forma de trapez pentru marcajele rutiere
    pt_upper_left = (int(width * 0.45), int(height * 0.75))
    pt_upper_right = (int(width * 0.55), int(height * 0.75))
    pt_lower_right = (int(width * 0.90), height)
    pt_lower_left = (int(width * 0.10), height)

    trap_pts = np.array([[pt_lower_left, pt_upper_left, pt_upper_right, pt_lower_right]], dtype=np.int32)
    
    mask = np.zeros_like(gray)
    cv2.fillPoly(mask, trap_pts, 255)
    roi_gray = cv2.bitwise_and(gray, mask)

    # 3. Binarizare / Threshold (evidențiem marcajele albe)
    _, binary = cv2.threshold(roi_gray, 200, 255, cv2.THRESH_BINARY)

    # 4. Vizualizare marcaje suprapuse pe imaginea originală (Culoare verde)
    final_frame = frame.copy()
    final_frame[binary == 255] = [0, 255, 0]

    # ---------------------------------------------------------------------
    # AFIȘARE REZULTATE
    # ---------------------------------------------------------------------
    cv2.imshow('Original Frame', frame)
    cv2.imshow('Lane Detection Binary', binary)
    cv2.imshow('Lane Detection Final', final_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

s.close()
cv2.destroyAllWindows()

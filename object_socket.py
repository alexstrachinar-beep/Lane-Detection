import socket
import select
import pickle
import datetime

from typing import *


class ObjectSocketParams:
    """Clasă de configurare ce conține constante folosite pentru socket-urile de obiecte.

    Attributes:
        OBJECT_HEADER_SIZE_BYTES (int): Dimensiunea în octeți a antetului care specifică 
            mărimea obiectului (4 octeți).
        DEFAULT_TIMEOUT_S (float): Timpul de așteptare implicit în secunde (1 secundă).
        CHUNK_SIZE_BYTES (int): Dimensiunea maximă a bucăților de date (chunks) 
            citite la un pas (1024 octeți).
    """
    OBJECT_HEADER_SIZE_BYTES = 4
    DEFAULT_TIMEOUT_S = 1
    CHUNK_SIZE_BYTES = 1024


class ObjectSenderSocket:
    """Clasă pentru gestionarea părții de expediere (server/sender) a obiectelor Python prin TCP.

    Attributes:
        ip (str): Adresa IP pe care ascultă conexiunile.
        port (int): Portul pe care ascultă conexiunile.
        sock (socket.socket): Socket-ul principal care ascultă conexiunile primite.
        conn (Optional[socket.socket]): Socket-ul activ de conexiune cu receiver-ul.
        print_when_awaiting_receiver (bool): Indică dacă se afișează mesaje în consolă 
            la așteptarea/conectarea receiver-ului.
        print_when_sending_object (bool): Indică dacă se afișează mesaje în consolă 
            la trimiterea fiecărui obiect.
    """
    ip: str
    port: int
    sock: socket.socket
    conn: socket.socket
    print_when_awaiting_receiver: bool
    print_when_sending_object: bool

    def __init__(self, ip: str, port: int,
                 print_when_awaiting_receiver: bool = False,
                 print_when_sending_object: bool = False):
        """Inițializează socket-ul de sender și așteaptă o conexiune de la un receiver.

        Args:
            ip (str): Adresa IP pe care socket-ul va face bind (ex: '127.0.0.1').
            port (int): Portul pe care socket-ul va face bind.
            print_when_awaiting_receiver (bool, optional): Dacă este True, afișează mesaje de log 
                când așteaptă și stabilește conexiunea. Valoarea implicită este False.
            print_when_sending_object (bool, optional): Dacă este True, afișează mesaje de log 
                la trimiterea de obiecte. Valoarea implicită este False.
        """
        self.ip = ip
        self.port = port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.ip, self.port))
        self.conn = None

        self.print_when_awaiting_receiver = print_when_awaiting_receiver
        self.print_when_sending_object = print_when_sending_object

        self.await_receiver_conection()

    def await_receiver_conection(self):
        """Blochează execuția și așteaptă conectarea unui receiver.

        Metoda pune socket-ul în modul de ascultare (listen) și acceptă prima 
        conexiune primită, stocând socket-ul rezultat în `self.conn`.
        """
        if self.print_when_awaiting_receiver:
            print(f'[{datetime.datetime.now()}][ObjectSenderSocket/{self.ip}:{self.port}] awaiting receiver connection...')

        self.sock.listen(1)
        self.conn, _ = self.sock.accept()

        if self.print_when_awaiting_receiver:
            print(f'[{datetime.datetime.now()}][ObjectSenderSocket/{self.ip}:{self.port}] receiver connected')

    def close(self):
        """Închide conexiunea activă cu receiver-ul și resetează atributul `conn` la None."""
        self.conn.close()
        self.conn = None

    def is_connected(self) -> bool:
        """Verifică dacă există o conexiune activă cu un receiver.

        Returns:
            bool: True dacă conexiunea este activă, False în caz contrar.
        """
        return self.conn is not None

    def send_object(self, obj: Any):
        """Serializează un obiect Python și îl trimite prin conexiunea socket.

        Obiectul este serializat folosind modulul `pickle`. Mai întâi se trimite dimensiunea 
        datelor (pe un număr fix de octeți), urmată de datele serializate propriu-zise.

        Args:
            obj (Any): Orice obiect Python serializabil cu `pickle` care urmează să fie trimis.
        """
        data = pickle.dumps(obj)
        data_size = len(data)
        data_size_encoded = data_size.to_bytes(ObjectSocketParams.OBJECT_HEADER_SIZE_BYTES, 'little')
        self.conn.sendall(data_size_encoded)
        self.conn.sendall(data)
        if self.print_when_sending_object:
            print(f'[{datetime.datetime.now()}][ObjectSenderSocket/{self.ip}:{self.port}] Sent object of size {data_size} bytes.')


class ObjectReceiverSocket:
    """Clasă pentru gestionarea părții de recepție (client/receiver) a obiectelor Python prin TCP.

    Attributes:
        ip (str): Adresa IP a sender-ului la care se conectează.
        port (int): Portul sender-ului la care se conectează.
        conn (socket.socket): Socket-ul conectat la sender.
        print_when_connecting_to_sender (bool): Indică dacă se afișează mesaje la conectare.
        print_when_receiving_object (bool): Indică dacă se afișează mesaje la primirea unui obiect.
    """
    ip: str
    port: int
    conn: socket.socket
    print_when_connecting_to_sender: bool
    print_when_receiving_object: bool

    def __init__(self, ip: str, port: int,
                 print_when_connecting_to_sender: bool = False,
                 print_when_receiving_object: bool = False):
        """Inițializează socket-ul de receiver și se conectează la sender.

        Args:
            ip (str): Adresa IP a sender-ului.
            port (int): Portul sender-ului.
            print_when_connecting_to_sender (bool, optional): Dacă este True, afișează mesaje 
                în timpul procesului de conectare. Valoarea implicită este False.
            print_when_receiving_object (bool, optional): Dacă este True, afișează mesaje 
                la primirea obiectelor. Valoarea implicită este False.
        """
        self.ip = ip
        self.port = port
        self.print_when_connecting_to_sender = print_when_connecting_to_sender
        self.print_when_receiving_object = print_when_receiving_object

        self.connect_to_sender()

    def connect_to_sender(self):
        """Creează socket-ul client și inițiază conexiunea către adresa și portul sender-ului."""
        if self.print_when_connecting_to_sender:
            print(f'[{datetime.datetime.now()}][ObjectReceiverSocket/{self.ip}:{self.port}] connecting to sender...')

        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((self.ip, self.port))

        if self.print_when_connecting_to_sender:
            print(f'[{datetime.datetime.now()}][ObjectReceiverSocket/{self.ip}:{self.port}] connected to sender')

    def close(self):
        """Închide conexiunea cu sender-ul și setează `conn` la None."""
        self.conn.close()
        self.conn = None

    def is_connected(self) -> bool:
        """Verifică starea conexiunii cu sender-ul.

        Returns:
            bool: True dacă socket-ul este conectat, False în caz contrar.
        """
        return self.conn is not None

    def recv_object(self) -> Any:
        """Așteaptă și recepționează un obiect Python complet de la sender.

        Metoda citește mai întâi dimensiunea obiectului din antet, recepționează tot fluxul 
        de date corespunzător și îl reconstruiește (deserializează) cu `pickle`.

        Returns:
            Any: Obiectul Python deserializat primit de la sender.
        """
        obj_size_bytes = self._recv_object_size()
        data = self._recv_all(obj_size_bytes)
        obj = pickle.loads(data)
        if self.print_when_receiving_object:
            print(f'[{datetime.datetime.now()}][ObjectReceiverSocket/{self.ip}:{self.port}] Received object of size {obj_size_bytes} bytes.')
        return obj

    def _recv_with_timeout(self, n_bytes: int, timeout_s: float = ObjectSocketParams.DEFAULT_TIMEOUT_S) -> Optional[bytes]:
        """Așteaptă să citească un număr de octeți cu o limită de timp (timeout).

        Args:
            n_bytes (int): Numărul maxim de octeți de citit.
            timeout_s (float, optional): Timpul maxim de așteptare în secunde. 
                Valoarea implicită este definită în ObjectSocketParams.DEFAULT_TIMEOUT_S.

        Returns:
            Optional[bytes]: Octeții citiți dacă datele devin disponibile înainte de timeout, 
            sau None dacă a expirat timpul de așteptare.
        """
        rlist, _1, _2 = select.select([self.conn], [], [], timeout_s)
        if rlist:
            data = self.conn.recv(n_bytes)
            return data
        else:
            return None  # Returnat doar la timeout

    def _recv_all(self, n_bytes: int, timeout_s: float = ObjectSocketParams.DEFAULT_TIMEOUT_S) -> bytes:
        """Recepționează exact un număr specificat de octeți, gestionând bucăți succesive.

        Args:
            n_bytes (int): Numărul total de octeți care trebuie primiți.
            timeout_s (float, optional): Timpul de timeout aplicat pentru fiecare bucată citită. 
                Valoarea implicită este definită în ObjectSocketParams.DEFAULT_TIMEOUT_S.

        Returns:
            bytes: Datele brute recepționate sub formă de secvență de octeți.

        Raises:
            socket.error: Dacă expiră timpul de așteptare fără a primi noi date 
                înainte de completarea întregului pachet.
        """
        data = []
        left_to_recv = n_bytes
        while left_to_recv > 0:
            desired_chunk_size = min(ObjectSocketParams.CHUNK_SIZE_BYTES, left_to_recv)
            chunk = self._recv_with_timeout(desired_chunk_size, timeout_s)
            if chunk is not None:
                data += [chunk]
                left_to_recv -= len(chunk)
            else:  # Nu mai vin date, timeout
                bytes_received = sum(map(len, data))
                raise socket.error(f'Timeout elapsed without any new data being received. '
                                   f'{bytes_received} / {n_bytes} bytes received.')
        data = b''.join(data)
        return data

    def _recv_object_size(self) -> int:
        """Citește antetul fix al mesajului pentru a determina dimensiunea obiectului ce urmează a fi primit.

        Returns:
            int: Dimensiunea în octeți a obiectului ce urmează să fie recepționat.
        """
        data = self._recv_all(ObjectSocketParams.OBJECT_HEADER_SIZE_BYTES)
        obj_size_bytes = int.from_bytes(data, 'little')
        return obj_size_bytes

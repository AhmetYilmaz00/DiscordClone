import socket
import threading
import sounddevice as sd
import numpy as np

# Sunucu Bilgileri
HOST = '0.0.0.0'  # Tüm ağ arayüzlerinde dinlemek için
PORT = 12345        # Bağlantı noktası (Metin tabanlı iletişim)
AUDIO_PORT = 12346  # Bağlantı noktası (Sesli iletişim)

# Ses Ayarları
CHANNELS = 1
RATE = 44100
CHUNK = 1024

# İstemcileri ve Kullanıcı Adlarını Tutmak İçin Listeler
clients = []
nicknames = []

# Sunucu Soketi Oluşturma (Metin tabanlı iletişim)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

# Sunucu Soketi Oluşturma (Sesli iletişim)
audio_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
audio_server.bind((HOST, AUDIO_PORT))

# Mesajları Tüm İstemcilere Yayınlama Fonksiyonu
def broadcast(message, sender_client=None):
    for client in clients:
        if client != sender_client:
            client.send(message)

# Yeni Bağlantıları Kabul Etme ve İstemcileri Yönetme Fonksiyonu
def handle_client(client):
    while True:
        try:
            message = client.recv(1024)
            if message:
                broadcast(message, client)
        except:
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[index]
            broadcast(f'{nickname} ayrıldı!'.encode('utf-8'))
            nicknames.remove(nickname)
            break

# Yeni İstemcileri Kabul Etme Fonksiyonu
def receive():
    while True:
        client, address = server.accept()
        print(f"Bağlandı: {str(address)}")

        client.send('NICK'.encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8')
        nicknames.append(nickname)
        clients.append(client)

        print(f'Kullanıcı adı: {nickname}')
        broadcast(f'{nickname} katıldı!'.encode('utf-8'))
        client.send('Sunucuya bağlandınız!'.encode('utf-8'))

        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

# Sesli İletişimi Dinleme ve Yayınlama Fonksiyonu
def handle_audio():
    while True:
        try:
            data, addr = audio_server.recvfrom(CHUNK * CHANNELS * 2)
            if data:
                audio_data = np.frombuffer(data, dtype=np.int16)
                sd.play(audio_data, RATE)
                for client_addr in clients:
                    if client_addr.getpeername() != addr:
                        audio_server.sendto(data, client_addr.getpeername())
        except Exception as e:
            print(f"Ses iletiminde hata: {e}")
            break

# Sunucuyu Başlatma
print("Sunucu dinleniyor...")
receive_thread = threading.Thread(target=receive)
receive_thread.start()

audio_thread = threading.Thread(target=handle_audio, daemon=True)
audio_thread.start()
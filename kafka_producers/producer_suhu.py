import json
import time
import random
from kafka import KafkaProducer

# Konfigurasi Producer
bootstrap_servers = 'localhost:29092' # Sesuai port yang di-expose di docker-compose
topic_name = 'sensor-suhu-gudang'
gudang_ids = ["G1", "G2", "G3"]

producer = None
while producer is None:
    try:
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        print("Producer Suhu berhasil terhubung ke Kafka.")
    except Exception as e:
        print(f"Gagal terhubung ke Kafka (Suhu): {e}. Mencoba lagi dalam 5 detik...")
        time.sleep(5)

try:
    gudang_idx = 0
    while True:
        gudang_id = gudang_ids[gudang_idx % len(gudang_ids)]
        suhu = random.randint(70, 90) # Suhu antara 70 dan 90
        
        message = {
            "gudang_id": gudang_id,
            "suhu": suhu
        }
        
        producer.send(topic_name, value=message)
        print(f"Suhu Terkirim: {message}")
        
        gudang_idx += 1
        time.sleep(1) # Kirim data setiap detik
except KeyboardInterrupt:
    print("Producer Suhu dihentikan.")
finally:
    if producer:
        producer.flush()
        producer.close()
        print("Producer Suhu ditutup.")
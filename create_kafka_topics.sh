#!/bin/bash

KAFKA_CONTAINER_NAME="kafka" # Sesuaikan jika nama container Kafka berbeda

# Daftar topik yang akan dibuat
TOPICS=(
  "sensor-suhu-gudang"
  "sensor-kelembaban-gudang"
)

echo "Menunggu Kafka siap..."
# Cek sederhana apakah Kafka sudah bisa dihubungi
# Anda mungkin memerlukan mekanisme yang lebih robust untuk produksi
until docker exec $KAFKA_CONTAINER_NAME kafka-topics --bootstrap-server localhost:9092 --list > /dev/null 2>&1; do
  sleep 5
done
echo "Kafka siap."

for TOPIC_NAME in "${TOPICS[@]}"
do
  echo "Mengecek apakah topik '$TOPIC_NAME' sudah ada..."
  EXISTING_TOPIC=$(docker exec $KAFKA_CONTAINER_NAME kafka-topics --bootstrap-server localhost:9092 --list | grep -w $TOPIC_NAME)

  if [ -z "$EXISTING_TOPIC" ]; then
    echo "Membuat topik: $TOPIC_NAME"
    docker exec $KAFKA_CONTAINER_NAME \
      kafka-topics --create \
      --bootstrap-server localhost:9092 \
      --replication-factor 1 \
      --partitions 1 \
      --topic $TOPIC_NAME
  else
    echo "Topik '$TOPIC_NAME' sudah ada."
  fi
done

echo "Semua topik telah dicek/dibuat."
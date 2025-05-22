# Proyek-Pemantauan-Gudang-Real-time-dengan-Kafka-dan-PySpark_Tsaldia-Hukma-Cita_5027231036

Proyek ini mendemonstrasikan penggunaan Apache Kafka dan PySpark untuk memantau kondisi gudang penyimpanan secara real-time. Data suhu dan kelembaban dari sensor disimulasikan, dikirim melalui Kafka, dan kemudian dikonsumsi serta diolah oleh PySpark untuk mendeteksi kondisi abnormal dan kritis.

## 🎯 Latar Belakang Masalah

> Sebuah perusahaan logistik mengelola beberapa gudang penyimpanan yang menyimpan barang sensitif seperti makanan, obat-obatan, dan elektronik. Untuk menjaga kualitas penyimpanan, gudang-gudang tersebut dilengkapi dengan dua jenis sensor: Sensor Suhu dan Sensor Kelembaban. Sensor akan mengirimkan data setiap detik. Perusahaan ingin memantau kondisi gudang secara real-time untuk mencegah kerusakan barang akibat suhu terlalu tinggi atau kelembaban berlebih.

## 📋 Tugas yang Diimplementasikan

1.  **Pembuatan Topik Kafka**: Dua topik Kafka (`sensor-suhu-gudang` dan `sensor-kelembaban-gudang`) dibuat untuk menerima data sensor.
2.  **Simulasi Data Sensor (Producer Kafka)**: Dua producer Kafka terpisah dibuat untuk mengirimkan data suhu dan kelembaban simulasi setiap detik untuk minimal 3 gudang (G1, G2, G3).
3.  **Konsumsi dan Olah Data dengan PySpark**:
    *   Consumer PySpark dibuat untuk membaca data dari kedua topik Kafka.
    *   Filtering dilakukan untuk mendeteksi suhu > 80°C dan kelembaban > 70%.
4.  **Penggabungan Stream dan Peringatan Kritis**: Stream dari kedua sensor digabungkan berdasarkan `gudang_id` dan window waktu untuk mendeteksi kondisi bahaya ganda (suhu tinggi dan kelembaban tinggi pada gudang yang sama).

## 🎓 Tujuan Pembelajaran

*   Memahami cara kerja Apache Kafka dalam pengolahan data real-time.
*   Membuat Kafka Producer dan Consumer untuk simulasi data sensor.
*   Mengimplementasikan stream filtering dengan PySpark.
*   Melakukan join multi-stream dan analisis gabungan dari berbagai sensor.
*   Mencetak hasil analitik berbasis kondisi kritis gudang ke dalam output console.

## 📁 Struktur Proyek

Berikut adalah struktur direktori proyek:
```text
proyek-kafka-spark/
├── docker-compose.yml            # Mendefinisikan service Zookeeper, Kafka, Spark Master & Worker
├── kafka_producers/              # Direktori untuk skrip producer Kafka
│   ├── producer_suhu.py          # Producer untuk data suhu
│   ├── producer_kelembaban.py    # Producer untuk data kelembaban
│   └── requirements.txt          # Dependensi Python untuk producer (kafka-python)
├── spark_consumer/               # Direktori untuk skrip PySpark consumer/processor
│   └── pyspark_processor.py      # Skrip PySpark untuk mengonsumsi dan mengolah data
└── create_kafka_topics.sh      # Skrip bash untuk membuat topik Kafka secara otomatis
```

# 🚀 Realtime Warehouse Monitoring with Kafka & PySpark

Sistem ini memantau suhu dan kelembaban gudang secara real-time menggunakan:
- **Kafka** sebagai data streaming platform
- **Docker** untuk container orchestration
- **PySpark** untuk pemrosesan data stream

---

## ⚙️ Struktur File & Penjelasan Fungsi

### 📦 `docker-compose.yml`
- Menjalankan container untuk:
  * Zookeeper (`2181`)
  * Kafka (`9092`, `29092`)
  * Spark Master (`8080`, `7077`)
  * Spark Worker
- Membuat jaringan Docker: `kafka-spark-net`
- Mount direktori lokal `./spark_consumer` ke `/opt/bitnami/spark/app` agar script `PySpark` dapat diakses.

### 🛰️ `kafka_producers/producer_suhu.py`
- Kafka **producer** yang:
  * Mengirim data suhu (dalam format JSON) ke topik `sensor-suhu-gudang`
  * Data simulasi: `{"gudang_id": "GX", "suhu": YY}`
  * Berputar ke gudang `G1`, `G2`, `G3` setiap detik

### 💧 `kafka_producers/producer_kelembaban.py`
- Kafka **producer** kelembaban:
  * Mengirim data ke topik `sensor-kelembaban-gudang`
  * Format JSON: `{"gudang_id": "GX", "kelembaban": ZZ}`

### 📄 `kafka_producers/requirements.txt`
- Dependensi:
  ```text
  kafka-python

## 🔥 `spark_consumer/pyspark_processor.py`

**PySpark consumer + processor**:

- Membaca stream dari Kafka
- Parsing JSON dan menambahkan timestamp
- Melakukan **stream-stream join** suhu & kelembaban berdasarkan `gudang_id` dan window waktu
- Menentukan status:
  - `Aman`
  - `Suhu tinggi`
  - `Kelembaban tinggi`
  - `Bahaya tinggi! Barang berisiko rusak`
- Menggunakan `foreachBatch` untuk mencetak status per gudang ke konsol (**kecuali Aman**)

---

## ⚙️ `create_kafka_topics.sh`

Script shell untuk membuat topik Kafka:
- `sensor-suhu-gudang`
- `sensor-kelembaban-gudang`

Digunakan sekali saat setup awal.

---

## 🛠️ Contoh Kode Utama

### ✅ Kafka Producer (Contoh Suhu)

```python
from kafka import KafkaProducer
import json, time, random

producer = KafkaProducer(
    bootstrap_servers='localhost:29092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

gudang_ids = ["G1", "G2", "G3"]
while True:
    for gudang_id in gudang_ids:
        suhu = random.randint(70, 90)
        msg = {"gudang_id": gudang_id, "suhu": suhu}
        producer.send("sensor-suhu-gudang", value=msg)
        print(f"Dikirim: {msg}")
        time.sleep(1)
### ✅ PySpark - Join + Peringatan

```python
status_df = joined_df.select(
    col("gudang_id_suhu").alias("gudang_id"),
    col("suhu"),
    col("kelembaban")
).withColumn(
    "status_text",
    when((col("suhu") > 80) & (col("kelembaban") > 70), "Bahaya tinggi! Barang berisiko rusak")
    .when((col("suhu") > 80), "Suhu tinggi, kelembaban normal")
    .when((col("kelembaban") > 70), "Kelembaban tinggi, suhu aman")
    .otherwise("Aman")
)
```
## Output
![Screenshot (419)](https://github.com/user-attachments/assets/713c3680-0730-4a4c-a2c7-2da5201cd028)

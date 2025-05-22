from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, expr, current_timestamp, window, when
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType

# Inisialisasi Spark Session
spark = SparkSession.builder \
    .appName("RealtimeWarehouseMonitor") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN") # Mengurangi log spam

# Konfigurasi Kafka
kafka_bootstrap_servers = "kafka:9092"
topic_suhu = "sensor-suhu-gudang"
topic_kelembaban = "sensor-kelembaban-gudang"

# Schema
schema_suhu = StructType([StructField("gudang_id", StringType()), StructField("suhu", IntegerType())])
schema_kelembaban = StructType([StructField("gudang_id", StringType()), StructField("kelembaban", IntegerType())])

# Read Streams
df_suhu_raw = spark.readStream.format("kafka").option("kafka.bootstrap.servers", kafka_bootstrap_servers).option("subscribe", topic_suhu).option("startingOffsets", "latest").load()
df_suhu = df_suhu_raw.selectExpr("CAST(value AS STRING) as json_value").select(from_json(col("json_value"), schema_suhu).alias("data")).select("data.gudang_id", "data.suhu").withColumn("timestamp_suhu", current_timestamp())

df_kelembaban_raw = spark.readStream.format("kafka").option("kafka.bootstrap.servers", kafka_bootstrap_servers).option("subscribe", topic_kelembaban).option("startingOffsets", "latest").load()
df_kelembaban = df_kelembaban_raw.selectExpr("CAST(value AS STRING) as json_value").select(from_json(col("json_value"), schema_kelembaban).alias("data")).select("data.gudang_id", "data.kelembaban").withColumn("timestamp_kelembaban", current_timestamp())

# --- Tugas 3a & 3b: Konsumsi dan Filtering Individual (DINONAKTIFKAN outputnya) ---
# query_peringatan_suhu = df_suhu \
#     .filter(col("suhu") > 80) \
#     .selectExpr("'[Peringatan Suhu Tinggi]' as tipe_peringatan", "gudang_id", "concat('Suhu: ', suhu, '°C') as detail") \
#     .writeStream \
#     .outputMode("update") \
#     .format("console") \
#     .option("truncate", "false") \
#     .start()

# query_peringatan_kelembaban = df_kelembaban \
#     .filter(col("kelembaban") > 70) \
#     .selectExpr("'[Peringatan Kelembaban Tinggi]' as tipe_peringatan", "gudang_id", "concat('Kelembaban: ', kelembaban, '%') as detail") \
#     .writeStream \
#     .outputMode("update") \
#     .format("console") \
#     .option("truncate", "false") \
#     .start()

# --- Tugas 4: Gabungkan Stream dan Peringatan Gabungan ---
df_suhu_watermarked = df_suhu.withWatermark("timestamp_suhu", "15 seconds")
df_kelembaban_watermarked = df_kelembaban.withWatermark("timestamp_kelembaban", "15 seconds")

suhu_aliased = df_suhu_watermarked.alias("temp").select(col("temp.gudang_id").alias("gudang_id_suhu"), col("temp.suhu"), col("temp.timestamp_suhu"))
kelembaban_aliased = df_kelembaban_watermarked.alias("hum").select(col("hum.gudang_id").alias("gudang_id_kelembaban"), col("hum.kelembaban"), col("hum.timestamp_kelembaban"))

join_condition = expr("gudang_id_suhu = gudang_id_kelembaban AND timestamp_kelembaban >= timestamp_suhu - interval 10 seconds AND timestamp_kelembaban <= timestamp_suhu + interval 10 seconds")
joined_df = suhu_aliased.join(kelembaban_aliased, join_condition, "inner")

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

def process_and_print_gabungan(df, epoch_id):
    if df.count() > 0:
        collected_data = df.collect()
        for row in collected_data:
            gudang_id = row["gudang_id"]
            suhu = row["suhu"]
            kelembaban = row["kelembaban"]
            status = row["status_text"]

            if status == "Aman": # Jika tidak ingin menampilkan status "Aman"
                continue

            header_prefix = ""
            if status == "Bahaya tinggi! Barang berisiko rusak":
                header_prefix = "[PERINGATAN KRITIS]"
            elif status == "Suhu tinggi, kelembaban normal":
                header_prefix = "[Peringatan Suhu Tinggi]"
            elif status == "Kelembaban tinggi, suhu aman":
                header_prefix = "[Peringatan Kelembaban Tinggi]"
            
            if header_prefix: # Hanya cetak jika ada header (bukan 'Aman' yang di-skip)
                print(f"{header_prefix} Gudang {gudang_id}:")
                print(f"  - Suhu: {suhu}°C")
                print(f"  - Kelembaban: {kelembaban}%")
                print(f"  - Status: {status}")
                print("")

query_gabungan = status_df \
    .writeStream \
    .outputMode("append") \
    .foreachBatch(process_and_print_gabungan) \
    .start()

spark.streams.awaitAnyTermination()
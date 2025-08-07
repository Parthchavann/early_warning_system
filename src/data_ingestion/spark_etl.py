from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, from_json, window, avg, stddev, max, min,
    when, lit, to_timestamp, udf, collect_list, struct
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    TimestampType, IntegerType, ArrayType
)
from delta import DeltaTable, configure_spark_with_delta_pip
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PatientDataETL:
    def __init__(self, app_name: str = "PatientEWS_ETL"):
        builder = SparkSession.builder \
            .appName(app_name) \
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
            .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoint") \
            .config("spark.sql.shuffle.partitions", "10")
            
        self.spark = configure_spark_with_delta_pip(builder).getOrCreate()
        self.spark.sparkContext.setLogLevel("WARN")
        
    def get_vitals_schema(self) -> StructType:
        return StructType([
            StructField("patient_id", StringType(), False),
            StructField("timestamp", TimestampType(), False),
            StructField("heart_rate", DoubleType(), True),
            StructField("bp_systolic", DoubleType(), True),
            StructField("bp_diastolic", DoubleType(), True),
            StructField("respiratory_rate", DoubleType(), True),
            StructField("temperature", DoubleType(), True),
            StructField("spo2", DoubleType(), True),
            StructField("gcs", IntegerType(), True)
        ])
        
    def get_lab_results_schema(self) -> StructType:
        return StructType([
            StructField("patient_id", StringType(), False),
            StructField("timestamp", TimestampType(), False),
            StructField("test_name", StringType(), False),
            StructField("value", DoubleType(), False),
            StructField("unit", StringType(), True),
            StructField("is_critical", IntegerType(), True)
        ])
        
    def stream_from_kafka(
        self,
        bootstrap_servers: str,
        topic: str,
        schema: StructType
    ) -> DataFrame:
        df = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", bootstrap_servers) \
            .option("subscribe", topic) \
            .option("startingOffsets", "latest") \
            .option("failOnDataLoss", "false") \
            .load()
            
        parsed_df = df.select(
            from_json(col("value").cast("string"), schema).alias("data")
        ).select("data.*")
        
        return parsed_df
        
    def calculate_ews_score(self, vitals_df: DataFrame) -> DataFrame:
        ews_df = vitals_df \
            .withColumn("hr_score", 
                when((col("heart_rate") < 40) | (col("heart_rate") > 130), 3)
                .when((col("heart_rate") < 50) | (col("heart_rate") > 110), 2)
                .when((col("heart_rate") < 60) | (col("heart_rate") > 100), 1)
                .otherwise(0)) \
            .withColumn("rr_score",
                when((col("respiratory_rate") < 8) | (col("respiratory_rate") > 30), 3)
                .when((col("respiratory_rate") < 10) | (col("respiratory_rate") > 25), 2)
                .when((col("respiratory_rate") < 12) | (col("respiratory_rate") > 20), 1)
                .otherwise(0)) \
            .withColumn("temp_score",
                when((col("temperature") < 35.5) | (col("temperature") > 38.5), 3)
                .when((col("temperature") < 36.0) | (col("temperature") > 38.0), 2)
                .when((col("temperature") < 36.5) | (col("temperature") > 37.5), 1)
                .otherwise(0)) \
            .withColumn("spo2_score",
                when(col("spo2") < 85, 3)
                .when(col("spo2") < 90, 2)
                .when(col("spo2") < 94, 1)
                .otherwise(0)) \
            .withColumn("bp_score",
                when((col("bp_systolic") < 90) | (col("bp_systolic") > 180), 3)
                .when((col("bp_systolic") < 100) | (col("bp_systolic") > 160), 2)
                .when((col("bp_systolic") < 110) | (col("bp_systolic") > 140), 1)
                .otherwise(0)) \
            .withColumn("gcs_score",
                when(col("gcs") < 9, 3)
                .when(col("gcs") < 12, 2)
                .when(col("gcs") < 15, 1)
                .otherwise(0))
                
        ews_df = ews_df.withColumn("total_ews_score",
            col("hr_score") + col("rr_score") + col("temp_score") + 
            col("spo2_score") + col("bp_score") + col("gcs_score")
        )
        
        return ews_df
        
    def aggregate_vitals_window(
        self,
        vitals_df: DataFrame,
        window_duration: str = "5 minutes",
        slide_duration: str = "1 minute"
    ) -> DataFrame:
        aggregated = vitals_df \
            .withWatermark("timestamp", "10 minutes") \
            .groupBy(
                col("patient_id"),
                window(col("timestamp"), window_duration, slide_duration)
            ) \
            .agg(
                avg("heart_rate").alias("avg_heart_rate"),
                stddev("heart_rate").alias("std_heart_rate"),
                max("heart_rate").alias("max_heart_rate"),
                min("heart_rate").alias("min_heart_rate"),
                avg("bp_systolic").alias("avg_bp_systolic"),
                avg("bp_diastolic").alias("avg_bp_diastolic"),
                avg("respiratory_rate").alias("avg_respiratory_rate"),
                avg("temperature").alias("avg_temperature"),
                avg("spo2").alias("avg_spo2"),
                avg("total_ews_score").alias("avg_ews_score"),
                max("total_ews_score").alias("max_ews_score")
            ) \
            .select(
                col("patient_id"),
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                "*"
            )
            
        return aggregated
        
    def detect_sepsis_risk(self, df: DataFrame) -> DataFrame:
        sepsis_df = df \
            .withColumn("sirs_criteria",
                (when(col("avg_heart_rate") > 90, 1).otherwise(0) +
                 when(col("avg_respiratory_rate") > 20, 1).otherwise(0) +
                 when((col("avg_temperature") < 36) | (col("avg_temperature") > 38), 1).otherwise(0))
            ) \
            .withColumn("qsofa_score",
                (when(col("avg_respiratory_rate") >= 22, 1).otherwise(0) +
                 when(col("avg_bp_systolic") <= 100, 1).otherwise(0))
            ) \
            .withColumn("sepsis_risk_score",
                when((col("sirs_criteria") >= 2) & (col("qsofa_score") >= 2), 0.9)
                .when((col("sirs_criteria") >= 2) | (col("qsofa_score") >= 2), 0.6)
                .when((col("sirs_criteria") >= 1) | (col("qsofa_score") >= 1), 0.3)
                .otherwise(0.1)
            )
            
        return sepsis_df
        
    def write_to_delta(
        self,
        df: DataFrame,
        path: str,
        mode: str = "append",
        partition_by: Optional[list] = None
    ):
        writer = df.writeStream \
            .format("delta") \
            .outputMode(mode) \
            .option("checkpointLocation", f"{path}/_checkpoint")
            
        if partition_by:
            writer = writer.partitionBy(*partition_by)
            
        query = writer.start(path)
        return query
        
    def run_etl_pipeline(
        self,
        kafka_servers: str,
        vitals_topic: str,
        delta_path: str
    ):
        logger.info("Starting ETL pipeline...")
        
        vitals_stream = self.stream_from_kafka(
            kafka_servers,
            vitals_topic,
            self.get_vitals_schema()
        )
        
        ews_stream = self.calculate_ews_score(vitals_stream)
        
        aggregated_stream = self.aggregate_vitals_window(ews_stream)
        
        risk_stream = self.detect_sepsis_risk(aggregated_stream)
        
        query = self.write_to_delta(
            risk_stream,
            delta_path,
            partition_by=["patient_id"]
        )
        
        logger.info(f"ETL pipeline started. Query ID: {query.id}")
        return query
        
    def stop(self):
        self.spark.stop()
        logger.info("Spark session stopped")
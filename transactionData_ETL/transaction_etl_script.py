import sys
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql.functions import trim, col
from pyspark.sql.types import DoubleType
from awsglue.dynamicframe import DynamicFrame

# AWS Glue
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Reading data
df = spark.read.option("header", "true").csv("s3://my-ecom-raw-data-12345/transaction_data.csv")

duplicate_keys = df.groupBy("KEY").count().filter("count > 1")
duplicate_keys.show()

# Dropping nulls amd duplicate rows
df = df.dropna(subset=["KEY", "OBS_VALUE"]).dropDuplicates(["KEY"])

# Trimming
for colname in df.columns:
    if df.schema[colname].dataType.simpleString() == 'string':
        df = df.withColumn(colname, trim(col(colname)))

# OBS_VALUE to double
df = df.withColumn("OBS_VALUE", col("OBS_VALUE").cast(DoubleType()))

# Parquet
df.write.mode("overwrite").parquet("s3://my-ecom-processed-data-12345/transaction-data-cleaned/")

# DynamoDB: KEY->primary key
dyn_df = DynamicFrame.fromDF(df, glueContext, "dyn_df")
glueContext.write_dynamic_frame.from_options(
    frame=dyn_df,
    connection_type="dynamodb",
    connection_options={
        "dynamodb.output.tableName": "transaction_data",
        "dynamodb.throughput.write.percent": "0.5"
    }
)

job.commit()

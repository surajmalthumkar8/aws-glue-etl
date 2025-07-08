import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql.functions import col, trim
from pyspark.sql.types import DoubleType
from awsglue.dynamicframe import DynamicFrame

# Boilerplate
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Step 1: Read raw CSV from S3
raw_df = spark.read.option("header", "true").csv("s3://my-ecom-raw-data-12345/us-shein-appliances-3987.csv")

# Step 2: Rename column for DynamoDB compatibility
clean_df = (
    raw_df.withColumnRenamed("goods-title-link--jump href", "ProductID")
          .dropna(subset=["ProductID"])
          .dropDuplicates(["ProductID"])
)

# Optional: Clean columns (e.g., trim product name if exists)
if "goods-title-link" in clean_df.columns:
    clean_df = clean_df.withColumn("goods-title-link", trim(col("goods-title-link")))

# Optional: Cast price
if "price" in clean_df.columns:
    clean_df = clean_df.withColumn("price", col("price").cast(DoubleType()))

# Step 3: Write cleaned data to S3 in Parquet
clean_df.write.mode("overwrite").parquet("s3://my-ecom-processed-data-12345/cleaned-products/")

# Step 4: Write to DynamoDB (table with ProductID as primary key)
dyn_df = DynamicFrame.fromDF(clean_df, glueContext, "dyn_df")
glueContext.write_dynamic_frame.from_options(
    frame=dyn_df,
    connection_type="dynamodb",
    connection_options={
        "dynamodb.output.tableName": "EcomProducts",
        "dynamodb.throughput.write.percent": "0.5"
    }
)

job.commit()

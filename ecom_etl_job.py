import sys
import re
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql.functions import col, trim, regexp_replace, udf
from pyspark.sql.types import DoubleType
from awsglue.dynamicframe import DynamicFrame

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

raw_df = spark.read.option("header", "true").csv("s3://my-ecom-raw-data-12345/us-shein-appliances-3987.csv")

#Cleaning column names
for col_name in raw_df.columns:
    clean_name = re.sub(r'[^0-9a-zA-Z_]', '_', col_name.strip())
    raw_df = raw_df.withColumnRenamed(col_name, clean_name)


df = raw_df.withColumnRenamed("goods_title_link__jump_href", "ProductID")

df = df.dropna(subset=["ProductID"])

#Droping duplicate ProductIDs
df = df.dropDuplicates(["ProductID"]).dropDuplicates()

# Trim
if "goods_title_link" in df.columns:
    df = df.withColumn("goods_title_link", trim(col("goods_title_link")))

# float
if "price" in df.columns:
    df = df.withColumn("price", col("price").cast(DoubleType()))

if "discount" in df.columns:
    df = df.withColumn("discount_pct", parse_discount(col("discount")))

# Drop unnamed columns
columns_to_drop = [col for col in df.columns if col.startswith("_") or col.lower().startswith("unnamed")]
df = df.drop(*columns_to_drop)

# Parquet
df.write.mode("overwrite").parquet("s3://my-ecom-processed-data-12345/cleaned-products/")

# DynamoDB
dyn_df = DynamicFrame.fromDF(df, glueContext, "dyn_df")
glueContext.write_dynamic_frame.from_options(
    frame=dyn_df,
    connection_type="dynamodb",
    connection_options={
        "dynamodb.output.tableName": "EcomProducts",
        "dynamodb.throughput.write.percent": "0.5"
    }
)

job.commit()

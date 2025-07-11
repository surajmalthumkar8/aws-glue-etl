## AWS Glue ETL Pipeline for E-commerce and Transaction Data

Fully automated ETL pipeline built on AWS using Glue, S3, DynamoDB, Athena, and CloudFormation. It processes raw datasets from e-commerce and Transaction data and transforms them into clean, queryable formats for analytics and storage.

---

## 🧱 Architecture Overview

<img width="720" height="720" alt="transactionDataETL_architecture" src="https://github.com/user-attachments/assets/0ffd84c3-e699-4688-8238-ca108dcbffa8" />


### AWS CLI Commands:
aws cloudformation deploy --stack-name EcomETLStack --template-file ecom-etl-stack.yaml --capabilities CAPABILITY_NAMED_IAM

aws s3 cp ecom_etl_job.py s3://my-ecom-raw-data-12345/scripts/ecom_etl_job.py

aws glue start-crawler --name EcommerceRawCrawler

aws glue start-job-run --job-name EcomETLJob

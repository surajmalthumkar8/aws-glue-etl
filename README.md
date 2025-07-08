###
aws cloudformation deploy --stack-name EcomETLStack --template-file ecom-etl-stack.yaml --capabilities CAPABILITY_NAMED_IAM


aws s3 cp ecom_etl_job.py s3://my-ecom-raw-data-12345/scripts/ecom_etl_job.py
aws glue start-crawler --name EcommerceRawCrawler

aws glue start-job-run --job-name EcomETLJob
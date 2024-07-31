from fastapi import FastAPI, HTTPException, Request
import boto3
import json
import uvicorn
from pydantic import BaseModel
import time
import logging

# CloudWatch client
cloudwatch = boto3.client('cloudwatch', region_name='ap-south-1')

# Initialize logger
logger = logging.getLogger("api_logger")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
file_handler = logging.FileHandler("api_logs.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
logger.addHandler(file_handler)

endpoint_name = "fastapi-sentiment-classifier"
boto_session = boto3.Session(region_name='ap-south-1')
sagemaker_runtime = boto_session.client('sagemaker-runtime')

app = FastAPI()

class Review(BaseModel):
    text: str

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} (processed in {process_time:.2f} seconds)")
    
    # Send custom metrics to CloudWatch
    cloudwatch.put_metric_data(
        Namespace='API',
        MetricData=[
            {
                'MetricName': 'ProcessingTime',
                'Dimensions': [
                    {
                        'Name': 'Endpoint',
                        'Value': endpoint_name
                    },
                ],
                'Value': process_time,
                'Unit': 'Seconds'
            },
            {
                'MetricName': 'ResponseStatus',
                'Dimensions': [
                    {
                        'Name': 'Endpoint',
                        'Value': endpoint_name
                    },
                ],
                'Value': response.status_code,
                'Unit': 'Count'
            },
        ]
    )
    return response

@app.post("/predict/")
async def predict(review: Review):
    input_data = {"inputs": review.text}

    payload = json.dumps(input_data)
    try:
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            Body=payload,
            ContentType='application/json'
        )
    except Exception as e:
        logger.error(f"Error invoking SageMaker endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error invoking model endpoint")

    result = response['Body'].read().decode('utf-8')
    result = json.loads(result)
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
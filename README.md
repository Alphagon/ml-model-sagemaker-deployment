# AWS ML Model Deployment
### Setting up AWS
Create an AWS account [Free tier].

#### User Group Creation
Once the account setup is over, go to "IAM" and Create a user group with following permission policies enabled or checked
- AmazonS3FullAccess
- AmazonSageMakerFullAccess

#### Adding User to the User Group
Next go to "Users" and create a user and add this user to the above created User Group
Once created, select that user and create an access key for "Command Line Interface".
Once the access key is created notedown the 
- ACCESS KEY
- SECRET ACCESS KEY

#### Role Creation
Next go to roles and create a role with following policies, which we will later use it in creating an endpoint
- AmazonSageMakerFullAccess
- AmazonS3FullAccess 
And note the ARN of this new role.


### Setting up AWS CLI and Libraries for Local Machine

#### Installing AWS CLI on Local Machine
Next move on to your local machine and download the Amazon CLI
1. Download the cli package from amazon `curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"`
2. Extract the downloaded package `unzip -u awscliv2.zip`
3. Go inside the extracted folder and install it sudo ./install
4. Check the installation with the followingaws-cli/2.15.30 Python/3.11.6 Linux/5.10.205-195.807.amzn2.x86_64 botocore/2.4.5 command `aws --version`
You'll get an output something like `aws-cli/2.15.30 Python/3.11.6 Linux/5.10.205-195.807.amzn2.x86_64 botocore/2.4.5`

Next you need to configure the AWS CLI with the KEY and SECRET you created.
```
$ aws configure
AWS Access Key ID [None]: your_access_key_id
AWS Secret Access Key [None]: your_secret_access_key
Default region name [None]: us-west-2
Default output format [None]: json
```

#### Installing AWS python packages
Next download the python packages required to access AWS 
- boto3
- sagemaker


### Endpoint Creation

#### Creating zipped model
For creating an endpoint I'll be using a huggingface model 
`https://huggingface.co/finiteautomata/beto-sentiment-analysis/tree/main`

Download the model and the model dependency files
`git clone https://huggingface.co/finiteautomata/beto-sentiment-analysis`

Next create a tar file to push it to S3 bucket
```
cd beto-sentiment-analysis
tar zcvf model.tar.gz *
```

#### Pushing zipped model to S3
Create a S3 bucket to push the file too
```
aws s3api create-bucket \
    --bucket sentiment-classification-fastapi \
    --region ap-south-1 \
    --create-bucket-configuration LocationConstraint=ap-south-1
```
Any region outside of `us-east-1` requires `LocationConstraint` to be specified in order to create the bucket in desired location.

Push the .tar.gz file to S3 bucket
`aws s3 cp model.tar.gz s3://sentiment-classification-fastapi/`


### Deploying endpoint from Local Machine
Follow the following steps to create an endpoint
```
from sagemaker.huggingface.model import HuggingFaceModel

role = "arn:aws:iam::011528263565:role/dev" # Past the ARN of the role created
endpoint_name = "fastapi-sentiment-classifier" # Name the endpoint

# create Hugging Face Model Class
huggingface_model = HuggingFaceModel(
   model_data="s3://sentiment-classification-fastapi/model.tar.gz",  # path to your trained SageMaker model
   role=role,                                            # IAM role with permissions to create an endpoint
   transformers_version="4.26",                           # Mention the Transformers version used
   pytorch_version="1.13",                                # PyTorch version used
   py_version='py39',                                    # And Python version used
)

# deploy model to SageMaker Inference
predictor = huggingface_model.deploy(
   initial_instance_count=1,
   instance_type="ml.m5.xlarge",
   endpoint_name= endpoint_name
)

# Print the endpoint name
print(f'Model deployed at endpoint: {predictor.endpoint_name}')
```

Once endpoint is successfully created you can test it out using the following code
```
import boto3

endpoint_name = "fastapi-sentiment-classifier" 
boto_session = boto3.Session(region_name='ap-south-1')
sagemaker_runtime = boto_session.client('sagemaker-runtime')

input_data = {
   "inputs": "Camera - You are awarded a SiPix Digital Camera! call 09061221066 fromm landline. Delivery within 28 days."
}

payload = json.dumps(input_data)

# Make the prediction
response = sagemaker_runtime.invoke_endpoint(
    EndpointName=endpoint_name,
    Body=payload,
    ContentType='application/json'  # Set the content type to JSON
)

result = response['Body'].read().decode('utf-8')
print("Prediction result:", result)
```


### Wrapping the endpoint with FastAPI

First install the requirements 
- uvicorn
- fastapi
- pydantic

and execute the main.py code with the following command
`uvicorn main:app --reload`

#### Testing the API
Test the API using the following address `http://0.0.0.0:8000/docs`

or request using CURL
```
curl -X 'POST' \
  'http://localhost:8000/predict' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "text": "Camera - You are awarded a SiPix Digital Camera! call 09061221066 fromm landline. Delivery within 28 days."
  }'
```
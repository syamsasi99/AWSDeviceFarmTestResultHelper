# AWSDeviceFarmTestResultHelper
This utility is for updating the AWS device farm test results to google sheet


### Set Up

```sh
$ cd AWSDeviceFarmTestResultHelper
$ pip install -r requirements.txt
```

To set up the credentials for AWS device farm api, please reffer [here](https://boto3.readthedocs.io/en/latest/guide/quickstart.html)

To see more about gspread (Google sheet api), reffer [here](https://github.com/burnash/gspread)

You need to set up two configation files
 - ~/.aws/credentials
 - ~/.aws/config

The sample content of the files are given below

#### credentials
```sh
[default]
aws_access_key_id = YOUR_KEY_ID_HERE
aws_secret_access_key = YOUR_SECRET_KEY_HERE
```

#### config
```sh
[default]
region=YOUR_REGION_HERE
```

### Run
```sh
$ python aws_helper.py
```

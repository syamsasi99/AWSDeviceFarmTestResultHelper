import boto3
import requests
import logging
from datetime import datetime, timedelta
from feature_file_ownership import FeatureFileOwnership
from google_sheet_helper import GoogleSheetHelper


class AwsProjUtils:
    ''' AWS Sanity Project Utils Object
    '''

    def __init__(self, project_name):
        self.client = boto3.client("devicefarm")
        self.job_id = '00000'
        self.project_name = project_name
        self.device = ''
        #Set your job_arn and project_arn here
        self.job_arn = 'arn:aws:devicefarm:us-west-2:123456789:job:{project_id}/{run_id}/{job_id}'
        self.project_arn = 'arn:aws:devicefarm:us-west-2:123456789:project:{project_id}'

    def get_project_id(self):
        ''' get project id by project name from initilization 
        '''
        logging.info("get project id")
        project_arn = ''
        res = self.client.list_projects()
        aws_projects = res['projects']
        for project in aws_projects:
            if project['name'] == self.project_name:
                project_arn = project['arn']
                break
        project_id = project_arn.split(':')[-1]
        return project_id

    def get_run_arn_by_project(self, project_arn, run_id):
        ''' get run arn by project arn and run id 
            arn means path, not like id is a short num
        '''
        project_path = project_arn.replace("project", "run")
        return "{project}/{run}".format(project=project_path, run=run_id)

    def get_failed_suites(self, project_id, run_id):
        ''' Go though all failed test suites 
            arn means path, not like id is a short num
        '''
        logging.info(
            "get project id is {project_id}, run_id is {run_id}".format(
                project_id=project_id, run_id=run_id))
        job_arn = self.job_arn.format(project_id=project_id, run_id=run_id, job_id=self.job_id)
        suites = self.client.list_suites(arn=job_arn)
        res = self.client.get_job(arn=job_arn)
        device = res['job']['device']
        self.device = '{name}-{os}-{platform}'.format(
            name=device['name'],
            os=device['os'],
            platform=device['platform'])
        new_suites = []
        for suite in suites['suites']:
            if suite['result'] == 'FAILED':
                new_suites.append(suite)
        return new_suites

    def get_all_suites(self, project_id, run_id):
        ''' Go though all suites
            arn means path, not like id is a short num
        '''
        logging.info(
            "get project id is {project_id}, run_id is {run_id}".format(
                project_id=project_id, run_id=run_id))
        job_arn = self.job_arn.format(project_id=project_id, run_id=run_id, job_id=self.job_id)
        suites = self.client.list_suites(arn=job_arn)
        res = self.client.get_job(arn=job_arn)
        device = res['job']['device']
        self.device = '{name}-{os}-{platform}'.format(
            name=device['name'],
            os=device['os'],
            platform=device['platform'])
        new_suites = []
        for suite in suites['suites']:
            new_suites.append(suite)
        return new_suites

    def get_all_run_ids(self, project_id):
        ''' Get All run ids
            arn means path, not like id is a short num
        '''
        logging.info(
            "get project id is {project_id}".format(
                project_id=project_id))
        all_run_ids = []
        project_arn = self.project_arn.format(project_id=project_id)
        run_info = self.client.list_runs(arn=project_arn)
        all_runs = run_info['runs']
        for run in all_runs:
            created_date = run['created']
            #Change the name depends on your test name on AWS
            if run['name'] not in ['sanity1', 'sanity2', 'sanity3','sanity4']:
                continue

            if (created_date.date() == datetime.today().date()):
                arn = run['arn']
                run_id = arn.split('/')[-1]
                print(run_id)
                all_run_ids.append(run_id);
        return all_run_ids

    def get_failed_test_info_set_by_suites(self, suites):
        ''' get all failed test info by failed suites
        '''
        test_info_set = []
        test_info = {}
        test_info['device'] = self.device
        for suite in suites:
            test_info['feature'] = suite['name']
            res = self.client.list_tests(arn=suite['arn'])
            tests = res['tests']
            for test in tests:
                if test['result'] == 'PENDING':
                    raise Exception("The run is pending status")
                if test['result'] == 'FAILED':
                    test_info['result'] = test['result']
                    test_info['start_time'] = test['created']
                    test_info['scenario'] = test['name']
                    test_info['execution_time'] = test['deviceMinutes']['total']
                    test_info['error'] = self.get_error_details_by_test(test['arn'])
                    test_info_set.append(test_info.copy())
        return test_info_set

    def get_all_test_info_set_by_suites(self, suites):
        ''' get all test info by failed suites
        '''
        test_info_set = []
        test_info = {}
        test_info['device'] = self.device
        for suite in suites:
            test_info['feature'] = suite['name']
            res = self.client.list_tests(arn=suite['arn'])
            tests = res['tests']
            for test in tests:
                test_info['start_time'] = test['created']
                test_info['scenario'] = test['name']
                test_info['execution_time'] = test['deviceMinutes']['total']
                test_info['result'] = test['result']
                if test['result'] == 'PENDING':
                    raise Exception("The run is pending status")
                if test['result'] == 'FAILED':
                    test_info['error'] = self.get_error_details_by_test(test['arn'])
                else:
                    test_info['error'] = ""
                test_info_set.append(test_info.copy())
        return test_info_set

    def get_error_details_by_test(self, test_arn):
        logging.info("getting error details {test_arn}".format(test_arn=test_arn))
        res = self.client.list_artifacts(arn=test_arn, type='FILE')
        artifacts = res['artifacts']
        url = ''
        for artifact in artifacts:
            if artifact['name'] == 'Appium Java Output':
                url = artifact['url']
        return self.__parse_exception_details(url)

    def __parse_exception_details(self, url):
        ''' download log file to grab error details
        '''
        logging.info("downloading {url}".format(url=url))
        if not url:
            return ""
        res = requests.get(url, stream=True)
        lines = res.text.split('\n')
        err = []
        for line in lines:
            if 'AssertionError' in line or 'Exception:' in line and "WARN" not in line:
                err.append(line)
        return "||".join(err)

    def flatten_test_info_set(self, test_info_set):
        test_info_arr = []
        test_info_str = '{start_time},{feature},{scenario},{device},{execution_time},{error},{result}'
        for test_info in test_info_set:
            test_info_arr.append(
                test_info_str.format(
                    device=test_info['device'],
                    feature=test_info['feature'],
                    start_time=test_info['start_time'],
                    scenario=test_info['scenario'],
                    execution_time=test_info['execution_time'],
                    error=test_info['error'],
                    result=test_info['result'],
                )
            )
        return test_info_arr


if __name__ == '__main__':
    logging.basicConfig(filename='myapp.log', level=logging.INFO)
    user_data = FeatureFileOwnership()
    sheet_helper = GoogleSheetHelper()

    feature_user_map = user_data.get_feature_file_data();
    logging.info(feature_user_map)

    aws = AwsProjUtils("YOUR_AWS_PROJECT_NAME_HERE")
    project_id = aws.get_project_id()
    all_run_ids = aws.get_all_run_ids(project_id)

    logging.info(all_run_ids)
    if not all_run_ids:
        raise Exception("Could not find any run today!")
    all_data=[]
    for run_id in all_run_ids:
        suites = aws.get_all_suites(project_id, run_id)
        logging.info(suites)
        all_test_info = aws.get_failed_test_info_set_by_suites(suites)
        logging.info(all_test_info)

        for test_info in all_test_info:
            device = test_info['device']
            feature = test_info['feature']
            start_time = test_info['start_time']
            scenario = test_info['scenario']
            if scenario in ["Setup Test", "Teardown Test"]:
                continue
            execution_time = test_info['execution_time']
            error = test_info['error']
            try:
                result = test_info['result']
            except:
                result = ""
            class_name = feature.split('.')[-1]
            owner = ""
            try:
                owner = feature_user_map[class_name.lower()]
            except:
                owner = ""
            test_info['owner'] = owner
            logging.info("***********")
            logging.info(device)
            logging.info(feature)
            logging.info(start_time)
            logging.info(scenario)
            logging.info(execution_time)
            logging.info(error)
            logging.info(result)
            logging.info(class_name)
            logging.info(owner)
            logging.info("***********")
            device_info = device.split("-")
            test_info['device_name'] = device_info[0]
            test_info['version'] = device_info[1]
            test_info['platform'] = device_info[2]
            all_data.append(test_info)

    logging.info(len(all_data))

    if not all_data:
        raise Exception("No test data found!!")
    sheet_helper.append_data_on_main_sheet(all_data)

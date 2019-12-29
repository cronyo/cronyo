import boto3
import botocore.session
import jmespath
from functools import partial


def boto_session():
    return boto3.session.Session()


def aws(service, action, **kwargs):
    client = boto_session().client(service)
    query = kwargs.pop('query', None)
    if client.can_paginate(action):
        paginator = client.get_paginator(action)
        result = paginator.paginate(**kwargs).build_full_result()
    else:
        result = getattr(client, action)(**kwargs)
    if query:
        result = jmespath.compile(query).search(result)
    return result


def region():
    return boto_session().region_name


def check_aws_credentials():
    session = botocore.session.get_session()
    session.get_credentials().access_key
    session.get_credentials().secret_key


iam = partial(aws, 'iam')
aws_lambda = partial(aws, 'lambda')
events = partial(aws, 'events')

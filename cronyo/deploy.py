from botocore.client import ClientError
import os
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
try:
    from cronyo import logger
    from cronyo.config import config
    from cronyo.aws_api import iam, aws_lambda, events, region, check_aws_credentials
except ImportError:
    import logger
    from config import config
    from aws_api import iam, aws_lambda, events, region, check_aws_credentials


logger = logger.setup()
LIVE = 'live'
REVISIONS = 5
POLICY = """{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        }
    ]
}"""
ASSUMED_ROLE_POLICY = """{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            }
        }
    ]
}"""

WIRING = [
    {
        "lambda": {
            "FunctionName": "cronyo-http_post",
            "Handler": "cronyo.http_post",
            "MemorySize": 128,
            "Timeout": 30
        }
    },
    {
        "lambda": {
            "FunctionName": "cronyo-http_get",
            "Handler": "cronyo.http_get",
            "MemorySize": 128,
            "Timeout": 30
        }
    }
]


def prepare_zip():
    from pkg_resources import resource_filename as resource
    from yaml import dump
    logger.info('creating/updating cronyo.zip')
    with ZipFile('cronyo.zip', 'w', ZIP_DEFLATED) as zipf:
        info = ZipInfo('config.yml')
        info.external_attr = 0o664 << 16
        zipf.writestr(info, dump(config))
        zipf.write(resource('cronyo', 'config.py'), 'config.py')
        zipf.write(resource('cronyo', 'cronyo.py'), 'cronyo.py')
        zipf.write(resource('cronyo', 'logger.py'), 'logger.py')
        for root, dirs, files in os.walk(resource('cronyo', 'vendor')):
            for file in files:
                real_file = os.path.join(root, file)
                relative_file = os.path.relpath(real_file,
                                                resource('cronyo', ''))
                zipf.write(real_file, relative_file)


def role():
    new_role = False
    try:
        logger.info('finding role')
        iam('get_role', RoleName='cronyo')
    except ClientError:
        logger.info('role not found. creating')
        iam('create_role', RoleName='cronyo',
            AssumeRolePolicyDocument=ASSUMED_ROLE_POLICY)
        new_role = True

    role_arn = iam('get_role', RoleName='cronyo', query='Role.Arn')
    logger.debug('role_arn={}'.format(role_arn))

    logger.info('updating role policy')

    iam('put_role_policy', RoleName='cronyo', PolicyName='cronyo',
        PolicyDocument=POLICY)

    if new_role:
        from time import sleep
        logger.info('waiting for role policy propagation')
        sleep(5)

    return role_arn


def _cleanup_old_versions(name):
    logger.info('cleaning up old versions of {0}. Keeping {1}'.format(
        name, REVISIONS))
    versions = _versions(name)
    for version in versions[0:(len(versions) - REVISIONS)]:
        logger.debug('deleting {} version {}'.format(name, version))
        aws_lambda('delete_function',
                   FunctionName=name,
                   Qualifier=version)


def _function_alias(name, version, alias=LIVE):
    try:
        logger.info('creating function alias {0} for {1}:{2}'.format(
            alias, name, version))
        arn = aws_lambda('create_alias',
                         FunctionName=name,
                         FunctionVersion=version,
                         Name=alias,
                         query='AliasArn')
    except ClientError:
        logger.info('alias {0} exists. updating {0} -> {1}:{2}'.format(
            alias, name, version))
        arn = aws_lambda('update_alias',
                         FunctionName=name,
                         FunctionVersion=version,
                         Name=alias,
                         query='AliasArn')
    return arn


def _versions(name):
    versions = aws_lambda('list_versions_by_function',
                          FunctionName=name,
                          query='Versions[].Version')
    return versions[1:]


def _get_version(name, alias=LIVE):
    return aws_lambda('get_alias',
                      FunctionName=name,
                      Name=alias,
                      query='FunctionVersion')


def rollback_lambda(name, alias=LIVE):
    all_versions = _versions(name)
    live_version = _get_version(name, alias)
    try:
        live_index = all_versions.index(live_version)
        if live_index < 1:
            raise RuntimeError('Cannot find previous version')
        prev_version = all_versions[live_index - 1]
        logger.info('rolling back to version {}'.format(prev_version))
        _function_alias(name, prev_version)
    except RuntimeError as error:
        logger.error('Unable to rollback. {}'.format(repr(error)))


def rollback(alias=LIVE):
    for lambda_function in ('cronyo-track'):
        rollback_lambda(lambda_function, alias)


def create_update_lambda(role_arn, wiring):
    name, handler, memory, timeout = (wiring[k] for k in ('FunctionName',
                                                          'Handler',
                                                          'MemorySize',
                                                          'Timeout'))
    try:
        logger.info('finding lambda function')
        function_arn = aws_lambda('get_function',
                                  FunctionName=name,
                                  query='Configuration.FunctionArn')
    except ClientError:
        function_arn = None
    if not function_arn:
        logger.info('creating new lambda function {}'.format(name))
        with open('cronyo.zip', 'rb') as zf:
            function_arn, version = aws_lambda('create_function',
                                               FunctionName=name,
                                               Runtime='python3.8',
                                               Role=role_arn,
                                               Handler=handler,
                                               MemorySize=memory,
                                               Timeout=timeout,
                                               Publish=True,
                                               Code={'ZipFile': zf.read()},
                                               query='[FunctionArn, Version]')
    else:
        logger.info('updating lambda function {}'.format(name))
        aws_lambda('update_function_configuration',
                   FunctionName=name,
                   Runtime='python3.8',
                   Role=role_arn,
                   Handler=handler,
                   MemorySize=memory,
                   Timeout=timeout)
        with open('cronyo.zip', 'rb') as zf:
            function_arn, version = aws_lambda('update_function_code',
                                               FunctionName=name,
                                               Publish=True,
                                               ZipFile=zf.read(),
                                               query='[FunctionArn, Version]')
    function_arn = _function_alias(name, version)
    _cleanup_old_versions(name)
    logger.debug('function_arn={} ; version={}'.format(function_arn, version))
    return function_arn


def preflight_checks():
    logger.info('checking aws credentials and region')
    if region() is None:
        logger.error('Region is not set up. please run aws configure')
        return False
    try:
        check_aws_credentials()
    except AttributeError:
        logger.error('AWS credentials not found. please run aws configure')
        return False
    return True


def run():
    prepare_zip()
    role_arn = role()
    for component in WIRING + config.get("extra_wiring", []):
        function_arn = create_update_lambda(role_arn, component['lambda'])


if __name__ == '__main__':
    try:
        preflight_checks()
        run()
    except Exception:
        logger.error('preflight checks failed')

from botocore.client import ClientError
import json
import secrets
import hashlib
import oyaml as yaml
try:
    from cronyo import logger
    from cronyo.config import config, config_filename, generate_config
    from cronyo.aws_api import events, aws_lambda
except ImportError:
    import logger
    from config import config, config_filename, generate_config
    from aws_api import events, aws_lambda

NAMESPACE = config.get("namespace", "cronyo")
logger = logger.setup()


def _namespaced(name, separator="-"):
    return "{0}{2}{1}".format(NAMESPACE, name, separator)


def _targets_for_rule(rule):
   return events(
       "list_targets_by_rule",
       Rule=rule["Name"],
       EventBusName="default"
   )["Targets"]


def _export_rule(rule):
    export = {
        "name": rule["Name"],
    }
    if rule.get("Description") is not None:
        export["description"] = rule.get("Description")
    export["state"] = rule["State"]

    if "cron" in rule.get("ScheduleExpression"):
        export["cron"] = rule["ScheduleExpression"][5:-1]
    if "rate" in rule.get("ScheduleExpression"):
        export["rate"] = rule["ScheduleExpression"][5:-1]

    targets = _targets_for_rule(rule)
    if len(targets) > 0:
        target = targets[0]
        export["target"] = {
            "name": target["Arn"].split("function:")[-1],
            "input": json.loads(target["Input"])
        }
    return export


def export(prefix):
    logger.info('exporting rules')
    if prefix is None:
        rules = events("list_rules", EventBusName="default")['Rules']
    else:
        rules = events("list_rules", EventBusName="default", NamePrefix=prefix)['Rules']
    print(yaml.dump([_export_rule(rule) for rule in rules]))


def add(cron_expression,
        target_arn,
        target_input,
        name=_namespaced(secrets.token_hex(10)),
        description=None):

    rules = _find([name, _namespaced(name)])
    if len(rules) > 0:
        logger.warn("rule with name {} already exists. "
                    "Use `update` instead?".format(name))
        return

    put(name, cron_expression, target_arn, target_input, description)


def update(cron_expression,
        target_arn,
        target_input,
        name=_namespaced(secrets.token_hex(10)),
        description=None):

    rules = _find([name, _namespaced(name)])
    if len(rules) > 0:
        put(name, cron_expression, target_arn, target_input, description)


def _find(names):
    rules = []
    for name in names:
        rules += events(
            "list_rules",
            EventBusName="default",
            NamePrefix=name
        )["Rules"]
    if len(rules) == 0:
        logger.warn("no rules found for {}".format(names))
        return []
    return rules


def _delete(rules):
    for rule in rules:
        events("remove_targets", Rule=rule["Name"], Ids=["1"])
        events("delete_rule", Name=rule["Name"])
        logger.info("rule {} deleted".format(rule["Name"]))


def _disable(rules):
    for rule in rules:
        logger.info("disabling rule {}".format(rule["Name"]))
        events("disable_rule", Name=rule["Name"])


def _enable(rules):
    for rule in rules:
        logger.info("enabling rule {}".format(rule["Name"]))
        events("enable_rule", Name=rule["Name"])


def delete(name):
    rules = _find([name, _namespaced(name)])
    for rule in rules:
        logger.info("deleting rule:\n{}".format(yaml.dump(_export_rule(rule))))
    _delete(rules)


def disable(name):
    rules = _find([name, _namespaced(name)])
    _disable(rules)


def enable(name):
    rules = _find([name, _namespaced(name)])
    _enable(rules)


def _get_target_arn(name):
    try:
        function_arn = aws_lambda('get_function',
                                  FunctionName=name,
                                  query='Configuration.FunctionArn')
    except ClientError:
        function_arn = None
    return function_arn

def put(name,
        cron_expression,
        function_name,
        target_input={},
        description=None):

    logger.info("finding lambda function {}".format(function_name))
    target_arn = \
        _get_target_arn(function_name) or \
        _get_target_arn(_namespaced(function_name))
    if not target_arn:
        logger.error("unable to find lambda function for {}".format(function_name))
        return

    logger.debug(
        "create / update cron rule {0}: {1} for target {2}".format(
            name,
            cron_expression,
            target_arn
        )
    )
    if description:
        rule = events("put_rule",
                      Name=name,
                      ScheduleExpression=cron_expression,
                      Description=description)
    else:
        rule = events("put_rule",
                      Name=name,
                      ScheduleExpression=cron_expression)
    events(
        "put_targets",
        Rule=name,
        Targets=[
            {
                "Id": "1",
                "Arn": target_arn,
                "Input": json.dumps(target_input)
            }
        ]
    )
    try:
        logger.debug("setting lambda permission")
        source_arn = rule["RuleArn"]
        if source_arn.find(NAMESPACE) > 0:
            rule_prefix = rule["RuleArn"].split("/{}".format(NAMESPACE))[0]
            source_arn = "{}/{}*".format(rule_prefix, NAMESPACE)
        logger.debug("lambda permission SourceArn:{}".format(source_arn))
        aws_lambda(
            "add_permission",
            FunctionName=target_arn,
            Action="lambda:InvokeFunction",
            Principal="events.amazonaws.com",
            SourceArn=source_arn,
            StatementId=hashlib.sha1(source_arn.encode("utf-8")).hexdigest()
        )
    except ClientError as error:
        logger.debug("permission already set. {}".format(error))

    for rule in _find([name]):
        logger.info("rule created/updated:\n{}".format(yaml.dump(_export_rule(rule))))

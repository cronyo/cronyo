import click
import json
import logging
try:
    from cronyo import logger
    from cronyo.deploy import run, preflight_checks
    from cronyo.config import config, config_filename, generate_config
    from cronyo import cron_rules
except ImportError:
    import logger
    from deploy import run, preflight_checks
    from config import config, config_filename, generate_config
    import cron_rules

NAMESPACE = config.get("namespace", "cronyo")
logger = logger.setup()


@click.group()
@click.option('--debug', is_flag=True)
def cli(debug):
    if debug:
        logger.setLevel(logging.DEBUG)


@cli.command()
def preflight():
    logger.info('running preflight checks')
    preflight_checks()


@cli.command()
@click.option('--preflight/--no-preflight', default=True)
def deploy(preflight):
    if preflight:
        logger.info('running preflight checks')
        if not preflight_checks():
            return
    logger.info('deploying')
    run()


@cli.command()
@click.option('--all', is_flag=True)
def export(all):
    cron_rules.export(NAMESPACE, all)


@cli.command()
@click.argument('lambda_function')
@click.argument('lambda_args')
@click.option('--cron', nargs=6, type=str)
@click.option('--rate', nargs=2, type=str)
@click.option('--name', default=None)
@click.option('--description', default=None)
def add(lambda_function, lambda_args, cron, rate, name, description):
    if len(cron) == 0:
        cron_expression = "rate({0})".format(" ".join(rate))
    else:
        cron_expression = "cron({0})".format(" ".join(cron))

    if name:
        cron_rules.add(
            cron_expression,
            lambda_function,
            target_input=json.loads(lambda_args),
            name=name,
            description=description
        )
    else:
        cron_rules.add(
            cron_expression,
            lambda_function,
            target_input=json.loads(lambda_args),
            description=description
        )


@cli.command()
@click.argument("name")
def delete(name):
    cron_rules.delete(name)

@cli.command()
@click.argument("name")
def disable(name):
    cron_rules.disable(name)

@cli.command()
@click.argument("name")
def enable(name):
    cron_rules.enable(name)


@cli.command()
def configure():
    if not config:
        logger.info('generating new config {}'.format(config_filename))
        generate_config(config_filename)
    click.edit(filename=config_filename)


if __name__ == '__main__':
    cli()

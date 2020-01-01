# Cronyo

The missing cron CLI for AWS Cloudwatch and Lambda

## What is it?

A simple CLI + Lambda functions to manage your cron jobs on AWS

Key Features:

* Simple command line interface to manage cron jobs (much simpler than
  [aws events put-rules, aws lambda add-permission, aws events put-targets](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/RunLambdaSchedule.html) or Cloudformation)
* Pre-built AWS Lambda functions for simple HTTP GET/POST requests, or use your own lambdas.
* Cost Effective (you'll need a TON of cron rules to worry about costs).
* Simple but Secure (HTTP GET/POST include an HMAC signature so you can validate the request is genuine).
* Easy deployment of lambda functions using `cronyo deploy`. No need to twiddle with AWS.
* Easily add, delete, enable, disable and export (to yaml) your cron rules.

## Background

[read the blog post: Simple and Secure Cron using AWS Lambda](https://blog.gingerlime.com/2019/simple-and-secure-cron-using-aws-lambda/)

Cronyo takes the next step, and provides an automated solution with a CLI.

## Roadmap

* import from yaml
* export/import from crontab-esque files
* add other lambdas?

## Installation / Quick Start

You will need an AWS account with the `aws cli` installed. Then run:

```bash
$ pip install cronyo
$ cronyo configure
$ cronyo deploy # (optional, if you want to use the http POST/GET lambdas)
```

It will automatically configure two AWS Lambda functions (`cronyo-http_post` and `cronyo-http_get`)

## Examples

* `cronyo --help` - prints a help screen.
* `cronyo configure` - opens your editor so you can edit the config.json file. Use it to update your redis settings.
* `cronyo preflight` - runs preflight checks to make sure you have access to AWS.
* `cronyo deploy` - deploys the code and configs to AWS automatically.
* `cronyo export` - exports all existing cron rules to yaml
* `cronyo export --prefix` - exports all existing cron rules starting with `prefix` to yaml
* `cronyo add http_get '{"url": "https://example.com"}' --cron "5 4 * * ? *"` - sends an HTTP GET request to example.com at 4:05am every day
* `cronyo disable cronyo-24a0b5504111d9b1d797` - disables cron with the name `cronyo-24a0b5504111d9b1d797`
* `cronyo enable cronyo-24a0b5504111d9b1d797` - enables cron with the name `cronyo-24a0b5504111d9b1d797`
* `cronyo delete cronyo-24a0b5504111d9b1d797` - deletes cron with the name `cronyo-24a0b5504111d9b1d797`
* `cronyo update http_get '{"url": "https://example.com"}' --cron "5 4 * * ? *" --name myrule` - updates an existing rule

## Advanced

### Names

cronyo creates a name for your cron jobs automatically (unless a custom name is specified). Names are required unique identifiers, and cannot be changed after creation (this is AWS limitation). Names can only contain certain characters.

cronyo comes with a (configurable) namespace -- `cronyo` by default. You can change the default using `cronyo configure`.

### cron expressions

cronyo supports `cron` or `rate` expresssions. See the [AWS
docs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html) for specific info.

Note that `--cron "<expr>"` must be surrounded by quotes, however `--rate` won't work with quotes. This is because cron
expressions include characters like `*` which mess-up the CLI input.

### adding a cron job

* `cronyo add http_get '{"url": "https://example.com"}' --cron "5 4 * * ? *"` will send an HTTP GET request to example.com at 4:05am every day
* `cronyo add http_post '{"url": "https://example.com"}' --rate 5 minutes` will send an HTTP POST request to example.com every 5 minutes
* `cronyo add http_post '{"url": "https://example.com", "headers": {"User-Agent": "007"}, "cookies": {"biscuit": "oreo"}, "params": {"a": "b"}, "data": {"key": "value"}}' --rate 5 minutes` will send an HTTP POST with custom cookies, headers, URL params and form data.
* `cronyo add arn:aws:lambda:us-east-1:313623401231:function:cronyo-http_post:live '{"url": "https://example.com"}' --rate 5 minutes` will call a lambda function with a specific ARN with given event paramaters every 5 minutes
* `cronyo add http_post '{"url": "https://example.com"}' --rate 5 minutes --name my-cron-job` using `--name` to provide a custom name (see Names above)
* `cronyo add http_post '{"url": "https://example.com"}' --rate 5 minutes --description "describe your cron job"` using `--description` to provide a description for the job.

## License

Cronyo is distributed under the MIT license. All 3rd party libraries and components are distributed under their
respective license terms.

```
Copyright (C) 2020 Yoav Aner

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```


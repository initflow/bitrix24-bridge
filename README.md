
# Bitrix24-bridge
middleware for processing command to bitrix API

- async processing
- rate limit lock (100 req / 2 sec + 2 req / 1 sec)
- optimize list loading, convert list() commands with paginating to batch() commands with list() as subcommand
- manual auth and update access token via http request



## HOWTO

#### Start app:

> python manage.py run

> python manage.py debug

help: `python manage.py --help`

Or use docker

> docker-compose -d up app

Main app entry point is app.py:create_app() 

For ASGI servers use bridge.asgi:app entrypoint

On start app server create AMQP - client to listen and send message, by default used RABBITMQ_ environment variables

#### Setup RabbitMQ:

Main setup functions defined in `rabbitmq-init.sh`

Or use `app.sh:setup_rabbitmq()`

Both methods require environment variables with connection settings


## Command

AMQP client wait command in format:

```json
{
    "action": "list",
    "method": "crm.product.list",
    "params": {},
    "meta": {}
}
```

Where:
- action: str - action type (not api type, like get, delete, update), e.g. list, batch or default, if null or unknown type, will be used default (single request)
- method: str - api method, by default method = {entity}.{api_method_type}, e.g. crm.product.list, crm.product.get, crm.product.delete
- params: Dict - json params for method
- meta - by default it Dict, but can be used Any, return with CommandResponse

## Command Response

AMQP client send result in format:
```json
{
  "action" : "list",
  "method" : "crm.product.list",
  "params" : {},
  "result" : [],
  "status_code" : 200,
  "next" : null,
  "total" : 5,
  "meta" : {},
}
```

Where:
- action: str - from Command
- method: str - from Command
- params: Dict - from Command
- meta - from Command
- result: List - list of response, always List
- status_code: int
- next: int - next page pagination number, always a multiple of 50
- total: int - total objects in result (without pagination)


#!/usr/bin/env bash
FUNCTION=
if [ ! -z $1 ]; then
    FUNCTION="$1"
fi

URL="http://rabbitmq:15672/cli/rabbitmqadmin"

function set_exchanges() {
    rabbitmqadmin declare exchange --vhost=$RABBITMQ_VIRTUAL_HOST --user=$RABBITMQ_USER --password=$RABBITMQ_PASS name=$RABBITMQ_EXCHANGE type=${RABBITMQ_EXCHANGE_TYPE,,} durable=${RABBITMQ_EXCHANGE_DURABLE,,}
    rabbitmqctl list_exchanges -p $RABBITMQ_VIRTUAL_HOST
}

function set_queues() {
    rabbitmqadmin declare queue --vhost=$RABBITMQ_VIRTUAL_HOST --user=$RABBITMQ_USER --password=$RABBITMQ_PASS name=$RABBITMQ_MESSAGE_QUEUE durable=${RABBITMQ_QUEUE_DURABLE,,}
    rabbitmqadmin declare queue --vhost=$RABBITMQ_VIRTUAL_HOST --user=$RABBITMQ_USER --password=$RABBITMQ_PASS name=$RABBITMQ_COMMAND_QUEUE durable=${RABBITMQ_QUEUE_DURABLE,,}
    rabbitmqctl list_queues -p $RABBITMQ_VIRTUAL_HOST
}

function set_bindings() {
    rabbitmqadmin declare binding --vhost=$RABBITMQ_VIRTUAL_HOST --user=$RABBITMQ_USER --password=$RABBITMQ_PASS source=$RABBITMQ_EXCHANGE destination_type="queue" destination=$RABBITMQ_MESSAGE_QUEUE routing_key=$RABBITMQ_ROUTING_KEY
    rabbitmqadmin declare binding --vhost=$RABBITMQ_VIRTUAL_HOST --user=$RABBITMQ_USER --password=$RABBITMQ_PASS source=$RABBITMQ_EXCHANGE destination_type="queue" destination=$RABBITMQ_COMMAND_QUEUE routing_key=$RABBITMQ_COMMAND_ROUTING_KEY

    rabbitmqctl list_bindings -p $RABBITMQ_VIRTUAL_HOST
}


function check() {
    wait_server
    type rabbitmqctl > /dev/null 2>&1 || { echo >&2 "rabbitmqctl is required but it is not installed. Aborting."; exit 1; }
    type rabbitmqadmin > /dev/null 2>&1 || { echo >&2 "rabbitmqadmin is required but it is not installed.
    Download from $URL, add .py extension and install into /usr/local/bin/rabbitmqadmin.
    Aborting."; exit 1; }
}


function clear() {
    wait_server
    rabbitmqadmin --vhost=$RABBITMQ_VIRTUAL_HOST --user=$RABBITMQ_USER --password=$RABBITMQ_PASS delete binding source=$RABBITMQ_EXCHANGE destination_type="queue" destination=$RABBITMQ_MESSAGE_QUEUE destination_type="queue" properties_key="$RABBITMQ_ROUTING_KEY"
    rabbitmqadmin --vhost=$RABBITMQ_VIRTUAL_HOST --user=$RABBITMQ_USER --password=$RABBITMQ_PASS delete binding source=$RABBITMQ_EXCHANGE destination_type="queue" destination=$RABBITMQ_COMMAND_QUEUE destination_type="queue" properties_key=$RABBITMQ_COMMAND_ROUTING_KEY
    echo "Bindings [$RABBITMQ_ROUTING_KEY, $RABBITMQ_COMMAND_ROUTING_KEY] deleted..."

    rabbitmqadmin --vhost=$RABBITMQ_VIRTUAL_HOST --user=$RABBITMQ_USER --password=$RABBITMQ_PASS delete exchange name=$RABBITMQ_EXCHANGE
    echo "Exchange $RABBITMQ_EXCHANGE deleted"
    rabbitmqadmin --vhost=$RABBITMQ_VIRTUAL_HOST --user=$RABBITMQ_USER --password=$RABBITMQ_PASS delete queue name=$RABBITMQ_MESSAGE_QUEUE
    rabbitmqadmin --vhost=$RABBITMQ_VIRTUAL_HOST --user=$RABBITMQ_USER --password=$RABBITMQ_PASS delete queue name=$RABBITMQ_COMMAND_QUEUE
    echo "Queues [$RABBITMQ_MESSAGE_QUEUE, $RABBITMQ_COMMAND_QUEUE] deleted"

    echo "Rabbitmq cleared with success."
}

function wait_server() {

    echo "Wait for starting rabbitmq-server"

    echo "."
    rabbitmqctl wait --pid 1 > /dev/null 2>&1

    while [ $? != 0 ]
    do
        echo "."
        rabbitmqctl wait --pid 1 > /dev/null 2>&1
    done

}

function init() {
    wait_server
    set_exchanges
    set_queues
    set_bindings
    echo "Rabbitmq configured with success."
}


function show-help() {
    echo 'Functions:'
    echo './app.sh [check] [clear] [init]'
}

case "$1" in
-h|--help)
    show-help
    ;;
*)
    if [ ! -z $(type -t $FUNCTION | grep function) ]; then
        $1
    else
        show-help
    fi
esac
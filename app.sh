#!/usr/bin/env bash
FUNCTION=
if [ ! -z $1 ]; then
    FUNCTION="$1"
fi

platform='unknown'
unmaster=`uname`
project_name='bitrix24-bridge'

if [[ $unmaster == 'Linux' ]]; then
   platform='linux'
elif [[ $unmaster == 'MINGW64_NT-10.0' ]]; then
    platform='windows'
elif [[ $unmaster == 'Darwin' ]]; then
   platform='mac'
fi




show-help() {
    echo 'Functions:'
    echo './app.sh [start] [stop] [restart] [build] [first_run]'
}

rundocker() {
    echo "Project: $project_name"
    echo 'Stop all containert'
    docker stop $(docker ps -a -q)
    echo ''
    echo 'Start containers'
    docker-compose -p $project_name up -d
    echo ''
}

start() {
    rundocker
}

migrate() {
    echo 'migrate - Not support'
    # docker exec -it $(get_container_name 'app') python manage.py migrate
}

logs() {
  docker logs $(get_container_name 'app')
}

rabbitmq_logs() {
  docker logs $(get_container_name 'rabbitmq')
}

redis_logs() {
  docker logs $(get_container_name 'redis')
}

setup_rabbitmq() {
    docker exec -it $(get_container_name 'rabbitmq') bash rabbitmq-init.sh init
}

clear_rabbitmq() {
    docker exec -it $(get_container_name 'rabbitmq') bash rabbitmq-init.sh init
}

rabbitmq_cmd() {
    echo $1
    docker exec -it $(get_container_name 'rabbitmq') bash rabbitmq-init.sh $1
}

createsuperuser() {
    echo 'createsuperuser - Not support'
    #docker exec -it $(get_container_name 'app') python manage.py createsuperuser
}


makemigrations() {
    echo 'makemigrations - Not support'
    #docker exec -it $(get_container_name 'app') python manage.py makemigrations
}


collectstatic() {
    echo 'collectstatic - Not support'
  #  docker exec -it $(get_container_name 'app') bash -c "cd app && npm i && npm q build"
    # docker exec -it $(get_container_name 'app') python manage.py collectstatic --noinput -v 0
}

compilemessages() {
    echo 'compilemessages - Not support'
    # docker exec -it $(get_container_name 'app') django-admin compilemessages -v 0
}

get_container_name() {
   docker ps -a --filter="name=bitrix24-bridge_$1" --format '{{.Names}}'
}


stop() {
    echo 'Stop all containert'
    docker stop $(docker ps -a -q)
}

restart() {
    start
}

first_run() {
    local DB_NAME=$(get_variable 'DB_NAME')
    local DB_USER=$(get_variable 'DB_USER')
    local DB_PASS=$(get_variable 'DB_PASS')
    rundocker

    docker exec -it $(get_container_name 'postgres') psql -U postgres -c "CREATE DATABASE $DB_NAME;"
    docker exec -it $(get_container_name 'postgres') psql -U postgres -c  "CREATE USER $DB_USER WITH ENCRYPTED PASSWORD '$DB_PASS';"
    docker exec -it $(get_container_name 'postgres') psql -U postgres -c  "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO  $DB_USER;"
    docker exec -it $(get_container_name 'postgres') psql -U postgres -d $DB_NAME -c 'create extension hstore;'

    setup_rabbitmq
}

update() {
   echo 'Build containers with cache'
   docker-compose -p $project_name build app
}


build() {
   echo 'Build containers'
   docker-compose -p $project_name build --no-cache
}


get_variable(){
    while read p; do
      A="$(echo $p | cut -d'=' -f1)"
      B="$(echo $p | cut -d'=' -f2)"
      if [[ $A = $1 ]]
      then
        echo $B
      fi
    done <.env
}

case "$1" in
-h|--help)
    show-help
    ;;
*)
    if [ ! -z $(type -t $FUNCTION | grep function) ]; then
        $1 $2 $3 $4 $5
    else
        show-help
    fi
esac

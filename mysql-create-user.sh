#!/bin/bash
username=root
password=ab12cd
if [ $# -ne 2 ]
then
    echo "E.g. create_database.sh database password"
    exit 1
fi
mysql -u$username -p$password -e "create database $1";
mysql -u$username -p$password -e "create user '$1'@'%' identified by '$2'"
mysql -u$username -p$password -e "create user '$1'@'localhost' identified by '$2'"
mysql -u$username -p$password -e "use $1;grant all privileges on $1.* to '$1'@'%'"
mysql -u$username -p$password -e "use $1;grant all privileges on $1.* to '$1'@'localhost'"
mysql -u$username -p$password -e "flush privileges"

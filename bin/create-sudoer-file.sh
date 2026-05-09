#!/usr/bin/env bash

user=${USER}
file=/etc/sudoers.d/${user}
echo "${user} ALL=(ALL:ALL) NOPASSWD: ALL" | sudo tee "${file}"

ls -l "${file}"
cat "${file}"


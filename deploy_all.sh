#!/bin/bash

script='/home/dorowu/Dropbox/mynotes/tools/deploy_wiki.py'
notebook='/home/dorowu/Dropbox/mynotes'
deploy_path='/home/dorowu/src/dokuwiki-deploy'
user='doro'

rm -rf ${deploy_path}/data/pages/${user}/*
rm -rf ${deploy_path}/data/media/${user}/*

#/home/doro/Dropbox/mynotes/iworldcom/gnome_power_manager /home/doro/Dropbox/mynotes/iworldcom/gnome_power_manager.txt
find $notebook -name '*.txt' -exec $script $notebook $deploy_path $user - {} \;
#/home/dorowu/Dropbox/mynotes /var/www/wiki doro /home/dorowu/Dropbox/mynotes/android/disassembly /home/dorowu/Dropbox/mynotes/android/disassembly.txt

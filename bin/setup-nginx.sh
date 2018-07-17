#!/usr/bin/env bash

# TODO: Change project dir name

sudo rm /etc/nginx/sites-enabled/default
sudo rm /etc/nginx/sites-available/geocore
sudo rm /etc/nginx/sites-enabled/geocore
sudo cp conf/nginx.conf /etc/nginx/sites-available/geocore
sudo ln -s /etc/nginx/sites-available/geocore /etc/nginx/sites-enabled/geocore
sudo /etc/init.d/nginx reload

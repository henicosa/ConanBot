#!/bin/bash
docker build ./ -t conanbot
sh ./start.sh
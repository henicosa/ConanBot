#!/bin/bash
docker build ./ -t conanbot
docker run -p 5111:5000 conanbot
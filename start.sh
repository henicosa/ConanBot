#!/bin/bash
docker run -p 5111:5000 --restart unless-stopped -v $(pwd)/app:/app/app --name "conanbot" conanbot
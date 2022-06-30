#!/bin/bash
docker build -t everest-cross-compiler .

docker run -it --rm --privileged \
  --cap-add=ALL \
  -v /dev:/dev \
  -v /lib/modules:/lib/modules \
  --mount type=bind,source=$SSH_AUTH_SOCK,target=/ssh-agent \
  --env SSH_AUTH_SOCK=/ssh-agent \
  everest-cross-compiler \
  bash

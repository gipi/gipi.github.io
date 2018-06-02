---
layout: post
comments: true
title: "Docker: cheat sheet"
tags: [docker, container, cheat sheet, WIP]
---

In the following we are using the usual terminology for the virtualization/sandboxing
environment:

 - **Host:** the external system that runs the container
 - **Guest:** the running container

| Command | Description |
|---------|-------------|
| docker info | |
| docker build -t \<name\> \<url\>#\<branch\>:\<subdir\> | |
| docker run -it -v \<host\>:\<guest\> \<image/name\> \<cmd\> | |
| docker run -p \<port host\>:\<port guest\> --link \<container id or name\>:\<label\> | run and allow connection with the given container |
| docker commit \<container id\> \<image/name\> | |
| docker inspect \<image/name\> | |
| docker ps | ``ps`` but for containers |
| docker ps -l | as above but only the latest |
| docker ps -s | give me also the size |
| docker update --restart=no | |

## Useful images

 - ``php:5.6-apache``

## Links

 - [Another cheat sheet](https://github.com/wsargent/docker-cheat-sheet)
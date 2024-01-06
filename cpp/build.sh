#!/usr/bin/env sh

cmake -Bbin
make -C bin
mv bin/compile_commands.json .

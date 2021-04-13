#!/bin/sh -e

# allow the container to be started with `--user`
if [ "$1" = 'python' -a "$(id -u)" = '0' ]; then
	find . \! -user batimap -exec chown batimap '{}' +
	exec su batimap -- "$0" "$@"
fi

exec "$@"

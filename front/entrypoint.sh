#!/bin/sh -e

echo $0 $1
# allow the container to be started with `--user`
if [ "$1" = 'yarn' -a "$(id -u)" = '0' ]; then
	find . \! -user node -exec chown node '{}' +
	exec su node -- "$0" "$@"
fi

exec "$@"

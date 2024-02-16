#!/bin/bash

DATABASE="${MONGO_TEST_DB}"
# Verify arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <container_name_or_id> <host_directory>"
    echo "Example: ./init_test_db.sh mongodb ../../mongodb_test_db/flexibility_test"
    exit 1
fi

# Parse argument
container_name_or_id="$1"
host_directory="$2"
container_directory="/backup/$DATABASE"

# Check if the container is running
if [ "$(docker inspect -f '{{.State.Running}}' "$container_name_or_id" 2>/dev/null)" != "true" ]; then
    echo "Error: Container is not running."
    exit 1
fi

# Check if the container directory exists, create it if not
docker exec "$container_name_or_id" sh -c "[ -d $container_directory ] || mkdir -p $container_directory"

# Copy the directory from host to container
docker cp "$host_directory" "$container_name_or_id":"$container_directory"


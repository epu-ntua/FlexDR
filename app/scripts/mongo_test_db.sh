#!/bin/bash

# MongoDB connection details
HOST="localhost"
PORT="27017"
USERNAME="${MONGO_INITDB_ROOT_USERNAME}"
PASSWORD="${MONGO_INITDB_ROOT_PASSWORD}"
DATABASE="${MONGO_TEST_DB}"

# Backup directory
BACKUP_DIR="./backup"

# Create a backup
backup() {
  echo "Creating a backup of the MongoDB database..."
  mongodump --host $HOST --port $PORT --username $USERNAME --password $PASSWORD --db $DATABASE --out $BACKUP_DIR --authenticationDatabase=admin
  echo "Backup should exist in $BACKUP_DIR"
}

# Restore from the backup
restore() {
  echo "Restoring the MongoDB database from the backup..."
  mongorestore --host $HOST --port $PORT --username $USERNAME --password $PASSWORD --db $DATABASE $BACKUP_DIR/$DATABASE --authenticationDatabase=admin
}

# Drop database
drop() {
  echo "Dropping Database"
  mongosh --host $HOST --port $PORT --username $USERNAME --password $PASSWORD --db DATABASE --authenticationDatabase=admin $DATABASE --eval "db.dropDatabase()"
}

# Usage info
usage() {
  echo "Usage: $0 {backup|restore|drop}"
  exit 1
}

# Verify cli arguments
if [ "$#" -ne 1 ]; then
  usage
fi

# Select action
case $1 in
  "backup")
    backup
    ;;
  "restore")
    restore
    ;;
  "drop")
    drop
    ;;
  *)
    usage
    ;;
esac
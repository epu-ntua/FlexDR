#!/bin/bash

# Confirm backup existence
read -p "Test database will be dropped. Continue only if a backup is available ? (y/n): " choice

# Check the user's choice
if [ "$choice" == "y" ] || [ "$choice" == "Y" ]; then
    echo "Continuing...."
else
    echo "Script execution aborted."
    exit 1
fi

# Execute docker commands from host to the containers mongo & backend app
drop_database="docker exec -it mongodb /scripts/mongo_test_db.sh drop"
initialize_test_database="docker exec -it mongodb /scripts/mongo_test_db.sh restore"
run_tests_with_coverage="docker exec -it flexibility-backend /code/app/scripts/run_coverage.sh"

# Drop test database
echo "Dropping test database..."
eval "$drop_database"

# Reinitialize test db with test data
echo "Reinitializing test database..."
eval "$initialize_test_database"

# Execute tests with coverage
echo "Executing coverage and pytest..."
eval "$run_tests_with_coverage"

echo "Script completed"

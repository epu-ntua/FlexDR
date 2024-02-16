# I-NERGY UC7 - FlexDR
## Repository information
This is the repository of FlexDR backend application developed within I-NERGY UC7 project.\
FlexDR service consists of additional services which can be found using the following urls:
* FlexDR Front-end repository [I-NERGY FlexDR frontend repository](https://github.com/I-NERGY/FlexDR_frontend)
* FlexDR Orchestration engine [I-NERGY FlexDR orchestration engine repository](https://github.com/I-NERGY/dagster-orchestrator)

## Deployment guidelines
This section provides instructions to deploy FlexDR FastAPI service and MongoDB locally in docker containers, using Docker Compose.
[Docker-compose file](docker-compose.yaml) makes use of the environment variables defined in [env file](.env.local) which contains default values for local installation.
In order to start the containers, run:
```shell
docker-compose --env-file=.env.local up --build -d
```

In order see endpoints documentation users can visit the url: <service_url>:<service_port>/docs
e.g. http://localhost:8002/docs:

More details on how interact with the application could be found in the documentation section of the repository.

## Run tests
In order to run the tests:
1. Start application ([More](#running-application))
2. Run [script](app/scripts/init_test_db.sh) initialising the database with test data. (Example: ```./init_test_db.sh mongodb ../../mongodb_test_db/flexibility_test```)
3. Run [script](app/scripts/run_tests.sh) executing tests with coverage (here). This process will take care of cleaning and restoring database prior to tests

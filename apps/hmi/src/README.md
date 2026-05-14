# HMI Web Application for GRBL controllers

## Docker compose project
The HMI WebApp can be deployed using Docker (run in the `hmi` folder):
```
docker compose up -d
```

## Environment variables
The following environment variables need to be defined

- `HMI_USER_ID`: User ID of the user that will run the WebApp
- `KSQL_HOST`: url to the ksqlDB server
- `HMI_NC_FILES_FOLDER`: abolsute path to the instance folder to be used by the WebApp
- `HMI_NC_FILES_FOLDER`: absolute path to the folder containing the nc-files

Note: the folders `HMI_NC_FILES_FOLDER` and `HMI_NC_FILES_FOLDER` need to have `rw` access rights for the user with UID `HMI_USER_ID`.

## Run directly

### Environment variables required
Can be defined in `.flaskenv`:
```
FLASK_APP=hmi.hmi
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=4444
```
or in `.env` for the ones that should not go to GitHub:
```
KSQL_HOST=.....
```

### Run the app
```
flask --debug run
```
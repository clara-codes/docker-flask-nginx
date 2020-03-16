# Docker-Flask-Nginx

This is a demo on how to use [Flask](https://flask.palletsprojects.com/en/1.1.x/quickstart/) to build RESTful HTTP API, deployed using [Nginx](https://flask.palletsprojects.com/en/1.0.x/deploying/uwsgi/) and continerized with [Docker](https://docs.docker.com/get-started/). 

## App Summary

This app simulates a food delivery ordering system, where users can create orders, deliverymen can take oder, and the system admin can view all existing orders. 

## Makefile

For the ease of building the container and running tests, I use make (*Makefile*) to organize and run these targets. 

## Containerize with Docker and docker-compose

Docker builds images automatically by reading the instructions from a *Dockerfile*. I use [**multi-stage build**](https://docs.docker.com/develop/develop-images/multistage-build/) for Docker image here to build the image for different purpose i.e. deployment, automated testing. In the *Makefile* you can see the command to build to different build_targets. For example to build automated tests:

```shell
$ make image BUILD_TARGET=test_builder
```

(Available build_targets: `builder`, `test_builder`) 

[**docker-compose**](https://docs.docker.com/compose/gettingstarted/) is a great way to spin up all dependent containers for deployment, in my case the Flask container is dependent on a PostgreSQL instance. In *docker-compose.yml*, which is the file docker-compose uses to run, has two service: `order-api-db` and `order-api-app`, corresponds to the PostgreSQL and Flask service respectively. In addition, environment variables can be neatly managed through *docker-compose.yml*. 

The **entry script** - *start.sh* (for `--target=builder`) used in docker-compose set-up the database and create tables, configure the log files and start-up the nginx server. While as for the entry script - *start_test.sh* (for `--target=test_builder`) will exit the container after running all unit tests and integration tests. You can examine the test results with:

```shell
$ docker logs <container name or id>
```

**Health check** can also be implemented with docker-compose. Create a health check endpoint (see *order_app/views.py*) that returns HTTP 200 and [define the health check in the *docker-compose.yml*.](https://docs.docker.com/compose/compose-file/) In this setup, the healthcheck is for deployment with `-—target=builder` (the health check for automated test build with `—target=test_builder` ),  where it will ping the `order-api-app` service's endpoint `/healthcheck` every `1m30s`, and the health check starts `40s` after the service start-up. You can inspect the health of the docker container with: 

```shell
$ docker inspect --format='{{json . State.Health}}' <container name or id>
```

The output contains the state of the container health: 

```json
{
  "Status":"healthy","FailingStreak":0,
  "Log":[
    {
      "Start":"2020-03-16T04:25:04.9109452Z",
      "End":"2020-03-16T04:25:05.1827724Z",
      "ExitCode":0,
      "Output":"  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current\n                                 Dload  Upload   Total   Spent    Left  Speed\n\r  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0{\n  \"data\": \"hello world.\"\n}\n\r100    29  100    29    0     0   3625      0 --:--:-- --:--:-- --:--:--  3625\n"
    },
    {
      "Start":"2020-03-16T04:26:35.109024Z",
      "End":"2020-03-16T04:26:35.3982733Z",
      "ExitCode":0,
      "Output":"  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current\n                                 Dload  Upload   Total   Spent    Left  Speed\n\r  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0\r100    29  100    29    0     0   3222      0 --:--:-- --:--:-- --:--:--  3625\n{\n  \"data\": \"hello world.\"\n}\n"
    },
    ...
    }
  ]
}
```

You can also simply see the state of the container health when you do to show all running containers: 

```shell
$ docker ps
```

You can see the state of the health e.g. `(healthy)` in the STATUS column.

At last, In the *Makefile* you can see the command to run docker-compose in the background (`-d`):

```shell
$ make docker-compose
```

This will start all services in the *docker-compose.yml*.

## Web server with Nginx and uWsgi

To deploy my flask service, I use Nginx as web server to handle requests and communicate with uWsgi, and uWsgi to invoke callable object to my web service (flask). This is illustrated below: 

![nginx-uwsgi-flask](https://raw.githubusercontent.com/clara-codes/docker-flask-nginx/master/readme-images/nginx-uwsgi-flask.png)

Source: [A Guide to Scaling Machine Learning Models in Production](https://hackernoon.com/a-guide-to-scaling-machine-learning-models-in-production-aa8831163846)

The configuration for Nginx is in /nginx.conf, and the configuration for uWsgi is in /uwsgi.ini. One can optimise the performance of the web server by tweaking the configurations in /nginx.conf. One thing to note, I have chosen to use `processes = 4` in the /uwsgi.ini configuration, since Python has a **GIL** (Global Interpreter Lock), only one thread can run at a time. By <u>running multiple uWsgi processes, each has its own instance of Python and GIL, hence allowing concurrent requests.</u> 

## Endpoints

All routes of the endpoints are defined in */orders/views.py*

### POST  /orders 

Usecase: users to place an order.

 I use the [Google Map Distance Matrix API ](https://cloud.google.com/maps-platform/routes/) to find the distance between origin and destination. The API key can be set in *docker-compose.yml* `GMAP_TOKEN`.

Request body example:

```json
{
	"origin": ["50.456399", "12.707580"],
	"destination": ["59.436487", "24.747193"]
}
```

Response body (HTTP) 200) example:

```json
{
  "distance": 1728057,
  "id": 16,
  "status": "UNASSIGNED"
}
```

If the 1) request body fails the jsonschema validation, 2) the order cannot be created on the database level, it will respond with HTTP  400 and with response body of the error message.

You can find the functions to the endpoint in `order_app/place_order.py`.

In here, I use [flask-inputs](https://pythonhosted.org/Flask-Inputs/) and [jsonschema](https://python-jsonschema.readthedocs.io/en/stable/) to validate the request body json, it gives a clean and neat way to maintain the validity of the request body. The unit test (`tests/unit_tests/tests_place_order.py`) coverage includes different invalid request body cases. While as the integration test covers other functions that requires database connectivity, I do so with **real database connectively** to a test database - `TestDB`. 

### PATCH /orders/:id

Usercase: deliverymen to take an order.

Request body example:

```json
{
    "status": "TAKEN"
}
```

Response body (HTTP 200) example: 

```json
{
    "status": "SUCCESS"
}
```

If the 1) request parameters or request body fail the jsonschema validation, 2) the request to place order fails e.g. the order is already taken (status: "TAKEN"), 3) the status update at the database level fails (cannot obtain row lock since it's occupied etc.), it will respond with HTTP  400 and with response body of the error message.

Consider the case where multiple deliverymen try to take the same order (same order id) concurrently (**concurrent request**), that would lead to a **race condition**, and we need to control how the requests are being processed, or any requests need to be failed. In here, I use [**database row-level locking**](https://www.postgresql.org/docs/9.1/explicit-locking.html) to <u>allow only one request update the order record and failing the others. In particular, one can use the PostgreSQL `FOR UPDATE` clause with `NOWAIT</u>`.

The functions to this endpoint can be found in `order_app/take_order.py`. Both unit tests and integration tests are implemented for this endpoint. In addition, I adopted an open source tool for **load testing** - [Locust](https://locust.io/). The load test can be started with: 

```shell
make test-load
```

After running the `locust` command, you can see in the output - `locust.main: Starting web monitor at http://*:8089`. Now if you open `localhost:8089`, you can see the Locust UI. Just input the total users, hatch rate and host (hostname of the actual host, e.g. localhost) to start the load test.

![locust-ui](https://raw.githubusercontent.com/clara-codes/docker-flask-nginx/master/readme-images/locust%20ui.png)

❌ !!! IMPORTANT: You should do the load testing by spinning up the containers with **connection to a Test Database**,  since there is no mocking involved! You can change the connection to a test database instead in *docker-compose.yml*. Also be mindful of the Google Map Distance Matrix API call limit when doing load testing.

While the test is running, the statistics will be shown on the UI : 

![locust-ui-stats](https://raw.githubusercontent.com/clara-codes/docker-flask-nginx/master/readme-images/locust%20ui%20stats.png)

As you can see, only one `PATCH /order` succeeded, because the other fail due to concurrent request or order having been taken returning HTTP 400, which is the expected behaviour.

### GET /orders

Usecase: for system admin to view existing orders.

In here we use pagination to divide all existing orders from database into discrete pages to be returned as json - an array of order items.

Request example: 

```http
GET /orders/?page=1&limit=3
```

Response body (HTTP 200) example:

```json
[
  {
    "distance": 1728057,
    "id": 1761,
    "status": "UNASSIGNED"
  },
  {
    "distance": 4105,
    "id": 1760,
    "status": "UNASSIGNED"
  },
  {
    "distance": 4105,
    "id": 1759,
    "status": "UNASSIGNED"
  }
]
```

If the 1) request parameters fail validation, 2) cannot retrieve orders from database, it will return HTTP 400 with an error message. In here the pagination is implemented with [flask-sqlalchemy](https://flask-sqlalchemy.palletsprojects.com/en/2.x/api/). 

Only integration test is implemented for this endpoint, since the only function that needs testing requires database connectivity. You can find the functions to this endpoint in `/order_app/order_list.py`. 

## Testing

Directory: tests/ 

The tests/ folder is only copied for the container for build target `--target=test_builder`. Since this folder is unnecessary for deployment, but for automated testing. One can optionally copy the folder to build the deployment image to run the tests in the deployed container. 

### Unit Test

Directory: /tests/unit_tests/ 

We use python [unittest](https://docs.python.org/3/library/unittest.html) framework. And we run all the unit test `unittest.TestCase` in make target: `test-unit`. Optionally, one can group `unittest.TestCase` that should be run together.

The unit tests cover all functions or class functions that do not require database connectivity. In addition, the unit tests cover both success and failure cases for the functions, in particular the unit tests cover whether the functions are returning error message when errors are expected to occur and be captured.

To isolate the functionalities that I want to test, I used `unittest.mock` to mock database connection and calls to external api i.e. Google Map Distance Matrix API.

###  Integration Test

Directory: /tests/integration_tests/

All executions of integration tests can be executed with make target: `test-integration`. The integration tests cover all functions or class functions that **require database connectivity**, including the functions to create database and tables. Again, same as unit tests, the integration tests include  `unittest.mock` is used to make the functions connect to the test database `TestDB` instead of the real database for isolating the test data for testing (not mocking the database connection), it is also used to mock the external API call to exclude uncontrollable factors to the integration tests.

### Load Test (end-to-end performance testing)

Directory: /tests/integration_tests/load_tests/

I use load test here to expose the concurrency problem, and test service to handle concurrent requests. 

All executions of the load tests can be executed with make target: `make test-load` (as describe earlier under section - Endpoint). No mocking is involved for load testing, so one should configure (in *docker-compose.yml*) the running service to be tested to connect to a Test Database. Load test is only implemented for endpoints: `GET /orders` and `PATCH /order/:id`, since high request traffic is expected only for these 2 endpoints.

To summarise, I have the follow tests in place:

1. Tests with mock database connectivity and  mock external API calls.
2. Tests with real database connectivity (to a Test Database) and mock external API calls
3. Tests with real database connectivity (to a Test Database) and real external API calls.

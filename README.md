# Docker-Flask-Nginx

This is a demo on how to use [Flask](https://flask.palletsprojects.com/en/1.1.x/quickstart/) to build RESTful HTTP API, deployed using [Nginx](https://flask.palletsprojects.com/en/1.0.x/deploying/uwsgi/) and containerized with [Docker](https://docs.docker.com/get-started/). 

## App Summary

This app simulates a food delivery ordering system, where users can create orders, deliverymen can take orders, and the system admin can view all existing orders. 

## Makefile

For the ease of building the container and running tests, I use make (*Makefile*) to organize and run these targets.

💡The **Makefile contains all the commands** that one will need to make docker image, spin up the containers, and run all the tests. The major use cases of the Makefile: 

To deploy the services: 

```shell
$ make image BUILD_TARGET=builder
#this will build a docker image named order-api to the stage - builder
$ make docker-compose
#this will spin up all services, including the web service using docker image order-api
```

Note: If you have run the above commands locally, the port of the database is published as `8888`, you can connect to database at host: `localhost` and port: `8888`(you may find the username, password and database in */docker-compose.yml*). The port of the API service is published as `8080`, you can request the APIs at `http://localhost:8080` . 

To run automated tests: 

```shell
$ make image BUILD_TARGET=test_builder
#this will build a docker image named order-api to the stage - test_builder
$ make docker-compose
#this will spin up a container and run the automated tests and exit with code 0
```



## Containerize with Docker and docker-compose

Docker builds images automatically by reading the instructions from a *Dockerfile*. I use [**multi-stage build**](https://docs.docker.com/develop/develop-images/multistage-build/) for Docker image here to build the image for different purposes i.e. deployment, automated testing. In the *Makefile* you can see the command to build to different build_targets. For example to build automated tests:

```shell
$ make image BUILD_TARGET=test_builder
```

(Available build_targets: `builder`, `test_builder`) 

🐳 [**docker-compose**](https://docs.docker.com/compose/gettingstarted/) is a great way to spin up all dependent containers for deployment, in my case the Flask container is dependent on a PostgreSQL instance. In */docker-compose.yml*, which is the file docker-compose uses to run, has two services: `order-api-db` and `order-api-app`, corresponding to the PostgreSQL and Flask service respectively. In addition, environment variables can be neatly managed through */docker-compose.yml*. 

In the *Makefile* you can see the command to run docker-compose in the background (with flag`-d`):

```shell
$ docker-compose --file docker-compose.yml up -d
```

Or instead you can just run:

```shell
$ make docker-compose
```

This will start all services in the *docker-compose.yml*.

The **entry script** - */start.sh* (for `--target=builder`) used in docker-compose sets-up the database and creates tables, configures the log files and starts-up the nginx server. While as for the entry script - */start_test.sh* (for `--target=test_builder`) will exit the container after running all unit tests and integration tests. You can examine the test results with:

```shell
$ docker logs <container name or id>
#in the default setup, the container name is order-api-app
```

**Health check** is also implemented with docker-compose. I have created a health check endpoint (see *order_app/views.py*) that returns HTTP 200 and [defined the health check in the *docker-compose.yml*.](https://docs.docker.com/compose/compose-file/) In this setup, the healthcheck is for deployment with `-—target=builder` (the health check for automated test build with `—target=test_builder` ),  where it will ping the `order-api-app` service's endpoint - `/healthcheck` every `1m30s`, and the health check starts `40s` after the service start-up. You can inspect the health of the docker container with: 

```shell
$ docker inspect --format='{{json .State.Health}}' <container name or id>
#in the default setup, the container name is order-api-app
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

You can also simply see the state of the container health by listing all running containers: 

```shell
$ docker ps
```

The output will look like this:

![docker ps healthy](https://raw.githubusercontent.com/clara-codes/docker-flask-nginx/master/readme-images/docker%20ps%20healthy.png)

You can see the state of the health i.e. `(healthy)`, `(unhealthy)` or `(starting)` in the STATUS column.

## Web server with Nginx and uWsgi

To deploy my Flask service, I use Nginx as the web server to handle requests and communicate with uWsgi, and uWsgi to invoke the callable object to my web service (Flask). This is illustrated below: 

![nginx-uwsgi-flask](https://raw.githubusercontent.com/clara-codes/docker-flask-nginx/master/readme-images/nginx-uwsgi-flask.png)

Source: [A Guide to Scaling Machine Learning Models in Production](https://hackernoon.com/a-guide-to-scaling-machine-learning-models-in-production-aa8831163846)

🐍 The configurations for Nginx is in /nginx.conf, and the configurations for uWsgi is in /uwsgi.ini. One can optimise the performance of the web server by tweaking the configurations in /nginx.conf. One thing to note, I have chosen to use `processes = 4` in the /uwsgi.ini configurations, since Python has a **GIL** (Global Interpreter Lock), thus only one thread can run at a time. By <u>running multiple uWsgi processes, each has its own instance of Python and GIL, hence allowing concurrent requests.</u> 

## Endpoints

All routes of the endpoints are defined in */orders/views.py*

### POST  /orders 

Use case: users to place an order.

 I use the [Google Map Distance Matrix API ](https://cloud.google.com/maps-platform/routes/) to find the distance between origin and destination. The API key can be set in */docker-compose.yml* `GMAP_TOKEN`. Without a valid token, HTTP 400 will be raised by the endpoint since distance cannot be retrieved from the Google Map Distance Matrix API.

Request body example:

```json
{
  "origin": ["50.456399", "12.707580"],
  "destination": ["59.436487", "24.747193"]
}
```

Response body (HTTP 200) example:

```json
{
  "distance": 1728057,
  "id": 16,
  "status": "UNASSIGNED"
}
```

If the 1) request body fails the jsonschema validation or 2) the order cannot be created on the database level, it will respond with HTTP  400 and with response body of the error message.

You can find the functions to the endpoint in `order_app/place_order.py`.

In here, I use [flask-inputs](https://pythonhosted.org/Flask-Inputs/) and [jsonschema](https://python-jsonschema.readthedocs.io/en/stable/) to validate the request body json, it gives a clean and neat way to maintain the validity of the request body. The unit test (`tests/unit_tests/tests_place_order.py`) coverage includes different invalid request body cases. While as the integration test covers other functions that requires database connectivity, I do so with **real database connectivity** to a test database - `TestDB`. 

### PATCH /orders/:id

Use case: deliverymen to take an order.

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

If the 1) request parameters fails validation or request body fails the jsonschema validation, 2) the request to place order fails e.g. the order is already taken (status: "TAKEN") or 3) the status update at the database level fails (cannot obtain row lock since it's occupied etc.), it will respond with HTTP  400 with response body of the error message.

🔒 Consider the case where multiple deliverymen try to take the same order (same order id) concurrently (**concurrent request**), that would lead to a **race condition**, and we need to control how the requests are being processed, or some requests need to be marked as fails. In here, I use [**database row-level locking**](https://www.postgresql.org/docs/9.1/explicit-locking.html) to <u>allow only one request to update the order record and fail the others. In particular, one can use the PostgreSQL `FOR UPDATE` clause with `NOWAIT</u>`.

The functions to this endpoint can be found in `order_app/take_order.py`. Both unit tests and integration tests are implemented for this endpoint. In addition, I adopted an open source tool for **load testing** - [Locust](https://locust.io/). 

❌ !!! IMPORTANT: You should do the load testing by spinning up the containers with **connection to a Test Database**,  since there is no mocking involved! You can change the connection to a test database instead in *docker-compose.yml*. Also be mindful of the Google Map Distance Matrix API (used in Place Order) call limit when doing load testing.

Prerequisite: [locust](https://locust.io/). You can install the version that's used here with `pip install locustio==0.14.5`

The load test can be started with: 

```shell
make test-load
```

After running the `locust` command, you can see in the output - `locust.main: Starting web monitor at http://*:8089`. Now if you open `localhost:8089`, you can see the Locust UI. Just input the total users, hatch rate and host (hostname of the actual host, i.e. localhost) to start the load test.

![locust ui](https://github.com/clara-codes/docker-flask-nginx/blob/master/readme-images/locust%20ui.png?raw=true)

While the test is running, the statistics will be shown on the UI : 

![locust ui stats](https://raw.githubusercontent.com/clara-codes/docker-flask-nginx/master/readme-images/locust%20ui%20stats.png)

As you can see, only one `PATCH /orders` succeeded, that's because the other failed due to concurrent requests or orders having been taken hence returning HTTP 400, which is the expected behaviour.

### GET /orders

Use case: for system admin to view existing orders.

Here we use pagination to divide all existing orders from the database into discrete pages to be returned as json - an array of order items.

Request example: 

```http
GET /orders?page=1&limit=3
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

If 1) the request parameters fail validation or 2) cannot retrieve orders from the database, it will return HTTP 400 with an error message. In here the pagination is implemented with [flask-sqlalchemy](https://flask-sqlalchemy.palletsprojects.com/en/2.x/api/). 

Only integration tests are implemented for this endpoint, since the only function that needs testing requires database connectivity. You can find the functions to this endpoint in `/order_app/order_list.py`. 

## Testing

Directory: tests/ 

You will need to have built the docker image with `--target=test_builder` to run the tests. The tests/ folder is only copied for the container for build target `--target=test_builder`. Since this folder is unnecessary for deployment, but only for automated testing. One can optionally copy the folder to build the deployment image to run the tests in the deployed container. 

As described earlier, in the Makefile section, you can **run the automated tests (unit tests and integration tests) simply using two commands**.

### Unit Test

Directory: /tests/unit_tests/ 

If one wants to run unit tests only and without using docker-compose:

```bash
$ make image BUILD_TARGET=test_builder
#this will build a docker image named order-api to the stage - test_builder
$ docker run -it <name of image> bash
#The default name of the image is order-api
```

And this will bring you to an interactive bash session, then you can just run:

```shell
$ make test-unit
```

I use python [unittest](https://docs.python.org/3/library/unittest.html) framework to write the tests. And you can run all the unit tests `unittest.TestCase` in make target: `test-unit`. Optionally, one can group `unittest.TestCase` that should be run together.

The unit tests cover all functions or class functions that do not require database connectivity. In addition, the unit tests cover both success and failure cases for the functions, in particular the unit tests cover whether the functions are returning error messages when errors are expected to occur and be captured.

To isolate the functionalities that I want to test, I used `unittest.mock` to mock database connection and calls to external api i.e. Google Map Distance Matrix API.

###  Integration Test

Directory: /tests/integration_tests/

Since real database connectivity is required for integration tests, it's recommended to use docker-compose to run them, as described as the Makefile section, i.e.:

```shell
$ make image BUILD_TARGET=test_builder
#this will build a docker image named order-api to the stage - test_builder
$ make docker-compose
#this will spin up a container and run the automated tests and exit with code 0
```

All executions of integration tests can be executed with make target: `test-integration`. The integration tests cover all functions or class functions that **require database connectivity**, including the functions to create the database and tables. In the integration tests, `unittest.mock`  is used to make the functions connect to the test database `TestDB` instead of the real database for isolating the test data for testing (not mocking the database connection), it is also used to mock the external API call to exclude uncontrollable factors to the integration tests.

### Load Test (end-to-end performance testing)

Directory: /tests/integration_tests/load_tests/

I use load test here to expose the concurrency problem, and test the service on handling concurrent requests. To start the load test:

```shell
$ make test-load
```

All executions of the load tests can be executed with make target: `make test-load` (as described earlier under section - Endpoint). No mocking is involved for load testing, so one should configure (in /*docker-compose.yml*) the running service to be tested with connection to a Test Database. Load test is only implemented for endpoints: `GET /orders` and `PATCH /order/:id`, since high request traffic is expected only for these 2 endpoints.

To summarise, I have the following tests in place:

1. Tests with mock database connectivity and  mock external API calls.
2. Tests with real database connectivity (to a Test Database) and mock external API calls
3. Tests with real database connectivity (to a Test Database) and real external API calls.
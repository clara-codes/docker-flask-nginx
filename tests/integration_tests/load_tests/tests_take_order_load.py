from locust import HttpLocust, TaskSet, task, between
from app.settings import TEST_DIR
import os, json

class OrderBehavior(TaskSet):

	def on_start(self):
		#self.place_order()
		pass

	def place_order(self):
		origins = ["59.456399", "24.707580"]
		destinations = ["59.436487", "24.747193"]
		self.client.post("http://localhost:8080/orders", json='{"origin": origins, "destination": destinations}')

	@task(1)
	def take_order(self):
		self.client.patch("http://localhost:8080/orders/1", json={"status":"TAKEN"})

class WebsiteUser(HttpLocust):
    task_set = OrderBehavior
    wait_time = between(5, 9)
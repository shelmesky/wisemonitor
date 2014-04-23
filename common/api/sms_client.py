#!encoding: utf-8--

import re
import json

import tornado.ioloop
import tornado.web
from tornado.httpclient import AsyncHTTPClient
from tornado.httpclient import HTTPClient
from tornado.httpclient import HTTPRequest

from sms_config import cell_phones


def send_sms(data, data_type):
	if data_type == "nagios":
		space = " "
		created_time = data["created_time"]
		msg = data['message']
		host = msg["host"]
		service = msg["service"]
		output = msg["output"]
		final_message = created_time + space + host
		if service:
			final_message += space + service
		final_message += space + output

		phones = None
		for rule in cell_phones:
			if re.match(rule[0], host):
				phones = rule[1]
				break

			if re.match(rule[0], service):
				phones = rule[1]
				break

			if re.match(rule[0], output):
				phones = rule[1]
				break

		if phones != None:
			do_send_sms(phones, str(final_message))

	if data_type == "xen":
		pass


def do_send_sms(cell, data):
	http_client = HTTPClient()
	sms_url = "http://172.31.11.203:8080/notify/sms/"
	request = HTTPRequest(sms_url)
	request.headers["Content-Type"] = "application/json"
	request.headers["HTTP_HEAD_ENCODING"] = "utf-8"
	request.method = "POST"
	request.body = '{"id":"0","phones":"' + cell + '","content":"' + data + '"}'
	resp = http_client.fetch(request)
	if resp.code != 201:
		raise RuntimeError("SMS Gateway Error: " + str(resp.code))
	print resp.code, resp.body


if __name__ == "__main__":
	# make a simple test
	send_sms("15317098900", "ok")


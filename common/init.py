from tornado import web


class WiseHandler(web.RequestHandler):
	@property
	def http_host(self):
		return self.request.host
	
	def compute_etag(self):
		return None
	
	def get_error_html(self, status_code, **kwargs):
		if status_code == 403:
			pass
		elif status_code == 405:
			pass
		elif status_code == 500:
			pass
		else:
			pass


class PageNotFound(web.RequestHandler):
	def get(self):
		self.set_status(404)
		self.render("404.html")
	

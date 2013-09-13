from tornado import web


class WiseHandler(web.RequestHandler):
	@property
	def http_host(self):
		return self.request.host
	
	def compute_etag(self):
		return None
	

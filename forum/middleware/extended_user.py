class ExtendedUser(object):    
    def process_request(self, request):
        if request.user.is_authenticated():
            request.user = request.user.user
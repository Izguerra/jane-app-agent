import urllib.request
import urllib.error

# Note: No trailing slash
url = "http://localhost:3000/api/customers"

try:
    # Don't follow redirects automatically
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url)
    with opener.open(req) as response:
        print(f"Response Code: {response.getcode()}")
        print(f"Response Headers: {response.info()}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} {e.reason}")
    print(f"Headers: {e.headers}")
    if e.code in [301, 302, 307, 308]:
        print(f"Redirect Location: {e.headers.get('Location')}")
except Exception as e:
    print(f"Error: {e}")

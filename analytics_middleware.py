import settings
ga_html = """
<script type="text/javascript">

  var _gaq = _gaq || [];
  _gaq.push(['_setAccount', '%s']);
  _gaq.push(['_trackPageview']);

  (function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
  })();

</script></head>"""

class GoogleAnalyticsMiddleware:
    def process_response(self, request, response):
        ga_id = settings.GOOGLE_ANALYTICS_ID
        if ga_id and "text/html" in response.get('content-type', ''):
            current = response.content
            replacement = ga_html % ga_id
            response.content = current.replace("</head>", replacement)
        return response

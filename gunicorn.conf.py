import multiprocessing

bind = "0.0.0.0:5000"
workers = int(multiprocessing.cpu_count() * 2) + 1
accesslog = "-"   # stdout
errorlog = "-"    # stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" "%({X-Request-ID}i)s"'

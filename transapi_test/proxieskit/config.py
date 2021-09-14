class Config(object):
    API_IP = '0.0.0.0' # server ip
    API_PORT = '65430'	 # server port
    VERIFICATION_TIMEOUT = 1.5 # proxy availability test time
    STORAGE_GOOGLE_UPPER_BOUND = 100	# max storage which can reach self-designed verification sites
    STORAGE_NONGOOGLE_UPPER_BOUND = 200	# max storage of normal proxies
    STORAGE_LOWER_BOUND = 50		# minimum number of proxies
    STORAGE_WATCH_SLEEP_TIME = 30	# check volumn of proxy pool every 60 seconds
    

configger = Config()

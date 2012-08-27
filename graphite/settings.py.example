# Number of seconds ago from now, if a start timestamp is not given.
# XenServer stores 5sec data for 10min (600sec).  We use a number slight
# less than 600 so that we won't be affected by small discrepancy in time.
COLLECTOR_START_SECONDS_AGO = 500


# Redis config for cache
REDIS = ('localhost', 6379, 0)


# XenServer hosts (usually pool masters) for looking up VM names.
# Each tuple is (host, username, password)
XENSERVERS = (
    ('192.2.4.61', 'rrd', '123456'),
)

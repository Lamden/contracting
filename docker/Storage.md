# Some Notes on Storage #

* We're stopping use of myrocks, keeping the Docker container in the repo for, benchmarks, etc.
* We're looking at larger than memory Redis compatible stores and sharding proxies for future expansion.

## Redis compatible larger than memory datastores ##
* ardb - https://github.com/yinqiwen/ardb
* Ledisdb - https://github.com/siddontang/ledisdb
* ssdb - https://github.com/ideawu/ssdb
* Any others?

## Redis proxies ##
* twemproxy
* dynomite
* codis
* xcodis
  * From author of Ledis
* Any others?

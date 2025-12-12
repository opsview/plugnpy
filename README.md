# plugnpy


*A Simple Python Library for creating [Opsview Opspack plugins](https://docs.itrsgroup.com/docs/opsview/6.11.7/configuration/service-checks-and-host/active-checks/index.html).*

[![Master Build Status](https://secure.travis-ci.org/opsview/plugnpy.png?branch=master)](https://travis-ci.org/opsview/plugnpy?branch=master)
[![Master Coverage Status](https://coveralls.io/repos/opsview/plugnpy/badge.svg?branch=master&service=github)](https://coveralls.io/github/opsview/plugnpy?branch=master)

* **category**    Libraries
* **copyright**   2003-2025 ITRS Group Ltd
* **license**     Apache License Version 2.0 (see [LICENSE](LICENSE))
* **link**        https://github.com/opsview/plugnpy


## Installing the Library

For Opsview versions above 6.1. **plugnpy** is preinstalled.

For Opsview versions below 6.1, Opsview Python's **pip** needs to be used to install the library.

```
/opt/opsview/python/bin/pip install <location of plugnpy-version.tar.gz>
```

To install the library locally, download the release package and install with **pip**.

```
pip install <location of plugnpy-version.tar.gz>
```

## Quick Start

This project includes a Makefile that allows you to test and build the project in a Linux-compatible system with simple commands.

To see all available options:
```
make help
```

To create a development environment:
```
make venv
```

To run the tests in the development environment:
```
make test
```

To build the library in the development environment:
```
make build
```

This will create a `plugnpy-VERSION.tar.gz` file in the `dist` directory which can be installed in the same way as the prepackaged one above.

The coverage report is available at:
```
htmlcov/index.html
```

## Writing Checks

The core of a check written using plugnpy is the **Check** object. A **Check** object must be instantiated before metrics can be defined.

```python
import plugnpy
check = plugnpy.Check()
```

To add metrics to this check, simply use the **add_metric()** method of the **Check** object. This takes in arguments to add a **Metric** object to an internal array.

```python
check.add_metric('disk_usage', 30.5, '%', display_name="Disk Usage",
                 display_format='{name} is {value}{unit}')
```

The **Metric** objects are then used to create the final output when the **final()** method is called.

```python
check.final()
```

This would produce the following output:

`METRIC OK - Disk Usage is 30.50% | disk_usage=30.50%;;`

You can also specify the precision of the value in the summary and the performance data that you want to output, by using the **summary_precision** and **perf_data_precision** parameters when adding metrics (default is 2 decimal places):

```python
check.add_metric('disk_usage', 30.55432, '%', display_name="Disk Usage",
                 display_format='{name} is {value}{unit}', summary_precision=3, perf_data_precision=4)
```
This would produce the following output:

`METRIC OK - Disk Usage is 30.554% | disk_usage=30.5543%;;`

## Checks with thresholds

To apply thresholds to a metric, simply set the threshold values in the **add_metric()** call.

```python
check.add_metric('cpu_usage', 70.7, '%', warning_threshold='70', critical_threshold='90',
                 display_name="CPU Usage", display_format="{name} is {value}{unit}")
```

This would produce the following output:

`METRIC WARNING - CPU Usage is 70.70% | cpu_usage=70.70%;70;90`

The library supports all Nagios threshold definitions as found here: [Nagios Development Guidelines · Nagios Plugins](https://nagios-plugins.org/doc/guidelines.html#THRESHOLDFORMAT).

As well as being fully compatible with Nagios thresholds, **plugnpy** allows thresholds to be specified in friendly units.

```python
check.add_metric('mem_swap', 100, 'B', '10MB', '20MB', display_name="Memory Swap")
```

This would produce the following output:

`METRIC OK - Memory Swap is 100.00B | mem_swap=100.00B;10MB;20MB`

## Writing checks with multiple metrics

Writing service checks with multiple metrics is easy. Simply create the **Check** object and add multiple metrics using the **add_metric()** method.

```python
check = plugnpy.Check()
check.add_metric('disk_usage', 30.5, '%', '70', '90', display_name="Disk Usage",
                 display_format='{name} is {value}{unit}')
check.add_metric('cpu_usage', 70.7, '%', '70', '90', display_name="CPU Usage",
                 display_format='{name} is {value}{unit}')
check.final()
```

This would produce the following output:

`METRIC WARNING - Disk Usage is 30.50%, CPU Usage is 70.70% | disk_usage=30.50%;70;90 cpu_usage=70.70%;70;90`

When adding multiple metrics, the separator between metrics can be customised. By default this is set to `', '` but can easily be changed or removed by setting the **sep** field when creating the **Check** object.

```python
check = plugnpy.Check(sep=' + ')
```

Adding multiple metrics to the **Check** object would then produce the following output:

`METRIC OK - Disk Usage is 30.50% + CPU Usage is 70.70% | disk_usage=30.5%;70;90 cpu_usage=70.70%;70;90`

## Checks with automatic conversions

To create a check with automatic value conversions, simply call the **add_metric()** method with the **convert_metric** field set to **True**.
The unit passed in should not have any existing prefix - for example, pass your value in **B** rather than **KB** or **MB**.

Setting the **convert_metric** field to **True** will override the unit (displayed in the summary) with the best match for the conversion.
By default, **convert_metric** is set to **True** only for metrics in **B**, **b**, **Bps** and **bps**.

The supported conversion prefixes are:

|Prefix Name | Prefix Symbol | Base 1000         |
|:-----------|:--------------|:------------------|
|exa         |E              | 1000<sup>6</sup>  |
|peta        |P              | 1000<sup>5</sup>  |
|tera        |T              | 1000<sup>4</sup>  |
|giga        |G              | 1000<sup>3</sup>  |
|mega        |M              | 1000<sup>2</sup>  |
|kilo        |K              | 1000<sup>1</sup>  |
|milli       |m              | 1000<sup>-1</sup> |
|micro       |u              | 1000<sup>-2</sup> |
|nano        |n              | 1000<sup>-3</sup> |
|pico        |p              | 1000<sup>-4</sup> |


The units supporting these prefixes are as follows:

|Unit          |Supported conversion prefixes   |
|:-------------|:-------------------------------|
|s             |p, n, u, m                      |
|B, b, Bps, bps|K, M, G, T, P, E                |
|W, Hz         |p, n, u, m, K, M, G, T, P, E    |


For example, adding the metric:

```python
check.add_metric('mem_buffer', 1829863424, 'B', '1073741824', '2147483648',
                 display_name="Memory Buffer", convert_metric=True)
```
Would produce the following output:

`METRIC WARNING - Memory Buffer is 1.70GB | mem_buffer=1829904384.00B;1073741824;2147483648`

And adding the metric below:

```python
check.add_metric('latency', 0.0002, 's', '0.0004', '0.0007', display_name="Latency",
                 convert_metric=True, summary_precision=1, perf_data_precision=4)
```
Would produce the following output:

`METRIC WARNING - Latency is 0.2ms | latency=0.0002s;0.0004;0.0007`

All unit conversions are dealt with inside the library (as long as **convert_metric** is set to **True**), allowing values to be entered without having to do any manual conversions.

For metrics with the **unit** related to bytes (**B**, **b**, **Bps** or **bps**), conversions are done based on the International Electrotechnical Commission (IEC) standard, using 1024 as the base multiplier. However the library also supports the International System (SI) standard, which uses 1000 as the base multiplier, this can be changed by calling **add_metric()**  with the **si_bytes_conversion** field set to **True** (**False** by default).

```python
check.add_metric('mem_buffer', 1000, 'B', '1GB', '2GB', display_name="Memory Buffer",
                 convert_metric=True, si_bytes_conversion=True, summary_precision=0)
```

This would produce the following output:

`METRIC OK - Memory Buffer is 1KB | mem_buffer=1000.00B;1GB;2GB`


For metrics using any other unit, conversions are done using the SI standard (1000 as the base multiplier).

## Helper methods

The **Metric** class includes two helper methods to make developing service checks easier.

The **evaluate()** method evaluates a metric value against the specified warning and critical thresholds and returns the status code.

```python
status_code = metric.evaluate(15, '10', '20')
```

The above example would return the value `1`, since the value is above the warning threshold but not the critical threshold.

The **convert_value()** method converts a given value and unit to a more human friendly value and unit.

```python
value, unit = metric.convert_value(2048, 'B')
```

The above example would return `2.00` as the value and `'KB'` as the unit.
Both methods support the **si_bytes_conversion** field. See [**Checks with automatic conversions**](#checks-with-automatic-conversions) above for more details.

## Using the Argument Parser

**plugnpy** comes with its own Argument Parser. This parser inherits from **argparse.ArgumentParser** but will exit with code 3 when called with the -h/--help flag.

The parser also has the ability to print copyright information when -h/--help is called.

This can either be setup when the **Parser** object is created.

```python
parser = plugnpy.Parser(description="Monitors Memory Utilisation",
                        copyright="Example Copyright 2017-2018")
```

Or added after by calling the **set_copyright()** method.
```python
parser = plugnpy.Parser(description="Monitors Memory Utilisation")
parser.set_copyright("Example Copyright 2017-2018")
```

To use the parser, create an object of type **plugnpy.Parser** and use as you would normally use an **argparse.ArgumentParser** object.

## Using the Exceptions

**plugnpy** comes with its own **Exception** objects. They have no special implementation beyond their names and can be found in **plugnpy.Exceptions**. To be consistent, here are the appropriate times to raise each exception:

| Exception              | Usage                                                                                                                                                                |
|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ParamError             | To be thrown when user input causes the issue (i.e, wrong password, invalid input type, etc.)                                                                        |
| ParamErrorWithHelp     | To be thrown when user input causes the issue (i.e, wrong password, invalid input type, etc.) and help text needs to be printed.                                     |
| ResultError            | To be thrown when the API/Metric Check returns either no result (when this isn't expected) or returns a result that is essentially unusable.                         |
| AssumedOK              | To be thrown when the status of the check cannot be identified. This is usually used when the check requires the result of a previous run and this is the first run. |
| InvalidMetricThreshold | This should not be thrown in a plugin. It is used internally in checks.py when an invalid metric threshold is passed in.                                             |
| InvalidMetricName      | This should not be thrown in a plugin. It is used internally in checks.py when an invalid metric name is passed in.                                                  |

## Cache Manager client

**plugnpy** comes with an http client which is able to connect to the opsview-cachemanager component.
This allows the plugins to use the cache manager to store temporary data into memory which can be consumed by other
servicechecks which require the same data.

The module consists of two classes, namely **CacheManagerClient** and **CacheManagerUtils**, which provide easy to use
interfaces to communicate with the opsview-cachemanager.

### CacheManagerClient
A simple client to set or get cached data from the cache manager.

The cache manager client requires the **namespace** of the plugin and the **host** ip and **port** of the cache manager
to be supplied. These are provided to the plugin as opsview-executor encrypted environment variables.

```python
host = os.environ.get('OPSVIEW_CACHE_MANAGER_HOST')
port = os.environ.get('OPSVIEW_CACHE_MANAGER_PORT')
namespace = os.environ.get('OPSVIEW_CACHE_MANAGER_NAMESPACE')
```

A cache manager client can then be created:
```python
client = CacheManagerClient(host, port, namespace)
```

Items inserted into the cache manager are namespaced, ensuring naming collisions are avoided and potentially sensitive
data cannot be read by other unauthorized plugins.

Optionally, when creating the client, the **concurrency**, **connection_timeout** and **network_timeout** parameters can
be specified to modify the number of concurrent http connection allowed (default: 1), the number of seconds before the
HTTP connection times out (default: 30) and the number of seconds before the data read times out (default: 30),
respectively.

```python
client = CacheManagerClient(host, port, namespace, concurrency=1, connection_timeout=30,
                            network_timeout=30)
```
Once a cache manager client has been created, the **get_data** and **set_data** methods can be used to get and set data
respectively.

The **set_data** method can be called with the **key** and **data** parameters, this will store the specified data,
under the given key. Optionally, the **ttl** parameter (Time To Live) can be used to specify the number of seconds the
data is valid for (default: 900). It is expected that session information and other temporary data will be stored in the
cache manager. 15 minutes has been chosen as the default to ensure data does not have to be recreated too often, but in
the event of a change in data, the cached information does not persist for too long.

```python
client.set_data(key, data, ttl=900)
```

The **get_data** method can be called with the **key** parameter to retrieve data stored under the specified key.
Optionally, the **max_wait_time** parameter can be used to specify the number of seconds to wait before timing out
(default: 30).

```python
client.get_data(key, max_wait_time=30)
```

Calling the **get_data** method when the data exists in the cache manager will return the data. However, if the data
does not exist in the cache manager, it will return a lock. Obtaining a lock means the cache manager expects the
component to make the call to get the data directly and then use the **set_data** method to set the data in the cache
manager, ready to be used by other components. Any concurrent components calling the **get_data** method will block if
they cannot obtain the lock, this ensures that only one component sets the data. Once the data has been set, all blocked
components will be unblocked and return the newly cached data. The **max_wait_time** parameter of the **get_data**
method has a default of 30 seconds, but needs to be large enough for this cycle to be completed.


### CacheManagerUtils

#### get_via_cachemanager

To simplify calls to the cache manager, **plugnpy** provides a helper utility method **get_via_cachemanager**, this will
create the cache manager client and call the **get_data** and **set_data** methods as required.

This method expects the following parameters:
* no_cachemanager: True if cache manager is not required, False otherwise.
* key: The key to store the data under.
* ttl: The Time To Live, number of seconds the data is valid for in the cache manager.
* func: The function to retrieve the data, if the data is not in the cache manager.
* args: The arguments to pass to the user's data retrieval function.
* kwargs: The keyword arguments to pass to the user's data retrieval function.


```python
def api_call(string):
  return string[::-1]

CacheManagerUtils.get_via_cachemanager(no_cachemanager, 'my_key', 300, api_call, 'hello')
```

In this example, if the data exists in the cache manager under the key `'my_key'`, the call to **get_via_cachemanager**
will simply return the data. However, if the data does not exist in the cache manager, the call to
**get_via_cachemanager** will call the **api_call** method with the argument `'hello'` and then set the data in the
cachemanager, so future calls can use the data from the cache manager. The data is valid for the time specified by the
TTL.

#### set_data

Sometimes data must be inserted or updated in the cache manager, without retrieving the existing data. In these
scenarios the **set_data** method can be used, this will create the cache manager client and call the **set_data**
method of the **CacheManagerClient** internally.

```python
CachemanagerUtils.set_data(key, data, ttl)
```

#### generate_key

CacheManagerUtils also contains a **generate_key** method which can be used to create a unique key for cache manager
based on the arguments that are passed in. All arguments are first escaped if they contain the cache manager delimiter
(`#`), and then joined by the delimiter before a SHA-256 hash is generated.

```python
CacheManagerUtils.generate_key('foo', 'b#ar', 'b\#az')
```

This would be equivalent to:

```python
hash_string('foo#b\#ar#b\\\#az')
```

### Utils

#### convert_seconds

**utils.py** contains a helper method **convert_seconds** to allow converting seconds to a more human readable format.
For values more than `60` seconds, the seconds value will be omitted from the output, for values greater than `60`, the
value will be returned in seconds.
For example passing in the value `90060` to **convert_seconds** will return `1d 1h 1m`,
and passing in the value `45` will return `45s`.


## State Manager client

The State Manager provides a persistent data store for plugins.
Data is held until its `time-to-live` expires and will remain in the store across system reboots and upgrades.

*Requires Opsview 6.11.7 or later.*

### StateManagerClient
A simple client to store or fetch data from the state manager.

The state manager client requires the **namespace** of the plugin and the **host** ip and **port** of the state manager
to be supplied. These are provided to the plugin as `opsview-executor` encrypted environment variables.

```python
host = os.environ.get('OPSVIEW_STATE_MANAGER_HOST')
port = os.environ.get('OPSVIEW_STATE_MANAGER_PORT')
namespace = os.environ.get('OPSVIEW_STATE_MANAGER_NAMESPACE')
```

A state manager client can then be created using these values:
```python
client = StateManagerClient(host, port, namespace)
```

Two methods are available with the State Manager client, `store_data` and `fetch_data`.
These methods are be used to save and retrieve data respectively.

#### store_data

 - The `store_data` method can be called with the `key` and `data` parameters,
   this will store the specified data, under the given key.
 - The `ttl` parameter is used to specify the number of seconds for which the data is valid.
 - An optional `timestamp` parameter can be used to mark the time the data was obtained.
   This can be useful when there is a degree of latency between the source of the data and the call to the `store_data` method.
   If `timestamp` is in the future, then the current time will be used instead.

#### fetch_data

The `fetch_data` method can be called with the `key` parameter to retrieve data stored under the specified key.

```python
data = client.fetch_data(key)
```

### StateManagerUtils

To simplify calls to the state manager even further, **plugnpy** provides this utility class.
It has two methods for storing and fetching data, and handles the underlying connection details.

```python
from plugnpy.statemanager import StateManagerUtils

client = StateManagerUtils()
```

Once the client has been created, the `store_data` and `fetch_data` methods can be used to save and retrieve data respectively.

#### store_data

 - The `store_data` method can be called with the `key` and `data` parameters,
   this will store the specified data, under the given key.
 - The `ttl` parameter is used to specify the number of seconds for which the data is valid.
 - An optional `timestamp` parameter can be used to mark the time the data was obtained.
   This can be useful when there is a degree of latency between the source of the data and the call to the `store_data` method.
   If `timestamp` is in the future, then the current time will be used instead.

```python
client.store_data(key, data, ttl=3600)
```

#### fetch_data

The `fetch_data` method can be called with the `key` parameter to retrieve data stored under the specified key.

```python
data = client.fetch_data(key)
```

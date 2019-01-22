# plugnpy


*A Simple Python Library for creating [Opsview Opspack plugins](https://github.com/opsview/Opsview-Integrations/blob/master/WHAT_IS_A_MONITORING_PLUGIN.md).*

* **category**    Libraries
* **copyright**   2018-2019 Opsview Ltd
* **license**     Apache License Version 2.0 (see [LICENSE](LICENSE))
* **link**        https://github.com/opsview/plugnpy


## Installing the Library

For use with versions of Opsview below 6.1, Opsview Python's pip will need to be used to install this library, as they do not ship with it pre-installed.

`/opt/opsview/python/bin/pip install <location of plugnpy-version.tar.gz>`

To install the library locally, download the release package and simply install with pip.

`pip install <location of plugnpy-version.tar.gz>`

## Quick Start

This project includes a Makefile that allows you to test and build the project in a Linux-compatible system with simple commands.

To see all available options:
```
make help
```

To build a Conda development environment:  
```
make conda_dev
. activate
```

To test inside a `conda_dev` environment using setuptools:  
```
make test
```

To build and test the project inside a Conda environment:  
```
make build
```

The coverage report is available at:  
```env-~#PROJECT#~/conda-bld/coverage/htmlcov/index.html```


## Building the Library

Should you wish (or if you've made improvements to the source code and you want to use them), the library can be built with the following command.

`python setup.py sdist`

This will create a plugnpy-version.tar.gz file in /dist which should be installed the same way as the prepackaged one above.


## Writing Checks

All plugins written using the Library must first import it. This can be done by simply writing import plugnpy at the top of the script.

The core of a check written using plugnpy is the Check object. A Check object must be instantiated before Metrics can be defined.

```python
check = plugnpy.Check()
```

To add metrics to this check, simply use the add_metric() method of your Check object. This takes in arguments to add a Metric object to an internal array. It is these Metric objects that are called upon to create the final output.

```python
check.add_metric('metric_name', metric_value, unit, warning_threshold, critical_threshold,
                 display_name="Metric Name", msg_fmt="{name} at {value}{unit}",
                 convert_metric=True)
```

### Checks with thesholds

To create a check with thresholds, simply set the threshold values in the add_metric() call. Ideally, these metrics would come from user passed arguments but they are hardcoded here as an example.

```python
check.add_metric('cpu_usage', 70.7, '%', 60, 80, display_name="CPU Usage",
                 msg_fmt="{name} at {value}{unit}")
```

This line would create the following output:

`METRIC WARNING - CPU Usage at 70.7% | cpu_usage=70.7%;60;80`

The library supports all nagios threshold definitions as found here: [Nagios Development Guidelines · Nagios Plugins](https://nagios-plugins.org/doc/guidelines.html#THRESHOLDFORMAT).

### Checks with metrics with units

To create a check with thresholds, simply set the unit in the add_metric() call.

```python
check.add_metric('mem_buffer', 1829863424, 'B', "1GB", "2GB", display_name="Memory Buffer",
                 convert_metric=True)
```

This line would create the following output:

`METRIC WARNING - Memory Buffer is 1.70GB | mem_buffer=1829904384B;1073741824;2147483648`

As you can see, all unit conversion is dealt with inside the library (so long as *convert_metric* is set to true!), allowing users to input their thresholds in friendly units rather than having to calculate the bytes themselves. Having *convert_metric* set to True will ignore the unit passed in and override it with the best match in Bytes.

## Using the Argument Parser

plugnpy comes with its own Argument Parser. This parser is essential argparse.ArgumentParser (a Python built in) but with its own  error() and  exit() to quit with the appropriate exit codes for Opspack UNKNOWNS.

The Parser also has the ability to print copyright information when -h/--help is called. This can either be setup when the Parser object is created, or added after.

```python
# Example 1
parser = plugnpy.Parser(description="Monitors Memory Utilisation",
                        copyright="Example Copyright 2017-2018")

# Example 2
parser = plugnpy.Parser(description="Monitors Memory Utilisation")
parser.set_copyright("Example Copyright 2017-2018")
```

To use the parser, create an object of type plugnpy.Parser and use as you would normally use an ArgumentParser object.

## Using the Exceptions

plugnpy comes with its own Exception objects. These mirror the Exceptions we've used in recent Opspacks. They have no special implementation beyond their names and can be found in plugnpy.Exceptions. To be consistent, here is the appropriate times to raise each Exception.

| Exception              | Usage                                                                                                                                                                |
|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ParamError             | To be thrown when user input causes the issue (i.e, wrong password, invalid input type, etc.)                                                                        |
| ResultError            | To be thrown when the API/Metric Check returns either no result (when this isn't expected) or returns a result that is essentially unusable.                         |
| AssumedOK              | To be thrown when the status of the check cannot be identified. This is usually used when the check requires the result of a previous run and this is the first run. |
| InvalidMetricThreshold | This shouldn't be thrown in a plugin. It is used internally in checks.py when an invalid metric threshold is passed in.                                              |
| InvalidMetricName      | This shouldn't be thrown in a plugin. It is used internally in checks.py when an invalid metric name is passed in.                                              |

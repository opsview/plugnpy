# plugnpy


*A Simple Python Library for creating [Opsview Opspack plugins](https://github.com/opsview/Opsview-Integrations/blob/master/WHAT_IS_A_MONITORING_PLUGIN.md).*

[![Master Build Status](https://secure.travis-ci.org/opsview/plugnpy.png?branch=master)](https://travis-ci.org/opsview/plugnpy?branch=master)
[![Master Coverage Status](https://coveralls.io/repos/opsview/plugnpy/badge.svg?branch=master&service=github)](https://coveralls.io/github/opsview/plugnpy?branch=master)

* **category**    Libraries
* **copyright**   2018-2019 Opsview Ltd
* **license**     Apache License Version 2.0 (see [LICENSE](LICENSE))
* **link**        https://github.com/opsview/plugnpy


## Installing the Library

For Opsview versions above 6.1. plugnpy is preinstalled.

For Opsview versions below 6.1, Opsview Python's pip needs to be used to install the library.

```
/opt/opsview/python/bin/pip install <location of plugnpy-version.tar.gz>
```

To install the library locally, download the release package and install with pip.

```
pip install <location of plugnpy-version.tar.gz>
```

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
```
env-~#PROJECT#~/conda-bld/coverage/htmlcov/index.html
```


## Building the Library

Should you wish (or if you've made improvements to the source code and you want to use them), the library can be built with the following command.

```
python setup.py sdist
```

or

```
make wheel
```

This will create a `plugnpy-VERSION.RELEASE.tar.gz` file in the `dist` directory which should be installed the same way as the prepackaged one above.


## Writing Checks

All plugins written using the Library must first import it. This can be done by simply writing import plugnpy at the top of the script.

The core of a check written using plugnpy is the **Check** object. A **Check** object must be instantiated before metrics can be defined.

```python
check = plugnpy.Check()
```

To add metrics to this check, simply use the **add_metric()** method of your **Check** object. This takes in arguments to add a **Metric** object to an internal array.

```python
check.add_metric('disk_usage', 30.5, '%', '70', '90',
                 display_name='Disk Usage', display_format='{name} is {value}{unit}')
```

The **Metric** objects are then used to create the final output when the **final()** method is called.

```python
check.final()
```

This would produce the following output:

`METRIC OK - Disk Usage is 30.5% | disk_usage=30.5%;70;90`

## Writing checks with multiple metrics

Writing service checks with multiple metrics is easy. Simply create the **Check** object and add multiple metrics using the **add_metric()** method.

```python
check = plugnpy.Check()
check.add_metric('disk_usage', 30.5, '%', '70', '90', display_name='Disk Usage',
                 display_format='{name} is {value}{unit}')
check.add_metric('cpu_usage', 70.7, '%', '70', '90', display_name='CPU Usage',
                 display_format='{name} is {value}{unit}')
check.final()
```

This would produce the following output:

`METRIC WARNING - Disk Usage is 30.5%, CPU Usage is 70.7% | disk_usage=30.5%;70;90 cpu_usage=70.7%;70;90`

When adding multiple metrics, the separator between metrics can be customised. By default this is set to `', '` but can easily be changed by setting the **sep** field when creating the **Check** object.

```python
check = plugnpy.Check(sep=' ')
```

Adding multiple metrics to the **Check** object would then produce the following output:

`METRIC OK - Disk Usage is 30.5% CPU Usage is 70.7% | disk_usage=30.5%;70;90 cpu_usage=70.7%;70;90`

### Checks with thresholds

To apply thresholds to a metric, simply set the threshold values in the **add_metric()** call.

```python
check.add_metric('cpu_usage', 70.7, '%', '70', '90', display_name='CPU Usage',
                 display_format="{name} is {value}{unit}")
```

This would produce the following output:

`METRIC WARNING - CPU Usage is 70.7% | cpu_usage=70.7%;70;90`

The library supports all nagios threshold definitions as found here: [Nagios Development Guidelines · Nagios Plugins](https://nagios-plugins.org/doc/guidelines.html#THRESHOLDFORMAT).

As well as being fully compatible with nagios thresholds, plugnpy allows thresholds to be specified in friendly units.

```python
check.add_metric('mem_swap', 100, 'B', '10MB', '20MB', display_name='Memory Swap')
```

This would produce the following output:

`METRIC OK - Memory Swap is 100B | mem_swap=100B;10MB;20MB`

### Checks with automatic conversions

To create a check with automatic value conversions, simply call the **add_metric()** method with the **convert_metric** field set to **True**.

**Note**: Setting the **convert_metric** field to **True** will override the unit (displayed in the summary) with the best match for the conversion.

```python
check.add_metric('mem_buffer', 1829863424, 'B', '1073741824', '2147483648', display_name='Memory Buffer',
                 convert_metric=True)
```

This would produce the following output:

`METRIC WARNING - Memory Buffer is 1.70GB | mem_buffer=1829904384B;1073741824;2147483648`

All unit conversions are dealt with inside the library (as long as **convert_metric** is set to **True**), allowing values to be entered without having to do any manual conversions.

For metrics with the **unit** set to bytes (**B**), conversions are done based on the International Electrotechnical Commission (IEC) standard, using 1024 as the multiplier. However the library also supports the International System (SI) standard, which uses 1000 as the multiplier, this can be changed by calling **add_metric()**  with the **si_bytes_conversion** field set to **True** (**False** by default).

```python
check.add_metric('mem_buffer', 1000, 'B', '1GB', '2GB', display_name='Memory Buffer',
                 convert_metric=True, si_bytes_conversion=True)
```

This would produce the following output:

`METRIC OK - Memory Buffer is 1KB | mem_buffer=1000;1GB;2GB`


For metrics using any other unit, conversions are done using the SI standard (1000 as the multiplier).

## Helper methods

The metric class includes two helper methods to make developing service checks easier.

The **evaluate()** method evaluates a metric value against the specified warning and critical thresholds and returns the status code.

```python
status_code = metric.evaluate(15, '10', '20')
```

The above example would return the value '`1`', since the value is above the warning threshold but not the critical threshold.

The **convert_value()** method converts a given value and unit to a more human friendly value and unit.

```python
value, unit = metric.convert_value(2048, 'B')
```

The above example would return '`2.00`' as the value and '`KB`' as the unit.

Both methods support the **si_bytes_conversion** field. See [**Checks with automatic conversions**](#checks-with-automatic-conversions) above for more details.

## Using the Argument Parser

plugnpy comes with its own Argument Parser. This parser inherits from argparse.ArgumentParser but will exit with code 3 when called with the -h/--help flag.

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

plugnpy comes with its own Exception objects. They have no special implementation beyond their names and can be found in plugnpy.Exceptions. To be consistent, here is the appropriate times to raise each Exception.

| Exception              | Usage                                                                                                                                                                |
|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ParamError             | To be thrown when user input causes the issue (i.e, wrong password, invalid input type, etc.)                                                                        |
| ResultError            | To be thrown when the API/Metric Check returns either no result (when this isn't expected) or returns a result that is essentially unusable.                         |
| AssumedOK              | To be thrown when the status of the check cannot be identified. This is usually used when the check requires the result of a previous run and this is the first run. |
| InvalidMetricThreshold | This shouldn't be thrown in a plugin. It is used internally in checks.py when an invalid metric threshold is passed in.                                              |
| InvalidMetricName      | This shouldn't be thrown in a plugin. It is used internally in checks.py when an invalid metric name is passed in.                                              |

# impydance - Impedance measurements using BK894

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This module provides basic functionality to interact with the BK
Precision
[BK894](https://www.bkprecision.com/products/component-testers/894-500khz-lcr-meter.html)
Bench LCR meter.

## Installation and usage

The module requires the following:
* Python 3 (tested with Python 3.9)
* [NI-visa](https://www.ni.com/nl-nl/support/downloads/drivers/download.ni-visa.html)
* The [pyvisa](https://pyvisa.readthedocs.io/en/latest/) package
* Configure the interface as `USBTMC` in the settings menu of the instrument

You can simply clone the repository to your folder of choice using
[git](https://git-scm.com/downloads):

```
git clone https://github.com/wjbg/impydance.git
```

The module can be run from the command prompt and features a decent
help description.

```
python impydance --help
```

As a first step, you need to generate a configuration file:

```
python impydance cfg
```

This will create a file `impydance.cfg` with a device ID, a frequency
range for measurement, an AC voltage, and a measurement function. The
file can be edited to your liking. Next, you can perform a frequency
or amplitude sweep. By default, `impydance` will use the generated
configuration file.

```
python impedance fsweep

python impedance asweep
```

The data is stored in case a file name is provided:

```
python impedance fsweep data.txt
```

In addition, the `--batch` can be used to perform five consecutive
sweeps:

```
python impedance fsweep --batch data.txt
```

Additional information for the `asweep` and `fsweep` is available via
the `--help` flag:

```
python impedance fsweep --help
```

Of course the module can also be used in an interactive computing
environment (e.g. Jupyter). The functions are documented and usage
should be fairly straightforward.

## License

Free as defined in the [MIT](https://choosealicense.com/licenses/mit/)
license.

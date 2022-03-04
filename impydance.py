"""Python module to perform frequency and amplitude sweeps on the
BK894 LCR bench meter, using NI-VISA and the pyvisa package."""
import argparse
from argparse import RawTextHelpFormatter
from datetime import datetime

try:
    import pyvisa
except ImportError as e:
    print("Could not import pyvisa. Make sure to install NI-visa from:\n\n")
    print("  https://www.ni.com/nl-nl/support/downloads/drivers/download.ni-visa.html\n\n")
    print("and then install pyvisa using your package manager.")


FREQ_QLOG_RANGE = [100, 200, 500,
                   1000, 2000, 5000,
                   10000, 20000, 50000,
                   100000, 200000, 500000]
V_LIN_RANGE = [0.2, 0.4, 0.6, 0.8, 1.0,
               1.2, 1.4, 1.6, 1.8, 2.0]
DEFAULT_FREQUENCY = 1000
DEFAULT_VOLTAGE = 0.5
DEFAULT_KEY = "ZTD"

def find_device():
    """Scans for devices and prompts user to select one and returns its name.

    Returns
    -------
    device : string
             Name of the device.

    """
    rm = pyvisa.ResourceManager()
    devices = rm.list_resources()
    print("\nConnected devices")
    print("----------------------------------------------------")
    for i, device in enumerate(devices):
        print(str(i) + ": " + device)
    print("q: Quit")
    choice = input("\nSelect device by number: ")
    return None if choice == "q" else devices[int(choice)]

def connect_device(device):
    """Connect to device and returns resource object.

    Parameters
    ----------
    device : string
             Name of the device.

    Returns
    -------
    vi     : pyvisa resource object

    """
    rm = pyvisa.ResourceManager()
    try:
        vi = rm.open_resource(device)
        vi.timeout = 5000
        query_device(vi)
    except:
        vi = 0
        print("Could not connect to device...\n")
        print("You can try the following:\n")
        print("- Make sure to set remote control to USBTCM\n")
        print("- Reconnect the USB cable to your pc.\n")
        print("- Generate a new configuration file.")
    return vi

def query_device(vi):
    """Prints device information for provided resource object.

    Parameters
    ----------
    vi     : pyvisa resource object

    """
    info = vi.query("*idn?").split(',')
    print('\nDevice information')
    print('------------------------------------------')
    print('Manufacturer : ' + info[0].strip())
    print('Model        : ' + info[1].strip())
    print('Series       : ' + info[2].strip())
    print('Firmware     : ' + info[3].strip())
    print('Hardware     : ' + info[4].strip())
    print('------------------------------------------')

def frequency_sweep(vi, freqs=FREQ_QLOG_RANGE, V=DEFAULT_VOLTAGE,
                    key=DEFAULT_KEY):
    """Performs a frequency sweep and returns data.

    Parameters
    ----------
    vi    : pyvisa resource object
    freqs : list(dim=1, type=int)
            List with frequencies in Hz (defaults to FREQ_QLOG_RANGE).
    V     : float
            AC voltage level in V (defaults to DEFAULT_VOLTAGE).
    key   : string
            Type of measurement to perform. Check manual
            for available options (defaults to DEFAULT_KEY).

    Returns
    -------
    data  : list(dim=2)
            List with with frequencies and measured results.

    """
    if not frequencies_available(freqs):
        raise Exception("Requested frequencies may be out of range.")
    if measurements_available(key):
        vi.write("FUNC:IMP " + key)
    else:
        raise Exception("Requested measurement is not available.")
    if 0.0 < V <= 2.0:
        vi.write("VOLT " + str(V) + " V")
    else:
        raise Exception("Requested voltage out of range.")

    data = [[]*3]*len(freqs)
    print("\nFrequency sweep")
    print("AC voltage: {:.3f} V\n".format(V))
    print("Frequency [Hz]    {:12s}{:12s}".format(*result_header(key)))
    print("-----------------------------------------")
    for i, freq in enumerate(freqs):
        vi.write("FREQ " + str(freq) + "Hz")
        result = vi.query("fetch?").split(",")[:2]
        data[i] = [freq, float(result[0]), float(result[1])]
        print("{:<18.0f}{:<12.3e}{:<12.3e}".format(data[i][0],
                                                   data[i][1],
                                                   data[i][2]))
    print("------------------------------------------\n")
    return data

def amplitude_sweep(vi, V=V_LIN_RANGE, freq=DEFAULT_FREQUENCY,
                    key=DEFAULT_KEY):
    """Performs an amplitude sweep and returns data.

    Parameters
    ----------
    vi    : pyvisa resource object
    V     : list(dim=1, type=float)
            List with voltages in V (defaults to V_LIN_RANGE).
    freq  : int
            frequency in Hz (defaults to DEFAULT_FREQUENCY).
    key   : string
            Type of measurement to perform. Check manual
            for available options (defaults to DEFAULT_KEY).

    Returns
    -------
    data  : list(dim=2)
            List with with amplitudes and measured results.

    """
    if frequencies_available([freq]):
        vi.write("FREQ " + str(freq) + "Hz")
    else:
        raise Exception("Requested frequency may be out of range.")
    if measurements_available(key):
        vi.write("FUNC:IMP " + key)
    else:
        raise Exception("Requested measurement is not available.")
    if not all([0.0 < v <= 2.0 for v in V]):
        raise Exception("Requested voltages out of range.")

    data = [[]*3]*len(V)
    print("\nAmplitude sweep")
    print("Frequency: {:<8.0f} Hz\n".format(freq))
    print("Amplitude [V]    {:12s}{:12s}".format(*result_header(key)))
    print("-----------------------------------------")
    for i, v in enumerate(V):
        vi.write("VOLT " + str(v) + " V")
        result = vi.query("fetch?").split(",")[:2]
        data[i] = [v, float(result[0]), float(result[1])]
        print("{:<15.3f}{:<12.3e}{:<12.3e}".format(data[i][0],
                                                   data[i][1],
                                                   data[i][2]))
    print("------------------------------------------\n")
    return data

def frequencies_available(freqs, limits=[1, 5E5]):
    "True if provided frequencies are permitted."
    return (all([freq >= limits[0] for freq in freqs]) and
            all([freq <= limits[1] for freq in freqs]))

def measurements_available(key):
    """True if provided measurement key is valid.

    Parameters
    ----------
    key : string
          Key to identify measurement type. Check BK984 manual for
          valid options.

    """
    functions = ["CPD", "CPQ", "CPG", "CPRP", "CSD", "CSQ", "CSRS",
                 "LPQ", "LPD", "LPG", "LPRP", "LSD", "LSQ", "LSRS",
                 "RX", "ZTD", "ZTR", "GB", "YTD", "YTR"]
    return (key.upper() in functions)

def result_header(key):
    "Returns table header entries for selected measurement key."
    headers = {"CPD": ["Cp [F]", "Dissip. [-]"],
               "CPQ": ["Cp [F]", "Quality [-]"],
               "CPG": ["Cp [F]", "Cond. [S]"],
               "CPRP": ["Cp [F]", "Resis. [Ohm]"],
               "CSD": ["Cp [F]", "Dissip. [-]"],
               "CSQ": ["Cp [F]", "Quality [-]"],
               "CSRS": ["Cp [F]", "Resis. [Ohm]"],
               "LPD": ["Lp [H]", "Dissip. [-]"],
               "LPQ": ["Lp [H]", "Quality [-]"],
               "LPG": ["Lp [H]", "Cond. [S]"],
               "LPRP": ["Lp [H]", "Resis. [Ohm]"],
               "LSD": ["Lp [H]", "Dissip. [-]"],
               "LSQ": ["Lp [H]", "Quality [-]"],
               "LSRS": ["Lp [H]", "Resis. [Ohm]"],
               "ZTD": ["Z [Ohm]", "Theta [Deg]"],
               "ZTR": ["Z [Ohm]", "Theta [Rad]"],
               "GB": ["Z [Ohm]", "Theta [Deg]"],
               "YTD": ["Z [Ohm]", "Theta [Deg]"],
               "YTR": ["Z [Ohm]", "Theta [Deg]"]}
    return headers[key.upper()]

def save_data(data, fn, f_or_a, key):
    """Saves measurement data in tab-delimited text file.

    Parameters
    ----------
    data   : list (dim=2)
             Data to store.
    fn     : string
             Filename.
    f_or_a : string
             Sweep type: either "freq" or "amplitude"
    key    : string
             Measurement key for use in file header.

    """
    with open(fn, 'a') as f:
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        f.write("# Timestamp: " + timestamp + "\n")
        if f_or_a == "freq":
            f.write("# {:6s}\t{:8s}\t{:8s}\n".format("Freq [Hz]",
                                                     *result_header(key)))
        elif f_or_a == "amplitude":
            f.write("# {:6s}\t{:8s}\t{:8s}\n".format("Ampl. [V]",
                                                     *result_header(key)))
        for d in data:
            f.write("{:<8}\t{:1.8e}\t{:1.8e}\n".format(*d))
        f.write("\n")

def write_config(fn):
    """Writes a basic configuration file.

    File contains the device name, which is the user can select from a list,
    a list of frequencies, and the AC voltage. File can be edited by the user.

    Parameters
    ----------
    fn : string
         Filename

    """
    device = find_device()
    if device:
        with open(fn, 'w') as f:
            f.write("# Auto-generated configuration file for a frequency sweep.\n")
            f.write("# Frequencies are provided in Hz. Feel free to change, but\n")
            f.write("# respect the range (1 Hz - 500 kHz) of the equipment. AC\n")
            f.write("# voltage can be varied between 50 mV and 2 V. Do not change\n")
            f.write("# the device name or the keywords.\n")
            f.write("device = " + device + "\n")
            f.write("freq = " +
                    ", ".join([str(freq) for freq in FREQ_QLOG_RANGE]) +
                    "\n")
            f.write("voltage = " + str(DEFAULT_VOLTAGE) + "\n")
            f.write("measurement = " + DEFAULT_KEY + "\n")
            print("\nConfiguration file saved as: "+ fn)

def read_config(fn):
    """Read configuration file.

    Parameters
    ----------
    fn : string
         File to read.

    Returns
    -------
    device : string
             Device name.
    freqs  : list(dim=1, type=int)
             List with frequencies
    V      : list(dim=1, type=float)
             List with AC voltage
    key    : string
             Measurement key (defaults to "ZTD")

    """
    device, freqs, V, key = "", [], [], ""
    with open(fn, 'r') as f:
        for line in f.readlines():
            if line.split("=")[0].strip() == "device":
                device = line.split("=")[1].strip()
            elif line.split("=")[0].strip() == "freq":
                freqs = [int(freq) for freq in
                         line.split("=")[1].split(",")]
            elif line.split("=")[0].strip() == "voltage":
                V = [float(V) for V in
                         line.split("=")[1].split(",")]
            elif line.split("=")[0].strip() == "measurement":
                key = line.split("=")[1].strip()
    if not all([device, freqs, V, key]):
        print("Could not parse config file. Make sure to define:\n")
        print("- device\n")
        print("- freqs\n")
        print("- V\n\n")
        print("You also can generate a new config file:\n\n")
        print("   python <NAME> --new-config\n")
    return device, freqs, V, key

def parse_args():
    "Argparser function for command line usage."
    parser = argparse.ArgumentParser(prog="impydance",
               formatter_class=RawTextHelpFormatter,
               description="Python script to read data from a BK894 LCR meter.")
    subparsers = parser.add_subparsers(help="command", dest="command")
    subparsers.required = True

    parser_fsweep = subparsers.add_parser("fsweep",
                        formatter_class=RawTextHelpFormatter,
                        description="Perform frequency sweep.")
    parser_fsweep.add_argument("-b", "--batch", action="store_true",
                        help="perform batch run of 5 sweeps and save to file")
    parser_fsweep.add_argument("--config", required=False,
                        default="impydance.cfg",
                        help="use provided configuration file\n"
                               "will use impydance.cfg if not provided")
    parser_fsweep.add_argument("filename", nargs="?",
                        help="filename to save (append) measured data\n"
                             "data will not be saved in no filename is provided")

    parser_asweep = subparsers.add_parser("asweep",
                        formatter_class=RawTextHelpFormatter,
                        description="Perform amplitude sweep.")
    parser_asweep.add_argument("-b", "--batch", action="store_true",
                        help="perform batch run of 5 sweeps and save to file")
    parser_asweep.add_argument("--config", required=False,
                        default="impydance.cfg",
                        help="use provided configuration file\n"
                               "will use impydance.cfg if not provided")
    parser_asweep.add_argument("filename", nargs="?",
                        help="filename to save (append) measured data\n"
                             "data will not be saved in no filename is provided")

    parser_config = subparsers.add_parser("cfg",
                        formatter_class=RawTextHelpFormatter,
                        description="Generate new config file.")
    parser_config.add_argument("filename", nargs="?",
                        default="impydance.cfg",
                        help="filename to store configuration\n"
                               "defaults to impydance.cfg if not provided")
    args = parser.parse_args()
    return args

def main():
    "Code for command line usage."
    inputs = parse_args()
    if inputs.command == "cfg":
        write_config(inputs.filename)
    elif inputs.command == "fsweep":
        device, freqs, V, key = read_config(inputs.config)
        vi = connect_device(device)
        if len(V) > 1:
            print("\nList of voltages supplied, will use first in list.")
        if inputs.filename:
            print("\nCreating or appending to {:s}".format(inputs.filename))
            for _ in range(5 if inputs.batch else 1):
                data = frequency_sweep(vi, freqs, V[0], key)
                save_data(data, inputs.filename, "freq", key)
        else:
            _ = frequency_sweep(vi, freqs, V[0], key)
    elif inputs.command == "asweep":
        device, freqs, V, key = read_config(inputs.config)
        vi = connect_device(device)
        if len(freqs) > 1:
            print("\nList of frequencies supplied, will use first in list.")
        if inputs.filename:
            print("\nCreating or appending to {:s}".format(inputs.filename))
            for _ in range(5 if inputs.batch else 1):
                data = amplitude_sweep(vi, V, freqs[0], key)
                save_data(data, inputs.filename, "amplitude", key)
        else:
            _ = amplitude_sweep(vi, V, freqs[0], key)

if __name__ == "__main__":
    main()

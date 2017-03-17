# Configuration
This document explains the configuration notes for customizing the pharos remote printing package. You can customize the EULA and print queue configuration using the EULA and printers.conf files respectively.

## EULA
An end user license agreement can be defined in a EULA file. This file should be named "EULA" and kept in the same directory as the setup.py file.
This EULA will be presented to the user when the setup.py program is ran and the user will be prompted for accepting the EULA. If the user accepts the EULA then the setup will continue else it will terminate

## PRINTERS CONFIGURATION
The printers can be defined using the printers.conf file in the same location as the setup.py file. The printer configuration file is defined as below:

### Sample configuration file begin
```
[Printers]
printers=Linux_Laser, Linux_Color

[Linux_Laser]
Make=HP
Model=HP LaserJet 9040
Driver=HP LaserJet 9040 pcl3, hpcups
DuplexerInstalled=Yes
DefaultDuplex=No
LPDServer=printserver.university.edu
LPDQueue=Linux_Laser_Printer
Location=University Campus at City Name
Description=University Any Building Black and White Printer

[Linux_Color]
Make=HP
Model=HP Color LaserJet 5550
Driver=HP Color LaserJet 5550 pcl3, hpcups
DuplexerInstalled=Yes
DefaultDuplex=Yes
LPDServer=printserver.university.edu
LPDQueue=Linux_Color_Printer
Location=University Campus at City Name
Description=University Any Building Color Printer
```

The above configuration file is divided into two parts. The first part is [Printers] which defines which printers need to be installed as part of the setup process. Each printer is then defined within its own section in the configuration file.
The printer configuration consists of the following parts:
- Make: This is the manufacturer of the printer.
- Model: This is the exact model of the printer. This is information used to search for available drivers on the system during the installation process.
- Driver: This is the exact driver of the printer. If driver version is not specified then the closest available driver will be used. This is information used to search for available drivers on the system during the installation process. If the driver is not available on the system the printer will not be installed.
- DuplexerInstalled: This option is currently designed to work with HP drivers. It enables the duplexing unit for the print queue.
- DefaultDuplex: This will enable all jobs to print as duplex. Please make sure to check the charging for simplex jobs as this option tends to cause the page counter to miscount single page jobs as two sheets.
- LPDServer: This is the pharos print server address (DNS hostname or IP Address)
- LPDQueue: This is the pharos print server queue name that the job will be printed to. Make sure that it does not include any spaces. Also this queue should be setup as a "Held" queue within pharos and "Must use popups" property should be set to "No"
- Location: This is a string describing the location of the printer
- Description: This is a string describing the printer.

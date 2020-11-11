```
                    __   _ __      _______ _________      ___        _
                   / /  (_) /____ / __/ _ /_  __/ _ |____/ _ |__ __ (_)__  __ _
                  / /__/ / __/ -_)\ \/ __ |/ / / __ /___/ __ |\ \ // / _ \/  ' \
                 /____/_/\__/\__/___/_/ |_/_/ /_/ |_|  /_/ |_/_\_\/_/\___/_/_/_/
           Test/integration of LiteSATA core on the Axiom Beta Dual SATA Plugin Module.
                                 Copyright (c) 2020, EnjoyDigital
                                     Powered by Migen & LiteX
```
![License](https://img.shields.io/badge/License-BSD%202--Clause-orange.svg)

<p align="center"><img src="https://github.com/enjoy-digital/litesata_axiom/raw/master/doc/board.jpg"></p>

[> Intro
--------
This small project is an attempt to test and integrate [LiteSATA](https://github.com/enjoy-digital/litesata) core on the [Axiom Beta Dual SATA Plugin Module](https://wiki.apertus.org/index.php/Dual_SATA_Plugin_Module).

The Axiom Beta Dual SATA plugin Module has been developed by Apertus to connects the Axiom Beta camera to hard disk drives and solid-state drives:

![enter image description here](https://wiki.apertus.org/images/0/09/00-DSAT-001-_AXIOM_Beta_Dual_SATA_Plugin_Module_V0.6_R1.0_Top_Populated_Show_sm.jpg)
The module is connected to the Axiom Beta through the two plugin connectors (repurposed PCIe connectors that are used by all Axiom Beta plugins), provides 4 SATA connectors, a 150MHz SATA reference clock and is equipped with a  [TE0714 FPGA Module](https://shop.trenz-electronic.de/en/TE0714-03-50-2I-FPGA-Module-with-Xilinx-Artix-7-XC7A50T-2CSG325I-3-3V-Configuration-4-x-3-cm) from Trenz that will be running the LiteSATA core and test design.

<p align="center"><img src="https://shop.trenz-electronic.de/media/image/b8/2d/ae/TE0714-03-50-2I_0_600x600.jpg" width="400"></p>

[> Prerequisites
----------------
- Python3, Vivado WebPACK and OpenOCD.
- An OpenOCD compatible JTAG cable.
- A USB/UART cable.

[> Installing LiteX
-------------------
```sh
$ wget https://raw.githubusercontent.com/enjoy-digital/litex/master/litex_setup.py
$ chmod +x litex_setup.py
$ sudo ./litex_setup.py init install
```

[> Build and Load the bitstream
--------------------------------
```sh
$ ./litesata_axiom.py --port=0 --gen=2 --build --load
```

[> Open LiteX server
--------------------
```sh
$ lxserver --uart --uart-port=/dev/ttyUSBX
```

[> Enjoy :)
-----------
```sh
$ ./test_bist.py
```

<p align="center"><img src="https://github.com/enjoy-digital/litesata_axiom/raw/master/doc/bist.png"></p>

> **Note**: Since the BIST test will **both read and write to the SATA HDD/SSD**, please make sure **you don't have useful contents on it** before running the test...

For more examples of LiteSATA integration, you can have a look at [LiteSATA benches](https://github.com/enjoy-digital/litesata/tree/master/bench) or [LiteX-Boards targets](https://github.com/litex-hub/litex-boards/tree/master/litex_boards/targets).
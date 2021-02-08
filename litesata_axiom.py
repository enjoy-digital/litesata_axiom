#!/usr/bin/env python3

# Copyright (c) 2020 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import sys
import argparse

from migen import *

from litex.build.openocd import OpenOCD
from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform

from litex.soc.cores.clock import S7PLL
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from litesata.common import *
from litesata.phy import LiteSATAPHY
from litesata.core import LiteSATACore
from litesata.frontend.arbitration import LiteSATACrossbar
from litesata.frontend.bist import LiteSATABIST

from litescope import LiteScopeAnalyzer

# IOs ----------------------------------------------------------------------------------------------

_io = [
    # Clk / Rst
    ("clk25", 0, Pins("T14"), IOStandard("LVCMOS33")),

    # Serial
    ("serial", 0,
        Subsignal("tx", Pins("U12")), # TP7
        Subsignal("rx", Pins("T12")), # TP8
        IOStandard("LVCMOS33")
    ),

    # Leds
    ("module_led", 0, Pins("K18"), IOStandard("LVCMOS33")),
    ("user_led_n", 0, Pins("V12"), IOStandard("LVCMOS33")),
    ("user_led_n", 1, Pins("U11"), IOStandard("LVCMOS33")),
    ("user_led_n", 2, Pins("U9"),  IOStandard("LVCMOS33")),
    ("user_led_n", 3, Pins("V11"), IOStandard("LVCMOS33")),

    # SATA
    ("sata", 0,
        Subsignal("clk_p", Pins("D6")),
        Subsignal("clk_n", Pins("D5")),
        Subsignal("tx_p",  Pins("B2")),
        Subsignal("tx_n",  Pins("B1")),
        Subsignal("rx_p",  Pins("G4")),
        Subsignal("rx_n",  Pins("G3")),
    ),
    ("sata", 1,
        Subsignal("clk_p", Pins("D6")),
        Subsignal("clk_n", Pins("D5")),
        Subsignal("tx_p",  Pins("D2")),
        Subsignal("tx_n",  Pins("D1")),
        Subsignal("rx_p",  Pins("C4")),
        Subsignal("rx_n",  Pins("C3")),
    ),
    ("sata", 2,
        Subsignal("clk_p", Pins("D6")),
        Subsignal("clk_n", Pins("D5")),
        Subsignal("tx_p",  Pins("F2")),
        Subsignal("tx_n",  Pins("F1")),
        Subsignal("rx_p",  Pins("A4")),
        Subsignal("rx_n",  Pins("A3")),
    ),
    ("sata", 3,
        Subsignal("clk_p", Pins("D6")),
        Subsignal("clk_n", Pins("D5")),
        Subsignal("tx_p",  Pins("H2")),
        Subsignal("tx_n",  Pins("H1")),
        Subsignal("rx_p",  Pins("E4")),
        Subsignal("rx_n",  Pins("E3")),
    ),
]

# Platform -----------------------------------------------------------------------------------------

class Platform(XilinxPlatform):
    default_clk_name   = "clk25"
    default_clk_period = 1e9/25e6

    def __init__(self):
        XilinxPlatform.__init__(self, "xc7a50t-csg325-2", _io, toolchain="vivado")

    def create_programmer(self):
        return OpenOCD("openocd_xc7_ft232.cfg", "bscan_spi_xc7a200t.bit")

    def do_finalize(self, fragment):
        XilinxPlatform.do_finalize(self, fragment)
        self.add_period_constraint(self.lookup_request("clk25", loose=True), 1e9/25e6)

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys       = ClockDomain()

        # # #

        self.submodules.pll = pll = S7PLL(speedgrade=-1)
        pll.register_clkin(platform.request("clk25"), 25e6)
        pll.create_clkout(self.cd_sys, sys_clk_freq)

# SATATestSoC --------------------------------------------------------------------------------------

class SATATestSoC(SoCMini):
    def __init__(self, platform, port=0, gen="gen2", with_analyzer=False):
        assert gen in ["gen1", "gen2"]
        sys_clk_freq  = int(100e6)
        sata_clk_freq = {"gen1": 75e6, "gen2": 150e6}[gen]

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq)

        # SoCMini ----------------------------------------------------------------------------------
        SoCMini.__init__(self, platform, sys_clk_freq,
            ident         = "LiteSATA bench on Axiom Beta SATA",
            ident_version = True)

        # JTAGBone ---------------------------------------------------------------------------------
        self.add_jtagbone()

        # SATA -------------------------------------------------------------------------------------
        # PHY
        self.submodules.sata_phy = LiteSATAPHY(platform.device,
            pads       = platform.request("sata", port),
            gen        = gen,
            clk_freq   = sys_clk_freq,
            data_width = 16)
        self.add_csr("sata_phy")

        # Core
        self.submodules.sata_core = LiteSATACore(self.sata_phy)

        # Crossbar
        self.submodules.sata_crossbar = LiteSATACrossbar(self.sata_core)

        # BIST
        self.submodules.sata_bist = LiteSATABIST(self.sata_crossbar, with_csr=True)
        self.add_csr("sata_bist")

        # Timing constraints
        platform.add_period_constraint(self.sata_phy.crg.cd_sata_tx.clk, 1e9/sata_clk_freq)
        platform.add_period_constraint(self.sata_phy.crg.cd_sata_rx.clk, 1e9/sata_clk_freq)
        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.sata_phy.crg.cd_sata_tx.clk,
            self.sata_phy.crg.cd_sata_rx.clk)

        # Leds -------------------------------------------------------------------------------------
        # sys_clk
        sys_counter = Signal(32)
        self.sync.sys += sys_counter.eq(sys_counter + 1)
        self.comb += platform.request("user_led_n", 0).eq(~sys_counter[26])
        # tx_clk
        tx_counter = Signal(32)
        self.sync.sata_tx += tx_counter.eq(tx_counter + 1)
        self.comb += platform.request("user_led_n", 1).eq(~tx_counter[26])
        # rx_clk
        rx_counter = Signal(32)
        self.sync.sata_rx += rx_counter.eq(rx_counter + 1)
        self.comb += platform.request("user_led_n", 2).eq(~rx_counter[26])
        # ready
        self.comb += platform.request("module_led").eq(self.sata_phy.ctrl.ready)
        self.comb += platform.request("user_led_n", 3).eq(~self.sata_phy.ctrl.ready)

        # Analyzer ---------------------------------------------------------------------------------
        if with_analyzer:
            analyzer_signals = [
                self.sata_phy.phy.tx_init.fsm,
                self.sata_phy.phy.rx_init.fsm,
                self.sata_phy.ctrl.fsm,

                self.sata_phy.ctrl.ready,
                self.sata_phy.source,
                self.sata_phy.sink,

                self.sata_core.command.sink,
                self.sata_core.command.source,

                self.sata_core.link.rx.fsm,
                self.sata_core.link.tx.fsm,
                self.sata_core.transport.rx.fsm,
                self.sata_core.transport.tx.fsm,
                self.sata_core.command.rx.fsm,
                self.sata_core.command.tx.fsm,
            ]
            self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals, 512, csr_csv="analyzer.csv")
            self.add_csr("analyzer")

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteSATA bench on Axiom Beta SATA")
    parser.add_argument("--build",         action="store_true", help="Build bitstream")
    parser.add_argument("--load",          action="store_true", help="Load bitstream (to SRAM)")
    parser.add_argument("--port",          default="0",         help="SATA Port: 0 (default), 1, 2 or 3")
    parser.add_argument("--gen",           default="2",         help="SATA Gen: 1 or 2 (default)")
    parser.add_argument("--with-analyzer", action="store_true", help="Add LiteScope Analyzer")
    args = parser.parse_args()

    build_name = f"litesata_axiom_p{args.port}"

    platform = Platform()
    soc = SATATestSoC(platform, port=int(args.port, 0), gen="gen" + args.gen, with_analyzer=args.with_analyzer)
    builder = Builder(soc, csr_csv="csr.csv", output_dir=f"build/{build_name}")
    builder.build(build_name=build_name, run=args.build)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(os.path.join(builder.gateware_dir, soc.build_name + ".bit"))

if __name__ == "__main__":
    main()

import argparse
import os

import m5
from m5.objects import *
from m5.objects.BaseCPU import BaseCPU as BaseCPUClass

parser = argparse.ArgumentParser()

parser.add_argument("--binary", required=True)
parser.add_argument("--size", type=int, default=100000)
parser.add_argument("--threads", type=int, default=1)
parser.add_argument("--num-cpus", type=int, default=1)
parser.add_argument("--mem-size", default="512MB")

args = parser.parse_args()

binary = os.path.abspath(args.binary)

if not os.path.isfile(binary):
    m5.fatal("Executable not found: " + binary)

if args.threads < 1 or args.num_cpus < 1:
    m5.fatal("Thread and CPU counts must be positive.")

if args.threads > args.num_cpus:
    m5.fatal("CPU count must be at least the application thread count.")

# Create the system.
system = System()

system.clk_domain = SrcClockDomain(
    clock="1GHz",
    voltage_domain=VoltageDomain()
)

system.mem_mode = "timing"
system.mem_ranges = [AddrRange(args.mem_size)]

# Create the memory bus.
system.membus = SystemXBar()

system.system_port = system.membus.cpu_side_ports

# Simple memory model.
system.mem_ctrl = SimpleMemory(
    range=system.mem_ranges[0],
    latency="30ns"
)

system.mem_ctrl.port = system.membus.mem_side_ports

# Create the requested number of MinorCPU cores.
system.cpu = [
    BaseCPUClass(cpu_id=i)
    for i in range(args.num_cpus)
]

# Create the application process.
process = Process()

process.cmd = [
    binary,
    str(args.size),
    str(args.threads)
]

system.workload = SEWorkload.init_compatible(binary)

# Configure each CPU.
for cpu in system.cpu:

    cpu.clk_domain = system.clk_domain

    cpu.workload = process

    cpu.createThreads()

    cpu.createInterruptController()

    cpu.connectAllPorts(system.membus)

# Create the simulation root.
root = Root(
    full_system=False,
    system=system
)

m5.instantiate()

print("\n========================================")
print(" GEM5 MINORCPU DAXPY SIMULATION")
print("========================================")

print("Executable  :", binary)
print("Vector size :", args.size)
print("Threads     :", args.threads)
print("CPU cores   :", args.num_cpus)
print("Memory mode :", system.mem_mode)

print("========================================\n")

exit_event = m5.simulate()

print(
    "Exiting @ tick %i because %s"
    % (m5.curTick(), exit_event.getCause())
)

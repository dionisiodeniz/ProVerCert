The cfg_logger directory contains a module for PX4-Autopilot that has been tested for the commit:

commit 271d3f01a389bbf25386e94ed9142cebddeffa51 (HEAD -> main, origin/main, origin/HEAD)
Author: Hamish Willee <hamishwillee@gmail.com>
Date:   Fri Feb 6 06:17:44 2026 +1100

To add it to the PX-Autopilot it needs to be added to a new directory:

PX4-Autopilot/src/modules/cfg_logger

Then it needs to be configured by executing the following command from the PX4-Autopilot directory (to run with the simulator):

make px4_sitl_default boardconfig

The make sure that the cfg_logger module is "checked"

Then you can compile the simulation model and run as as you always do by running:

make px4_sitl gz_x500

This will first compile the new code and then run the simulator
#!/bin/bash
# ProVer-Cert Source Code
# Copyright 2026 Carnegie Mellon University.
# NO WARRANTY. THIS CARNEGIE MELLON UNIVERSITY AND SOFTWARE ENGINEERING INSTITUTE MATERIAL IS FURNISHED ON AN "AS-IS" BASIS. CARNEGIE MELLON UNIVERSITY MAKES NO WARRANTIES OF ANY KIND, EITHER EXPRESSED OR IMPLIED, AS TO ANY MATTER INCLUDING, BUT NOT LIMITED TO, WARRANTY OF FITNESS FOR PURPOSE OR MERCHANTABILITY, EXCLUSIVITY, OR RESULTS OBTAINED FROM USE OF THE MATERIAL. CARNEGIE MELLON UNIVERSITY DOES NOT MAKE ANY WARRANTY OF ANY KIND WITH RESPECT TO FREEDOM FROM PATENT, TRADEMARK, OR COPYRIGHT INFRINGEMENT.
# Licensed under a BSD (SEI)-style license, please see license.txt or contact permission@sei.cmu.edu for full terms.
# [DISTRIBUTION STATEMENT A] This material has been approved for public release and unlimited distribution.  Please see Copyright notice for non-US Government use and distribution.
# This Software includes and/or makes use of Third-Party Software each subject to its own license.
# DM26-0076


sudo cpupower frequency-set -g performance --min 2000MHz --max 2000MHz

SIMULATION_DIRECTORY=/home/dionisio/git/PX4/PX4-Autopilot
# We use taskset to set the affinity of the command and its children to only the fast CPUs.
#SIMULATION_EXECUTABLE="taskset -c 0,1,3,4,5,6,7,9,11 /home/dionisio/git/PX4/PX4-Autopilot/build/px4_sitl_default/bin/px4"
#SIMULATION_EXECUTABLE="/home/dionisio/git/PX4/PX4-Autopilot/build/px4_sitl_default/bin/px4"
SIMULATION_EXECUTABLE="make px4_sitl gz_x500"
MISSION_EXECUTABLE=/home/dionisio/git/PX4/MAVSDK/cpp/examples/fly_random_mission/build/fly_mission
ANALYZER_EXECUTABLE="/usr/bin/python /home/dionisio/git/ProVerCert/visual-pmc/clipmc.py"
BASE_TEMPLATE=obs-template.json

angles=5
rounds=1000
rlength=10

# To increase the gazebo transport thread pool use:
# export GZ_TRANSPORT_THREAD_POOL_SIZE=8


for ((angles=100 ; angles <= 100; angles += 5))
do
    echo "Running Experiment for angle=${angles} rounds=${rounds} roundlength=${rlength}"
    
	# start the simulator
	gnome-terminal -- /usr/bin/bash -c "cd ${SIMULATION_DIRECTORY} && GZ_SIM_SYSTEM_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/gz-sim-8/plugins PX4_GZ_WORLD=default PX4_SIM_LOCKSTEP=1 GZ_RENDERING_ENGINE=ogre QT_QPA_PLATFORM=offscreen PX4_SIM_SPEED_FACTOR=10 PX4_PARAM_SDLOG_PROFILE=3 HEADLESS=1 ${SIMULATION_EXECUTABLE}"
	sleep 15

	# execute the mission
	${MISSION_EXECUTABLE} udpin://0.0.0.0:14540 missionrounds=${rounds} roundlength=${rlength} maxturnshift=${angles} shutdown=true distance=5.0|| break

	sleep 10
	# kill any residual simulator
	kill -9 `pgrep gz`
	kill -9 `pgrep ruby`

	sleep 10
	
	# copy the basic template
	cp ${BASE_TEMPLATE} obs-${angles}-${rounds}.json

	# recover the samples
	${ANALYZER_EXECUTABLE} populate_template templatefile:=obs-${angles}-${rounds}.json logfile:=/home/dionisio/git/PX4/PX4-Autopilot/build/px4_sitl_default/rootfs/transitions.json

	echo "Experiment for angle=${angles} rounds=${rounds} roundlength=${rlength} DONE!"
	echo "============================================================================\n"
done

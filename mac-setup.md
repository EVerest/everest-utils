# How To: Develop on a Mac

## Preparation

1. Clone the repository `git clone git@github.com:EVerest/everest-utils.git`
1. From inside VSCode, type `Cmd+Shift+P`
1. Select the directory `everest-utils/docker/everest-playground` to start a 
DevContainer - all the following commands must be executed in VSCode terminals
 inside the DevContainer.
1. Run `. init.sh` to initialize the dependencies.
1. Compile and install 

```bash
cmake .. -DBUILD_SHARED_LIBS=on && make install
```

## MQTT
Open a terminal tab to start the MQTT server

```bash
cd /workspace/docker ; ./mqtt-devcontainer.sh
```

## Nodered / Simulator UI
Open a terminal tab to start the Nodered server

```bash
cd /workspace/everest-cpp/everest-core/build ; ./run-scripts/nodered-sil.sh
```

## Software-in-the-loop Simulator
Open a terminal tab to start the simulation

```bash
export LD_LIBRARY_PATH=$(find / -name "*.so*" 2>/dev/null | 
  xargs -I {} dirname {} | sort -u | tr '\n' ':' | sed 's/:$//')

cd /workspace/everest-cpp/everest-core/build ; ./run-scripts/run-sil.sh
```

Open http://localhost:1880/ui and test the Charging Station and EV simulators.

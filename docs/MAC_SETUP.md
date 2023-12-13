# Mac Development Setup

## Application Installs

* Install [Homebrew](https://brew.sh/) this will prompt for a bunch of passwords entries. It is working just get to the end!
* Install [Docker Desktop](https://docs.docker.com/desktop/install/mac-install/)
* Install [VSCode](https://formulae.brew.sh/cask/visual-studio-code)
    * Install [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension

## GitHub Setup

Create an ssh keypair:

```
ssh-keygen -t rsa -a 100 -Z aes128-gcm@openssh.com
```

Create a file `config` in the ~/.ssh folder:

```
touch ~/.ssh/config
```

Add the following to the file:

```
Host github.com
    AddKeysToAgent yes
    User git
    PubkeyAcceptedAlgorithms +ssh-rsa
```

## Standup Dev Playground

### TL;DR

This repo includes a script that does the setup steps below checking that your environment is setup correctly 
and if so running the commands to stand up the Docker network and dev playground.

```shell
$> bin/devup
```

### Create docker network

```
docker network create --driver bridge --ipv6  --subnet fd00::/80 infranet_network --attachable
```

### Start up the docker EVerest Playground

docker compose -f ./everest-utils/docker/docker-compose.yml" up -d mqtt-server 
docker compose -f ./everest-utils/docker/docker-compose.yml" up -d nodered

## Start VSCode Docker Dev Environment

In VSCode:

* Press `CMD + Shift + P`
* type `Dev Containers: Open Folder in Container...`
* Navigate and open the docker/everest-playground folder. 

This will open the EVerest Playground as a VSCode dev container. You should now be ready to go.

## Initialize 

Now we run commands inside the Playground based on the instructions from the [`everest-cpp`](/everest-cpp/README.md)
subdirectory.

Initialize the EVerest workspace sourcing the *[init.sh](./init.sh)* file:

```bash
. init.sh
```

The working directory will be changed to *everest-core/build*. Here you can use cmake and make to build the project:

```bash
cmake .. && make install
```

You can also use [make's -j flag](https://www.gnu.org/software/make/manual/html_node/Parallel.html) to speed up
the build:

```bash
cmake .. && make install -j12
```

### Starting the NodeRed Environment

```bash
./dist/bin/manager --config ../config/config-sil-dc.yaml
```

This will prompt you to open a browser at `http://localhost:8849/`.

## Stopping things

Code > File > Close Remost Connection

## Resources

* [Node-RED](https://nodered.org/)

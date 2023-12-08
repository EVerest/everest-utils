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

## Create docker network

```
docker network create --driver bridge --ipv6  --subnet fd00::/80 infranet_network --attachable
```




## Resources

* [Node-RED](https://nodered.org/)

./dist/bin/manager --config ../config/config-sil-ocpp201.yaml
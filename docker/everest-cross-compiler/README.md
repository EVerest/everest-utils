# EVerest cross compilation

You can use this dev container to generate a sysroot and cross compile everest

## Dependencies
The following tools have to be installed on the host to be able to run this docker image as a dev container
```bash
sudo apt-get install qemu-user-static qemu-system qemu-utils qemu-system-misc binfmt-support
```

At least on OpenSUSE Tumbleweed some of these packages are not available, here you can use:
```bash
docker run --privileged --rm tonistiigi/binfmt --install arm
```

For 64 bit support:
```bash
docker run --privileged --rm tonistiigi/binfmt --install arm64
```

You can either use this dev container or use the docker container directly with the provided run.sh:
```bash
./run.sh
```

This directory contains useful scripts for working with meta-everest

_parsebb.py_ parses .bb files and returns a json object containing the repository link, branch, revision and direct link to a file relative to the repo link

_cargolock2bb_ converts a Cargo.lock file, that can also be loaded via an URL, into a .bb file

_snapshot2bb_ parses a snapshot.yaml file and modifies the corresponding recipe .bb files

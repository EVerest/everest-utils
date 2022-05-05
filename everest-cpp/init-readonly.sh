#!/bin/bash
##
## SPDX-License-Identifier: Apache-2.0
## Copyright 2020 - 2022 Pionix GmbH and Contributors to EVerest
##
echo "Installing required tools, initializing workspace, changing into everest-core/build"
if [ -d "everest-dev-environment" ] ; then
    echo "Directory 'everest-dev-environment' already exists, trying to update its contents..."
    (cd everest-dev-environment && git pull)
else
    git clone https://github.com/EVerest/everest-dev-environment.git || { echo "Could not clone everest-dev-environment."; return; }
fi
(cd everest-dev-environment/dependency_manager && python3 -m pip install .)
edm --register-cmake-module
edm --config everest-dev-environment/everest-complete-readonly.yaml --workspace .
edm --update
(cd everest-utils/ev-dev-tools && python3 -m pip install .)
mkdir -p everest-core/build
cd everest-core/build
echo ""
echo "You can now build everest-core with the following commands:"
echo ""
echo "cmake .. && make install -j$(nproc)"

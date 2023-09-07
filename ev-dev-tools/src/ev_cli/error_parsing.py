# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0
# Copyright 2020 - 2022 Pionix GmbH and Contributors to EVerest
#
"""
Provide error parsing functionality.
author: andreas.heinrich@pionix.de
"""

from . import helpers

from pathlib import Path
from typing import Dict, List

import yaml, jsonschema, jsonref

class ErrorParser:
    """Error parser class."""
    validators: Dict = {}
    generated_template_data: Dict = {}

    @classmethod
    def extract_namespace(cls, ref: str) -> str:
        namespace = None
        if '#/' in ref:
            namespace = ref.split('#/')[0]
        namespace = namespace.split('/')[-1]
        namespace = namespace.split('.')[0]
        return namespace

    @classmethod
    def generate_template_data(cls, data: Dict, namespace: str) -> Dict:
        """Generate template data for the provided error declaration."""
        return {
            'namespace': namespace,
            'name': data['name'],
            'description': data['description']
        }

    @classmethod
    def generate_template_data_list(cls, data: List[Dict], base_uri) -> List[Dict]:
        """Generate template data list for the provided data."""
        result = []
        for entry in data:
            if not entry['$ref']:
                raise helpers.EVerestParsingException(f'Error list: { entry } needs to include "$ref" as a key.')
            namespace = cls.extract_namespace(entry['$ref'])
            entry_data = jsonref.replace_refs(entry, base_uri=base_uri, loader=helpers.yaml_ref_loader, proxies=False)
            if isinstance(entry_data, list):
                for error_declaration in entry_data:
                    print(yaml.dump(error_declaration))
                    result.append(cls.generate_template_data(error_declaration, namespace))
            else:
                result.append(cls.generate_template_data(entry_data, namespace))
        return result

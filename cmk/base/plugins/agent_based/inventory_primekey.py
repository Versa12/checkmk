#!/usr/bin/env python3
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from typing import NamedTuple

from .agent_based_api.v1 import Attributes, register, SNMPTree
from .agent_based_api.v1.type_defs import InventoryResult, StringTable
from .utils.primekey import DETECT_PRIMEKEY


class _Section(NamedTuple):
    pki_appl_version: str
    local_node_id: int


def parse(string_table: StringTable) -> _Section | None:
    """
    >>> parse([['PrimeKeyAppliance.3.9.2', '1']])
    _Section(pki_appl_version='PrimeKeyAppliance.3.9.2', local_node_id=1)
    """
    if not string_table:
        return None

    return _Section(pki_appl_version=string_table[0][0], local_node_id=int(string_table[0][1]))


register.snmp_section(
    name="primekey",
    parse_function=parse,
    detect=DETECT_PRIMEKEY,
    fetch=SNMPTree(
        ".1.3.6.1.4.1.22408.1.1.2.1",
        [
            "7.118.101.114.115.105.111.110.1",  # PKI appliance version
            "8.99.108.117.115.116.101.114.49.1",  # local node id
        ],
    ),
)


def inventory_primekey(section: _Section) -> InventoryResult:
    """
    >>> list(inventory_primekey(_Section(pki_appl_version='PrimeKeyAppliance.3.9.2', local_node_id=1)))
    [Attributes(path=['hardware', 'system'], inventory_attributes={'pki_appliance_version': 'PrimeKeyAppliance.3.9.2', 'node_name': 1}, status_attributes={})]
    """

    yield Attributes(
        path=["hardware", "system"],
        inventory_attributes={
            "pki_appliance_version": section.pki_appl_version,
            "node_name": section.local_node_id,
        },
    )


register.inventory_plugin(
    name="primekey",
    inventory_function=inventory_primekey,
)

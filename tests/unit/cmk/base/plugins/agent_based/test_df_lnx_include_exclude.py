#!/usr/bin/env python3
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from collections.abc import Mapping

from cmk.base.plugins.agent_based.df import discover_df
from cmk.base.plugins.agent_based.df_section import parse_df

STRING_TABLE = [
    ["tmpfs", "tmpfs", "1620324", "2320", "1618004", "1%", "/run"],
    ["/dev/mapper/ubuntu--vg-root", "ext4", "242791844", "59957024", "170431928", "27%", "/"],
    ["tmpfs", "tmpfs", "8101604", "226244", "7875360", "3%", "/dev/shm"],
    ["tmpfs", "tmpfs", "5120", "4", "5116", "1%", "/run/lock"],
    ["tmpfs", "tmpfs", "8101604", "0", "8101604", "0%", "/sys/fs/cgroup"],
    ["/dev/nvme0n1p2", "ext4", "721392", "294244", "374684", "44%", "/boot"],
    ["/dev/nvme0n1p1", "vfat", "523248", "31468", "491780", "7%", "/boot/efi"],
    ["tmpfs", "tmpfs", "1620320", "68", "1620252", "1%", "/run/user/1000"],
    ["tmpfs", "tmpfs", "8101604", "8612", "8092992", "1%", "/opt/omd/sites/netapp/tmp"],
    ["tmpfs", "tmpfs", "8101604", "6360", "8095244", "1%", "/opt/omd/sites/heute/tmp"],
    ["tmpfs", "tmpfs", "8101604", "6460", "8095144", "1%", "/opt/omd/sites/site1/tmp"],
    ["tmpfs", "tmpfs", "8101604", "6456", "8095148", "1%", "/opt/omd/sites/site2/tmp"],
    ["tmpfs", "tmpfs", "8101604", "6484", "8095120", "1%", "/opt/omd/sites/site3/tmp"],
    ["tmpfs", "tmpfs", "8101604", "6476", "8095128", "1%", "/opt/omd/sites/site4/tmp"],
    ["tmpfs", "tmpfs", "8101604", "6404", "8095200", "1%", "/opt/omd/sites/site5/tmp"],
    ["tmpfs", "tmpfs", "8101604", "6388", "8095216", "1%", "/opt/omd/sites/site10/tmp"],
    ["[df_inodes_start]"],
    ["tmpfs", "tmpfs", "2025401", "1287", "2024114", "1%", "/run"],
    ["/dev/mapper/ubuntu--vg-root", "ext4", "15491072", "1266406", "14224666", "9%", "/"],
    ["tmpfs", "tmpfs", "2025401", "120", "2025281", "1%", "/dev/shm"],
    ["tmpfs", "tmpfs", "2025401", "7", "2025394", "1%", "/run/lock"],
    ["tmpfs", "tmpfs", "2025401", "18", "2025383", "1%", "/sys/fs/cgroup"],
    ["/dev/nvme0n1p2", "ext4", "46848", "321", "46527", "1%", "/boot"],
    ["/dev/nvme0n1p1", "vfat", "0", "0", "0", "-", "/boot/efi"],
    ["tmpfs", "tmpfs", "2025401", "105", "2025296", "1%", "/run/user/1000"],
    ["tmpfs", "tmpfs", "2025401", "1547", "2023854", "1%", "/opt/omd/sites/netapp/tmp"],
    ["tmpfs", "tmpfs", "2025401", "1531", "2023870", "1%", "/opt/omd/sites/heute/tmp"],
    ["tmpfs", "tmpfs", "2025401", "1541", "2023860", "1%", "/opt/omd/sites/site1/tmp"],
    ["tmpfs", "tmpfs", "2025401", "1541", "2023860", "1%", "/opt/omd/sites/site2/tmp"],
    ["tmpfs", "tmpfs", "2025401", "1541", "2023860", "1%", "/opt/omd/sites/site3/tmp"],
    ["tmpfs", "tmpfs", "2025401", "1541", "2023860", "1%", "/opt/omd/sites/site4/tmp"],
    ["tmpfs", "tmpfs", "2025401", "1541", "2023860", "1%", "/opt/omd/sites/site5/tmp"],
    ["tmpfs", "tmpfs", "2025401", "1536", "2023865", "1%", "/opt/omd/sites/site10/tmp"],
    ["[df_inodes_end]"],
]


DISCOVERY_RULE = {
    "ignore_fs_types": ["tmpfs", "nfs", "smbfs", "cifs", "iso9660"],
    "never_ignore_mountpoints": ["~.*/omd/sites/[^/]+/tmp$"],
    "groups": [
        {"group_name": "group1", "patterns_include": ["/opt/omd/sites/*"], "patterns_exclude": []},
        {
            "group_name": "group2",
            "patterns_include": ["/opt/omd/sites/site[12]/*"],
            "patterns_exclude": [],
        },
        {
            "group_name": "group2",
            "patterns_include": ["/opt/omd/sites/site[3]/*"],
            "patterns_exclude": [],
        },
        {"group_name": "group3", "patterns_include": ["*"], "patterns_exclude": []},
        {
            "group_name": "group4",
            "patterns_include": ["/opt/omd/sites/*"],
            "patterns_exclude": ["/opt/omd/sites/site[2,4]/*"],
        },
        {
            "group_name": "group5",
            "patterns_include": ["/opt/omd/sites/site1*"],
            "patterns_exclude": ["/opt/omd/sites/site10/*"],
        },
        {"group_name": "group5", "patterns_include": [""], "patterns_exclude": [""]},
        {"group_name": "group_empty_1", "patterns_include": [""], "patterns_exclude": []},
        {"group_name": "group_empty_2", "patterns_include": ["/notfound"], "patterns_exclude": []},
        {"group_name": "group_empty_3", "patterns_include": [], "patterns_exclude": ["*"]},
        {"group_name": "group_empty_4", "patterns_include": ["*"], "patterns_exclude": []},
        {"group_name": "group_empty_4", "patterns_include": [], "patterns_exclude": ["*"]},
        {"group_name": "group_empty_5", "patterns_include": [], "patterns_exclude": []},
    ],
}


EXPECTED_DISCOVERY: dict[str | None, Mapping] = {
    "group1": {
        "patterns": (["/opt/omd/sites/*"], []),
        "grouping_behaviour": "mountpoint",
        "item_appearance": "mountpoint",
        "mountpoint_for_block_devices": "volume_name",
    },
    "group2": {
        "patterns": (["/opt/omd/sites/site[12]/*", "/opt/omd/sites/site[3]/*"], []),
        "grouping_behaviour": "mountpoint",
        "item_appearance": "mountpoint",
        "mountpoint_for_block_devices": "volume_name",
    },
    "group3": {
        "patterns": (["*"], []),
        "grouping_behaviour": "mountpoint",
        "item_appearance": "mountpoint",
        "mountpoint_for_block_devices": "volume_name",
    },
    "group4": {
        "patterns": (["/opt/omd/sites/*"], ["/opt/omd/sites/site[2,4]/*"]),
        "grouping_behaviour": "mountpoint",
        "item_appearance": "mountpoint",
        "mountpoint_for_block_devices": "volume_name",
    },
    "group5": {
        "patterns": (["/opt/omd/sites/site1*", ""], ["/opt/omd/sites/site10/*", ""]),
        "grouping_behaviour": "mountpoint",
        "item_appearance": "mountpoint",
        "mountpoint_for_block_devices": "volume_name",
    },
}


def test_discovery() -> None:
    discovered_services = list(discover_df(DISCOVERY_RULE, parse_df(STRING_TABLE)))
    assert {s.item: s.parameters for s in discovered_services} == EXPECTED_DISCOVERY

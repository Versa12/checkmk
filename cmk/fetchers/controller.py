#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

#
# Protocol: <header><payload>

import sys
import enum
import json
from pathlib import Path
from typing import Any, Union, Dict

from cmk.utils.paths import core_fetcher_config_dir
from cmk.utils.type_defs import HostName

from . import TCPDataFetcher
from . import SNMPDataFetcher
from . import ProgramDataFetcher

from ._base import AbstractDataFetcher


class FetcherFactory:
    def __init__(self):
        self._type_to_class: Dict[str, Any] = {
            "snmp": SNMPDataFetcher,
            "program": ProgramDataFetcher,
            "tcp": TCPDataFetcher,
        }

    def make(self, fetcher_type: str, fetcher_params: Dict[str, Any]) -> AbstractDataFetcher:
        return self._type_to_class[fetcher_type].from_json(fetcher_params)


#
# At the moment Protocol and API are opened to critic.
# Base structure and API are fixed
#


class Header:
    """Header is fixed size(6+8+9+9 = 32 bytes) string in format

      header: <ID>:<'SUCCESS'|'FAILURE'>:<HINT>:<SIZE>:
      ID   - 5 bytes protocol id, "base0" at the start
      HINT - 8 bytes string. Arbitrary data, usually some error info
      SIZE - 8 bytes string 0..9

    Example:
        "base0:SUCCESS:        :12345678:"

    """
    class State(str, enum.Enum):
        SUCCESS = "SUCCESS"
        FAILURE = "FAILURE"
        WAITING = "WAITING"

    fmt = "{:<5}:{:<7}:{:<8}:{:<8}:"
    length = 32

    def __init__(self, name: str, state: Union['Header.State', str], hint: str,
                 payload_length: int) -> None:
        self.name = name
        self.state = Header.State(state) if isinstance(state, str) else state
        self.hint = hint
        self.payload_length = payload_length

    def __repr__(self) -> str:
        return "%s(%r, %r, %r, %r)" % (
            type(self).__name__,
            self.name,
            self.state,
            self.hint,
            self.payload_length,
        )

    def __str__(self) -> str:
        return Header.fmt.format(self.name[:5], self.state[:7], self.hint[:8], self.payload_length)

    def __eq__(self, other: Any) -> bool:
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(str(self))

    def __len__(self) -> int:
        return Header.length

    @classmethod
    def from_network(cls, data: str) -> 'Header':
        try:
            # to simplify parsing we are using ':' as a splitter
            name, state, hint, payload_length = data[:Header.length].split(":")[:4]
            return cls(name, state, hint, int(payload_length, base=10))
        except ValueError as exc:
            raise ValueError(data) from exc

    def clone(self) -> 'Header':
        return Header(self.name, self.state, self.hint, self.payload_length)

    @staticmethod
    def default_protocol_name() -> str:
        return "fetch"


def make_success_answer(data: str) -> str:
    return str(
        Header(name=Header.default_protocol_name(),
               state=Header.State.SUCCESS,
               hint=" ",
               payload_length=len(data))) + data


def make_failure_answer(data: str, *, hint: str) -> str:
    return str(
        Header(name=Header.default_protocol_name(),
               state=Header.State.FAILURE,
               hint=hint,
               payload_length=len(data))) + data


def make_waiting_answer() -> str:
    return str(
        Header(name=Header.default_protocol_name(),
               state=Header.State.WAITING,
               hint=" ",
               payload_length=0))


# NOTE: This function is not stub, but simplified
def run_fetchers(serial: str, host_name: HostName, timeout: int) -> None:
    # check that file is present, because lack of the file is not an error at the moment
    json_file = build_json_file_path(serial=serial, host_name=host_name)

    if not json_file.exists():
        sys.stdout.write(make_failure_answer("fetcher file is absent", hint="config"))
        return

    # Usually OMD_SITE/var/check_mk/core/fetcher-config/[config-serial]/[host].json
    _run_fetchers_from_file(file_name=json_file)


def _run_fetchers_from_file(file_name: Path) -> None:
    with open(file_name) as f:
        data = json.load(f)

        fetchers = data["fetchers"]
        ff = FetcherFactory()
        for entry in fetchers:
            try:
                fetcher_type = entry["fetcher_type"]
                fetcher_params = entry["fetcher_params"]
                fetcher = ff.make(fetcher_type=fetcher_type, fetcher_params=fetcher_params)
                output = str(fetcher.data())  # temporary: just to provide kind text of output
                sys.stdout.write(make_success_answer(output))

            # the exception is too broad by design
            # we need specs for Exception coming from fetchers
            # also (probably) we need a guard to log all exceptions in checkmk
            except Exception as e:
                sys.stdout.write(make_failure_answer(str(e), hint="failed"))

    sys.stdout.write(make_waiting_answer())


def run(serial: str, host_name: HostName, timeout: int) -> None:
    run_fetchers(serial=serial, host_name=host_name, timeout=timeout)
    sys.stdout.write(make_waiting_answer())


def read_json_file(serial: str, host_name: HostName) -> str:
    json_file = build_json_file_path(serial=serial, host_name=host_name)
    return json_file.read_text(encoding="utf-8")


def build_json_file_path(serial: str, host_name: HostName) -> Path:
    return Path("{}/{}/{}.json".format(core_fetcher_config_dir, serial, host_name))

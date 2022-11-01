#!/usr/bin/env python3
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import warnings
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from cmk.utils.crypto import password_hashing
from cmk.utils.type_defs import UserId

from cmk.gui.exceptions import MKUserError
from cmk.gui.userdb import htpasswd


@pytest.fixture(name="htpasswd_file")
def htpasswd_file_fixture(tmp_path: Path) -> Path:
    htpasswd_file_path = tmp_path / "htpasswd"
    htpasswd_file_path.write_text(
        "\n".join(
            sorted(
                [
                    # Pre 1.6 hashing formats (see cmk.gui.userdb.htpasswd for more details)
                    "bärnd:$apr1$/FU.SwEZ$Ye0XG1Huf2j7Jws7KD.h2/",
                    "cmkadmin:NEr3kqi287FQc",
                    "harry:$1$478020$ldQUQ3RIwRYk5wjKfsWPD.",
                    # A disabled user
                    "locked:!NEr3kqi287FQc",
                    # A >= 1.6 sha256 hashed password
                    "sha256user:$5$rounds=535000$5IFtH0zYpQ6STBre$Nkem2taHfBFswWj3xERRpmEI.20G5is0VBcPpUuf3J2",
                    # A >= 2.1 bcrypt hashed password
                    "bcrypt_user:$2b$12$3xoc9iu.EiyGVVPlDMC21esAiZqef9e6sogmM4UCi4s8qSvmvJWVC",
                ]
            )
        )
        + "\n",
        encoding="utf-8",
    )
    return Path(htpasswd_file_path)


@pytest.mark.parametrize(
    "password",
    [
        "blä",
        "😀",
        "😀" * 18,
        "a" * 71,
    ],
)
def test_hash_password(password: str) -> None:
    # Suppress this warning from passlib code. We can not do anything about this and it clutters our
    # unit test log
    # tests/unit/cmk/gui/test_userdb_htpasswd_connector.py::test_hash_password
    # (...)/handlers/bcrypt.py:378: DeprecationWarning: NotImplemented should not be used in a boolean context
    # if not result:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        hashed_pw = htpasswd.hash_password(password)
    password_hashing.verify(password, hashed_pw)


def test_truncation_error() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        with pytest.raises(MKUserError):
            htpasswd.hash_password("A" * 72 + "foo")
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        with pytest.raises(MKUserError):
            htpasswd.hash_password("😀" * 19)


def test_user_connector_verify_password(htpasswd_file: Path, monkeypatch: MonkeyPatch) -> None:
    c = htpasswd.HtpasswdUserConnector({})
    mock_htpwd = htpasswd.Htpasswd(htpasswd_file)
    monkeypatch.setattr(c, "_htpasswd", mock_htpwd)

    assert c.check_credentials(UserId("cmkadmin"), "cmk") == "cmkadmin"
    assert c.check_credentials(UserId("bärnd"), "cmk") == "bärnd"
    assert c.check_credentials(UserId("sha256user"), "cmk") == "sha256user"
    assert c.check_credentials(UserId("harry"), "cmk") == "harry"
    assert c.check_credentials(UserId("bcrypt_user"), "cmk") == "bcrypt_user"
    assert c.check_credentials(UserId("dingeling"), "aaa") is None
    assert c.check_credentials(UserId("locked"), "locked") is False

    # Check no exception is raised, when setting a password > 72 chars a exception is raised...
    assert c.check_credentials(UserId("bcrypt_user"), "A" * 100) is False

#!/usr/bin/env python
# ssh-import-id - Authorize SSH public keys from trusted online identities.
#
# Copyright (c) 2013 Casey Marshall <casey.marshall@gmail.com>
# Copyright (c) 2013-16 Dustin Kirkland <dustin.kirkland@gmail.com>
#
# ssh-import-id is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# ssh-import-id is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ssh-import-id.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import base64
import binascii
import getpass
import hashlib
import json
import logging
import os
import platform
import struct
import sys
import urllib.error
from urllib.parse import quote_plus
from urllib.request import Request, urlopen


VERSION = "5.13"
DEFAULT_TIMEOUT = 15.0
DEFAULT_PROTO = "lp"
ALIASED_PROTOS = {
    "ssh-import-id-gh": "gh",
    "ssh-import-id-gl": "gl",
    "ssh-import-id-lp": "lp",
}

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError


def build_parser(prog):
    parser = argparse.ArgumentParser(
        description="Authorize SSH public keys from trusted online identities.",
        prog=prog,
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="Write output to file (default ~/.ssh/authorized_keys)",
    )
    parser.add_argument(
        "-r",
        "--remove",
        action="store_true",
        default=False,
        help="Remove a key from authorized keys file",
    )
    parser.add_argument(
        "-u",
        "--useragent",
        metavar="USERAGENT",
        default="",
        help="Append to the http user agent string",
    )
    parser.add_argument("userids", nargs="+", metavar="USERID", help="User IDs to import")
    return parser


def die(msg):
    logging.error(msg)
    raise SystemExit(1)


def read_string(buf, off):
    if off + 4 > len(buf):
        raise SystemExit("truncated:%s" % buf)
    slen = struct.unpack(">I", buf[off : off + 4])[0]
    off += 4
    return buf[off : off + slen], off + slen


def rsa_keylen(buf):
    alg, off = read_string(buf, 0)
    if alg != b"ssh-rsa":
        raise ValueError(f"key is type {alg} not ssh-rsa: {buf}")
    _, off = read_string(buf, off)
    klenbuf, off = read_string(buf, off)
    return int.from_bytes(klenbuf, "big").bit_length()


def dsa_keylen(buf):
    alg, off = read_string(buf, 0)
    if alg != b"ssh-dss":
        raise ValueError(f"key is type {alg} not ssh-dss: {buf}")
    mpint, off = read_string(buf, off)
    return int.from_bytes(mpint, "big").bit_length()


def key_fingerprint(fields):
    if not fields or len(fields) < 2:
        return None

    key_type = fields[0]
    key_b64 = fields[1]
    comment = " ".join(fields[2:]) if len(fields) > 2 else "no comment"

    try:
        key_ascii = key_b64.encode("ascii")
        key_bytes = base64.b64decode(key_ascii)
    except (UnicodeDecodeError, binascii.Error):
        return None

    digest = hashlib.sha256(key_bytes).digest()
    fp_b64 = base64.b64encode(digest).decode("ascii").rstrip("=")
    fingerprint = f"SHA256:{fp_b64}"

    key_map = {
        "ssh-ed25519": ("256", "ED25519"),
        "ecdsa-sha2-nistp256": ("256", "ECDSA"),
        "ecdsa-sha2-nistp384": ("384", "ECDSA"),
        "ecdsa-sha2-nistp521": ("521", "ECDSA"),
        "sk-ecdsa-sha2-nistp256@openssh.com": ("256", "ECDSA-SK"),
        "sk-ssh-ed25519@openssh.com": ("256", "ED25519-SK"),
    }

    if key_type == "ssh-rsa":
        bits, ptype = (str(rsa_keylen(key_bytes)), "RSA")
    elif key_type == "ssh-dss":
        bits, ptype = (str(dsa_keylen(key_bytes)), "DSA")
    else:
        bits, ptype = key_map.get(key_type, ("?", key_type))

    return [bits, fingerprint, comment, f"({ptype})"]


def get_keyfile(path=None):
    if not path:
        if os.environ.get("HOME"):
            home = os.environ["HOME"]
        else:
            home = os.path.expanduser("~" + getpass.getuser())
        return os.path.join(home, ".ssh", "authorized_keys")

    if path == "-":
        return path

    abs_path = os.path.abspath(os.path.expanduser(path))

    if os.environ.get("HOME"):
        home = os.environ["HOME"]
    else:
        home = os.path.expanduser("~" + getpass.getuser())

    home_abs = os.path.abspath(home)
    tmp_abs = os.path.abspath("/tmp")
    if not (
        abs_path.startswith(home_abs + os.sep)
        or abs_path.startswith(tmp_abs + os.sep)
        or abs_path == home_abs
    ):
        die("Output path must be within user's home directory or /tmp: %s" % path)

    return abs_path


def assert_parent_dir(keyfile):
    if keyfile == "-":
        return True

    parent_dir = os.path.dirname(keyfile) if os.path.dirname(keyfile) else "."
    if not os.path.exists(parent_dir):
        umask = os.umask(0o077)
        os.makedirs(parent_dir, 0o700)
        os.umask(umask)
    if os.path.isdir(parent_dir):
        return True
    die("Parent directory not found for output [%s]" % keyfile)


def read_keyfile(output_path):
    keyfile = get_keyfile(output_path)
    if keyfile == "-" or not os.path.exists(keyfile):
        return []

    try:
        with open(keyfile, "r", encoding="utf-8") as fp:
            return fp.readlines()
    except OSError:
        die("Could not read authorized key file [%s]" % keyfile)


def write_keyfile(output_path, keyfile_lines, mode):
    output_file = get_keyfile(output_path)
    if output_file == "-":
        for line in keyfile_lines:
            if line:
                sys.stdout.write(line)
                sys.stdout.write("\n\n")
        sys.stdout.flush()
        return

    if assert_parent_dir(output_file):
        with open(output_file, mode, encoding="utf-8") as fh:
            for line in keyfile_lines:
                if line.strip():
                    fh.write(line)
                    fh.write("\n\n")


def fp_tuple(fp):
    return " ".join([fp[0], fp[1], fp[-1]])


def key_list(keyfile_lines):
    keys = []
    for line in keyfile_lines:
        ssh_fp = key_fingerprint(line.split())
        if ssh_fp:
            keys.append(fp_tuple(ssh_fp))
    logging.debug("Already have SSH public keys: [%s]", " ".join(keys))
    return keys


def user_agent(extra=""):
    ssh_import_id = f"ssh-import-id/{VERSION}"
    python = "python/%d.%d.%d" % (
        sys.version_info.major,
        sys.version_info.minor,
        sys.version_info.micro,
    )
    linux_dist = linux_distribution()
    uname = f"{platform.system()}/{platform.release()}/{platform.machine()}"
    return " ".join(part for part in [ssh_import_id, python, linux_dist, uname, extra] if part)


def linux_distribution():
    fields = {}
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as fh:
            for raw_line in fh:
                line = raw_line.strip()
                if not line or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                fields[key] = value.strip().strip('"')
    except OSError:
        return "linux/unknown"

    distro_id = fields.get("ID", "linux")
    version_id = fields.get("VERSION_ID", "unknown")
    codename = fields.get("VERSION_CODENAME", "")
    parts = [distro_id, version_id]
    if codename:
        parts.append(codename)
    return "/".join(parts)


def fetch_keys_lp(lpid, useragent):
    conf_file = "/etc/ssh/ssh_import_id"
    try:
        url = os.getenv("URL")
        if url is None and os.path.exists(conf_file):
            try:
                with open(conf_file, "r", encoding="utf-8") as fh:
                    contents = fh.read()
            except OSError:
                raise Exception("Failed to read %s" % conf_file)

            try:
                conf = json.loads(contents)
            except JSONDecodeError:
                raise Exception("File %s did not have valid JSON." % conf_file)

            url_template = conf.get("URL")
            if url_template and "{}" in url_template:
                url = url_template.format(quote_plus(lpid))
            elif url_template and url_template.count("%") == url_template.count("%s"):
                url = url_template.replace("%s", "{}").format(quote_plus(lpid))
            elif url_template:
                die("Invalid URL template in config file: %s" % conf_file)
        elif url is not None:
            if "{}" in url:
                url = url.format(quote_plus(lpid))
            elif url.count("%") == url.count("%s"):
                url = url.replace("%s", "{}").format(quote_plus(lpid))
            else:
                die("Invalid URL template in environment variable")

        if url is None:
            url = "https://launchpad.net/~{}/+sshkeys".format(quote_plus(lpid))

        headers = {"User-Agent": user_agent(useragent)}
        try:
            with urlopen(Request(url, headers=headers), timeout=DEFAULT_TIMEOUT) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            msg = "Requesting Launchpad keys failed."
            if exc.code == 404:
                msg = "Launchpad user not found."
            die(msg + " status_code=%d user=%s" % (exc.code, lpid))
    except Exception as exc:
        die(str(exc))


def fetch_keys_gh(ghid, useragent):
    x_ratelimit_remaining = "x-ratelimit-remaining"
    help_url = "https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api"
    keys = ""
    try:
        url = "https://api.github.com/users/%s/keys" % quote_plus(ghid)
        headers = {"User-Agent": user_agent(useragent)}
        try:
            with urlopen(Request(url, headers=headers), timeout=DEFAULT_TIMEOUT) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as exc:
            msg = "Requesting GitHub keys failed."
            if exc.code == 404:
                msg = 'Username "%s" not found at GitHub API.' % ghid
            elif exc.hdrs.get(x_ratelimit_remaining) == "0":
                msg = "GitHub REST API rate-limited this IP address. See %s ." % help_url
            die(msg + " status_code=%d user=%s" % (exc.code, ghid))

        for keyobj in data:
            keys += "%s %s@github/%s\n" % (keyobj["key"], ghid, keyobj["id"])
    except Exception as exc:
        die(str(exc))
    return keys


def fetch_keys_gl(glid, useragent):
    keys = ""
    try:
        gitlab_url = os.getenv("GITLAB_URL", "https://gitlab.com").rstrip("/")
        url = "{}/{}.keys".format(gitlab_url, quote_plus(glid))
        headers = {"User-Agent": user_agent(useragent)}

        try:
            with urlopen(Request(url, headers=headers), timeout=DEFAULT_TIMEOUT) as resp:
                keys_data = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            msg = "Requesting GitLab keys failed."
            if exc.code == 404:
                msg = 'Username "%s" not found at GitLab.' % glid
            die(msg + " status_code=%d user=%s url=%s" % (exc.code, glid, url))

        for line in keys_data.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                keys += "{} {}@gitlab\n".format(line, glid)
    except Exception as exc:
        die(str(exc))
    return keys


def fetch_keys(proto, username, useragent):
    if proto == "lp":
        return fetch_keys_lp(username, useragent)
    if proto == "gh":
        return fetch_keys_gh(username, useragent)
    if proto == "gl":
        return fetch_keys_gl(username, useragent)
    die("ssh-import-id protocol handler %s: not found or cannot execute" % proto)


def import_keys(proto, username, useragent, output_path):
    local_keys = key_list(read_keyfile(output_path))
    result = []
    keyfile_lines = []
    comment_string = "# ssh-import-id %s:%s" % (proto, username)
    for line in fetch_keys(proto, username, useragent).splitlines():
        line = line.strip()
        fields = line.split()
        fields.append(comment_string)
        ssh_fp = key_fingerprint(fields)
        if not ssh_fp:
            continue
        if fp_tuple(ssh_fp) in local_keys:
            logging.info("Already authorized %s", ssh_fp[:3] + ssh_fp[-1:])
            result.append(fields)
            continue
        keyfile_lines.append(" ".join(fields))
        result.append(fields)
        logging.info("Authorized key %s", ssh_fp[:3] + ssh_fp[-1:])

    write_keyfile(output_path, keyfile_lines, "a+")
    return result


def remove_keys(proto, username, output_path):
    comment_string = "# ssh-import-id %s:%s\n" % (proto, username)
    update_lines = []
    removed = []
    for line in read_keyfile(output_path):
        if line.endswith(comment_string):
            ssh_fp = key_fingerprint(line.split())
            logging.info("Removed labeled key %s", ssh_fp[:3] + ssh_fp[-1:])
            removed.append(line)
        else:
            update_lines.append(line)
    write_keyfile(output_path, update_lines, "w")
    return removed


def default_proto(argv0):
    return ALIASED_PROTOS.get(os.path.basename(argv0), DEFAULT_PROTO)


def split_userid(userid, fallback_proto):
    user_pieces = userid.split(":")
    if len(user_pieces) == 2:
        return user_pieces[0], user_pieces[1]
    if len(user_pieces) == 1:
        return fallback_proto, userid
    die("Invalid user ID: [%s]" % userid)


def main(argv=None):
    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
    os.umask(0o177)

    argv = sys.argv[1:] if argv is None else argv
    prog = os.path.basename(sys.argv[0])
    parser = build_parser(prog)
    options = parser.parse_args(argv)

    errors = []
    keys = []
    fallback_proto = default_proto(sys.argv[0])

    for userid in options.userids:
        proto, username = split_userid(userid, fallback_proto)
        if options.remove:
            changes = remove_keys(proto, username, options.output)
            action = "Removed"
        else:
            changes = import_keys(proto, username, options.useragent, options.output)
            action = "Authorized"
        keys.extend(changes)
        if not changes:
            errors.append(userid)

    logging.info("[%d] SSH keys [%s]", len(keys), action)
    if errors:
        die("No matching keys found for [%s]" % ",".join(errors))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python2

import os
import re
import json
import urlparse
import argparse
import requests

# factorio --version | grep Version | awk '{print $2}'

parser = argparse.ArgumentParser(description="Fetches Factorio update packages (e.g., for headless servers)")
parser.add_argument('-d', '--dry-run', action='store_true', dest='dry_run',
                    help="Don't download files, just state which updates would be downloaded.")
parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
                    help="Print URLs and stuff as they happen.")
parser.add_argument('-l', '--list-packages', action='store_true', dest='list_packages',
                    help="Print a list of valid packages (e.g., 'core-linux_headless64', etc.).")
parser.add_argument('-p', '--package', default='core-linux_headless64',
                    help="Which Factorio package to look for updates for, "
                    "e.g., core-linux_headless64 for a 64-bit Linux headless Factorio. Use --list-packages to "
                    "fetch an updated list.")
parser.add_argument('-f', '--for-version',
                    help="Which Factorio version you currently have, e.g., 0.12.2. (To check your current version, run: `factorio --version`)")
parser.add_argument('-O', '--output-path', default='/tmp',
                    help='Where to put downloaded files.  (Default: %(default)s')
parser.add_argument('-x', '--experimental', action='store_true', dest='experimental',
                    help="Download experimental versions, too (otherwise only stable updates are considered).")

verbose = False

class DownloadFailed(Exception): pass


def version_key(v):
    if v is None:
        return []
    return [int(x) for x in re.sub(r'(\.0+)*$','', v).split(".")]


def get_updater_data():
    payload = {'apiVersion': 2}
    r = requests.get('https://updater.factorio.com/get-available-versions')
    if not r.ok:
        raise DownloadFailed('Could not download version list.', r.status_code, r.reason)
    return r.json()


def pick_updates(updater_json, factorio_package, from_version, experimental=False):
    latest = [None, None]
    available_updates = {}
    current_version = from_version
    updates = []

    # Get latest stable version
    for row in updater_json[factorio_package]:
        if 'from' not in row:
            latest[0] = row['stable']
            continue

    # Get latest experimental version
    if experimental:
        for row in updater_json[factorio_package]:
            if 'from' in row:
                latest[1] = max(latest[1], row['to'], key=version_key)

    # Get available updates
    for row in updater_json[factorio_package]:
        # if from_version >= current_version...
        if 'from' in row and max(row['from'], current_version, key=version_key) == row['from']:
            # ...and not experimental and to_version <= last_stable
            if not experimental and min(row['to'], latest[0], key=version_key) == row['to']:
                # record this update
                available_updates[row['from']] = row['to']
            # ...or if experimental
            elif experimental:
                # record this update
                available_updates[row['from']] = row['to']

    # Create update list
    while current_version in available_updates:
        new_version = available_updates[current_version]
        if not experimental and max(current_version, latest[0], key=version_key) == current_version:
            break

        updates.append({'from': current_version, 'to': new_version})
        current_version = new_version

    return updates, latest


def get_update_link(package, from_ver, to_ver):
    payload = {
        'package': package,
        'from': from_ver,
        'to': to_ver,
        'apiVersion': 2
    }
    r = requests.get('https://updater.factorio.com/get-download-link', params=payload)
    if r.status_code != 200:
        raise DownloadFailed('Could not obtain download link.', r.status_code)
    return r.json()[0]


def fetch_update(output_path, url):
    fname = os.path.basename(urlparse.urlsplit(url).path)
    fpath = os.path.join(output_path, fname)
    r = requests.get(url, stream=True, verify=False)
    with open(fpath, 'wb') as fd:
        for chunk in r.iter_content(8192):
            fd.write(chunk)
    print 'Wrote {}, apply with `factorio --apply-update {}`'.format(fpath, fpath)


def main():
    global verbose
    args = parser.parse_args()
    verbose = args.verbose

    j = get_updater_data()
    if args.list_packages:
        print 'Available packages:'
        for package, versions in j.iteritems():
            latest = filter(lambda x: 'stable' in x, versions)
            print '  {} (v{})'.format(package, latest[0]['stable'])
        return 0

    if args.for_version is None:
        if os.path.isfile('factorio/data/base/info.json'):
            args.for_version = json.load(open('factorio/data/base/info.json')).get('version')
        else:
            parser.error('Please specify version with the --for-version flag.')

    updates, latest = pick_updates(j, args.package, args.for_version, args.experimental)

    if not updates:
        message = 'No updates available for version %s' % args.for_version
        if not args.experimental:
            if latest[0]:
                message += ' (latest stable is %s).' % latest[0]
            else:
                message += '.'
            message += ' Did you want `--experimental`?'
        else:
            message += ' (latest experimental is %s).' % latest[1]
        print message
        return 1

    for u in updates:
        if args.dry_run:
            print 'Dry run: would have fetched update from %s to %s.' % (u['from'], u['to'])
        else:
            url = get_update_link(args.package, u['from'], u['to'])
            if url:
                fetch_update(args.output_path, url)


if __name__ == '__main__':
    main()

import argparse
import logging

import getconf

from . import core
from . import sync


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help="Configuration file")
    parser.add_argument('--dry-run', '-n', action='store_true', help="Don't execute any change")
    parser.add_argument('--syslog', action='store_true', help="Log to syslog instead of stdout/stderr")

    opts = parser.parse_args()
    if not opts.syslog:
        root_logger = logging.getLogger()
        root_logger.addHandler(logging.StreamHandler())
        root_logger.setLevel(logging.INFO)

    config = getconf.ConfigGetter('folksync', [opts.config])

    source = core.load_source(
        name=config.getstr('core.source'),
        config=config,
    )

    sink_names = config.getlist('core.sinks')
    sinks = [core.load_sink(sink_name, config) for sink_name in sink_names]

    syncer = sync.Syncer(
        source=source,
        sinks=sinks,
    )

    syncer.run(dry_run=opts.dry_run)


if __name__ == '__main__':
    main()

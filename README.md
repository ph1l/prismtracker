# prismtracker - An APRS Tracker Daemon

```
                               _..____..,.
                    __gaawwprISMTR4C<3rQQQQmgwwag,
              __awwmWBVT?!"MmQQQQQQQQQQQQQW?TV$WQQQgap
          .gwgBT?"~'      jQQQQQQQQQQQQQQQQm,  -"?9$QQmw/
       qamT?^`           _WVQQQQQQWWQQQQQQQQm,      "9WWQa,
    _a2?~                jf -"9QP~   "$QQQQQQL        -4WQL.
  _%!'                  -Q[   j@      )WQQQQQm          ]QQr
_/^                     -Qc   ]m      .QQQQQQD           WQ`
                         4[ _gwWw,   qyQQQQQQf           mF
                         ]QyQQQWQQQmQQQQQQQQ@`          qF
                          "WWQQQQQQWWQQQQQQ@'          _^
                           )4WQQQQQQQQQQQW?'
                             "?9WWQQQQBT"'
                                  """
```

This program aims to be a lightweight, extensible APRS client specifically
written to run as a daemon for tracking and telemetry purposes.

It currently supports building APRS compressed position reports with course,
speed, optional altitude, and optional timestamps from a running local gpsd
instance.  It can broadcast APRS packets either through the Linux AX.25 stack
by calling out to the `beacon` program or send packets directly to an APRS-IS
server.  It is designed to run from systemd as a service and be part of a
headless installation.

Questions, comments, and patches are welcome. Email elektron@halo.nu

## Links

- Official git repo: https://k6fsm.net/prismtracker.git
- Github mirror: https://github.com/ph1l/prismtracker

## Installation

### via pip

    pip3 install prismtracker

### from source

    git clone https://k6fsm.net/prismtracker.git
    cd prismtracker
    python3 ./setup.py build
    sudo python3 ./setup.py install


## Example Usage

    prismtracker --call NOCALL-5 --symbol x --beacon --beacon-port ax0 --algorithm smart

## Setting up a systemd service

After you test the daemon out from the command line, if you want to make it a
system service you can use the config files here to do that. The commands below
assume you're running them as root, use `sudo` if you need to escalate your
privileges.


### Create /etc/systemd/system/prismtracker.service

    [Unit]
    Description=APRS daemon
    Wants=gpsd.service
    After=gpsd.service
    
    [Service]
    Type=simple
    EnvironmentFile=-/etc/default/prismtracker
    ExecStart=/usr/local/bin/prismtracker $DAEMON_OPTS
    User=nobody
    Restart=on-failure
    RestartSec=5s
    
    [Install]
    WantedBy=multi-user.target


### Create and edit /etc/default/prismtracker

    DAEMON_OPTS="--call NOCALL-5 --symbol x --beacon --beacon-port ax0 --algorithm smart"


### Setup and start the service

* Reload the systemd service files

      # systemctl daemon-reload

* Start the service and check the status:

      # systemctl start prismtracker.service
      # systemctl status prismtracker.service

* Enable it for start on boot:

      # systemctl enable prismtracker.service


### Disable and stop the service

    # systemctl stop prismtracker.service
    # systemctl disable prismtracker.service


## See also

### ax25systemd

a convenient way to configure your AX.25 network on boot. https://github.com/F4FXL/ax25systemd


## Other Refrences

APRS Documentation available here: http://www.aprs.org/

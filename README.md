credmgr
=======

securely manage privileged account credentials via shamir secret sharing

what is the problem credmgr is trying to solve?
-----------------------------------------------
- root access is problematic for many reasons - if that requires further explanation this tool is probably not for you
- there are times when it may be absolutely necessary to have that root password, for example, in a disaster-recovery scenario

how does credmgr work?
----------------------
- generates a random password in memory (of configurable length and complexity)
- generates hashes (salted, of course!) from that cleartext password (still in memory) in any hash format [passlib](http://packages.python.org/passlib/lib/passlib.hash.html) supports
- shards the cleartext using [shamir sharing](http://en.wikipedia.org/wiki/Shamir%27s_Secret_Sharing) so that the cleartext is recoverable by joining back together a configurable fraction of the shards
- emails these shards to their respective shard-holders (encrypted to the shard-holder's individual gpg pubkey) along with contact details for the other shard holders and instructions for how to reassemble the cleartext
- outputs all the requested password hash formats for deployment

what kind of systems can credmgr create hashes for?
---------------------------------------------------
- short answer: a ton. look at the [passlib](http://packages.python.org/passlib/lib/passlib.hash.html) docs for a full listing
- [BCrypt](http://en.wikipedia.org/wiki/Bcrypt), [PBKDF2](http://en.wikipedia.org/wiki/PBKDF2), and [SHA-512](http://en.wikipedia.org/wiki/SHA-2) are probably the most interesting
  - also supported are various windows, dbms, and other application-specific and/or archaic formats

recommended deployment strategy
-------------------------------
- __validate this in a test enviroment__ before you reset your root passwords in production!!!
- you'll need to have a good [sudoers](http://en.wikipedia.org/wiki/Sudo) (or [equivalent](http://en.wikipedia.org/wiki/Comparison_of_privilege_authorization_features)) setup in place so your system / network admins can continue to do their jobs
- deploy the password hashes, preferably via a configuration management system, such as [puppet](http://puppetlabs.com/), [chef](http://www.opscode.com/chef/), [microsoft sccm](https://www.microsoft.com/en-us/server-cloud/system-center/configuration-manager-2012.aspx), [etc](https://en.wikipedia.org/wiki/Comparison_of_open_source_configuration_management_software)
- __establish and communicate a clear policy__ for under what circumstances the root password(s) can be recovered, workflows, management approval process, etc to put some accountability around this
- if you're using a log management tool that supports alerts or script execution based on log events, consider setting up a system that watches for successful root logins and then generates a ticket to regenerate and reset the root password on that system.


the good
--------
- it works __if__ you set it up properly
- it's an elegant, versatile, and __free__ solution to an otherwise tricky problem

the bad
-------
- it still needs __lots__ of improvements
- for the moment it might be a little tricky to setup unless you're moderately comfortable with linux, python, and gpg. 
  - if you've managed to read this far, you're probably up to it

the ugly
--------
- there may be (read: surely are) nasty problems with my implementation (remember, __this is 0.1 code__, my friend!)
- there may be undisclosed vulnerabilities in the underlying dependencies (external binaries and python modules)
- __use at your own risk!__

how to get credmgr up and running
---------------------------------
- platform dependencies
  - for the moment, credmgr will only run on a native posix system (or [cygwin](http://www.cygwin.com/)) because it makes a couple of fuggly-ass subshell calls.
  - it has only been tested on debian
  - the crypto operations depend on __lots of system entropy__ - if you're planning to run in a virtualized environment consider installing [rng-tools](https://www.gnu.org/software/hurd/user/tlecarrour/rng-tools.html) or you may spend a lot of time waiting

- python version dependencies
  - this has only been tested on python 2.7. 
    - it may work under 2.6. 
    - it probably _won't_ run under 3.x.

- external binary dependencies
  - you'll need to have [gnupg](http://www.gnupg.org/) up-and-running
  - you'll also need to have [ssss](http://point-at-infinity.org/ssss/) installed
  - if you're running linux, there should be packages for both gnupg and ssss available in your native package manager
    - if not, you'll have to build / package from source

- python module dependencies
  - these are listed in [requirements.txt](http://github.com/treyka/credmgr/blob/master/requirements.txt) 
  - install these from [pip](http://www.pip-installer.org/en/latest/index.html) or from your native package manager
    - what?! you don't know about pip? okay, let me point you at [the salty crane's excellent writeup](http://www.saltycrane.com/blog/2009/05/notes-using-pip-and-virtualenv-django/)

- initial configuration
  - you'll need to have all the public keys for your shard-holders imported to your gpg keyring
    - consider creating a separate credmgr user and putting a dedicated, standalone gpg setup in its home directory so as not to create dependencies on your own gpg keyring
  - checkout credmgr from github (i'm assuming you know how to do __that__)
  - cd credmgr/
  - cp example_config/* config/
    - hint: you can have _multiple_ config dirs
  - put all your shard-holders' info into config/contacts.yaml 
  - put all your site-wide defaults into config/defaults.yaml
  - use config/example_cred.yaml as a template for your credential-specific config
    - settings in defaults.yaml and your credential-specific yaml are merged at runtime
    - in case of conflict, settings in your credential-specific yaml take precedence over defaults.yaml
    - you have to specifically list shard-holders (using the shard_holders array) in your defaults.yaml and/or your credential-specific yaml
      - ie, it doesn't automatically include _everyone_ listed in contacts.yaml and you can specify different sets of shard-holders for different credentials
  - try it out!
    - credmgr.py --configdir path_to_config_dir --cred-yaml path_to_credential-specific_yaml 
    - if everything's setup correctly:
      - you should see password hashes (in all your requested formats) on stdout
      - you'll wait (up to a couple of minutes) for the shamir key-sharding operation, depending on your hardware and the availability of system entropy
      - the configured shard-holders should receive individual emails, encrypted to their public-keys, providing their shard material, some explanation about what it's for, instructions for how to reassemble the cleartext, and a contact list for all the other shard-holders.


todo
----
- refactor to use [VIFF](http://viff.dk/) or [python-shamir](http://github.com/kgodey/python-shamir) instead of ssss
- refactor to use [python-gnupg](http://packages.python.org/python-gnupg/) instead of calling gpg in a subshell
- once these subshell calls are eliminated, credmgr should be portable to any platform that supports python
- put a sqlite backend behind it to support more complex trust management scenarios, like 
  - show me all the active sets of credentials in my environment
  - regenerate all the credentials using $deprecated_hashing_scheme
  - operations around hiring / firing (or promote / demote trust, depending on your use case)
- use gpg + web of trust in a more nuanced way
- find ways to better protect the cleartext while it's held in memory
  - warn the user if the system is swapping to an unencrypted swap partition?
- write a puppet class for better integration
- i've got lots of other ideas but...i only have so much free time :-/

License
-------
Apache License, Version 2.0

Please refer to the [LICENSE](http://github.com/treyka/credmgr/blob/master/LICENSE) file for further details.
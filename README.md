credmgr
=======

Securely manage privileged account credentials via Shamir secret sharing

What is the problem credmgr is trying to solve?
-----------------------------------------------
- Root access is problematic for many reasons - if that requires further explanation this tool is probably not for you.
- There are times when it may be absolutely necessary to have that root password, for example, in a disaster-recovery scenario.

How does credmgr work?
----------------------
- It generates a random password in memory (of configurable length and complexity).
- It generates hashes (salted, of course!) from that cleartext password (still in memory) in any hash format [passlib](http://packages.python.org/passlib/lib/passlib.hash.html) supports.
- It shards the cleartext using [Shamir sharing](http://en.wikipedia.org/wiki/Shamir%27s_Secret_Sharing) so that the cleartext is recoverable by joining back together a minimal subset of the shards.
  - FYI, the DNS root DNSSEC signing key is managed using Shamir sharing, cf.
    - [DNSSEC Practice Statement for the Root Zone KSK Operator](http://www.iana.org/dnssec/icann-dps.txt), section 4.2 - 'Procedural Controls'  
    - Bruce Schneier's 2010 blogpost [DNSSEC Root Key Split Among Seven People](http://www.schneier.com/blog/archives/2010/07/dnssec_root_key.html)
- It emails these shards to their respective shard-holders (encrypted to the shard-holder's individual GPG pubkey) along with contact details for the other shard holders and instructions for how to reassemble the cleartext.
- It outputs all the requested password hash formats for deployment.

What kind of systems can credmgr create hashes for?
---------------------------------------------------
- Short answer: a ton. Have a look at the [passlib](http://packages.python.org/passlib/lib/passlib.hash.html) docs for a full listing.
- [BCrypt](http://en.wikipedia.org/wiki/Bcrypt), [PBKDF2](http://en.wikipedia.org/wiki/PBKDF2), and [SHA-512](http://en.wikipedia.org/wiki/SHA-2) are probably the most interesting.
  - Various Windows, DBMS, and other application-specific and/or archaic formats are also supported.

Recommended Deployment Strategy
-------------------------------
- Validate
  - Make sure you __validate this in a test environment__ before you reset your root passwords in production!!!
    - Generate test password hash(es).
    - Create a test account(s) on all your target platform(s) and manually insert the credmgr-generated hash for the test account in /etc/shadow (or platform equivalent).
    - Verify that you can recover the cleartext password by reassembling the shards (using ssss-combine) _and_ successfully gain access to the test account via su (or platform equivalent).
- Prepare
  - You'll want to already have a good [sudoers](http://en.wikipedia.org/wiki/Sudo) (or [equivalent](http://en.wikipedia.org/wiki/Comparison_of_privilege_authorization_features)) setup in place so your system / network admins can continue to do their jobs.
    - Also test this, if you're moving away from a 'sudo su -' (or platform equivalent) workflow.
  - __Establish and communicate a clear policy__ for under what circumstances the root password(s) can be recovered, workflows, management approval process, etc to put some accountability around this.
    - Decide who within your organization will hold shards for which systems and which privileged accounts (depends on your environment and the classification / sensitivity of your various systems).
  - Document and test the recovery procedure and integrate it with your site security procedures.
- Deploy
  - Generate credmgr hash(es) for your target systems / platforms.
  - Deploy the password hashes across your whole environment, preferably via a configuration management system, cf.
    - [puppet](http://puppetlabs.com/)
    - [chef](http://www.opscode.com/chef/)
    - [microsoft sccm](https://www.microsoft.com/en-us/server-cloud/system-center/configuration-manager-2012.aspx)
    - [etc](https://en.wikipedia.org/wiki/Comparison_of_open_source_configuration_management_software)
- Monitor
  - If you're using a log management tool that supports alerts or script execution based on log events, consider configuring it to watch for successful root logins and automatically generates a ticket for incident response and/or to regenerate and reset the affected root password.


How to get credmgr up and running:
---------------------------------
- Satisfy general platform dependencies
  - For the moment, credmgr will only run on a native posix system (or [cygwin](http://www.cygwin.com/)) because it makes a couple of fuggly-ass subshell calls.
  - It has only been tested on Debian and CentOS.
  - The crypto operations depend on __lots of system entropy__ - if you're planning to run in a virtualized environment consider installing [rng-tools](https://www.gnu.org/software/hurd/user/tlecarrour/rng-tools.html) or you may spend a lot of time waiting.
  - For the moment credmgr smtp is totally simplistic so you'll need to make sure that mails sent from localhost will get properly delivered.

- Satisfy Python version dependencies
  - This has only been tested on python 2.7. 
    - It may work under 2.6. 
    - It probably _won't_ run under 3.x.

- Satisfy external binary dependencies:
  - You'll need to have [gnupg](http://www.gnupg.org/) up-and-running.
  - You'll need to have [ssss](http://point-at-infinity.org/ssss/) installed
  - If you're running linux, there should be packages for both gnupg and ssss available in your native package manager.
    - If not, you'll have to build / package from source.

- Satisfy Python module dependencies:
  - These are listed in [requirements.txt](http://github.com/treyka/credmgr/blob/master/requirements.txt).
  - Install these from [pip](http://www.pip-installer.org/en/latest/index.html) or from your native package manager.
    - What?! You don't know about pip? Okay, let me point you at [the Salty Crane's excellent writeup](http://www.saltycrane.com/blog/2009/05/notes-using-pip-and-virtualenv-django/).
  - __Note:__ I still haven't tested __all__ of the passlib hashing algorithms; some of these will have their own external dependencies.

- Initial configuration:
  - You'll need to have all the public keys for your shard-holders imported to your GPG keyring.
    - Consider creating a separate credmgr user and putting a dedicated, standalone GPG setup in its home directory so as not to create dependencies on your personal GPG keyring.
  - Checkout credmgr from github
  - cd credmgr/
  - cp example_config/* config/
    - Hint: you can have _multiple_ config dirs
  - Put all your shard-holders' info into config/contacts.yaml 
  - Put all your site-wide defaults into config/defaults.yaml
  - Use config/example_cred.yaml as a template for your credential-specific config(s)
    - Hint: settings in defaults.yaml and your credential-specific yaml are merged at runtime.
    - In case of conflict, settings in your credential-specific yaml take precedence over defaults.yaml.
    - You have to specifically list shard-holders (using the shard_holders array) in your defaults.yaml and/or your credential-specific yaml, ie, credmgr doesn't automatically include _everyone_ listed in contacts.yaml and you can specify different sets of shard-holders for different credentials.
  - Take her for a spin!
    - credmgr.py --configdir path_to_config_dir --cred-yaml path_to_credential-specific_yaml 
    - If everything's setup correctly:
      - You should see password hashes (in all your requested formats) on stdout.
      - You'll wait (up to a couple of minutes) for the shamir key-sharding operation, depending on your hardware and the availability of system entropy.
      - The configured shard-holders should receive individual emails, encrypted to their public-keys, providing their shard material, some explanation about what it's for, instructions for how to reassemble the cleartext, and a contact list for all the other shard-holders.

Planned for 0.2 release
-----------------------
- refactor to use [VIFF](http://viff.dk/) or [python-shamir](http://github.com/kgodey/python-shamir) instead of ssss
- refactor to use [python-gnupg](http://packages.python.org/python-gnupg/) instead of calling gpg in a subshell
- once these subshell calls are eliminated, credmgr should be portable to any platform that supports python
- put a sqlite backend behind it to support more complex trust management scenarios and reporting capability, ie
  - show me all the active sets of credentials in my environment
  - regenerate all the credentials using $deprecated_hashing_scheme
  - operations around hiring / firing (or promote / demote trust, depending on your use case)
- add cli flags to remove dependencies on yaml config
  - lets the thing be further automated via scripting
- use gpg + web of trust in a more nuanced, less slap-happy way
  - use gpg keyring for whatever you can and move whatever can be shifted from contacts.yaml to it
  - enable (optional) use of master shards for credential management (keyring passphrase, signing of shard mails, encryption of sqlite db)
- find ways to better protect the cleartext while it's held in memory
  - warn the user if the system is swapping to an unencrypted swap partition?
- write a puppet class for better integration
- provide an abstraction (perhaps a hash of a hash?) for nodes to indicate (via puppet reports) which root password they have set so as to provide a root password auditing capability
- clean up code
  - write unit tests
  - add docstrings

Todo - future
-------------
- create a receipt-confirmation system for shard-holders (something like mailman subscription system) so you can ensure there were no delivery problems prior to changing production password hashes
- create a sort of state machine, trap kill signals, and try to ensure that there is no execution path that lands you in an indeterminate state
- document (and add to requirements.txt) external dependencies for all the passlig hashing algorithms 
- i've got lots of other ideas but...i only have so much free time :-/

Disclaimer
----------
- tl;dr: __Use at your own risk!__
- You are free to use credmgr in any way you see fit, so long as you respect the terms of the license.
  - Apache License, Version 2.0 - cf. the project [LICENSE](http://github.com/treyka/credmgr/blob/master/LICENSE) file for further details.
- There may be security problems with my implementation (remember, __this is 0.1 code__, my friend!)
  - I've asked a number of people within the infosec and sysadmin communities to review this; so far, no-one has pointed out any implementation flaws.
- This is some rather _ugly_ code; it couldn't be much farther from PEP8 compliance (Python styleguide).
- credmgr presently lacks unit tests and docstrings.
- This is a minimally-viable implementation intended to validate the concepts; refinements will follow.
- There may be undisclosed vulnerabilities in the underlying dependencies (external binaries and python modules.)
  - This is also true for every other open-source project with external dependencies (which is basically all of them.)

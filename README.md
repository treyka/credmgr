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
- short answer: a ton. look at the [passlib](http://packages.python.org/passlib/lib/passlib.hash.html) documentation for a full list
- [BCrypt](http://en.wikipedia.org/wiki/Bcrypt), [PBKDF2](http://en.wikipedia.org/wiki/PBKDF2), and [SHA-512](http://en.wikipedia.org/wiki/SHA-2) are probably the most interesting
- also supported are various windows, dbms, and other application-specific and/or archaic formats

recommended deployment strategy
-------------------------------
- validate this in a test enviroment before you reset your root passwords in production!!!
- you'll need to have a good [sudoers](http://en.wikipedia.org/wiki/Sudo) (or [equivalent](http://en.wikipedia.org/wiki/Comparison_of_privilege_authorization_features)) setup in place so your system / network admins can continue to do their jobs
- deploy the password hashes, preferably via a configuration management system, such as [puppet](http://puppetlabs.com/), [chef](http://www.opscode.com/chef/), [microsoft sccm](https://www.microsoft.com/en-us/server-cloud/system-center/configuration-manager-2012.aspx), [etc](https://en.wikipedia.org/wiki/Comparison_of_open_source_configuration_management_software)
- establish and communicate a clear policy for under what circumstances the root password(s) can be recovered, workflows, management approval process, etc to put some accountability around this
- if you're using a log management tool that supports alerts or script execution based on log events, consider setting up a system that watches for successful root logins and then generates a ticket to regenerate and reset the root password on that system.


the good
--------
- it works if you set it up properly

the bad
-------
- it still needs a lot of improvement

the ugly
--------
- there may be unknown security problems in my implementation or the underlying libraries - use at your own risk!

how to get credmgr up and running
---------------------------------
- for the moment, credmgr will only run on a *nix system (or [cygwin](http://www.cygwin.com/)) because it makes a couple of bash subshell calls.
- this has only been tested on python 2.7. it may work under 2.6. it probably won't run under 3.x.
- you'll need to have [gnupg](http://www.gnupg.org/) up-and-running
- you'll need to have all the public keys for your shard-holders imported
- you'll also need to have [ssss](http://point-at-infinity.org/ssss/) installed
- if you're running linux, there should be packages for both gnupg and ssss available in your native package manager
- if not, you'll have to build / package from source
- 
- checkout the credmgr


todo
----
- refactor to use [VIFF](http://viff.dk/) or [python-shamir](http://github.com/kgodey/python-shamir) instead of ssss
- refactor to use [python-gnupg](http://packages.python.org/python-gnupg/) instead of calling gpg in a subshell
- once these subshell calls are eliminated, credmgr should be portable to any platform that supports python
- put a sqlite backend behind it to support more complex trust management scenarios, like 
  - show me all the active sets of credentials in my environment
  - regenerate all the credentials using $deprecated_hashing_scheme
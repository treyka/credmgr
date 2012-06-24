credmgr
=======

securely manage privileged account credentials via shamir secret sharing

what is the problem credmgr is trying to solve?
-----------------------------------------------
- root access is problematic for many reasons - if that requires further explanation this tool is probably not for you
- there are times when it may be absolutely necessary, ie, in a disaster-recovery scenario

how does credmgr work?
----------------------
- generates a random password in memory (of configurable length and complexity)
- generates hashes from that cleartext password (still in memory) in any hash format [passlib](http://packages.python.org/passlib/lib/passlib.hash.html) supports
- shards the cleartext using [shamir sharing](http://en.wikipedia.org/wiki/Shamir%27s_Secret_Sharing) so that the cleartext is recoverable by joining back together a configurable fraction of these shard
- emails these shards to the configured shard-holders (gpg-encrypted to the shard-holder's individual pubkey) along with contact details for the other shard holders and instructions for how to reassemble the cleartext
- outputs all the requested password hash formats

recommended strategy
--------------------
- validate this in a test enviroment before you reset your root passwords in production!!!
- you'll need to have a good [sudoers](http://en.wikipedia.org/wiki/Sudo) (or [equivalent](http://en.wikipedia.org/wiki/Comparison_of_privilege_authorization_features)) setup in place so your system / network admins can continue to do their jobs
- deploy the password hashes, preferably via a configuration management system, such as [puppet](http://puppetlabs.com/), [chef](http://www.opscode.com/chef/), [microsoft sccm](https://www.microsoft.com/en-us/server-cloud/system-center/configuration-manager-2012.aspx), [etc](https://en.wikipedia.org/wiki/Comparison_of_open_source_configuration_management_software)
- establish and communicate a clear policy for under what circumstances the root password(s) can be recovered, workflows, management approval process, etc to put some accountability around this
- if you're using a log management tool that supports alerts or script execution based on log events, consider setting up a system that watches for successful root logins and then generates a ticket to regenerate and reset the root password on that system.


the good
--------
- it works

the bad
-------
- it needs a lot of improvement

the ugly
--------
- there may be all sorts of security problems - use at your own risk!

how to get credmgr up and running
---------------------------------
- 

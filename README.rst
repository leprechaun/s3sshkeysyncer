===============================
S3 SSH Key Syncer
===============================

.. image:: https://img.shields.io/travis/leprechaun/s3sshkeysyncer.svg
        :target: https://travis-ci.org/leprechaun/s3sshkeysyncer

.. image:: https://img.shields.io/pypi/v/s3sshkeysyncer.svg
        :target: https://pypi.python.org/pypi/s3sshkeysyncer


This package will sync local linux users and ssh keys against an s3 location with [username].pub

Why?
----

Because key-management is painful, yet can be delightfully simple!

Let's face it, a lot of people don't re-key servers often, or at all. Using shared keys
is simple at first, but causes a lot of friction when it's time to change it.

When a organisation member leaves, or no longer requires access to certain servers,
you should be re-keying some, if not all your servers. You have to update your credentials
store, and keep everyone in the loop. Chances are, weeks later, people will still be
asking what "why am I getting 'permission denied'?"

Yeah.

Also, because you're using shared keys, all you'll be seeing in your logs is

    $time ssh: public key accepted for user generic-admin-name
    $time sudo: USER=generic-admin-name CMD=rm -rf / ...

That's not auditable at all. Forget about PCI-DSS.

How?
----

* create /etc/s3sshkeysyncer.conf

    [default]
    s3_location = s3://your-s3-bucket-name/some/hierachy/representing/your/organisation/
    enabled = true
    ignored_users = ec2-user,my-application-name

* create the bucket and appropriate hierarchy
* upload keys to that s3 location
  s3://your-s3-bucket-name/some/hierarchy/representing/your/organisation/leprechaun.pub
  s3://your-s3-bucket-name/some/hierarchy/representing/your/organisation/bozo.pub

**s3_location examples**

* s3://your-s3-bucket-name/application-name/
* s3://your-s3-bucket-name/project-name/application-name/
* s3://your-s3-bucket-name/company-name/project-name/application-name/

Whatever floats your boat.

**ignored_users**

s3sshkeysyncer will NOT affect UIDs below 1000. However, you may not want all
users to be affected by s3sshkeysyncer, you may add them to ignored_users as a
comma seperated list. example: user-that-runs-unicorn-or-something

**enabled**

If set to anything but 'true', s3sshkeysyncer will exit cleanly without changing
anything. You may be including s3sshkeysyncer as part of an AMI baking process,
but not want to enable it until you can configure it properly.

More How
--------

This package is meant to be run atleast on first boot of your instances, and will
take a list of user ssh public keys and create local users and add the key to
~/.ssh/authorized_keys

Users will have to log in using their own username.

    $time sshd: public key accepted for leprechaun
    $time sudo: USER=leprechaun CMD=rm -rf / ...

You get useful audit information in your logs.

You can run this package as a cron job, which will make sure that within $DELAY
users listed in the S3 bucket will have access, and those removed will have their
accounts disabled.

If you are using jump boxes to provide SSH access to machines that are otherwise
unaccessible, running s3sshkeysyncer on those boxes only would provide protection
adequate for many scenarios. Network access is no longer tied to a shared key
(which you likely don't rotate), but to individual ssh keys, which provide access
logs to your jump box. Depending on the size of your network, and log quality,
you can have a good clue as to who logged in where and did what. Or atleast,
narrow down a list from "any who has worked in the company/project in the past forever"
to "anyone of these 3 individuals who logged in to the jump box during this period"

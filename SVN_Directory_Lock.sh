#!/bin/bash

# variables setup - change depending on needs #
LOCKEDBY='User Userson'                                 Log "LOCKEDBY=$LOCKEDBY"
USER=user1                                            Log "USER=$USER"
EMAIL=$USER@website.com                             Log "EMAIL=$EMAIL"
BRANCH=trunk                                            Log "BRANCH=$BRANCH"
REASON='ESMBD-31313 - Merge of ESMBD-12345_bugfix FB'   Log "REASON=$REASON"

# Requirements
# Python
# Python-pip (AKA Pip)
# Pexpect (which includes pty)

#svn propset lock TRUE /svn/myrepo
#svn commit svn/myrepo

#svn propset ---- sets initial property for the lock
#svn commit [locked repo] ---- must be committed before property is active.
#svn propget ---- gets the property information for the lock
#svn propdel ---- deletes the lock. Anyone can delete a lock, but this must be done consciously and there will be a record of the change.

# Value of lock property is irrelevant to lock script. Script only checks to see if the lock property exists or not.
# For example, 'TRUE' above could be replaced with a custom descriptive text message describing rationale for the lock.

svn propset lock "Commits are not allowed at this time because $USER [$EMAIL] has $BRANCH locked for $REASON." /svn/myrepo
svn commit svn/myrepo
svn commit svn/myrepo -m 'Added Lock.'
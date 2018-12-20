#!/usr/bin/env python

"""This detects if a commit transaction is trying to commit files under
a directory with a lock property.

Pass the transaction_id and repository as arguments. This returns 0 if there
are no locks or a positive number representing the number of locks. If a '-v'
flag is passed this will also print out the lock and the file that is blocked
by the lock. 

Normally this would be called by a "pre-commit" shell script in a repository
hooks directory. Add the following code to "pre-commit":

    SVNLOOK=/usr/bin/svnlook
    REPOS="$1"
    TXN="$2"
    python /home/svn/repository/hooks/svn_dir_lock.py -v "$TXN" "$REPOS" >&2
    EXIT_STATUS=$?
    if [ $EXIT_STATUS -ne 0 ]; then
        echo "Delete locks before you commit." >&2
        exit 1
    fi

This requires that Pexpect be installed. See http://pexpect.sourceforge.net/

v. 1.0 Eli Shackelford
"""
import sys, os, traceback
import re
import getopt
from pexpect import run, spawn

def exit_with_usage():
    print globals()['__doc__']
    os._exit(1)

def parse_args (options='', long_options=[]):
    try:
        optlist, args = getopt.getopt(sys.argv[1:], options+'h?', long_options+['help','h','?'])
    except Exception, e:
        print str(e)
        exit_with_usage()
    options = dict(optlist)
    if [elem for elem in options if elem in ['-h','--h','-?','--?','--help']]:
        exit_with_usage()
    return (options, args)

def get_dirs_prop_changed (transaction_id, repository):
    """This returns a list of directories in the transaction with changed properties.
    """
    dirs_raw = run ('svnlook dirs-changed -t %(transaction_id)s %(repository)s' % locals())
    dirs_list = []
    for line in dirs_raw.splitlines():
        line = line.strip()
        m = re.search("^.U\s*([/.\w]*)", line)
        if m is not None:
            dirs_list.append(m.groups(0)[0])
    return dirs_list

def get_items_changed (transaction_id, repository):
    """This returns a list of files in the transaction.
    """
    files_raw = run ('svnlook changed -t %(transaction_id)s %(repository)s' % locals())
    files_list = []
    for line in files_raw.splitlines():
        line = line.strip()
        m = re.search("^\S*\s*([/.\w]*)", line)
        if m is not None:
            files_list.append(m.groups(0)[0])
    return files_list

def get_lock_prop_state_transaction (transaction_id, repository, item):
    state_raw = run ('svnlook propget -t %(transaction_id)s %(repository)s lock %(item)s' % locals())
    if 'TRUE' in state_raw.upper():
        return True
    else:
        return False

def get_lock_prop_state_pre (repository, item):
    state_raw = run ('svnlook propget %(repository)s lock %(item)s' % locals())
    if 'TRUE' in state_raw.upper():
        return True
    else:
        return False

def sub_dirs (path):
    """This returns all possible subpaths for a given path.
    >>> print sub_dirs ('a')
    None
    >>> print sub_dirs ('a/')
    ['/a/']
    >>> print sub_dirs ('a/b')
    ['/a/']
    >>> print sub_dirs ('a/b/')
    ['/a/', '/a/b/']
    >>> print sub_dirs ('a/b/c')
    ['/a/', '/a/b/']
    >>> print sub_dirs ('a/b/c/')
    ['/a/', '/a/b/', '/a/b/c/']
    """
    splits = path.split('/')
    if len(splits) < 2:
        return None
    splits = splits[:-1]
    dirs = ['']
    for p in splits:
        dirs.append (dirs[-1]+p+'/')
    dirs=dirs[1:]
    return dirs

def get_existing_locks (repository, items):
    locks=[]
    for i in items:
        subdirs = sub_dirs(i)
        for s in subdirs:
            if s in locks:
                continue
            if get_lock_prop_state_pre(repository, s) == True:
                locks.append(s)
    return locks

def remove_newly_cleared_locks (repository, transaction_id, items, locks):
    for l in locks:
        if l in items:
            if get_lock_prop_state_transaction(repository, transaction_id, l) == False:
                locks.remove(l)
    return locks

def under_lock (locks, items):
    locked_items = []
    for i in items:
        for l in locks:
            if l in i:
                locked_items.append((i,l))
    return locked_items

def main ():
    (options, args) = parse_args('v')
    # if args<=0:
    #     exit_with_usage()
    if '-v' in options:
        verbose_flag = True
    else:
        verbose_flag = False
    transaction_id = args[0]
    repository = args[1]
    #dirs_changed = get_dirs_prop_changed(transaction_id, repository)
    items_changed = get_items_changed(transaction_id, repository)
    # for each item in the transaction see if it has a lock prop.
#    locks=[]
#    for f in items_changed:
#        print f
#        if get_lock_prop_state_transaction(transaction_id, repository, f) == True:
#            locks.append(f)
    # a. adding new lock and files under lock --> allow
    # b. removing existing lock -> allow
    # c. adding files under old lock -> disallow
    locks = get_existing_locks(repository, items_changed)
    locks = remove_newly_cleared_locks(repository, transaction_id, items_changed, locks)
    locked_items = under_lock(locks, items_changed)
    if verbose_flag:
        for li in locked_items:
            print "LOCKED: " + li[0]
            print "    BY: " + li[1]
            print " # To remove lock use 'svn propdel lock "+li[1]+"'."
            print " # To check lock use 'svn propget lock "+li[1]+"'."
    return len(locked_items)

if __name__ == '__main__':
    try:
        exit_status = main()
        if exit_status is None:
            sys.exit(0)
        sys.exit(int(exit_status))
    except SystemExit, e:
        raise e
    except Exception, e:
        print 'ERROR, UNEXPECTED EXCEPTION'
        print str(e)
        traceback.print_exc()
        os._exit(1)
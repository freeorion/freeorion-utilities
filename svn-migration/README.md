# FreeOrion SVN to git migration

The scripts and data files in this directory were used to migrate the
FreeOrion project from a subversion repository hosted on sourceforge
to a git repository.

The migration is based on the subversion to git [migration guide][1]
provided by the KDE project.

The scripts are provided AS IS and there is no guarrantee by the
FreeOrion that they work for you.

## Dependencies

The scripts are based on bash and require the following software to
work properly:

* bash
* git
* svn
* rsync
* Qt Development Framework 4
* make

## Usage

First run

    ./freeorion-setup.sh

to download additional dependencies like svn2git and the kde-ruleset
repository and to download the original repository.  After that you
need to set up the mapping files:

* freeorion-ruleset -- rules to map svn structure into github tags, branches and commits
* freeorion-authors -- maps subversion users to git users
* freeorion-parent-remap -- reconnects missing parent child commit relations

The freeorion-authors map was created by running

    ./freeorion-collect-authors.sh > freeorion-authors

and modifying the resulting file accordingly.

Finally you need to run the

    ./freeorion-migrate.sh

script to create the git repository, assign missing tags and repack
the data.

[1]: https://techbase.kde.org/Projects/MoveToGit/UsingSvn2Git

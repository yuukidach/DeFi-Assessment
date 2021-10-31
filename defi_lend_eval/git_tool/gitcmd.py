import os
import tempfile
import re
import shlex
import logging
from typing import List, Union
from subprocess import check_output
from collections import defaultdict

from numpy import log2

__all__ = ['GitCommit']

logger = logging.getLogger(__name__)


def _run_command(cmd: str) -> str:
    """ run command line and return output

    Parameters
    ----------
    cmd : str
        command

    Returns
    -------
    str
        standard output
    """
    stdout = check_output(shlex.split(cmd)).decode('utf-8').rstrip('\n')
    return stdout


def _std_commit(commit: str) -> str:
    """ standardize a single commit id

    Args:
        commit (str): commit id

    Returns:
        str: standardized commit id
    """
    commit = re.sub(r'\W+', '', commit)
    commit = commit[:8]
    return commit


class GitCommit():
    def __init__(self, url: str):
        self.url = url
        self.cwd = os.getcwd()
        self.repo_dir = tempfile.TemporaryDirectory()
        self._clone_repo(self.repo_dir.name)

    def __enter__(self):
        os.chdir(self.repo_dir.name)
        self.init_commit = self.get_1st_commits()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        os.chdir(self.cwd)
        # remove temporary directory 
        self.repo_dir.cleanup()

    def _clone_repo(self, dir: str):
        """ Clone a git repo

        Parameters
        ----------
        dir : str
            Git repo saved directory
        """
        cmd = f'git clone {self.url} {dir}'
        _run_command(cmd)
        
    def _filter_by_1st_line(self, commits: list, key: str, exist: bool=True):
        """ Filter commits by the first line of their commit messages

        Parameters
        ----------
        commits : list
            list of commits id
        key : str
            keyword to be filterd, ignore case
        exist : bool, optional
            leave the commits with keyword in their messages, by default True
        """
        key = key.lower()
        wanted_commits = []
        logger.info(f'Before filtering "{key}" with status {exist}, '
                    f'{len(commits)} commits exist.')
        for commit in commits:
            cmd = f'git log --oneline {commit} --pretty=format:%s'
            output = _run_command(cmd).split('\n')[0].lower()
            if (key in output) == exist:
                wanted_commits.append(commit)
        logger.info(f'Now, {len(wanted_commits)} exist.')

        return wanted_commits
    
    @staticmethod
    def standardize_commit_id(commit: Union[list, str]):
        if isinstance(commit, str):
            return _std_commit(commit)
        return [_std_commit(c) for c in commit]
            
    def get_log(self, commit: str = None) -> str:
        """ Collect raw git logs

        Parameters
        ----------
        commit : str, optional
            Commit id, by default None. `None` means collect all commits

        Returns
        -------
        str
            git logs
        """
        if commit is not None:
            cmd = f'git --no-pager log --stat -1 {commit}'
        else:
            cmd = 'git --no-pager log --stat'
        output = _run_command(cmd)

        return output
    
    def get_commits(self, key: str=None) -> list:
        """Get list of commmits

        Args:
            key (str, optional): get commits containing a certain keyword in
                                 their commit messages. Defaults to None, means
                                 get all commmits.

        Returns:
            list: list of commit hash ids
        """
        if key is None:
            cmd = 'git log --all --pretty=format:%h'
        else:
            cmd = (
                f'git log --all -i --grep "{key}" '
                '--pretty=format:%h'
            )
        commits = _run_command(cmd)
        commits = [c for c in commits.split('\n') if c]
        commits = self.standardize_commit_id(commits)

        return commits
    
    def get_1st_commits(self) -> list:
        # commit repos have more than 1 root commit
        cmd = f'git rev-list --all --max-parents=0 HEAD'
        output = _run_command(cmd)
        commits = [c for c in output.split('\n') if c]
        return self.standardize_commit_id(commits)
    
    def is_in_1st_commits(self, commit: str) -> bool:
        res = False
        for c in self.init_commit:
            len1, len2= len(c), len(commit)
            if len1 < len2:
                res |= (c == commit[:len1])
            else:
                res |= (c[:len2] == commit)
        return res
    
    def get_msg(self, commit: str) -> str:
        """Get commit messages

        Args:
            commit (str): commit id

        Returns:
            str: messages
        """
        cmd = f'git log --format=%B -n 1 {commit}'
        return _run_command(cmd)

    def get_diff(self, commit: str) -> str:
        if self.is_in_1st_commits(commit):
            return ''
        cmd = f'git --no-pager diff -U0 {commit}^ {commit}'
        output = _run_command(cmd)
        return output
    
    def get_fix_commits(self) -> list:
        """ Get commit ids related to bug fix

        Returns
        -------
        list
            List of commit ids
        """
        fix_commits = self.get_commits('fix')
        merge_commits = self.get_commits('merge')
        # ignore merge commits which will lead to hundreds of changed lines
        commits = set(fix_commits) - set(merge_commits)
        
        commits = self._filter_by_1st_line(list(commits), 'fix')
        return commits
    
    def get_changed_filenames(self, commit: str, filter: str=None) -> list:
        """ Get changed files in a commit

        Parameters
        ----------
        commit : str
            Commit hash id

        filter : str
            Filter files. See `man git diff` for help

        Returns
        -------
        list
            List of files.
        """
        cmd = (
            f'git --no-pager diff {commit}^ {commit} --name-only '
            f'--ignore-submodules'
        )
        if filter is not None:
            cmd += f' --diff-filter={filter}'
        output = _run_command(cmd)
        filenames = output.split('\n')

        return filenames
    
    def get_changed_lines(self, commit: str, fnames: list) -> dict:
        """ Get changed lines in a commit

        Parameters
        ----------
        commit : str
            Commit hash id
        fnames : list
            List of file names

        Returns
        -------
        dict
            {filename: [(-start, nlines), (+start, n_lines)]}
        """
        fname_lines = defaultdict(list)
        for fname in fnames:
            cmd = f'git --no-pager diff {commit}^ {commit} -U0 -- {fname}'
            output = _run_command(cmd)
            headers = [l for l in output.split('\n') if re.match(r'^@@.+@@$', l)]
            
            # header will look like @@ -62,0 +63,3 @@
            for header in headers:
                match = re.match('@@ (\-.*) (\+.*) @@', header).groups()

                changes = []
                for change in match:
                    # header looks like @@ -198 +198 @@ if only one line changes
                    if ',' in change:
                        start, n_lines = change.split(',')
                    else:
                        start, n_lines = change, '1'
                    changes.append((start, n_lines))
                
                fname_lines[fname].append(changes)
        
        return fname_lines

    def blame_old_lines(self, commit: str, fname_lines: dict) -> dict:
        """ Get commit hash ids for changed lines

        Parameters
        ----------
        commit : str
            Current commit hash id
        fname_lines : dict
            Dictionary of file names and changed lines

        Returns
        -------
        dict
            {filename: bug_commits}
        """
        bug_sets = defaultdict(set)
        for fname, lines in fname_lines.items():
            for item in lines:
                n = int(item[0][1])
                # ignore unchanged commits
                if (n <= 0):
                    continue
                start = item[0][0][1:] # ingore '-' signal
                cmd = f'git --no-pager blame -L{start},+{n} {commit}^ -- {fname}'
                output = _run_command(cmd)
                lines = output.split('\n')
                bug_sets[fname].update([l.split(' ')[0] for l in lines])

        bug_commits = defaultdict(list)
        for fname, commits in bug_sets.items():
            bug_commits[fname] = self.standardize_commit_id(commits)
        return bug_commits
    
    def get_numstat(self, commit: str) -> list:
        """ Return short stats of the commit

        Parameters
        ----------
        commit : str
            commit id 

        Returns
        -------
        list
            [number of changed files, insertions, deletions]
        """
        if self.is_in_1st_commits(commit):
            return None
        res = [0 , 0]
        cmd = f'git diff --numstat {commit}^ {commit}'
        out = _run_command(cmd)
        for line in out.split('\n'):
            cnt = re.match(r'^(\d+).+(\d+)', line)
            if cnt is not None:
                res[0] += int(cnt.group(1))
                res[1] += int(cnt.group(2))
        return res
    
    def get_entropy(self, commit: str) -> float:
        if self.is_in_1st_commits(commit):
            return None
        ent = 0.0
        fnames = self.get_changed_filenames(commit, 'ad')
        for fname in fnames:
            # get total number of lines
            cmd = f'git --no-pager show {commit}:{fname}'
            out = _run_command(cmd)
            cnt = out.count('\n') + 1

            # get inserted lines
            cmd = f'git diff --numstat {commit}^ {commit} -- {fname}'
            out = _run_command(cmd)
            added = re.search(r'\d+', out)
            if added is None:
                continue
            added = int(added.group())
            if added == cnt:
                continue
            ent += -added/cnt*log2(added/cnt)
        return ent
        

if __name__ == '__main__':
    with GitCommit('https://github.com/Synthetixio/synthetix') as gc:
        commits = gc.get_fix_commits()
        # print(commits)
        files = gc.get_changed_filenames(commits[0])
        f_l = gc.get_changed_lines(commits[0], files)
        print(f_l)
        bug_commits = gc.blame_old_lines(commits[0], f_l)
        print(bug_commits)
        
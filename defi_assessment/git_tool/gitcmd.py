import os
import subprocess
import tempfile
import re
import shlex
import logging
from typing import Union
from subprocess import check_output
from collections import defaultdict
from numpy import log2
from .parser import get_subsys

__all__ = ['GitCommit']

logger = logging.getLogger(__name__)

COMMIT_LEN = 10


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
    # stdout = check_output(shlex.split(cmd, posix=False), encoding='utf-8')\
    #          .rstrip('\n')
    stdout = check_output(cmd, shell=True, encoding='utf-8').rstrip('\n')
    return stdout


def _run_single_pipeline_commands(cmds: list) -> str:
    cmd1, cmd2 = cmds[0], cmds[1]
    ps1 = subprocess.Popen(shlex.split(cmd1, posix=False),
                           stdout=subprocess.PIPE)
    stdout = check_output(shlex.split(cmd2, posix=False),
                          stdin=ps1.stdout,
                          encoding='utf-8').rstrip('\n')
    ps1.wait()
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

    def _filter_by_1st_line(self, commits: list, key: str, exist: bool = True):
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

    def get_commits(self, key: str = None) -> list:
        """Get list of commmits

        Args:
            key (str, optional): get commits containing a certain keyword in
                                 their commit messages. Defaults to None, means
                                 get all commmits.

        Returns:
            list: list of commit hash ids
        """
        if key is None:
            cmd = f'git log --all --pretty=format:%h --abbrev={COMMIT_LEN}'
        else:
            cmd = (
                f'git log --all -i --grep "{key}" '
                f'--pretty=format:%h --abbrev={COMMIT_LEN}'
            )
        commits = _run_command(cmd)
        commits = [c for c in commits.split('\n') if c]
        commits = self.standardize_commit_id(commits)

        return commits

    def get_author(self, commit: str) -> str:
        cmd = f'git log --pretty=format:%an -n 1 {commit}'
        out = _run_command(cmd)
        return out

    def get_1st_commits(self) -> list:
        # commit repos have more than 1 root commit
        cmd = 'git rev-list --all --max-parents=0 HEAD'
        output = _run_command(cmd)
        commits = [c for c in output.split('\n') if c]
        return self.standardize_commit_id(commits)

    def is_in_1st_commits(self, commit: str) -> bool:
        res = False
        for c in self.init_commit:
            len1, len2 = len(c), len(commit)
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

    def get_changed_filenames(self, commit: str, filter: str = None) -> list:
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
        if self.is_in_1st_commits(commit):
            return []

        cmd = (
            f'git --no-pager diff {commit}^ {commit} --name-only '
            f'--ignore-submodules'
        )
        if filter is not None:
            cmd += f' --diff-filter={filter}'
        output = _run_command(cmd)
        filenames = [f for f in output.split('\n') if f]

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
            headers = [line for line in output.split('\n')
                       if re.match(r'^@@.+@@$', line)]

            # header will look like @@ -62,0 +63,3 @@
            for header in headers:
                match = re.match(r'@@ (\-.*) (\+.*) @@', header).groups()

                changes = []
                for change in match:
                    # header looks like @@ -19 +19 @@ if only one line changes
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
                start = item[0][0][1:]  # ingore '-' signal
                cmd = (
                    f'git --no-pager blame -L{start},+{n} '
                    f'--abbrev={COMMIT_LEN} {commit}^ -- {fname}'
                )
                output = _run_command(cmd)
                lines = output.split('\n')
                bug_sets[fname].update([line.split(' ')[0] for line in lines])

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
        res = [0, 0]
        cmd = f'git diff --numstat {commit}^ {commit}'
        out = _run_command(cmd)
        for line in [line for line in out.split('\n') if line]:
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
            cmd = f'git --no-pager show {commit}:"{fname}" | wc -l'
            # out = _run_single_pipeline_commands([cmd, f'wc -l'])
            out = _run_command(cmd)
            cnt = int(out)

            # get inserted lines
            cmd = f'git diff --numstat {commit}^ {commit} -- "{fname}"'
            out = _run_command(cmd)
            added = re.search(r'\d+', out)
            if added is None or cnt == 0:
                continue
            added = int(added.group())
            if added == cnt or added == 0:
                continue
            ent += -added/cnt*log2(added/cnt)
        return ent

    def get_former_commits(self, commit: str) -> tuple:
        """Return proir commits and developers who have changed the files.
        """
        if self.is_in_1st_commits(commit):
            return []
        hset, anset = set(), set()
        fnames = self.get_changed_filenames(commit, filter='d')
        for fname in fnames:
            cmd = (
                f'git --no-pager log --pretty=format:%h,%an '
                f'--abbrev={COMMIT_LEN} --follow {commit} -- "{fname}"'
            )
            out = _run_command(cmd)
            lines = [line for line in out.split('\n') if line]
            for line in lines:
                line = line.split(',')
                h = self.standardize_commit_id(line[0])
                an = line[1]
                if h == commit:
                    anset.add(an)
                else:
                    hset.add(h)
                    anset.add(an)
        return hset, anset

    def get_author_time(self,
                        commit: str,
                        fname: str = None,
                        skip: int = 0) -> float:
        """get unix author time

        Parameters
        ----------
        commit : str
            commit id
        fname : str, optional
            filename, by default None
        skip : int, optional
            how many commit to skip, by default 0

        Returns
        -------
        float
            unix timestamp
        """
        cmd = f'git log --pretty=format:%at -n 1 --skip {skip} {commit}'
        if fname is not None:
            cmd += f' --follow -- "{fname}"'
        out = _run_command(cmd)
        if out is None or len(out) == 0:
            return None
        return float(out)

    def get_aver_interval(self, commit: str) -> float:
        if self.is_in_1st_commits(commit):
            return 0
        interval, cnt = 0.0, 0
        x = self.get_author_time(commit)

        fnames = self.get_changed_filenames(commit, filter='d')
        for fname in fnames:
            t = self.get_author_time(commit, fname, 1)
            if t is None:
                continue
            interval += x - float(t)
            cnt += 1

        if cnt == 0:
            return 0.0
        return interval / cnt / 3600  # turn into hours

    def get_author_exp(self, commit: str) -> set:
        """Get commits made by the same author before
        """
        author = self.get_author(commit)
        cmd = (
            f'git --no-pager log --author "{author}" --abbrev={COMMIT_LEN} '
            f'--pretty=format:%h {commit}^'
        )
        out = _run_command(cmd)
        out = [c for c in out.split('\n') if c]
        out = self.standardize_commit_id(out)
        return set(out)

    def get_author_recent_exp(self, commit: str):
        commits = self.get_author_exp(commit)
        rexp = 0.0
        x = self.get_author_time(commit)
        for c in commits:
            t = self.get_author_time(c)
            rexp += 1.0 / (1 + (x-t)/24/7)
        return rexp

    def get_author_subssys_exp(self, commit: str):
        commits = self.get_author_exp(commit)
        fnames = self.get_changed_filenames(commit, 'rd')
        subs0 = get_subsys(fnames)
        cnt = 0
        for c in commits:
            fnames = self.get_changed_filenames(c, 'ad')
            subs = get_subsys(fnames)
            if subs0 & subs:
                cnt += 1
        return cnt

    def get_author_proportion(self, commit: str):
        commits = self.get_author_exp(commit)
        related_commits, _ = self.get_former_commits(commit)
        if (len(related_commits) == 0):
            return 1.0
        return len(commits & related_commits) / len(related_commits)


if __name__ == '__main__':
    with GitCommit('https://github.com/Synthetixio/synthetix') as gc:
        commits = gc.get_fix_commits()
        # print(commits)
        files = gc.get_changed_filenames(commits[0])
        f_l = gc.get_changed_lines(commits[0], files)
        print(f_l)
        bug_commits = gc.blame_old_lines(commits[0], f_l)
        print(bug_commits)

import os
import tempfile
import re
import shlex
from subprocess import check_output
from collections import defaultdict

__all__ = ['GitCommit']


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


class GitCommit():
    def __init__(self, url: str):
        self.url = url
        self.cwd = os.getcwd()
        self.repo_dir = tempfile.TemporaryDirectory()
        self._clone_repo(self.repo_dir.name)

    def __enter__(self):
        os.chdir(self.repo_dir.name)
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
            cmd = f'git --no-pager log --stat 1 {commit}'
        else:
            cmd = 'git --no-pager log --stat'
        output = _run_command(cmd)

        return output
    
    def get_fix_commits(self) -> list:
        """ Get commit ids related to bug fix

        Returns
        -------
        list
            List of commit ids
        """
        cmd = (
            'git log --all -i --grep BUG --grep "fix " --grep ERROR '
            '--pretty=format:%h'
        )
        output = _run_command(cmd)
        commits = [c for c in output.split('\n') if c]
        
        return commits
    
    def get_changed_filenames(self, commit: str) -> list:
        """ Get changed files in a commit

        Parameters
        ----------
        commit : str
            Commit hash id

        Returns
        -------
        list
            List of files.
        """
        cmd = f'git --no-pager diff {commit}^ {commit} --name-only'
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
            headers = [l for l in output.split('\n') if '@@' in l]
            
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
        bug_commits = defaultdict(set)
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
                bug_commits[fname].update([l.split(' ')[0] for l in lines])

        return bug_commits


if __name__ == '__main__':
    with GitCommit('https://github.com/Synthetixio/synthetix') as gc:
        commits = gc.get_fix_commits()
        # print(commits)
        files = gc.get_changed_filenames(commits[0])
        f_l = gc.get_changed_lines(commits[0], files)
        print(f_l)
        bug_commits = gc.blame_old_lines(commits[0], f_l)
        print(bug_commits)
        
import os
import tempfile
import re
from subprocess import check_output
from collections import defaultdict


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
    stdout = check_output(cmd.split()).decode('utf-8').rstrip('\n')
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
            
    def get_raw_log(self, commit: str = None) -> str:
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
            'git log --all -i --grep BUG --grep FIX --grep ERROR '
            '--pretty=format:%h'
        )
        output = _run_command(cmd)
        commits = [c for c in output.split('\n') if c]
        
        return commits
    
    def get_commit_filenames(self, commit: str) -> list:
        cmd = f'git --no-pager diff {commit}^ {commit} --name-only'
        output = _run_command(cmd)
        filenames = output.split('\n')

        return filenames
    
    def get_changed_lines(self, commit: str, fnames: list) -> list:
        fname_lines = defaultdict(list)
        for fname in fnames:
            cmd = f'git --no-pager diff {commit}^ {commit} -U0 -- {fname}'
            output = _run_command(cmd)
            headers = [l for l in output.split('\n') if '@@' in l]
            
            # header will look like @@ -62,0 +63,3 @@
            for header in headers:
                match = re.match('@@ -(.*) +(.*) @@', header).group(1)

                # header looks like @@ -198 +198 @@ if only one line changes
                if ',' in match:
                    start, n_lines = match.split(',')
                else:
                    start, n_lines = match, '1'

                if int(n_lines) > 0:
                    fname_lines[fname].append((start, n_lines))
        
        return fname_lines


if __name__ == '__main__':
    with GitCommit('https://github.com/Synthetixio/synthetix') as gc:
        commits = gc.get_fix_commits()
        # print(commits)
        files = gc.get_commit_filenames(commits[0])
        print(gc.get_changed_lines(commits[0], files))
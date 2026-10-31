"""Execute the real persistence shell against a newer AI queue snapshot."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
class StaleIngestionTest(unittest.TestCase):
 def test_newer_ai_state_is_preserved_and_old_deployment_is_skipped(self):
  workflow=(ROOT/'.github/workflows/pages.yml').read_text()
  block=workflow.split('      - name: Commit only selected public state files',1)[1].split('  deploy:',1)[0]
  shell=block.split('        run: |\n',1)[1]
  shell='\n'.join(line[10:] for line in shell.splitlines())
  with tempfile.TemporaryDirectory() as d:
   cwd=Path(d)
   def git(*args):return subprocess.check_output(['git',*args],cwd=cwd,stderr=subprocess.DEVNULL,text=True).strip()
   git('init');git('-c','user.name=test','-c','user.email=test@example.invalid','commit','--allow-empty','-m','New AI state')
   head=git('rev-parse','HEAD')
   queue=cwd/'public/data/ai-analysis-queue.json';queue.parent.mkdir(parents=True);queue.write_text('{"status":"pending-review"}')
   output=cwd/'outputs'
   result=subprocess.run(['bash','-c',shell],cwd=cwd,env={**os.environ,'EXPECTED_BASE':'f'*40,'GITHUB_OUTPUT':str(output)},capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   self.assertEqual(output.read_text(),'superseded=true\n')
   self.assertEqual(queue.read_text(),'{"status":"pending-review"}')
   self.assertEqual(git('rev-parse','HEAD'),head)
   self.assertIn("needs.persist.outputs.superseded != 'true'",workflow)
if __name__=='__main__':unittest.main()

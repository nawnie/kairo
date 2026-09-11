import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from kairo_r11.benchmark import write


def child(root,out,boot,host,entry):
    files={'kairo_r11':['__init__.py','model.py','learn.py'],'kairo_r12':['__init__.py','transfer.py','compact.py'],
        'kairo_r13':['__init__.py','screen.py'],'kairo_r15':['__init__.py','planner.py','client.py'],
        'kairo_r18':['__init__.py','feedback.py'],'kairo_r19':['__init__.py','client.py'],
        'kairo_r20':['__init__.py','client.py'],'kairo_r21':['__init__.py','client.py','evidence.py'],
        'kairo_r22':['__init__.py','evidence.py','memory_client.py','file_client.py'],'kairo_r23':['__init__.py','client.py','challenges.py'],
        'kairo_r44':['__init__.py','backprop.py','structured.py','client.py']}
    result=None;out.mkdir(parents=True,exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='kairo_r23_agent_') as directory:
        working=Path(directory);copied=[]
        for package,names in files.items():
            (working/package).mkdir()
            for name in names:shutil.copyfile(root/package/name,working/package/name);copied.append(package+'/'+name)
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'};env.pop('PYTHONPATH',None)
        with (out/'CHILD_STDERR.log').open('w') as err:
            process=subprocess.Popen([sys.executable,'-m',entry],cwd=working,env=env,stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,stderr=err,text=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            try:
                process.stdin.write(json.dumps(boot)+'\n');process.stdin.flush()
                for line in process.stdout:
                    request=json.loads(line)
                    if request['op']=='result':result=request['result'];break
                    response=host.handle(request)
                    process.stdin.write(json.dumps(response)+'\n');process.stdin.flush()
                process.stdin.close();code=process.wait()
            finally:
                if process.poll() is None:process.terminate();process.wait()
                process.stdout.close()
                if not process.stdin.closed:process.stdin.close()
        assert result is not None and code==0, 'child failed; inspect stderr'
    write(out/'BOOTSTRAP.json',boot);write(out/'RESULT.json',result);write(out/'EVENTS.json',host.events)
    write(out/'BOUNDARY.json',{'copied_files':copied,'entry':entry,'private_files_copied':[],
        'child_exitcode':code,'fresh_process':True,'scope':'Code/input separation, not OS confinement.'})
    return result

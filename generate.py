import subprocess, time, os, urllib.request
proc = subprocess.Popen(['python', 'app.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(15)
os.makedirs('dist', exist_ok=True)
try:
    response = urllib.request.urlopen('http://localhost:8004/', timeout=30)
    html = response.read().decode('utf-8')
    with open('dist/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('Main page saved')
except Exception as e:
    print(f'Error: {e}')
finally:
    proc.terminate()
    proc.wait()

import subprocess, time, os, urllib.request

print('Starting app.py server...')
proc = subprocess.Popen(['python', 'app.py'])
os.makedirs('dist', exist_ok=True)

print('Waiting for server to start and pre-warm cache...')
max_retries = 36
for i in range(max_retries):
    try:
        response = urllib.request.urlopen('http://localhost:8004/', timeout=10)
        html = response.read().decode('utf-8')
        with open('dist/index.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print('Main page saved successfully!')
        break
    except Exception as e:
        print(f'Attempt {i+1}/{max_retries} failed: {e}. Retrying in 5s...')
        time.sleep(5)
else:
    print('Error: Failed to connect to server after multiple attempts.')

print('Terminating server...')
proc.terminate()
proc.wait()

import os
import subprocess

files = ['barras_limpio.csv', 'ramas_limpio.csv', 'gen_limpio.csv', 'Shunts_limpio.csv', 'FACTS_limpio.csv']
for f in files:
    if os.path.exists(f):
        print(f"Fixing {f}...")
        # Use textutil to read the rtf and output plain text to a tmp file
        tmp = f + ".txt"
        subprocess.run(['textutil', '-convert', 'txt', '-output', tmp, f])
        # Replace original with tmp
        if os.path.exists(tmp):
            os.rename(tmp, f)
            print(f"Fixed {f}")
        else:
            print(f"Failed to fix {f}")

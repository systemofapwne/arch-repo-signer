#!/usr/bin/env python3
from os import environ
from pathlib import Path

import gnupg
from flask import Flask, send_from_directory

SIGS            = environ.get('FLASK_PATH_SIGS',    '/sigs')
REPO            = environ.get('FLASK_PATH_REPO',    '/repo')
GPG_KEY_PRIV    = environ.get('FLASK_PATH_GPG_KEY', '/signing.key')

app = Flask(__name__)
gpg = gnupg.GPG()

@app.get('/<path:filename>.sig')
def serve_signature(filename):
    pkg = Path(REPO) / filename           # package or db
    sig = Path(SIGS) / f'{filename}.sig'

    # pkg does not exist or has been removed
    if not pkg.exists(): return 'File not found', 404

    # Signature exists and is older than pkg: Serve the sig
    if sig.exists() and sig.stat().st_mtime >= pkg.stat().st_mtime:
        return send_from_directory(SIGS, f'{filename}.sig')
    
    # Otherwise create a new signature and serve it
    try:
        if not sig.parent.exists(): sig.parent.mkdir(parents=True)
        if sig.exists(): sig.unlink()
        with open(pkg, 'rb') as file:
            gpg.sign_file(file, detach=True, binary=True, output=str(sig))
        return send_from_directory(SIGS, f'{filename}.sig')
    except:
        return 'Internal Server Error', 500

@app.get('/<path:filename>')
def serve_pkg(filename):
    try:
        return send_from_directory(REPO, filename)
    except:
        return 'File not found', 404


_keys_loaded = False
@app.before_request
def import_keys():
    global _keys_loaded
    if _keys_loaded: return
    try:
        gpg.import_keys_file(GPG_KEY_PRIV)
        _keys_loaded = True
    except:
        return 'Internal Server Error', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

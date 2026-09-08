from flask import Flask, request, jsonify, render_template
import json, hashlib, time, os

app = Flask(__name__)
DB = 'data.json'

def yukle():
    if os.path.exists(DB):
        return json.load(open(DB, 'r', encoding='utf-8'))
    return {'anahtarlar': {}}

def kaydet(db):
    json.dump(db, open(DB, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

@app.route('/')
def panel():
    return render_template('panel.html')

@app.route('/api/check', methods=['POST'])
def check():
    d = request.json or {}
    key = d.get('anahtar', d.get('key', ''))
    hwid = d.get('hwid', d.get('cihaz', ''))
    db = yukle()
    if key not in db['anahtarlar']:
        return jsonify({'gecerli': False, 'mesaj': 'Gecersiz anahtar'})
    k = db['anahtarlar'][key]
    if k.get('iptal'):
        return jsonify({'gecerli': False, 'mesaj': 'Iptal edilmis'})
    try:
        if time.time() > time.mktime(time.strptime(k['bitis'], '%Y-%m-%d %H:%M:%S')):
            return jsonify({'gecerli': False, 'mesaj': 'Sure doldu'})
    except: pass
    if hwid and hwid not in k.get('cihazlar', []):
        if len(k.get('cihazlar', [])) >= k.get('cihaz_limiti', 2):
            return jsonify({'gecerli': False, 'mesaj': 'Cihaz limiti doldu'})
        k.setdefault('cihazlar', []).append(hwid)
        kaydet(db)
    kalan = max(0, int((time.mktime(time.strptime(k['bitis'], '%Y-%m-%d %H:%M:%S')) - time.time()) / 86400))
    return jsonify({'gecerli': True, 'paket': k['paket'], 'cihaz': f"{len(k.get('cihazlar',[]))}/{k['cihaz_limiti']}", 'kalan_gun': kalan, 'mesaj': 'OK'})

@app.route('/api/panel', methods=['POST'])
def panel_api():
    d = request.json or {}
    islem = d.get('islem', '')
    if islem == 'olustur':
        db = yukle()
        raw = hashlib.sha256(f'{time.time()}{os.urandom(16).hex()}'.encode()).hexdigest()[:20].upper()
        key = f'SOJP-{raw[:4]}-{raw[4:8]}-{raw[8:12]}-{raw[12:16]}'
        gun = d.get('gun', 30)
        db['anahtarlar'][key] = {'paket': d.get('paket','full'), 'cihaz_limiti': d.get('cihaz_limiti',2), 'cihazlar': [], 'baslangic': time.strftime('%Y-%m-%d %H:%M:%S'), 'bitis': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()+gun*86400)), 'aktif': True, 'iptal': False}
        kaydet(db)
        return jsonify({'anahtar': key})
    elif islem == 'liste':
        return jsonify(yukle()['anahtarlar'])
    elif islem == 'iptal':
        db = yukle()
        k = d.get('anahtar','')
        if k in db['anahtarlar']:
            db['anahtarlar'][k]['iptal'] = True
            kaydet(db)
        return jsonify({'ok': True})
    return jsonify({'hata': 'bilinmeyen islem'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

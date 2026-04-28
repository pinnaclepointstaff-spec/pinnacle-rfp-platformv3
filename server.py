import json, os, uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import urllib.request
import urllib.error

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# ── Storage: use /data folder (persistent on Railway/Render volumes)
DATA_DIR = os.environ.get('DATA_DIR', '/home/claude/pinnacle_deploy/data')
DATA_FILE = os.path.join(DATA_DIR, 'store.json')

# ── API key: environment variable takes priority, then stored config
def get_api_key():
    env_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    if env_key:
        return env_key
    cfg_file = os.path.join(DATA_DIR, 'config.json')
    if os.path.exists(cfg_file):
        with open(cfg_file) as f:
            return json.load(f).get('api_key', '').strip()
    return ''

def save_api_key(key):
    os.makedirs(DATA_DIR, exist_ok=True)
    cfg_file = os.path.join(DATA_DIR, 'config.json')
    with open(cfg_file, 'w') as f:
        json.dump({'api_key': key}, f)

# ── Seed data
SEED = {
  "client_profile": {},
  "uploaded_docs": [],
  "bids": [
    {"id":"b1","title":"HCBS Community Supports Waiver — MD DDA","state":"MD","value":850000,"status":"prep","agency":"Maryland Department of Health / DDA","due":"2025-05-12","budget":"mid","notes":[{"text":"Staffing matrix drafted","ts":"Apr 20 09:15","author":"Team"},{"text":"Confirm EVV vendor selection","ts":"Apr 22 14:30","author":"Ops"}],"created":"2025-04-15"},
    {"id":"b2","title":"DSP Staffing Augmentation — VA DBHDS","state":"VA","value":300000,"status":"submitted","agency":"Virginia DBHDS","due":"2025-04-30","budget":"low","notes":[],"created":"2025-04-10"},
    {"id":"b3","title":"Educational Paraprofessional Staffing — DCPS","state":"DC","value":750000,"status":"new","agency":"DC Public Schools","due":"2025-06-01","budget":"mid","notes":[],"created":"2025-04-18"},
    {"id":"b4","title":"Group Home Residential Services — PG County MD","state":"MD","value":420000,"status":"won","agency":"Maryland DDA","due":"2025-03-15","budget":"high","notes":[],"created":"2025-02-10","debrief":{"factor":"Strong ISP compliance narrative and person-centered documentation","pricing":"Would keep premium tier — evaluators valued quality","gap":"None flagged"}},
    {"id":"b5","title":"Personal Supports Waiver — VA DMAS","state":"VA","value":480000,"status":"lost","agency":"Virginia DMAS","due":"2025-04-01","budget":"low","notes":[],"created":"2025-02-20","debrief":{"factor":"Undercut too aggressively — evaluators questioned quality","pricing":"Would use market tier next time","gap":"EVV documentation section was incomplete"}},
    {"id":"b6","title":"DC DDS Healthcare Staffing Vendor","state":"DC","value":650000,"status":"new","agency":"DC Department on Disability Services","due":"2025-06-25","budget":"mid","notes":[],"created":"2025-04-20"},
  ],
  "rfps": [
    {"id":1,"title":"HCBS Community Supports Waiver — Direct Support Services","agency":"Maryland Department of Health / DDA","state":"MD","type":"HCBS","value":850000,"due":"2025-05-12","daysLeft":18,"category":"HCBS Waiver","isNew":True,"score":None,"description":"Seeking qualified providers to deliver community-based supports for individuals with IDD under Maryland's Community Supports Waiver. EVV and ISP participation required.","competitor_avg":820000},
    {"id":2,"title":"Group Home Residential Services — IDD Population","agency":"Maryland DDA — Prince George's County","state":"MD","type":"Group Home","value":420000,"due":"2025-05-28","daysLeft":34,"category":"Residential","isNew":True,"score":None,"description":"Licensed Group Home operator sought for 6-bed facility serving adults with IDD. DDA licensure required.","competitor_avg":405000},
    {"id":3,"title":"DSP Staffing Augmentation — Therapeutic Group Homes","agency":"Virginia DBHDS","state":"VA","type":"Staffing","value":300000,"due":"2025-05-20","daysLeft":26,"category":"Staffing","isNew":False,"score":None,"description":"Qualified healthcare staffing vendor for 3 therapeutic group homes in Northern Virginia.","competitor_avg":288000},
    {"id":4,"title":"DDA Medical Day Services — Baltimore Region","agency":"Maryland DDA","state":"MD","type":"HCBS","value":1200000,"due":"2025-06-15","daysLeft":52,"category":"HCBS Waiver","isNew":False,"score":None,"description":"Large-scale Adult Medical Day Services under Maryland DDA Medicaid waiver. Multi-year contract.","competitor_avg":1150000},
    {"id":5,"title":"Supported Employment Services — DD Waiver","agency":"DC Department on Disability Services","state":"DC","type":"HCBS","value":560000,"due":"2025-05-30","daysLeft":36,"category":"HCBS Waiver","isNew":True,"score":None,"description":"DC DDS Supported Employment under DD Waiver. Job coaching, EVV compliance required.","competitor_avg":540000},
    {"id":6,"title":"Educational Paraprofessional Staffing — DCPS","agency":"DC Public Schools — Special Education","state":"DC","type":"Education","value":750000,"due":"2025-06-01","daysLeft":38,"category":"Education","isNew":True,"score":None,"description":"40+ paraprofessional positions across DCPS for 2025-26 school year.","competitor_avg":720000},
    {"id":7,"title":"Behavioral Health Technician Services — Group Homes","agency":"Virginia DBHDS — Region 4","state":"VA","type":"Staffing","value":220000,"due":"2025-05-15","daysLeft":21,"category":"Staffing","isNew":False,"score":None,"description":"Certified behavior technicians for 2 Group Homes serving adults with dual diagnoses.","competitor_avg":212000},
    {"id":8,"title":"Community Living Supports — Family Waiver","agency":"Maryland DDA","state":"MD","type":"HCBS","value":340000,"due":"2025-06-20","daysLeft":57,"category":"HCBS Waiver","isNew":False,"score":None,"description":"Community Living Supports through DDA Family Supports Waiver. ISP-driven model required.","competitor_avg":328000},
    {"id":9,"title":"Personal Supports Waiver — Home-Based Services","agency":"Virginia DMAS","state":"VA","type":"HCBS","value":480000,"due":"2025-05-25","daysLeft":31,"category":"HCBS Waiver","isNew":False,"score":None,"description":"Virginia DMAS personal care services for Personal Supports Waiver.","competitor_avg":462000},
    {"id":10,"title":"Group Home Expansion — 8-Bed Facility","agency":"Virginia DBHDS — Northern Region","state":"VA","type":"Group Home","value":290000,"due":"2025-06-10","daysLeft":47,"category":"Residential","isNew":False,"score":None,"description":"New 8-bed residential Group Home in Arlington County. DBHDS licensure required.","competitor_avg":278000},
    {"id":11,"title":"Healthcare Staff Leasing — Provider Network","agency":"DC DDS — Provider Relations","state":"DC","type":"Staffing","value":650000,"due":"2025-06-25","daysLeft":62,"category":"Staffing","isNew":True,"score":None,"description":"DC DDS staffing partnership across 5 residential facilities. Multi-year preferred vendor.","competitor_avg":625000},
    {"id":12,"title":"Respite Care — Family Caregiver Support Program","agency":"Maryland DDA — Montgomery County","state":"MD","type":"HCBS","value":180000,"due":"2025-05-18","daysLeft":24,"category":"HCBS Waiver","isNew":False,"score":None,"description":"Short-term respite care for families of individuals with IDD.","competitor_avg":173000},
  ],
  "checklist_state": {},
  "generated_responses": {},
  "competitor_data": {
    "MD": {"avg_rate_dsp":22.50,"avg_markup":1.28,"top_competitors":["ResCare/BrightSpring","ServiceSource","The Arc Maryland","Mosaic"],"recent_awards":[{"title":"HCBS Waiver — Anne Arundel","winner":"ServiceSource","value":920000,"tier":"market"},{"title":"DSP Staffing — Baltimore","winner":"ResCare","value":445000,"tier":"low"},{"title":"Group Home Ops — Montgomery","winner":"Mosaic","value":388000,"tier":"high"}]},
    "VA": {"avg_rate_dsp":21.00,"avg_markup":1.25,"top_competitors":["Didlake","The Arc of Virginia","NeuroRestorative","Grafton"],"recent_awards":[{"title":"DBHDS Residential Services","winner":"Didlake","value":315000,"tier":"market"},{"title":"DSP Augmentation","winner":"Grafton","value":188000,"tier":"low"}]},
    "DC": {"avg_rate_dsp":24.50,"avg_markup":1.32,"top_competitors":["LAYC Career Academy","Community Connections","Advocates for Justice","ServiceSource DC"],"recent_awards":[{"title":"DD Waiver Personal Supports","winner":"Community Connections","value":575000,"tier":"market"},{"title":"Educational Staffing","winner":"LAYC","value":698000,"tier":"mid"}]}
  }
}

def load_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    save_data(SEED)
    return SEED

def save_data(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)

# ══════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/health')
def health():
    return jsonify({"status": "ok", "version": "3.0"})

# ── AI PROXY ──────────────────────────────
@app.route('/api/ai', methods=['POST'])
def ai_proxy():
    api_key = get_api_key()
    if not api_key:
        return jsonify({"error": "No API key configured. Go to Settings and enter your Anthropic API key."}), 401

    payload = request.json or {}
    payload.setdefault('model', 'claude-sonnet-4-20250514')
    payload.setdefault('max_tokens', 1500)

    body = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=body,
        headers={
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01'
        },
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return jsonify(json.loads(resp.read()))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='replace')
        try:
            err = json.loads(err_body)
        except Exception:
            err = {"error": err_body}
        return jsonify(err), e.code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── API KEY MANAGEMENT ────────────────────
@app.route('/api/config/key', methods=['POST'])
def set_key():
    key = (request.json or {}).get('api_key', '').strip()
    if not key:
        return jsonify({"error": "Empty key"}), 400
    # If env key is set, don't override it
    if os.environ.get('ANTHROPIC_API_KEY'):
        return jsonify({"ok": True, "note": "Using environment variable key"})
    save_api_key(key)
    return jsonify({"ok": True})

@app.route('/api/config/status', methods=['GET'])
def key_status():
    key = get_api_key()
    configured = bool(key)
    preview = ('sk-ant-...' + key[-6:]) if len(key) > 10 else ''
    env_set = bool(os.environ.get('ANTHROPIC_API_KEY'))
    return jsonify({"configured": configured, "preview": preview, "env_set": env_set})

# ── DATA ──────────────────────────────────
@app.route('/api/data')
def get_data():
    return jsonify(load_data())

@app.route('/api/profile', methods=['POST'])
def save_profile():
    d = load_data()
    d['client_profile'] = request.json or {}
    save_data(d)
    return jsonify({"ok": True})

@app.route('/api/docs', methods=['POST'])
def save_doc():
    d = load_data()
    doc = request.json or {}
    doc['id'] = str(uuid.uuid4())
    doc['uploaded_at'] = datetime.now().isoformat()
    d.setdefault('uploaded_docs', [])
    d['uploaded_docs'] = [x for x in d['uploaded_docs'] if x.get('name') != doc.get('name')]
    d['uploaded_docs'].append(doc)
    save_data(d)
    return jsonify({"ok": True, "id": doc['id']})

@app.route('/api/docs/<doc_id>', methods=['DELETE'])
def delete_doc(doc_id):
    d = load_data()
    d['uploaded_docs'] = [x for x in d.get('uploaded_docs', []) if x.get('id') != doc_id]
    save_data(d)
    return jsonify({"ok": True})

@app.route('/api/bids', methods=['GET'])
def get_bids():
    return jsonify(load_data().get('bids', []))

@app.route('/api/bids', methods=['POST'])
def add_bid():
    d = load_data()
    bid = request.json or {}
    bid['id'] = 'b' + str(uuid.uuid4())[:8]
    bid['created'] = datetime.now().isoformat()
    bid.setdefault('notes', [])
    d.setdefault('bids', []).append(bid)
    save_data(d)
    return jsonify({"ok": True, "bid": bid})

@app.route('/api/bids/<bid_id>', methods=['PATCH'])
def update_bid(bid_id):
    d = load_data()
    for b in d.get('bids', []):
        if b['id'] == bid_id:
            b.update(request.json or {})
    save_data(d)
    return jsonify({"ok": True})

@app.route('/api/bids/<bid_id>/note', methods=['POST'])
def add_note(bid_id):
    d = load_data()
    note = {
        "text": (request.json or {}).get("text", ""),
        "ts": datetime.now().strftime("%b %d %H:%M"),
        "author": (request.json or {}).get("author", "Team")
    }
    for b in d.get('bids', []):
        if b['id'] == bid_id:
            b.setdefault('notes', []).append(note)
    save_data(d)
    return jsonify({"ok": True})

@app.route('/api/bids/<bid_id>/debrief', methods=['POST'])
def save_debrief(bid_id):
    d = load_data()
    for b in d.get('bids', []):
        if b['id'] == bid_id:
            b['debrief'] = request.json or {}
    save_data(d)
    return jsonify({"ok": True})

@app.route('/api/rfps', methods=['GET'])
def get_rfps():
    return jsonify(load_data().get('rfps', []))

@app.route('/api/rfps/<int:rfp_id>/score', methods=['POST'])
def save_score(rfp_id):
    d = load_data()
    for r in d.get('rfps', []):
        if r['id'] == rfp_id:
            r['score'] = (request.json or {}).get('score')
    save_data(d)
    return jsonify({"ok": True})

@app.route('/api/checklist', methods=['GET'])
def get_checklist():
    return jsonify(load_data().get('checklist_state', {}))

@app.route('/api/checklist', methods=['POST'])
def save_checklist():
    d = load_data()
    d['checklist_state'] = request.json or {}
    save_data(d)
    return jsonify({"ok": True})

@app.route('/api/responses', methods=['POST'])
def save_response():
    d = load_data()
    resp = request.json or {}
    resp_id = str(uuid.uuid4())[:8]
    resp['id'] = resp_id
    resp['created'] = datetime.now().isoformat()
    d.setdefault('generated_responses', {})[resp_id] = resp
    save_data(d)
    return jsonify({"ok": True, "id": resp_id})

@app.route('/api/competitor/<state>')
def competitor_data(state):
    return jsonify(load_data().get('competitor_data', {}).get(state.upper(), {}))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    print(f"\n{'='*50}")
    print(f"  Pinnacle Point RFP Platform")
    print(f"  Running on http://0.0.0.0:{port}")
    print(f"  API Key: {'SET via environment' if os.environ.get('ANTHROPIC_API_KEY') else 'Enter in app setup screen'}")
    print(f"{'='*50}\n")
    app.run(host='0.0.0.0', port=port, debug=debug)

"""
Lost & Found - Flask Backend (app.py)
Requirements: pip install flask flask-cors pymysql PyJWT bcrypt werkzeug

Put app.py in the SAME folder as login.html, register.html, dashboard.html, admin.html
Then run: python app.py
Open browser: http://localhost:5000
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pymysql
import bcrypt
import jwt
import os
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app, resources={r"/api/*": {
    "origins": "*",
    "allow_headers": ["Content-Type", "Authorization"],
    "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
}})

# ─── CONFIG ──────────────────────────────────────────────────────────────────

app.config['SECRET_KEY'] = 'my-super-secret-key-12345'

DB_CONFIG = {
    'host':        'localhost',
    'user':        'root',
    'password':    '4321',            # <-- your MySQL password
    'database':    'lost_found_db',  # <-- your database name
    'cursorclass': pymysql.cursors.DictCursor,
    'charset':     'utf8mb4'
}

EMAIL_CONFIG = {
    'smtp_host':   'smtp.gmail.com',
    'smtp_port':   587,
    'smtp_user':   'lostandfound0pvt@gmail.com',      # Your email
    'smtp_pass':   'foln jpsd rhus toew',          # App password
    'from_email':  'Lost & Found <lostandfound0pvt@gmail.com>',
    'enabled':     True
}


UPLOAD_FOLDER  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXT    = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_BYTES = 5 * 1024 * 1024   # 5 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

# ─── DB HELPER ───────────────────────────────────────────────────────────────

def get_db():
    return pymysql.connect(**DB_CONFIG)

# ─── JWT HELPERS  (must be defined BEFORE any route uses @token_required) ────

def generate_token(user_id, email, role='USER'):
    payload = {
        'user_id': user_id,
        'email':   email,
        'role':    role,
        'exp':     datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token      = None
        auth_header = request.headers.get('Authorization', '')

        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        # Fallback: token in query string (used by multipart/form-data uploads)
        if not token:
            token = request.args.get('token', '')

        if not token:
            return jsonify({'error': 'Token is missing.'}), 401

        try:
            data         = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = {'user_id': data['user_id'], 'email': data['email'], 'role': data.get('role', 'USER')}
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token.'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

# ─── SERVE HTML PAGES ────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('.', 'login.html')

@app.route('/login.html')
def login_page():
    return send_from_directory('.', 'login.html')

@app.route('/register.html')
def register_page():
    return send_from_directory('.', 'register.html')

@app.route('/dashboard.html')
def dashboard_page():
    return send_from_directory('.', 'dashboard.html')

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ─── AUTH ROUTES ─────────────────────────────────────────────────────────────

@app.route('/api/register', methods=['POST'])
def register():
    data     = request.get_json()
    name     = (data.get('name')     or '').strip()
    email    = (data.get('email')    or '').strip().lower()
    password = (data.get('password') or '').strip()

    if not name or not email or not password:
        return jsonify({'error': 'Name, email, and password are required.'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters.'}), 400

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                return jsonify({'error': 'Email already registered.'}), 409
            cur.execute(
                "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                (name, email, hashed)
            )
            conn.commit()
        return jsonify({'message': 'Registration successful.'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/login', methods=['POST'])
def login():
    data     = request.get_json()
    email    = (data.get('email')    or '').strip().lower()
    password = (data.get('password') or '').strip()

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()

        if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({'error': 'Invalid email or password.'}), 401

        token = generate_token(user['user_id'], user['email'], user['role'])
        return jsonify({
            'token':   token,
            'user_id': user['user_id'],
            'name':    user['name'],
            'role':    user['role']
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ─── IMAGE UPLOAD ─────────────────────────────────────────────────────────────

@app.route('/api/upload', methods=['POST'])
@token_required
def upload_image(current_user):
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided.'}), 400

    f = request.files['file']
    if not f or f.filename == '':
        return jsonify({'error': 'No file selected.'}), 400
    if not allowed_file(f.filename):
        return jsonify({'error': 'Only PNG, JPG, GIF, WEBP files allowed.'}), 400

    f.seek(0, 2)
    size = f.tell()
    f.seek(0)
    if size > MAX_FILE_BYTES:
        return jsonify({'error': 'File too large. Max 5 MB.'}), 400

    ext      = f.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    f.save(os.path.join(UPLOAD_FOLDER, filename))

    return jsonify({'url': f"/uploads/{filename}"}), 201


# ─── ADD ITEM WITH OPTIONAL IMAGE (multipart) ────────────────────────────────

@app.route('/api/items/with-image', methods=['POST'])
@token_required
def add_item_with_image(current_user):
    """Accepts multipart/form-data with optional image file + item fields."""
    title       = (request.form.get('title')       or '').strip()
    description = (request.form.get('description') or '').strip()
    location    = (request.form.get('location')    or '').strip()
    category    = (request.form.get('category')    or 'LOST').upper()
    image_url   = None

    if not title:
        return jsonify({'error': 'Title is required.'}), 400
    if category not in ('LOST', 'FOUND'):
        return jsonify({'error': 'Category must be LOST or FOUND.'}), 400

    # Handle optional image
    if 'image' in request.files:
        f = request.files['image']
        if f and f.filename:
            if not allowed_file(f.filename):
                return jsonify({'error': 'Only PNG, JPG, GIF, WEBP files allowed.'}), 400
            f.seek(0, 2); size = f.tell(); f.seek(0)
            if size > MAX_FILE_BYTES:
                return jsonify({'error': 'Image too large. Max 5 MB.'}), 400
            ext      = f.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            f.save(os.path.join(UPLOAD_FOLDER, filename))
            image_url = f"/uploads/{filename}"

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO items (title, description, category, location, date, image_url, user_id, status)
                   VALUES (%s, %s, %s, %s, CURDATE(), %s, %s, 'ACTIVE')""",
                (title, description, category, location, image_url, current_user['user_id'])
            )
            conn.commit()
            new_id = cur.lastrowid
        return jsonify({'message': 'Item added.', 'item_id': new_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ─── STATS ROUTE ─────────────────────────────────────────────────────────────

@app.route('/api/stats', methods=['GET'])
@token_required
def get_stats(current_user):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM items WHERE category='LOST'  AND status='ACTIVE'")
            lost = cur.fetchone()['cnt']

            cur.execute("SELECT COUNT(*) as cnt FROM items WHERE category='FOUND' AND status='ACTIVE'")
            found = cur.fetchone()['cnt']

            cur.execute("SELECT COUNT(*) as cnt FROM items WHERE status='RESOLVED'")
            resolved = cur.fetchone()['cnt']

            cur.execute("SELECT COUNT(*) as cnt FROM items WHERE user_id=%s", (current_user['user_id'],))
            mine = cur.fetchone()['cnt']

        return jsonify({'lost': lost, 'found': found, 'resolved': resolved, 'mine': mine}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ─── ITEMS ROUTES ────────────────────────────────────────────────────────────

@app.route('/api/items', methods=['GET'])
@token_required
def get_items(current_user):
    search   = request.args.get('search',   '').strip()
    category = request.args.get('category', '').strip().upper()
    status   = request.args.get('status',   '').strip().upper()
    mine     = request.args.get('mine',     '').strip().lower()

    conn = get_db()
    try:
        with conn.cursor() as cur:
            conditions, params = [], []

            if search:
                conditions.append("(title LIKE %s OR description LIKE %s OR location LIKE %s)")
                like = f'%{search}%'
                params += [like, like, like]

            if category in ('LOST', 'FOUND'):
                conditions.append("category = %s")
                params.append(category)

            if status in ('ACTIVE', 'RESOLVED'):
                conditions.append("status = %s")
                params.append(status)

            if mine == 'true':
                conditions.append("user_id = %s")
                params.append(current_user['user_id'])

            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
            cur.execute(f"SELECT * FROM items {where} ORDER BY created_at DESC", params)
            items = cur.fetchall()

        for item in items:
            for field in ('date', 'created_at'):
                if item.get(field) and hasattr(item[field], 'isoformat'):
                    item[field] = item[field].isoformat()

        return jsonify(items), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/items', methods=['POST'])
@token_required
def add_item(current_user):
    data        = request.get_json()
    title       = (data.get('title')       or '').strip()
    description = (data.get('description') or '').strip()
    location    = (data.get('location')    or '').strip()
    category    = (data.get('category')    or 'LOST').upper()
    image_url   = (data.get('image_url')   or '') or None

    if not title:
        return jsonify({'error': 'Title is required.'}), 400
    if category not in ('LOST', 'FOUND'):
        return jsonify({'error': 'Category must be LOST or FOUND.'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO items (title, description, category, location, date, image_url, user_id, status)
                   VALUES (%s, %s, %s, %s, CURDATE(), %s, %s, 'ACTIVE')""",
                (title, description, category, location, image_url, current_user['user_id'])
            )
            conn.commit()
            new_id = cur.lastrowid
        return jsonify({'message': 'Item added.', 'item_id': new_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/items/<int:item_id>', methods=['GET'])
@token_required
def get_item(current_user, item_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM items WHERE item_id = %s", (item_id,))
            item = cur.fetchone()
        if not item:
            return jsonify({'error': 'Item not found.'}), 404
        for field in ('date', 'created_at'):
            if item.get(field) and hasattr(item[field], 'isoformat'):
                item[field] = item[field].isoformat()
        return jsonify(item), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/items/<int:item_id>', methods=['PUT'])
@token_required
def update_item(current_user, item_id):
    data        = request.get_json()
    title       = (data.get('title')       or '').strip()
    description = (data.get('description') or '').strip()
    location    = (data.get('location')    or '').strip()
    category    = (data.get('category')    or '').upper()
    status      = (data.get('status')      or '').upper()
    image_url   = data.get('image_url')

    if category and category not in ('LOST', 'FOUND'):
        return jsonify({'error': 'Category must be LOST or FOUND.'}), 400
    if status and status not in ('ACTIVE', 'RESOLVED'):
        return jsonify({'error': 'Status must be ACTIVE or RESOLVED.'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM items WHERE item_id = %s", (item_id,))
            item = cur.fetchone()
            if not item:
                return jsonify({'error': 'Item not found.'}), 404

            cur.execute("SELECT role FROM users WHERE user_id = %s", (current_user['user_id'],))
            user = cur.fetchone()
            if item['user_id'] != current_user['user_id'] and user['role'] != 'ADMIN':
                return jsonify({'error': 'Permission denied.'}), 403

            cur.execute(
                """UPDATE items SET title=%s, description=%s, location=%s, category=%s, status=%s, image_url=%s
                   WHERE item_id=%s""",
                (
                    title       or item['title'],
                    description or item['description'],
                    location    or item['location'],
                    category    or item['category'],
                    status      or item['status'],
                    image_url if image_url is not None else item['image_url'],
                    item_id
                )
            )
            conn.commit()
        return jsonify({'message': 'Item updated.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/items/<int:item_id>', methods=['DELETE'])
@token_required
def delete_item(current_user, item_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM items WHERE item_id = %s", (item_id,))
            item = cur.fetchone()
            if not item:
                return jsonify({'error': 'Item not found.'}), 404

            cur.execute("SELECT role FROM users WHERE user_id = %s", (current_user['user_id'],))
            user = cur.fetchone()
            if item['user_id'] != current_user['user_id'] and user['role'] != 'ADMIN':
                return jsonify({'error': 'Permission denied.'}), 403

            cur.execute("DELETE FROM items WHERE item_id = %s", (item_id,))
            conn.commit()
        return jsonify({'message': 'Item deleted.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/items/<int:item_id>/resolve', methods=['PATCH'])
@token_required
def resolve_item(current_user, item_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM items WHERE item_id = %s", (item_id,))
            item = cur.fetchone()
            if not item:
                return jsonify({'error': 'Item not found.'}), 404

            cur.execute("SELECT role FROM users WHERE user_id = %s", (current_user['user_id'],))
            user = cur.fetchone()
            if item['user_id'] != current_user['user_id'] and user['role'] != 'ADMIN':
                return jsonify({'error': 'Permission denied.'}), 403

            cur.execute("UPDATE items SET status='RESOLVED' WHERE item_id=%s", (item_id,))
            conn.commit()
        return jsonify({'message': 'Item marked as resolved.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ─── USER PROFILE ────────────────────────────────────────────────────────────

@app.route('/api/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, name, email, phone, role, created_at FROM users WHERE user_id = %s",
                (current_user['user_id'],)
            )
            user = cur.fetchone()
        if not user:
            return jsonify({'error': 'User not found.'}), 404
        if user.get('created_at') and hasattr(user['created_at'], 'isoformat'):
            user['created_at'] = user['created_at'].isoformat()
        return jsonify(user), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    data         = request.get_json() or {}
    name         = (data.get('name')         or '').strip()
    phone        = (data.get('phone')        or '').strip()
    old_password = (data.get('old_password') or '').strip()
    new_password = (data.get('new_password') or '').strip()

    if not name:
        return jsonify({'error': 'Name is required.'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE user_id = %s", (current_user['user_id'],))
            user = cur.fetchone()
            if not user:
                return jsonify({'error': 'User not found.'}), 404

            if new_password:
                if len(new_password) < 6:
                    return jsonify({'error': 'New password must be at least 6 characters.'}), 400
                if not bcrypt.checkpw(old_password.encode('utf-8'), user['password'].encode('utf-8')):
                    return jsonify({'error': 'Current password is incorrect.'}), 401
                hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cur.execute(
                    "UPDATE users SET name=%s, phone=%s, password=%s WHERE user_id=%s",
                    (name, phone, hashed, current_user['user_id'])
                )
            else:
                cur.execute(
                    "UPDATE users SET name=%s, phone=%s WHERE user_id=%s",
                    (name, phone, current_user['user_id'])
                )
            conn.commit()
        return jsonify({'message': 'Profile updated.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# ─── CLAIMS ROUTES ───────────────────────────────────────────────────────────

@app.route('/api/items/<int:item_id>/claim', methods=['POST'])
@token_required
def submit_claim(current_user, item_id):
    """Anyone can claim an item they didn't post."""
    data    = request.get_json() or {}
    message = (data.get('message') or '').strip()
    # message is optional — contact can be made without description

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM items WHERE item_id = %s", (item_id,))
            item = cur.fetchone()
            if not item:
                return jsonify({'error': 'Item not found.'}), 404
            if item['user_id'] == current_user['user_id']:
                return jsonify({'error': 'You cannot claim your own item.'}), 400
            if item['status'] == 'RESOLVED':
                return jsonify({'error': 'This item is already resolved.'}), 400

            # Only one pending claim per user per item
            cur.execute(
                "SELECT claim_id FROM claims WHERE item_id=%s AND claimer_id=%s AND status='PENDING'",
                (item_id, current_user['user_id'])
            )
            if cur.fetchone():
                return jsonify({'error': 'You already have a pending claim on this item.'}), 409

            cur.execute(
                "INSERT INTO claims (item_id, claimer_id, message) VALUES (%s, %s, %s)",
                (item_id, current_user['user_id'], message)
            )
            conn.commit()
            new_claim_id = cur.lastrowid
        
        claimer_name = current_user.get('email', '').split('@')[0]
        conn2 = get_db()
        try:
            with conn2.cursor() as cur2:
                cur2.execute("SELECT name FROM users WHERE user_id=%s", (current_user['user_id'],))
                claimer = cur2.fetchone()
                if claimer:
                    claimer_name = claimer['name']
        except:
            pass
        finally:
            conn2.close()
        
        notify_claim_received(item['user_id'], claimer_name, item['title'], new_claim_id)
        
        return jsonify({'message': 'Claim submitted successfully.'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/claims/received', methods=['GET'])
@token_required
def get_received_claims(current_user):
    """Returns all claims on items owned by the current user."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.claim_id, c.item_id, c.message, c.status, c.created_at,
                       i.title  AS item_title, i.category AS item_category,
                       u.name   AS claimer_name,
                       u.email  AS claimer_email,
                       u.phone  AS claimer_phone
                FROM   claims c
                JOIN   items  i ON i.item_id   = c.item_id
                JOIN   users  u ON u.user_id   = c.claimer_id
                WHERE  i.user_id = %s
                ORDER  BY c.created_at DESC
            """, (current_user['user_id'],))
            rows = cur.fetchall()

        for r in rows:
            if r.get('created_at') and hasattr(r['created_at'], 'isoformat'):
                r['created_at'] = r['created_at'].isoformat()
            # Only expose contact details if claim is accepted
            if r['status'] != 'ACCEPTED':
                r['claimer_email'] = None
                r['claimer_phone'] = None

        return jsonify(rows), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/claims/sent', methods=['GET'])
@token_required
def get_sent_claims(current_user):
    """Returns all claims submitted by the current user."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.claim_id, c.item_id, c.message, c.status, c.created_at,
                       i.title    AS item_title, i.category AS item_category,
                       u.name     AS owner_name,
                       u.email    AS owner_email,
                       u.phone    AS owner_phone
                FROM   claims c
                JOIN   items  i ON i.item_id = c.item_id
                JOIN   users  u ON u.user_id = i.user_id
                WHERE  c.claimer_id = %s
                ORDER  BY c.created_at DESC
            """, (current_user['user_id'],))
            rows = cur.fetchall()

        for r in rows:
            if r.get('created_at') and hasattr(r['created_at'], 'isoformat'):
                r['created_at'] = r['created_at'].isoformat()
            # Only expose owner contact if accepted
            if r['status'] != 'ACCEPTED':
                r['owner_email'] = None
                r['owner_phone'] = None

        return jsonify(rows), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/claims/<int:claim_id>/accept', methods=['PATCH'])
@token_required
def accept_claim(current_user, claim_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.*, i.user_id AS owner_id, i.item_id
                FROM   claims c JOIN items i ON i.item_id = c.item_id
                WHERE  c.claim_id = %s
            """, (claim_id,))
            claim = cur.fetchone()
            if not claim:
                return jsonify({'error': 'Claim not found.'}), 404
            if claim['owner_id'] != current_user['user_id']:
                return jsonify({'error': 'Permission denied.'}), 403
            if claim['status'] != 'PENDING':
                return jsonify({'error': 'Claim is no longer pending.'}), 400

            # Accept this claim, reject all others for the same item
            cur.execute("UPDATE claims SET status='ACCEPTED' WHERE claim_id=%s", (claim_id,))
            cur.execute(
                "UPDATE claims SET status='REJECTED' WHERE item_id=%s AND claim_id != %s AND status='PENDING'",
                (claim['item_id'], claim_id)
            )
            # Auto-resolve the item
            cur.execute("UPDATE items SET status='RESOLVED' WHERE item_id=%s", (claim['item_id'],))
            conn.commit()
        
        owner_name = current_user.get('email', '').split('@')[0]
        conn2 = get_db()
        try:
            with conn2.cursor() as cur2:
                cur2.execute("SELECT name FROM users WHERE user_id=%s", (current_user['user_id'],))
                owner = cur2.fetchone()
                if owner:
                    owner_name = owner['name']
        except:
            pass
        finally:
            conn2.close()
        
        item_title = ''
        conn3 = get_db()
        try:
            with conn3.cursor() as cur3:
                cur3.execute("SELECT title FROM items WHERE item_id=%s", (claim['item_id'],))
                itm = cur3.fetchone()
                if itm:
                    item_title = itm['title']
        except:
            pass
        finally:
            conn3.close()
        
        notify_claim_status(claim['claimer_id'], item_title, 'ACCEPTED', owner_name)
        
        return jsonify({'message': 'Claim accepted. Item marked as resolved.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/claims/<int:claim_id>/reject', methods=['PATCH'])
@token_required
def reject_claim(current_user, claim_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.*, i.user_id AS owner_id
                FROM   claims c JOIN items i ON i.item_id = c.item_id
                WHERE  c.claim_id = %s
            """, (claim_id,))
            claim = cur.fetchone()
            if not claim:
                return jsonify({'error': 'Claim not found.'}), 404
            if claim['owner_id'] != current_user['user_id']:
                return jsonify({'error': 'Permission denied.'}), 403
            if claim['status'] != 'PENDING':
                return jsonify({'error': 'Claim is no longer pending.'}), 400

            cur.execute("UPDATE claims SET status='REJECTED' WHERE claim_id=%s", (claim_id,))
            conn.commit()
        
        owner_name = current_user.get('email', '').split('@')[0]
        conn2 = get_db()
        try:
            with conn2.cursor() as cur2:
                cur2.execute("SELECT name FROM users WHERE user_id=%s", (current_user['user_id'],))
                owner = cur2.fetchone()
                if owner:
                    owner_name = owner['name']
        except:
            pass
        finally:
            conn2.close()
        
        item_title = ''
        conn3 = get_db()
        try:
            with conn3.cursor() as cur3:
                cur3.execute("SELECT title FROM items WHERE item_id=%s", (claim['item_id'],))
                itm = cur3.fetchone()
                if itm:
                    item_title = itm['title']
        except:
            pass
        finally:
            conn3.close()
        
        notify_claim_status(claim['claimer_id'], item_title, 'REJECTED', owner_name)
        
        return jsonify({'message': 'Claim rejected.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/claims/pending-count', methods=['GET'])
@token_required
def pending_claim_count(current_user):
    """Badge count — pending claims on the current user's items."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) as cnt
                FROM   claims c JOIN items i ON i.item_id = c.item_id
                WHERE  i.user_id = %s AND c.status = 'PENDING'
            """, (current_user['user_id'],))
            count = cur.fetchone()['cnt']
        return jsonify({'count': count}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# ─── EMAIL HELPER ─────────────────────────────────────────────────────────────

def send_email(to_email, subject, html_body):
    if not EMAIL_CONFIG['enabled']:
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_CONFIG['from_email']
        msg['To'] = to_email
        msg.attach(MIMEText(html_body, 'html'))
        with smtplib.SMTP(EMAIL_CONFIG['smtp_host'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['smtp_user'], EMAIL_CONFIG['smtp_pass'])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def create_notification(user_id, notif_type, title, message, reference_id=None):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO notifications (user_id, type, title, message, reference_id) VALUES (%s, %s, %s, %s, %s)",
                (user_id, notif_type, title, message, reference_id)
            )
            conn.commit()
            notif_id = cur.lastrowid
        return notif_id
    except:
        pass
    finally:
        conn.close()


def notify_claim_received(item_owner_id, claimer_name, item_title, claim_id):
    title = "New claim on your item"
    msg = f"{claimer_name} has submitted a claim on your item '{item_title}'."
    create_notification(item_owner_id, 'CLAIM_RECEIVED', title, msg, claim_id)
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT email, name FROM users WHERE user_id = %s", (item_owner_id,))
            user = cur.fetchone()
            if user and EMAIL_CONFIG['enabled']:
                html = f"""
                <html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: #1a1a2e; color: white; padding: 20px; text-align: center;">
                    <h2 style="margin:0;">Lost & Found</h2>
                </div>
                <div style="padding: 20px;">
                    <h3>New Claim Received</h3>
                    <p>Hello {user['name']},</p>
                    <p><strong>{claimer_name}</strong> has submitted a claim on your item:</p>
                    <div style="background: #f4f5f7; padding: 15px; border-radius: 8px; margin: 15px 0;">
                        <strong>{item_title}</strong>
                    </div>
                    <p>Please log in to review and respond to this claim.</p>
                    <a href="http://localhost:5000/dashboard.html" style="background: #e94560; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Dashboard</a>
                </div></body></html>"""
                send_email(user['email'], title, html)
    except:
        pass
    finally:
        conn.close()


def notify_claim_status(claimer_id, item_title, status, owner_name):
    if status == 'ACCEPTED':
        title = "Your claim was accepted!"
        msg = f"Your claim on '{item_title}' was accepted by {owner_name}!"
    else:
        title = "Claim update"
        msg = f"Your claim on '{item_title}' was not selected by {owner_name}."
    create_notification(claimer_id, 'CLAIM_STATUS', title, msg)
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT email, name FROM users WHERE user_id = %s", (claimer_id,))
            user = cur.fetchone()
            if user and EMAIL_CONFIG['enabled']:
                bg = "#22c55e" if status == 'ACCEPTED' else "#6b7280"
                html = f"""
                <html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: #1a1a2e; color: white; padding: 20px; text-align: center;">
                    <h2 style="margin:0;">Lost & Found</h2>
                </div>
                <div style="padding: 20px;">
                    <h3 style="color: {bg};">{title}</h3>
                    <p>Hello {user['name']},</p>
                    <p>{msg}</p>
                    <div style="background: #f4f5f7; padding: 15px; border-radius: 8px; margin: 15px 0;">
                        <strong>{item_title}</strong>
                    </div>
                    <a href="http://localhost:5000/dashboard.html" style="background: #e94560; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Dashboard</a>
                </div></body></html>"""
                send_email(user['email'], title, html)
    except:
        pass
    finally:
        conn.close()


# ─── ADMIN ROUTES ─────────────────────────────────────────────────────────────

def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.get('role') != 'ADMIN':
            return jsonify({'error': 'Admin access required.'}), 403
        return f(current_user, *args, **kwargs)
    return decorated


@app.route('/api/admin/users', methods=['GET'])
@token_required
@admin_required
def get_all_users(current_user):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_id, name, email, phone, role, created_at,
                       (SELECT COUNT(*) FROM items WHERE user_id = users.user_id) as item_count
                FROM users ORDER BY created_at DESC
            """)
            users = cur.fetchall()
        for u in users:
            if u.get('created_at') and hasattr(u['created_at'], 'isoformat'):
                u['created_at'] = u['created_at'].isoformat()
        return jsonify(users), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/admin/users/<int:target_user_id>', methods=['PUT'])
@token_required
@admin_required
def admin_update_user(current_user, target_user_id):
    data = request.get_json() or {}
    role = data.get('role', '').upper()
    if role not in ('USER', 'ADMIN'):
        return jsonify({'error': 'Role must be USER or ADMIN.'}), 400
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET role=%s WHERE user_id=%s", (role, target_user_id))
            if cur.rowcount == 0:
                return jsonify({'error': 'User not found.'}), 404
            conn.commit()
        return jsonify({'message': 'User role updated.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/admin/users/<int:target_user_id>', methods=['DELETE'])
@token_required
@admin_required
def admin_delete_user(current_user, target_user_id):
    if target_user_id == current_user['user_id']:
        return jsonify({'error': 'Cannot delete yourself.'}), 400
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE user_id=%s", (target_user_id,))
            if cur.rowcount == 0:
                return jsonify({'error': 'User not found.'}), 404
            conn.commit()
        return jsonify({'message': 'User deleted.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/admin/items', methods=['GET'])
@token_required
@admin_required
def admin_get_all_items(current_user):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT i.*, u.name as owner_name, u.email as owner_email,
                       (SELECT COUNT(*) FROM claims WHERE item_id = i.item_id) as claim_count
                FROM items i
                JOIN users u ON u.user_id = i.user_id
                ORDER BY i.created_at DESC
            """)
            items = cur.fetchall()
        for item in items:
            for field in ('date', 'created_at'):
                if item.get(field) and hasattr(item[field], 'isoformat'):
                    item[field] = item[field].isoformat()
        return jsonify(items), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/admin/items/<int:item_id>', methods=['DELETE'])
@token_required
@admin_required
def admin_delete_item(current_user, item_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM items WHERE item_id=%s", (item_id,))
            if cur.rowcount == 0:
                return jsonify({'error': 'Item not found.'}), 404
            conn.commit()
        return jsonify({'message': 'Item deleted.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/admin/stats', methods=['GET'])
@token_required
@admin_required
def admin_get_stats(current_user):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM users")
            total_users = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) as cnt FROM items")
            total_items = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) as cnt FROM items WHERE status='RESOLVED'")
            resolved_items = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) as cnt FROM claims WHERE status='PENDING'")
            pending_claims = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) as cnt FROM items WHERE category='LOST' AND status='ACTIVE'")
            active_lost = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) as cnt FROM items WHERE category='FOUND' AND status='ACTIVE'")
            active_found = cur.fetchone()['cnt']
        return jsonify({
            'total_users': total_users,
            'total_items': total_items,
            'resolved_items': resolved_items,
            'pending_claims': pending_claims,
            'active_lost': active_lost,
            'active_found': active_found
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/admin/claims', methods=['GET'])
@token_required
@admin_required
def admin_get_all_claims(current_user):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.*, i.title as item_title, i.category as item_category,
                       u1.name as claimer_name, u1.email as claimer_email,
                       u2.name as owner_name, u2.email as owner_email
                FROM claims c
                JOIN items i ON i.item_id = c.item_id
                JOIN users u1 ON u1.user_id = c.claimer_id
                JOIN users u2 ON u2.user_id = i.user_id
                ORDER BY c.created_at DESC
            """)
            claims = cur.fetchall()
        for c in claims:
            if c.get('created_at') and hasattr(c['created_at'], 'isoformat'):
                c['created_at'] = c['created_at'].isoformat()
        return jsonify(claims), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# ─── NOTIFICATIONS ROUTES ─────────────────────────────────────────────────────

@app.route('/api/notifications', methods=['GET'])
@token_required
def get_notifications(current_user):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 50
            """, (current_user['user_id'],))
            notifs = cur.fetchall()
        for n in notifs:
            if n.get('created_at') and hasattr(n['created_at'], 'isoformat'):
                n['created_at'] = n['created_at'].isoformat()
        return jsonify(notifs), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/notifications/read/<int:notif_id>', methods=['PATCH'])
@token_required
def mark_notification_read(current_user, notif_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE notifications SET is_read=TRUE WHERE notif_id=%s AND user_id=%s",
                       (notif_id, current_user['user_id']))
            conn.commit()
        return jsonify({'message': 'Marked as read.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/notifications/read-all', methods=['PATCH'])
@token_required
def mark_all_notifications_read(current_user):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE notifications SET is_read=TRUE WHERE user_id=%s",
                       (current_user['user_id'],))
            conn.commit()
        return jsonify({'message': 'All marked as read.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/notifications/unread-count', methods=['GET'])
@token_required
def unread_notification_count(current_user):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM notifications WHERE user_id=%s AND is_read=FALSE",
                       (current_user['user_id'],))
            count = cur.fetchone()['cnt']
        return jsonify({'count': count}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# ─── HEALTH CHECK ────────────────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'Lost & Found API is running.'}), 200

# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("✅ Server running at http://localhost:5000")
    print("✅ Open http://localhost:5000 in your browser")
    app.run(debug=True, port=5000)
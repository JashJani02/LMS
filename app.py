import os
from flask import Flask, render_template_string, request, redirect, url_for, session, send_file, jsonify
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import io

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_elearning_platform'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Mock Database ---
data = {
    'subjects': ['WT', 'Mathematics-4', 'DSA', 'FDST'],
    'content': {
        'WT': {'videos': [], 'materials': []},
        'Mathematics-4': {'videos': [], 'materials': []},
        'DSA': {'videos': [], 'materials': []},
        'FDST': {'videos': [], 'materials': []},
    },
    'users': {
        '20230101001': {'gr': '123456', 'role': 'student', 'watched': set()},
        '99999999999': {'gr': '000000', 'role': 'faculty'}
    }
}

# --- HTML Template ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Marwadi University - FODS ICT</title>
    <style>
        body { font-family: 'Courier New', monospace; margin: 0; background: #f4f4f4; }
        header { background: #41bfe9; color: white; padding: 1rem; text-align: center; position: relative; }
        .container { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 80vh; padding: 20px; }
        
        .box { background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 320px; }
        input[type="text"], input[type="password"], input[type="file"], select { 
            width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ccc; border-radius: 20px; box-sizing: border-box;
        }
        .btn { 
            width: 100%; padding: 12px; background: #4ca5af; color: white; border: none; 
            border-radius: 20px; cursor: pointer; font-weight: bold; margin-top: 10px; font-size: 1rem;
        }
        .btn:hover { background: #333; }

        .dropdown { position: relative; display: inline-block; }
        .dropbtn { background: black; color: white; padding: 12px 24px; border-radius: 10px; cursor: pointer; font-size: 1.1rem; }
        .dropdown-content { display: none; position: absolute; background: white; min-width: 200px; box-shadow: 0 8px 16px rgba(0,0,0,0.2); z-index: 10; border-radius: 10px; }
        .dropdown-content a { color: black; padding: 12px 16px; text-decoration: none; display: block; border-bottom: 1px solid #eee; }
        .dropdown:hover .dropdown-content { display: block; }

        .tabs { display: flex; justify-content: center; background: #eee; border-bottom: 1px solid #ccc; }
        .tab-btn { padding: 15px 30px; cursor: pointer; border: none; background: none; font-family: inherit; font-weight: bold; }
        .tab-btn.active { border-bottom: 3px solid #41bfe9; color: #41bfe9; }
        .content-area { padding: 20px; max-width: 800px; margin: auto; background: white; min-height: 400px; width: 100%; box-sizing: border-box;}

        .item { border-bottom: 1px solid #eee; padding: 15px 0; display: flex; flex-direction: column; gap: 10px; position: relative; }
        video { width: 100%; border-radius: 10px; background: #000; }
        .progress-bar { width: 100%; background: #ddd; border-radius: 10px; height: 20px; margin: 20px 0; position: relative; }
        .progress-fill { background: #4ca5af; height: 100%; border-radius: 10px; transition: width 0.3s; }
        .nav-links { position: absolute; top: 50%; right: 20px; transform: translateY(-50%); }
        .nav-links a { color: white; text-decoration: none; font-size: 0.9rem; margin-left: 15px; border: 1px solid white; padding: 5px 10px; border-radius: 5px; }
        
        /* Faculty Controls */
        .controls { position: absolute; top: 10px; right: 0; display: flex; gap: 5px; }
        .ctrl-btn { font-size: 0.7rem; padding: 4px 8px; border-radius: 5px; border: none; cursor: pointer; color: white; font-family: inherit; }
        .btn-edit { background: #41bfe9; }
        .btn-del { background: #ff4444; }

        /* Modal Style */
        .modal { display: none; position: fixed; z-index: 100; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); align-items: center; justify-content: center; }
        .modal-content { background: white; padding: 2rem; border-radius: 15px; width: 90%; max-width: 400px; }
        
        .error-msg { color: #ff4444; text-align: center; font-size: 0.9rem; margin-top: 10px; }
        .hint { font-size: 0.7rem; color: #777; text-align: center; display: block; margin-top: 5px; }
    </style>
</head>
<body>

    <header>
        <h1>Marwadi University <br> FODS-ICT</h1>
        {% if session.get('user') %}
            <div class="nav-links">
                <span style="font-size: 0.8rem">ID: {{ session['user'] }}</span>
                <a href="{{ url_for('logout') }}">Logout</a>
            </div>
        {% endif %}
    </header>

    <div class="container">
        {% if view == 'login' %}
        <div class="box">
            <h2 style="text-align:center">LOGIN</h2>
            <form method="POST">
                <label>Enrollment Number</label>
                <input type="text" name="enrollment" placeholder="Enter Enrollment No." required>
                <label>GR Number</label>
                <input type="password" name="gr" placeholder="Enter GR No." required>
                <button type="submit" class="btn">Login</button>
            </form>
            {% if error %}<p class="error-msg">{{ error }}</p>{% endif %}
            <div style="margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;">
                <span class="hint">Testing Credentials:</span>
                <span class="hint">Student: 20230101001 / 123456</span>
                <span class="hint">Faculty: 99999999999 / 000000</span>
            </div>
        </div>

        {% elif view == 'main' %}
        <h2 style="text-align:center">WELCOME</h2>
        <b style="text-align:center">Department of ICT - Semester 4</b>
        <div class="dropdown" style="margin-top: 20px;">
            <button class="dropbtn">Select Subject</button>
            <div class="dropdown-content">
                {% for sub in subjects %}
                <a href="{{ url_for('subject_view', sub_name=sub) }}">{{ sub }}</a>
                {% endfor %}
            </div>
        </div>

        {% elif view == 'subject' %}
        <div style="width: 100%; max-width: 900px;">
            <div style="text-align: center; margin-bottom: 20px;">
                <a href="{{ url_for('index') }}" style="text-decoration: none; color: #41bfe9;">← Back to Subjects</a>
                <h2>{{ sub_name }}</h2>
            </div>
            
            <div class="tabs">
                <button id="tab-videos" class="tab-btn active" onclick="showSection('videos')">Videos</button>
                <button id="tab-materials" class="tab-btn" onclick="showSection('materials')">Materials</button>
                {% if role == 'student' %}
                <button id="tab-progress" class="tab-btn" onclick="showSection('progress')">Progress</button>
                {% endif %}
            </div>

            <div class="content-area">
                <div id="sec-videos">
                    <h3>Course Videos</h3>
                    {% if role == 'faculty' %}
                    <form action="{{ url_for('upload_content', sub_name=sub_name, type='video') }}" method="POST" enctype="multipart/form-data" class="box" style="width:100%; margin-bottom:20px; box-shadow: none; border: 1px dashed #ccc;">
                        <input type="text" name="title" placeholder="Video Title" required>
                        <input type="file" name="file" accept="video/*" required>
                        <button type="submit" class="btn">Upload Video</button>
                    </form>
                    {% endif %}
                    
                    {% for v in content.videos %}
                    <div class="item">
                        <strong>{{ v.title }}</strong>
                        {% if role == 'faculty' %}
                        <div class="controls">
                            <button class="ctrl-btn btn-edit" onclick="editContent('{{ sub_name }}', 'video', {{ loop.index0 }}, '{{ v.title }}')">Edit</button>
                            <button class="ctrl-btn btn-del" onclick="deleteContent('{{ sub_name }}', 'video', {{ loop.index0 }})">Delete</button>
                        </div>
                        {% endif %}
                        <video controls onplay="markWatched('{{ sub_name }}', '{{ loop.index0 }}')">
                            <source src="{{ url_for('serve_file', filename=v.filename) }}" type="video/mp4">
                        </video>
                        {% if role == 'student' %}
                            <span id="status-{{ loop.index0 }}" style="font-size: 0.8rem; font-weight: bold;">
                                {% if loop.index0|string in watched %} ✅ Watched {% else %} 🕒 Not watched {% endif %}
                            </span>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>

                <div id="sec-materials" style="display:none;">
                    <h3>Study Materials</h3>
                    {% if role == 'faculty' %}
                    <form action="{{ url_for('upload_content', sub_name=sub_name, type='material') }}" method="POST" enctype="multipart/form-data" class="box" style="width:100%; margin-bottom:20px; box-shadow: none; border: 1px dashed #ccc;">
                        <input type="text" name="title" placeholder="Material Title" required>
                        <input type="file" name="file" required>
                        <button type="submit" class="btn">Upload Material</button>
                    </form>
                    {% endif %}
                    
                    {% for m in content.materials %}
                    <div class="item" style="padding-right: 120px;">
                        <a href="{{ url_for('serve_file', filename=m.filename) }}" target="_blank">📄 {{ m.title }}</a>
                        {% if role == 'faculty' %}
                        <div class="controls">
                            <button class="ctrl-btn btn-edit" onclick="editContent('{{ sub_name }}', 'material', {{ loop.index0 }}, '{{ m.title }}')">Edit</button>
                            <button class="ctrl-btn btn-del" onclick="deleteContent('{{ sub_name }}', 'material', {{ loop.index0 }})">Delete</button>
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>

                {% if role == 'student' %}
                <div id="sec-progress" style="display:none;">
                    <h3>Your Progress</h3>
                    <div class="progress-bar"><div class="progress-fill" style="width: {{ progress }}%;"></div></div>
                    <p style="text-align:center">{{ progress }}% Completed</p>
                    
                    {% if progress >= 100 and content.videos|length > 0 %}
                    <div style="text-align:center; margin-top:20px; background: #e8f5e9; padding: 20px; border-radius: 10px;">
                        <p style="color:green; font-weight: bold;">Course Completed!</p>
                        <button onclick="openCertModal()" class="btn" style="width: auto; padding: 10px 30px;">Download Certificate</button>
                    </div>
                    {% endif %}
                </div>
                {% endif %}
            </div>
        </div>

        <!-- Certificate Modal -->
        <div id="certModal" class="modal">
            <div class="modal-content">
                <h3>Certificate Details</h3>
                <p style="font-size: 0.8rem; color: #666;">Please confirm your details for the certificate.</p>
                <form id="certForm" action="{{ url_for('get_certificate', sub_name=sub_name) }}" method="GET">
                    <label>Full Name</label>
                    <input type="text" name="full_name" placeholder="As it should appear on PDF" required>
                    <label>Confirm Enrollment</label>
                    <input type="text" name="confirm_enrollment" value="{{ session['user'] }}" required>
                    <div style="display:flex; gap:10px; margin-top:10px;">
                        <button type="button" class="btn" style="background:#666" onclick="closeCertModal()">Cancel</button>
                        <button type="submit" class="btn">Generate PDF</button>
                    </div>
                </form>
            </div>
        </div>
        {% endif %}
    </div>

    <script>
        function showSection(id) {
            document.getElementById('sec-videos').style.display = id === 'videos' ? 'block' : 'none';
            document.getElementById('sec-materials').style.display = id === 'materials' ? 'block' : 'none';
            if(document.getElementById('sec-progress')) document.getElementById('sec-progress').style.display = id === 'progress' ? 'block' : 'none';
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById('tab-' + id).classList.add('active');
        }

        function markWatched(sub, idx) {
            fetch(`/watch/${sub}/${idx}`, {method: 'POST'})
            .then(res => res.json())
            .then(data => {
                if(data.status === 'success') {
                    const el = document.getElementById(`status-${idx}`);
                    if(el) el.innerHTML = "✅ Watched";
                }
            });
        }

        // Faculty Content Management
        function editContent(sub, type, idx, oldTitle) {
            const newTitle = prompt("Enter new title:", oldTitle);
            if (newTitle && newTitle !== oldTitle) {
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = `/edit_content/${sub}/${type}/${idx}`;
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'new_title';
                input.value = newTitle;
                form.appendChild(input);
                document.body.appendChild(form);
                form.submit();
            }
        }

        function deleteContent(sub, type, idx) {
            if (confirm("Are you sure you want to delete this item? This action cannot be undone.")) {
                window.location.href = `/delete_content/${sub}/${type}/${idx}`;
            }
        }

        function openCertModal() { document.getElementById('certModal').style.display = 'flex'; }
        function closeCertModal() { document.getElementById('certModal').style.display = 'none'; }
    </script>
</body>
</html>
"""

# --- Helper Functions ---

def generate_certificate_pdf(student_name, enrollment, subject):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    p.setStrokeColorRGB(0.2, 0.5, 0.6)
    p.setLineWidth(5)
    p.rect(0.5*inch, 0.5*inch, width-inch, height-inch)
    p.setFont("Helvetica-Bold", 30)
    p.drawCentredString(width/2, height - 2*inch, "CERTIFICATE OF COMPLETION")
    p.setFont("Helvetica", 18)
    p.drawCentredString(width/2, height - 3*inch, "This is to certify that")
    p.setFont("Helvetica-Bold", 24)
    p.drawCentredString(width/2, height - 3.8*inch, str(student_name).upper())
    p.setFont("Helvetica", 16)
    p.drawCentredString(width/2, height - 4.5*inch, f"Enrollment: {enrollment}")
    p.drawCentredString(width/2, height - 5.5*inch, "has successfully completed the course")
    p.setFont("Helvetica-Bold", 22)
    p.drawCentredString(width/2, height - 6.2*inch, subject)
    p.setFont("Helvetica", 14)
    p.drawCentredString(width/2, height - 8*inch, "Issued by Marwadi University - FODS ICT Department")
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- Routes ---

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user' in session:
        return render_template_string(HTML_TEMPLATE, view='main', subjects=data['subjects'])
    error = None
    if request.method == 'POST':
        en = request.form.get('enrollment', '').strip()
        gr = request.form.get('gr', '').strip()
        if en in data['users'] and data['users'][en]['gr'] == gr:
            session['user'] = en
            session['role'] = data['users'][en]['role']
            return redirect(url_for('index'))
        error = "Invalid Enrollment or GR Number."
    return render_template_string(HTML_TEMPLATE, view='login', error=error)

@app.route('/subject/<sub_name>')
def subject_view(sub_name):
    if 'user' not in session: return redirect(url_for('index'))
    user_id, role = session['user'], session['role']
    content = data['content'].get(sub_name, {'videos': [], 'materials': []})
    progress, watched_indices = 0, []
    if role == 'student':
        watched = data['users'][user_id]['watched']
        current_sub_watched = [int(w.split(':')[1]) for w in watched if w.startswith(f"{sub_name}:")]
        watched_indices = [str(i) for i in current_sub_watched]
        if content['videos']:
            progress = int((len(current_sub_watched) / len(content['videos'])) * 100)
    return render_template_string(HTML_TEMPLATE, view='subject', sub_name=sub_name, content=content, role=role, progress=progress, watched=watched_indices)

@app.route('/upload/<sub_name>/<type>', methods=['POST'])
def upload_content(sub_name, type):
    if session.get('role') != 'faculty': return "Unauthorized", 403
    title, file = request.form.get('title'), request.files.get('file')
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        key = 'videos' if type == 'video' else 'materials'
        data['content'][sub_name][key].append({'title': title, 'filename': filename})
    return redirect(url_for('subject_view', sub_name=sub_name))

@app.route('/edit_content/<sub_name>/<type>/<int:idx>', methods=['POST'])
def edit_content(sub_name, type, idx):
    if session.get('role') != 'faculty': return "Unauthorized", 403
    new_title = request.form.get('new_title')
    key = 'videos' if type == 'video' else 'materials'
    if 0 <= idx < len(data['content'][sub_name][key]):
        data['content'][sub_name][key][idx]['title'] = new_title
    return redirect(url_for('subject_view', sub_name=sub_name))

@app.route('/delete_content/<sub_name>/<type>/<int:idx>')
def delete_content(sub_name, type, idx):
    if session.get('role') != 'faculty': return "Unauthorized", 403
    key = 'videos' if type == 'video' else 'materials'
    if 0 <= idx < len(data['content'][sub_name][key]):
        item = data['content'][sub_name][key].pop(idx)
        # Attempt to delete physical file
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], item['filename']))
        except:
            pass
    return redirect(url_for('subject_view', sub_name=sub_name))

@app.route('/watch/<sub_name>/<int:idx>', methods=['POST'])
def watch_video(sub_name, idx):
    if 'user' not in session: return jsonify({'status': 'fail'}), 401
    if session.get('role') == 'student':
        data['users'][session['user']]['watched'].add(f"{sub_name}:{idx}")
    return jsonify({'status': 'success'})

@app.route('/files/<filename>')
def serve_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(file_path) if os.path.exists(file_path) else ("File not found", 404)

@app.route('/certificate/<sub_name>')
def get_certificate(sub_name):
    if 'user' not in session: return redirect(url_for('index'))
    user_id = session['user']
    full_name = request.args.get('full_name', 'Student')
    confirm_en = request.args.get('confirm_enrollment', user_id)
    
    total_videos = len(data['content'][sub_name]['videos'])
    watched = [w for w in data['users'][user_id]['watched'] if w.startswith(f"{sub_name}:")]
    if total_videos > 0 and len(watched) >= total_videos:
        pdf_buffer = generate_certificate_pdf(full_name, confirm_en, sub_name)
        return send_file(pdf_buffer, download_name=f"Certificate_{sub_name}.pdf", as_attachment=True)
    return "Course not completed", 400

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)

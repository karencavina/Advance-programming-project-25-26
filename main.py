from flask import Flask, render_template, request, redirect, url_for, send_from_directory, abort, flash
from werkzeug.utils import secure_filename 
from werkzeug.exceptions import RequestEntityTooLarge
import os
import module1
#import module3
from graph import *

STATE = {
    "loaded": False,
    "obo": None,
    "gaf": None,
    "graph": None,
    'data': None
}

# flask set up 
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for flash messages

# paths / folders 
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 40 MB limit
app.config['ALLOWED_EXTENSIONS'] = {'.obo','.gaf','.gaf.gz'}

def allowed_file(filename):
    if not filename:
        return False
    else:
        name=  filename.lower()
    return name.endswith(".obo") or name.endswith(".gaf") or name.endswith(".gaf.gz")

# Ensure upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# handle file size limit error
@app.errorhandler(RequestEntityTooLarge)
def handle_file_size_error(e):
    flash("File is too large. Maximum allowed size is 200 MB.", "error")
    return redirect(url_for("upload"))



#Routs 
@app.route('/')
def home():
    return render_template('home.html', state=STATE)


@app.route('/visualize')
def visualize():
    # Handle visualization logic here
    return render_template('visualize.html',state=STATE)

@app.route('/search')
def search():    
    # Handle search logic here
    return render_template('search.html', state=STATE)


@app.route('/upload', methods=['GET','POST'])
def upload():
    if request.method == "GET":
        return render_template("upload.html", state=STATE)

    obo = request.files.get("obo_file")
    gaf = request.files.get("gaf_file")

    if not obo or not gaf or obo.filename == "" or gaf.filename == "":
        flash("Please upload both OBO and GAF files.", "error")
        return redirect(url_for("upload"))
    if not allowed_file(obo.filename):
        flash("Invalid OBO file type. Please upload a .obo file.", "error")
        return redirect(url_for("upload"))
    if not allowed_file(gaf.filename):
        flash("Invalid GAF file type. Please upload a .gaf or .gaf.gz file.", "error")
        return redirect(url_for("upload"))

    obo_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(obo.filename))
    gaf_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(gaf.filename))

    obo.save(obo_path)
    gaf.save(gaf_path)
    try:
        data = module1.load_all(obo_path, gaf_path)
        graph = create_graph(data)

        STATE["data"] = data
        STATE["graph"] = graph
        STATE["obo"] = obo_path
        STATE["gaf"] = gaf_path
        STATE["loaded"] = True

        flash("Files uploaded successfully.", "success")
        return redirect(url_for("home"))
    except Exception as e:
        app.logger.exception("Error while processing uploaded files")
        flash(f"An error occurred while processing the files: {str(e)}", "error")
        return redirect(url_for("upload"))
    

'''
@app.route('/search')
def search():
    query = request.args.get('query', '')
    # Here you would add logic to search the ontology data store
    results = []  # Placeholder for search results
    return render_template('search.html', query=query, results=results)

@app.route('/visualize')
def visualize():
    return render_template('visualize.html')
'''

if __name__== '__main__': 
    app.run(debug=True)




    



